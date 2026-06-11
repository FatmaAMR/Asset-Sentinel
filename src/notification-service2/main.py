from __future__ import annotations

import sys
from pathlib import Path
service_root = Path(__file__).resolve().parent
sys.path.insert(0, str(service_root))
sys.path.insert(1, str(service_root.parent))

import asyncio
import json
import logging
from contextlib import asynccontextmanager

import aio_pika
import uvicorn
from fastapi import FastAPI

from config import settings
from schemas.models import AlertMessage
from services.NotificationDispatcher import NotificationDispatcher
from services.notification_rag_consumer import stop_all_consumers
from api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification_service")

dispatcher = NotificationDispatcher()


async def _run_alert_consumer() -> None:
    while True:
        try:
            logger.info("Connecting to RabbitMQ alert queue: %s", settings.RABBITMQ_ALERT_QUEUE)
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                queue   = await channel.declare_queue(settings.RABBITMQ_ALERT_QUEUE, durable=True)
                logger.info("[*] Waiting for alerts on %s ...", settings.RABBITMQ_ALERT_QUEUE)
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


app = FastAPI(
    title       = "Notification Service",
    description = "Dispatches alerts and exposes RAG notification endpoints.",
    version     = "2.0.0",
    lifespan    = lifespan,
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host      = "0.0.0.0",
        port      = 8007,
        reload    = False,
        log_level = "info",
    )
