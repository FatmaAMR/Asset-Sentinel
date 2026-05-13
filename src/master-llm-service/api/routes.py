from fastapi import APIRouter
from schemas.models import LLMRequest, LLMResponse
from services.llama_engine import LlamaEngine

router = APIRouter()
engine = LlamaEngine()

@router.post("/predict")
async def handle_inference(request: LLMRequest):
    # This service blindly follows instructions sent to it
    result = engine.generate_response(
        system_instruction=request.system_instruction,
        user_input=request.user_input,
        max_tokens=request.max_tokens,
        temp=request.temperature
    )
    return LLMResponse(generated_text=result)