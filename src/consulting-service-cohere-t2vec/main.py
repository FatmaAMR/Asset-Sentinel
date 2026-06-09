"""
main.py
────────
Boots the FastAPI app.

Startup order
─────────────
1. Load global KB PDF chunks from ./knowledge into the PdfEmbedder
   (collection: settings.chroma_collection — Cohere text only, 1024-d).
2. Register the PdfEmbedder + LLMClient with service_factory.
   Per-machine SensorEmbedders are created lazily on first ingest-window/diagnose.
"""
import torch
import numpy as np

torch.manual_seed(42)
np.random.seed(42)
torch.use_deterministic_algorithms(True)
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from config                    import settings
from utils.logger              import setup_logging
from db.chroma_client          import get_chroma_collection
from services.pdf_loader       import load_pdfs
from services.embedder         import PdfEmbedder
from services.llm_client       import LLMClient
from services.service_factory  import init_services
from api.rag_router            import router as rag_router
from services.notification_bus import close_publisher

setup_logging()
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Starting — initialising PDF embedder and LLM ===")

    # Global KB — Cohere text embeddings only (1024-d)
    collection  = get_chroma_collection(settings.chroma_collection)
    pdf_embedder = PdfEmbedder(collection)
    llm          = LLMClient()

    # Ingest any PDFs already in the knowledge folder
    chunks = load_pdfs(settings.knowledge_folder)
    if chunks:
        pdf_embedder.build(chunks)
        logger.info("Startup ingest: %d PDF chunks loaded into global KB.", len(chunks))
    else:
        logger.info("No PDFs found in knowledge folder — global KB is empty.")

    init_services(pdf_embedder, llm)
    logger.info(
        "=== Service ready — global KB: '%s' | sensor collections created on demand ===",
        settings.chroma_collection,
    )
    yield
    await close_publisher()
    logger.info("=== Shutting down ===")


app = FastAPI(
    title       = "Consulting Service",
    description = (
        "RAG over maintenance PDF manuals (global KB) + "
        "per-machine sensor window similarity search (TS2Vec fused embeddings)"
    ),
    version     = "4.0.0",
    lifespan    = lifespan,
)

app.include_router(rag_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5173"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "consulting-service", "version": "4.0.0"}
