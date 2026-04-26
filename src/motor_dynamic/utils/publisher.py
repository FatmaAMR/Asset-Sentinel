"""
RabbitMQ publisher — wraps pika with:
  • durable exchange + queue declaration
  • persistent delivery mode (survives broker restart)
  • dead-letter exchange for failed messages
  • exponential back-off retry on publish error

Updated to publish dynamic FileRecord (no hardcoded field names).
"""

from __future__ import annotations

import logging
import time

import pika
import pika.exceptions
from pika.exchange_type import ExchangeType

from config.settings import settings
from schemas.models import MessageEnvelope

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    def __init__(self) -> None:
        self._connection = None
        self._channel    = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        params = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            virtual_host=settings.RABBITMQ_VHOST,
            credentials=pika.PlainCredentials(
                settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
            ),
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        logger.info(
            f"Connecting to RabbitMQ at "
            f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}"
        )
        self._connection = pika.BlockingConnection(params)
        self._channel    = self._connection.channel()

        # Dead-letter exchange + queue
        dlx = f"{settings.RABBITMQ_EXCHANGE}.dlx"
        self._channel.exchange_declare(exchange=dlx, exchange_type=ExchangeType.direct, durable=True)
        self._channel.queue_declare(queue=settings.RABBITMQ_DLX_QUEUE, durable=True)
        self._channel.queue_bind(
            queue=settings.RABBITMQ_DLX_QUEUE,
            exchange=dlx,
            routing_key=settings.RABBITMQ_ROUTING_KEY,
        )

        # Main exchange + queue
        self._channel.exchange_declare(
            exchange=settings.RABBITMQ_EXCHANGE,
            exchange_type=ExchangeType.direct,
            durable=True,
        )
        self._channel.queue_declare(
            queue=settings.RABBITMQ_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange":    dlx,
                "x-dead-letter-routing-key": settings.RABBITMQ_ROUTING_KEY,
            },
        )
        self._channel.queue_bind(
            queue=settings.RABBITMQ_QUEUE,
            exchange=settings.RABBITMQ_EXCHANGE,
            routing_key=settings.RABBITMQ_ROUTING_KEY,
        )
        logger.info(
            f"RabbitMQ ready — "
            f"exchange: '{settings.RABBITMQ_EXCHANGE}'  "
            f"queue: '{settings.RABBITMQ_QUEUE}'"
        )

    def close(self) -> None:
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
            if self._connection and not self._connection.is_closed:
                self._connection.close()
        except Exception as exc:
            logger.warning(f"Error closing RabbitMQ: {exc}")
        finally:
            self._channel    = None
            self._connection = None

    # ── Publish ───────────────────────────────────────────────────────────────

    def publish(self, envelope: MessageEnvelope) -> None:
        body  = envelope.to_bytes()
        rec   = envelope.record
        props = pika.BasicProperties(
            content_type  = "application/json",
            delivery_mode = 2,          # persistent
            message_id    = envelope.message_id,
            timestamp     = int(time.time()),
            headers = {
                "source":       envelope.source,
                "file_name":    rec.file_name,
                "file_index":   str(rec.file_index),
                "window_index": str(rec.window_index),
                "columns":      ",".join(rec.column_names),
            },
        )

        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                self._channel.basic_publish(
                    exchange=settings.RABBITMQ_EXCHANGE,
                    routing_key=settings.RABBITMQ_ROUTING_KEY,
                    body=body,
                    properties=props,
                )
                logger.debug(
                    f"Published {rec.file_name} "
                    f"window={rec.window_index} "
                    f"columns={rec.column_names}"
                )
                return
            except (
                pika.exceptions.AMQPConnectionError,
                pika.exceptions.StreamLostError,
                pika.exceptions.ChannelClosedByBroker,
            ) as exc:
                logger.warning(f"Publish attempt {attempt} failed: {exc}")
                if attempt < settings.MAX_RETRIES:
                    wait = 2 ** attempt
                    logger.info(f"Reconnecting in {wait}s…")
                    time.sleep(wait)
                    self.close()
                    self.connect()
                else:
                    raise
