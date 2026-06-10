import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file          = ENV_PATH,
        env_file_encoding = "utf-8",
        case_sensitive    = False,
        extra             = "ignore",
    )

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    chroma_path:       str = os.getenv("CHROMA_PATH",       "./chroma_db")
    chroma_collection: str = os.getenv("CHROMA_COLLECTION", "maintenance_manuals")

    # ── Knowledge base ────────────────────────────────────────────────────────
    knowledge_folder:  str = os.getenv("KNOWLEDGE_FOLDER", "./knowledge")

    # ── Cohere embedding ──────────────────────────────────────────────────────
    # API key — required for all embedding calls.
    cohere_api_key:    str = os.getenv("COHERE_API_KEY", "")

    # embed-english-v3.0      — English-only, best accuracy
    # embed-multilingual-v3.0 — multilingual, use if docs are not English
    embed_model:       str = os.getenv("EMBED_MODEL", "embed-english-v3.0")

    # Max items per Cohere batch request (hard API cap is 96 — never exceed).
    embed_batch_size:  int = int(os.getenv("EMBED_BATCH_SIZE", "64"))

    # ── master-llm-service ────────────────────────────────────────────────────
    master_llm_url:    str = os.getenv("MASTER_LLM_URL",       "http://localhost:8000")
    master_llm_key:    str = os.getenv("MASTER_LLM_ADMIN_KEY", "changeme")
    llm_timeout:       int = int(os.getenv("LLM_TIMEOUT",      "120"))

    # ── RAG ───────────────────────────────────────────────────────────────────
    rag_top_k:         int = int(os.getenv("RAG_TOP_K", "5"))

    # Web search fallback
    search_fallback:   bool = os.getenv("SEARCH_FALLBACK", "True").lower() == "true"
    tavily_api_key:    str  = os.getenv("TAVILY_API_KEY", "")

    # ── RabbitMQ ──────────────────────────────────────────────────────────────
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqps://epnwrxps:FJDX9jCp6ng-bHYxHocDRsYbBqsJ6yP3@cow.rmq2.cloudamqp.com/epnwrxps")

    # ── API ───────────────────────────────────────────────────────────────────
    host:      str = os.getenv("HOST",      "0.0.0.0")
    port:      int = int(os.getenv("PORT",  "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


@lru_cache
def get_settings() -> Settings:
    """Cached — only parsed once per process."""
    return Settings()


settings = get_settings()
