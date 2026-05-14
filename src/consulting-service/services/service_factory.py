"""
services/service_factory.py
────────────────────────────
Holds the singleton instances initialized in main.py.
Routes access them via get_rag_service() and get_embedder().
"""

import logging
from services.embedder            import Embedder
from services.llm_client             import LLMClient          # ← was LlamaClient
from services.rag_service         import RAGService
from services.agentic_rag_service import AgenticRAGService

logger = logging.getLogger("service_factory")

_embedder:    Embedder   | None = None
_rag_service: RAGService | None = None


def init_services(embedder: Embedder, llm: LLMClient) -> None:   # ← was llama
    """Called once from main.py lifespan to register instances."""
    global _embedder, _rag_service
    _embedder    = embedder
    _rag_service = RAGService(embedder, llm)                      # ← was llama
    logger.info("Services registered.")


def get_embedder() -> Embedder:
    if _embedder is None:
        raise RuntimeError("Services not initialized yet.")
    return _embedder


def get_rag_service() -> RAGService:
    if _rag_service is None:
        raise RuntimeError("Services not initialized yet.")
    return _rag_service
