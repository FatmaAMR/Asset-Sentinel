import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# Resolve the path to the src/.env file
# This assumes config.py is inside the src/ folder
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Points Pydantic to src/.env
        env_file = ENV_PATH,
        env_file_encoding = "utf-8",
        case_sensitive = False,
        extra = "ignore",
    )

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    # Using os.getenv as a secondary fallback if needed, 
    # though Pydantic handles this automatically from the env_file.
    chroma_path:       str = os.getenv("CHROMA_PATH", "./chroma_db")
    chroma_collection: str = os.getenv("CHROMA_COLLECTION", "maintenance_manuals")

    # ── Knowledge base ────────────────────────────────────────────────────────
    knowledge_folder:  str = os.getenv("KNOWLEDGE_FOLDER", "./knowledge")

    # ── Embedding model ───────────────────────────────────────────────────────
    embed_model:       str = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
    embed_batch_size:  int = int(os.getenv("EMBED_BATCH_SIZE", "64"))

    # ── Ollama / LLM ──────────────────────────────────────────────────────────
    ollama_url:        str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model:      str = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    llama_timeout:     int = int(os.getenv("LLAMA_TIMEOUT", "120"))

    # LLM generation options
    llm_temperature:   float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    llm_num_predict:   int   = int(os.getenv("LLM_NUM_PREDICT", "1024"))
    llm_num_ctx:       int   = int(os.getenv("LLM_NUM_CTX", "4096"))
    llm_repeat_penalty:float = float(os.getenv("LLM_REPEAT_PENALTY", "1.1"))

    # ── RAG ───────────────────────────────────────────────────────────────────
    rag_top_k:         int = int(os.getenv("RAG_TOP_K", "5"))
    
    # Web search fallback
    search_fallback:   bool  = os.getenv("SEARCH_FALLBACK", "True").lower() == "true"
    tavily_api_key:    str   = os.getenv("TAVILY_API_KEY", "")

    # ── API ───────────────────────────────────────────────────────────────────
    host:              str = os.getenv("HOST", "0.0.0.0")
    port:              int = int(os.getenv("PORT", "8000"))
    log_level:         str = os.getenv("LOG_LEVEL", "INFO")


@lru_cache
def get_settings() -> Settings:
    """Cached — only parsed once per process."""
    return Settings()


# Module-level singleton
settings = get_settings()