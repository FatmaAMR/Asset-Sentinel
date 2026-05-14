from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="The user prompt / input text")
    system_prompt: Optional[str] = Field(
        None, description="System instruction (role/persona)"
    )
    model: Optional[str] = Field(
        None,
        description="Override active model for this request. "
                    "Options: 'llama-3.2-1b', 'qwen-2.5'. "
                    "If None, uses the currently active model.",
    )
    max_tokens: int = Field(512, ge=1, le=4096)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    caller: Literal["querying", "consulting", "other"] = Field(
        "other", description="Which downstream service is calling"
    )


class GenerateResponse(BaseModel):
    text: str
    model_used: str
    tokens_generated: int
    caller: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SwitchModelRequest(BaseModel):
    model: str = Field(
        ..., description="Model key to switch to, e.g. 'llama-3.2-1b' or 'qwen-2.5'"
    )


class SwitchModelResponse(BaseModel):
    previous_model: str
    active_model: str
    message: str


class ModelListResponse(BaseModel):
    active_model: str
    available_models: list[str]
