"""
Lightweight HTTP API.

Start with:  uvicorn api.routes:app --reload --port 8000

GET  /health          — liveness probe
GET  /status          — registry summary (which files have been ingested)
POST /ingest/trigger  — kick off ingestion in background
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException

from db.connection import FileRegistry, get_session, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Motor Data Ingestion Service",
    description=(
        "Reads every CSV/TXT file from DATA_DIR and publishes windows to RabbitMQ. "
        "Change DATA_DIR in .env — no code changes required."
    ),
    version="3.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok"}


@app.get("/status", tags=["ops"])
def status():
    with get_session() as session:
        rows = session.query(FileRegistry).order_by(FileRegistry.id).all()
        return {
            "files_ingested":         len([r for r in rows if r.success]),
            "total_windows_published": sum(r.windows_published or 0 for r in rows),
            "files": [
                {
                    "file_key":          r.file_key,
                    "file_name":         r.file_name,
                    "windows_published": r.windows_published,
                    "ingested_at":       r.ingested_at.isoformat() if r.ingested_at else None,
                    "success":           r.success,
                    "error":             r.error_message,
                }
                for r in rows
            ],
        }


_running = False


@app.post("/ingest/trigger", tags=["ingestion"])
async def trigger(background_tasks: BackgroundTasks):
    global _running
    if _running:
        raise HTTPException(status_code=409, detail="Ingestion already running")
    background_tasks.add_task(_run)
    return {"message": "Ingestion started in background"}


async def _run():
    global _running
    _running = True
    try:
        from services.logic import IngestionService
        result = IngestionService().run()
        logger.info(f"Background ingestion complete: {result}")
    except Exception as exc:
        logger.exception(f"Background ingestion error: {exc}")
    finally:
        _running = False
