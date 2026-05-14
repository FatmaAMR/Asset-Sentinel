from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    default_model: str = "qwen2.5-1.5b"

    # key → ollama model tag (must match `ollama pull <tag>`)
    model_registry: Dict[str, str] = {
        "qwen2.5-1.5b": "qwen2.5:1.5b",
        "phi3-mini":     "phi3:mini",
        "gemma2-2b":     "gemma2:2b",
        "tinyllama":     "tinyllama",
    }

    default_max_tokens: int = 512
    default_temperature: float = 0.7

    ollama_base_url: str = "http://localhost:11434"

    db_url: str = "sqlite+aiosqlite:///./llm_service.db"
    admin_api_key: str = "gradteam"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()