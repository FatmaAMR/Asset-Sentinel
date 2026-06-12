"""
main.py
───────
Notification Service entry point.

Runs two things concurrently:
  1. FastAPI HTTP server  → serves the REST + SSE endpoints on port 8007
  2. RabbitMQ consumer    → listens on the alert queue and dispatches notifications
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# ── Path setup: local packages MUST win over parent src/ ──────────────────────
service_root = Path(__file__).resolve().parent
src_root     = str(service_root.parent)

# Purge any pre-existing src/ entry so it can't shadow local schemas/
while src_root in sys.path:
    sys.path.remove(src_root)

# Re-insert in correct priority order: local first, then src/
sys.path.insert(0, src_root)
sys.path.insert(0, str(service_root))

import aio_pika
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from schemas.models import AlertMessage
from services.NotificationDispatcher import NotificationDispatcher
from services.notification_rag_consumer import stop_all_consumers
from api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification_service")

dispatcher = NotificationDispatcher()


# ── RabbitMQ alert consumer (existing logic) ──────────────────────────────────

async def _run_alert_consumer() -> None:
    while True:
        try:
            logger.info("Connecting to RabbitMQ alert queue: %s", settings.RABBITMQ_ALERT_QUEUE)
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                queue   = await channel.declare_queue(settings.RABBITMQ_ALERT_QUEUE, durable=True)
                logger.info("[*] Waiting for alerts on %s …", settings.RABBITMQ_ALERT_QUEUE)

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            try:
                                data  = json.loads(message.body.decode())
                                alert = AlertMessage(**data)
                                logger.info("[!] Alert received: %s", alert.message_id)
                                await dispatcher.process_alert(alert)
                            except Exception as exc:
                                logger.exception("Failed to process alert message: %s", exc)

        except asyncio.CancelledError:
            logger.info("Alert consumer cancelled.")
            return
        except Exception as exc:
            logger.warning("Alert consumer error, retrying in 5 s: %s", exc)
            await asyncio.sleep(5)


# ── FastAPI lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer_task = asyncio.create_task(_run_alert_consumer(), name="alert-consumer")
    logger.info("Alert consumer task started.")
    yield
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    await stop_all_consumers()
    logger.info("Notification service shut down cleanly.")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "Notification Service",
    description = "Dispatches alerts and exposes RAG notification endpoints.",
    version     = "2.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(router)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host      = "0.0.0.0",
        port      = 8007,
        reload    = False,
        log_level = "info",
    )
    