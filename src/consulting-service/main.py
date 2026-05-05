"""
main.py
────────
Declares and wires all services (embedding model + LLM).
Routes access them via service_factory — no re-initialization there.
"""

import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()

from fastapi import FastAPI
from config                   import settings
from utils.logger             import setup_logging
from db.chroma_client         import get_chroma_collection
from services.pdf_loader      import load_pdfs
from services.embedder        import Embedder
from services.llama_client    import LlamaClient
from services.service_factory import init_services
from api.rag_router           import router as rag_router

setup_logging()
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Starting — initializing embedding model and LLM ===")

    # ── Declare all services here ─────────────────────────────────────────────
    collection = get_chroma_collection()
    embedder   = Embedder(collection)          # loads sentence-transformer model
    llama      = LlamaClient()                 # Ollama HTTP client


    # # Ingest PDFs from knowledge folder
    # chunks = load_pdfs(settings.knowledge_folder)
    # if chunks:
    #     result = embedder.build(chunks)
    #     logger.info("+%d new chunks | %d total",
    #                 result["chunks_added"], result["total_chunks"])
    # else:
    #     logger.warning("No PDFs found in '%s'. Upload via POST /rag/ingest",
    #                    settings.knowledge_folder)

    # Register into factory so routes can access them
    init_services(embedder, llama)

    logger.info("=== Service ready ===")
    yield
    logger.info("=== Shutting down ===")


app = FastAPI(
    title       = "Consulting Service",
    description = "RAG over maintenance PDF manuals",
    version     = "2.0.0",
    lifespan    = lifespan,
)

app.include_router(rag_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "consulting-service"}
