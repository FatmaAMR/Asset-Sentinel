"""
RabbitMQ consumer for forecasting-service.
Consumes MessageEnvelope from motor.raw queue and processes via pipeline.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Callable
import sys
from pathlib import Path
import signal
import time

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError, AMQPChannelError

# Add src to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from pipeline import ProcessingPipeline
from schemas.models import MessageEnvelope

logger = logging.getLogger(__name__)


class SensorConsumer:
    """Consumes sensor data messages from RabbitMQ and processes them."""

    def __init__(self):
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self.pipeline = ProcessingPipeline()
        self.processed_count = 0
        self.failed_count = 0
        self._shutdown = False

    def connect(self) -> None:  # Added missing method
        try:
            params = pika.URLParameters(settings.RABBITMQ_URL)
            params.heartbeat = 600
            params.blocked_connection_timeout = 300
            params.connection_attempts = 3
            params.retry_delay = 2

            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._channel.basic_qos(prefetch_count=1)

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

    def close(self) -> None:  # Added missing method
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
                # Deserialize message
                envelope = MessageEnvelope.from_bytes(body)
                logger.debug(f"[{envelope.message_id}] Received message")

                # Process via pipeline
                result = self.pipeline.process(envelope.to_dict())

                if result.get("success"):
                    self.processed_count += 1
                    logger.info(f"[{envelope.message_id}] Successfully processed")
                else:
                    self.failed_count += 1
                    logger.error(f"[{envelope.message_id}] Processing failed: {result.get('error')}")

                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as exc:
                logger.error(f"Error processing message: {exc}")
                self.failed_count += 1
                # Reject and requeue message
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        try:
            self._channel.basic_consume(
                queue=settings.RABBITMQ_QUEUE,
                on_message_callback=callback,
            )
            logger.info("Started consuming messages...")

            while not self._shutdown:
                self._channel.connection.process_data_events(time_limit=1)

        except Exception as exc:
            logger.error(f"Consumer error: {exc}")
            raise

    def stop_consuming(self) -> None:
        self._shutdown = True
        logger.info(f"Consumer stopped - Processed: {self.processed_count}, Failed: {self.failed_count}")

    def get_stats(self) -> Dict[str, Any]:
        return {"processed": self.processed_count, "failed": self.failed_count}


def run_consumer() -> None:
    """Run the consumer in a loop with error handling."""
    consumer = SensorConsumer()

    def signal_handler(signum: int, frame: Any) -> None:
        logger.info("Received shutdown signal")
        consumer.stop_consuming()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        consumer.connect()
        consumer.start_consuming()
    except Exception as exc:
        logger.error(f"Consumer failed: {exc}")
    finally:
        consumer.close()
        consumer.stop_consuming()