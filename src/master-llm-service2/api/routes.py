from fastapi import APIRouter, HTTPException, Header, Depends
from schemas.llm_schemas import (
    GenerateRequest,
    GenerateResponse,
    SwitchModelRequest,
    SwitchModelResponse,
    ModelListResponse,
)
from services.inference import inference_service
from services.model_loader import loader
from db.model_registry import record_model_switch
from config.settings import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ------------------------------------------------------------------
# Dependency: verify admin API key
# ------------------------------------------------------------------

def verify_admin_key(x_admin_key: str = Header(...)):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin API key")


# ------------------------------------------------------------------
# Main inference endpoint — called by querying & consulting services
# ------------------------------------------------------------------

@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """
    Generate text using the active (or specified) LLM.

    Both the **querying service** and **consulting service** call this endpoint.

    - Set `caller` to `"querying"` or `"consulting"` for logging/tracing.
    - Pass `model` to override the active model for this single request.
    - Pass `system_prompt` to set a role/persona (e.g. "You are a financial advisor.").
    """
    try:
        return await inference_service.generate(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during generation")
        raise HTTPException(status_code=500, detail="Internal inference error")


# ------------------------------------------------------------------
# Model management endpoints (admin-only)
# ------------------------------------------------------------------

@router.post(
    "/admin/switch-model",
    response_model=SwitchModelResponse,
    dependencies=[Depends(verify_admin_key)],
)
async def switch_model(request: SwitchModelRequest) -> SwitchModelResponse:
    """
    Switch the active LLM at runtime without restarting the service.

    Requires header: `X-Admin-Key: <admin_api_key>`

    Example:
        curl -X POST http://localhost:8000/admin/switch-model \\
             -H "Content-Type: application/json" \\
             -H "X-Admin-Key: changeme" \\
             -d '{"model": "qwen-2.5"}'
    """
    if request.model not in settings.model_registry:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{request.model}'. "
                   f"Available: {list(settings.model_registry.keys())}",
        )

    previous = loader.current_model_name or "none"
    try:
        loader.load(request.model)
        await record_model_switch(request.model)
    except Exception as e:
        logger.exception("Failed to switch model")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")

    return SwitchModelResponse(
        previous_model=previous,
        active_model=request.model,
        message=f"Switched from '{previous}' to '{request.model}' successfully.",
    )


@router.get("/models", response_model=ModelListResponse)
def list_models() -> ModelListResponse:
    """Return all available model keys and which one is currently active."""
    return ModelListResponse(
        active_model=loader.current_model_name or settings.default_model,
        available_models=list(settings.model_registry.keys()),
    )
