"""
api/rag_router.py
──────────────────
FastAPI router — gets services from factory, never initializes anything.

  POST /rag/ask      → ask a question, get structured answer
  POST /rag/ingest   → upload a PDF into ChromaDB
  GET  /rag/status   → how many chunks are in the knowledge base
"""

import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File

from schemas.rag_schemas       import AskRequest, AskResponse, IngestResponse
from services.pdf_loader       import load_pdfs
from services.service_factory  import get_rag_service, get_embedder
from config                    import settings

logger        = logging.getLogger("rag_router")
router        = APIRouter(prefix="/rag", tags=["RAG"])
KNOWLEDGE_DIR = settings.knowledge_folder


@router.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        result = await get_rag_service().ask(body.question, top_k=body.top_k)
    except Exception as exc:
        logger.exception("RAG ask failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return AskResponse(
        question = result["question"],
        answer   = result["answer"],
        sources  = result["sources"],
        intent   = "RAG",
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    save_path = os.path.join(KNOWLEDGE_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())
    logger.info("Saved PDF: %s", save_path)

    try:
        embedder = get_embedder()
        chunks   = load_pdfs(KNOWLEDGE_DIR)
        if not chunks:
            return IngestResponse(
                status       = "no_content_found",
                chunks_added = 0,
                total_chunks = embedder.collection.count(),
            )
        result = embedder.build(chunks)
        return IngestResponse(
            status       = "ok",
            chunks_added = result["chunks_added"],
            total_chunks = result["total_chunks"],
        )
    except Exception as exc:
        logger.exception("Ingest failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status")
async def status():
    try:
        return {
            "status":       "ready",
            "total_chunks": get_embedder().collection.count(),
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}

from services.llm_client import LLMClient

@router.post("/switch-model")
async def switch_model(model_key: str):
    """
    Tell master-llm-service to switch its active model.
    Example: POST /rag/switch-model?model_key=qwen2.5-1.5b
    """
    llm = LLMClient()
    try:
        result = await llm.switch_model(model_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))