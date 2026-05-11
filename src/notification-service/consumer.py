from __future__ import annotations

import logging
import json
import sys
import asyncio
import signal
import time
from pathlib import Path
from typing import Any, Dict

import pika
from pika.adapters.blocking_connection import BlockingChannel

# Add src to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Use your existing settings structure
from config.settings import settings
from services.logic import NotificationDispatcher
from schemas.models import AlertMessage

logger = logging.getLogger(__name__)

class NotificationConsumer:
    """Consumes alert messages and triggers the notification dispatcher."""

    def __init__(self):
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self.dispatcher = NotificationDispatcher()
        self.processed_count = 0
        self.failed_count = 0
        self._shutdown = False

    def connect(self) -> None:
        try:
            # Using the RABBITMQ_URL from your .env
            params = pika.URLParameters(settings.RABBITMQ_URL)
            params.heartbeat = 600
            params.blocked_connection_timeout = 300

            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._channel.basic_qos(prefetch_count=1)

            # Declare the exchange as TOPIC to match the system architecture
            self._channel.exchange_declare(
                exchange=settings.RABBITMQ_EXCHANGE,
                exchange_type='topic',
                durable=True,
            )
            
            # Use the specific Alert Queue and Routing Key from .env
            self._channel.queue_declare(
                queue=settings.RABBITMQ_ALERT_QUEUE,
                durable=True,
            )
            self._channel.queue_bind(
                exchange=settings.RABBITMQ_EXCHANGE,
                queue=settings.RABBITMQ_ALERT_QUEUE,
                routing_key=settings.RABBITMQ_ALERT_ROUTING_KEY,
            )

            logger.info(f"Notification Service connected to: {settings.RABBITMQ_ALERT_QUEUE}")
        except Exception as exc:
            logger.error(f"Failed to connect to Remote RabbitMQ: {exc}")
            raise

    def close(self) -> None:
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
            if self._connection and not self._connection.is_closed:
                self._connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as exc:
            logger.warning(f"Error closing RabbitMQ: {exc}")

    def start_consuming(self) -> None:
        if not self._channel:
            raise RuntimeError("Not connected to RabbitMQ")

        def callback(
            ch: BlockingChannel,
            method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties,
            body: bytes,
        ) -> None:
            try:
                # 1. Deserialize message
                data = json.loads(body)
                alert = AlertMessage(**data)
                
                logger.info(f"[{alert.message_id}] Received {alert.alert_level} for {alert.machine_id}")

                # 2. Process via Dispatcher (Async Bridge)
                # Since we use asyncio inside the dispatcher, we bridge it here
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.dispatcher.process_alert(alert))
                loop.close()

                self.processed_count += 1
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as exc:
                logger.error(f"Error processing alert: {exc}")
                self.failed_count += 1
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        try:
            self._channel.basic_consume(
                queue=settings.RABBITMQ_ALERT_QUEUE,
                on_message_callback=callback,
            )
            logger.info("Notification Service is listening for alerts...")

            while not self._shutdown:
                self._connection.process_data_events(time_limit=1)

        except Exception as exc:
            logger.error(f"Consumer error: {exc}")
            raise

    def stop_consuming(self) -> None:
        self._shutdown = True

def run_consumer() -> None:
    consumer = NotificationConsumer()

    def signal_handler(signum: int, frame: Any) -> None:
        logger.info("Received shutdown signal")
        consumer.stop_consuming()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        consumer.connect()
        consumer.start_consuming()
    except Exception as exc:
        logger.error(f"Notification Consumer failed: {exc}")
    finally:
        consumer.close()

if __name__ == "__main__":
    run_consumer()