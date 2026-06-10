"""
services/service_factory.py
────────────────────────────
Singleton registry for all service instances.

Two distinct embedding pipelines are registered here:

  PdfEmbedder   — global knowledge-base (Cohere text only, 1024-d)
                  collection: settings.chroma_collection  ("maintenance_manuals")

  SensorEmbedder — per-machine sensor windows (Cohere text + TS2Vec, 1280-d)
                  collection: "sensor_{machine_id}"

Access pattern:
  get_pdf_embedder()              → global KB PdfEmbedder
  get_sensor_embedder(machine_id) → per-machine SensorEmbedder  (auto-created)
  get_embedder(machine_id=None)   → back-compat: None→pdf, str→sensor
  get_rag_service()               → RAGService over the global KB
  get_diagnose_service(machine_id)→ DiagnoseService with SensorEmbedder
"""

import logging
from services.embedder            import PdfEmbedder, SensorEmbedder
from services.llm_client          import LLMClient
from services.rag_service         import RAGService
from services.diagnose_service    import DiagnoseService
from services.agentic_rag_service import AgenticRAGService
from db.chroma_client             import get_chroma_collection

logger = logging.getLogger("service_factory")

# ── Singletons ─────────────────────────────────────────────────────────────────

_pdf_embedder:  PdfEmbedder  | None = None
_rag_service:   RAGService   | None = None
_llm:           LLMClient    | None = None

# Per-machine caches  {machine_id: instance}
_sensor_embedders:        dict[str, SensorEmbedder]  = {}
_machine_diagnose_services: dict[str, DiagnoseService] = {}


def init_services(pdf_embedder: PdfEmbedder, llm: LLMClient) -> None:
    """Called once from main.py lifespan to register the default instances."""
    global _pdf_embedder, _rag_service, _llm
    _pdf_embedder = pdf_embedder
    _llm          = llm
    _rag_service  = RAGService(pdf_embedder, llm)
    logger.info(
        "Services initialised — global KB collection: '%s'.",
        pdf_embedder.collection.name,
    )


# ── PDF / global KB ────────────────────────────────────────────────────────────

def get_pdf_embedder() -> PdfEmbedder:
    """Return the global KB PdfEmbedder (Cohere text only)."""
    if _pdf_embedder is None:
        raise RuntimeError("Services not initialised yet — call init_services() first.")
    return _pdf_embedder


# ── Sensor / per-machine ───────────────────────────────────────────────────────

def get_sensor_embedder(machine_id: str) -> SensorEmbedder:
    """
    Return the SensorEmbedder for a specific machine.

    Each machine gets its own ChromaDB collection ("sensor_{machine_id}"),
    created on first use.  The collection uses cosine distance and stores
    1280-d fused vectors (Cohere 1024-d + TS2Vec 256-d).
    """
    if machine_id not in _sensor_embedders:
        collection_name = f"sensor_{machine_id}"
        logger.info(
            "Auto-creating sensor collection '%s' for machine '%s'.",
            collection_name, machine_id,
        )
        collection = get_chroma_collection(collection_name)
        _sensor_embedders[machine_id] = SensorEmbedder(collection)

    return _sensor_embedders[machine_id]


# ── Back-compat: get_embedder(machine_id=None) ─────────────────────────────────

def get_embedder(machine_id: str | None = None):
    """
    Backwards-compatible accessor used by existing router code.

    machine_id is None  → returns PdfEmbedder  (global KB)
    machine_id is str   → returns SensorEmbedder (per-machine)

    New code should call get_pdf_embedder() or get_sensor_embedder() directly.
    """
    if machine_id is None:
        return get_pdf_embedder()
    return get_sensor_embedder(machine_id)


# ── RAG (global KB) ────────────────────────────────────────────────────────────

def get_rag_service() -> RAGService:
    if _rag_service is None:
        raise RuntimeError("Services not initialised yet.")
    return _rag_service


# ── LLM ────────────────────────────────────────────────────────────────────────

def get_llm() -> LLMClient:
    if _llm is None:
        raise RuntimeError("Services not initialised yet.")
    return _llm


# ── Diagnose (per-machine) ─────────────────────────────────────────────────────

def get_diagnose_service(machine_id: str) -> DiagnoseService:
    """
    Return the DiagnoseService for a specific machine.
    Uses a SensorEmbedder so sensor similarity searches run in the fused
    1280-d space — not in the global PDF collection.
    """
    if machine_id not in _machine_diagnose_services:
        sensor_emb = get_sensor_embedder(machine_id)
        llm        = get_llm()
        _machine_diagnose_services[machine_id] = DiagnoseService(sensor_emb, llm)
        logger.info("DiagnoseService created for machine '%s' (sensor collection).", machine_id)

    return _machine_diagnose_services[machine_id]
