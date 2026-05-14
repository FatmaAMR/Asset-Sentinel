from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routes import router
from config.settings import settings
from services.model_loader import loader
from db.model_registry import init_db, record_model_switch  # ← add
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting master-llm-service, loading default model: {settings.default_model}")

    await init_db()                                          # ← creates DB + table
    logger.info("Database ready")

    loader.load(settings.default_model)

    await record_model_switch(                               # ← log startup model
        settings.default_model,
        switched_by="startup"
    )
    logger.info(f"Active model: {settings.default_model}")

    yield

    logger.info("Shutting down master-llm-service")


app = FastAPI(
    title="Master LLM Service",
    description="Central LLM gateway with swappable models (Llama, Qwen)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "active_model": loader.current_model_name,
    }