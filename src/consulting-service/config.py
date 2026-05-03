"""
config.py
──────────
Single source of truth for all service settings.
Reads from environment variables / .env file automatically.

Usage anywhere in the project:
    from config import settings
    print(settings.ollama_model)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file        = ".env",
        env_file_encoding = "utf-8",
        case_sensitive  = False,
        extra           = "ignore",
    )

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    chroma_path:       str = "./chroma_db"
    chroma_collection: str = "maintenance_manuals"

    # ── Knowledge base ────────────────────────────────────────────────────────
    knowledge_folder:  str = "./knowledge"

    # ── Embedding model ───────────────────────────────────────────────────────
    embed_model:       str = "all-MiniLM-L6-v2"
    embed_batch_size:  int = 64

    # ── Ollama / LLM ──────────────────────────────────────────────────────────
    ollama_url:        str = "http://localhost:11434"
    ollama_model:      str = "qwen2.5:1.5b"
    llama_timeout:     int = 120

    # LLM generation options
    llm_temperature:   float = 0.1
    llm_num_predict:   int   = 1024
    llm_num_ctx:       int   = 4096
    llm_repeat_penalty:float = 1.1

    # ── RAG ───────────────────────────────────────────────────────────────────
    rag_top_k:         int = 5
    
    # Web search fallback
    search_fallback:    bool  = True
    tavily_api_key:     str   = ""

    # ── API ───────────────────────────────────────────────────────────────────
    host:              str = "0.0.0.0"
    port:              int = 8002
    log_level:         str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Cached — only parsed once per process."""
    return Settings()


# Module-level singleton — import this everywhere
settings = get_settings()
