import logging
from schemas.llm_schemas import GenerateRequest, GenerateResponse
from services.model_router import router as model_router
from services.model_loader import loader

logger = logging.getLogger(__name__)


class InferenceService:
    """
    High-level service called by API routes.
    Handles model resolution, loading, and generation in one place.
    """

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        # 1. Resolve which model key to use
        model_key = model_router.resolve(request.model)

        # 2. Ensure that model is loaded (swap if needed)
        model_router.ensure_loaded(model_key)

        logger.info(
            f"[{request.caller}] Generating with model='{model_key}' "
            f"max_tokens={request.max_tokens} temp={request.temperature}"
        )

        # 3. Run generation
        text, tokens_generated = loader.generate(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        logger.info(f"[{request.caller}] Generated {tokens_generated} tokens.")

        return GenerateResponse(
            text=text,
            model_used=model_key,
            tokens_generated=tokens_generated,
            caller=request.caller,
        )


inference_service = InferenceService()
