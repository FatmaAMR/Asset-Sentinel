"""
RabbitMQ publisher for motor_dynamic.
Publishes MessageEnvelope to the motor.raw queue.
"""

from __future__ import annotations

import logging
from typing import Any, Dict
import sys
from pathlib import Path

import pika
from pika.adapters.blocking_connection import BlockingChannel

# Add src to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import settings
from schemas.models import MessageEnvelope

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """Publishes sensor data messages to RabbitMQ."""

    def __init__(self):
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self.published_count = 0

    def connect(self) -> None:
        try:
            params = pika.URLParameters(settings.RABBITMQ_URL)
            params.heartbeat = 600
            params.blocked_connection_timeout = 300
            params.connection_attempts = 3
            params.retry_delay = 2

            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()

            # Declare the exchange and queue
            self._channel.exchange_declare(
                exchange=settings.RABBITMQ_EXCHANGE,
                exchange_type='direct',
                durable=True,
            )
            self._channel.queue_declare(
                queue=settings.RABBITMQ_QUEUE,
                durable=True,
            )
            self._channel.queue_bind(
                exchange=settings.RABBITMQ_EXCHANGE,
                queue=settings.RABBITMQ_QUEUE,
                routing_key=settings.RABBITMQ_ROUTING_KEY,
            )

            logger.info(f"Connected to RabbitMQ and declared queue: {settings.RABBITMQ_QUEUE}")
        except Exception as exc:
            logger.error(f"Failed to connect to RabbitMQ: {exc}")
            raise

    def publish(self, envelope: MessageEnvelope) -> None:
        if not self._channel:
            raise RuntimeError("Not connected to RabbitMQ")

        try:
            self._channel.basic_publish(
                exchange=settings.RABBITMQ_EXCHANGE,
                routing_key=settings.RABBITMQ_ROUTING_KEY,
                body=envelope.to_bytes(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    message_id=envelope.message_id,
                    timestamp=int(envelope.timestamp),
                ),
            )
            self.published_count += 1
            logger.debug(f"Published message {envelope.message_id}")
        except Exception as exc:
            logger.error(f"Failed to publish message {envelope.message_id}: {exc}")
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
        finally:
            self._channel = None
            self._connection = None

    def get_stats(self) -> Dict[str, Any]:
        return {"published": self.published_count}