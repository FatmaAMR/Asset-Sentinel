"""
RabbitMQ consumer for forecasting-service.
Consumes MessageEnvelope from motor.raw queue and processes via pipeline.
"""

from __future__ import annotations

import logging
import signal
import ssl
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict

import certifi
import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPChannelError, AMQPConnectionError

# ==============================================================================
# GLOBAL MONKEY-PATCH: Fixes the Windows ASN1 Store Bug Across Entire Project
# ==============================================================================
_original_create_default_context = ssl.create_default_context

def _patched_create_default_context(purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None, cadata=None):
    """Overrides default context creation to force certifi, bypassing corrupt Windows Certs."""
    if cafile is None and capath == None and cadata is None:
        return _original_create_default_context(purpose, cafile=certifi.where())
    return _original_create_default_context(purpose, cafile=cafile, capath=capath, cadata=cadata)

ssl.create_default_context = _patched_create_default_context
# ==============================================================================

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
        
        # This will now initialize flawlessly without crashing on background publishers!
        self.pipeline = ProcessingPipeline()
        
        self.processed_count = 0
        self.failed_count = 0
        self._shutdown = False

    def connect(self) -> None:
        """Establishes connection to RabbitMQ with secure SSL configurations."""
        try:
            params = pika.URLParameters(settings.RABBITMQ_URL)
            
            # Explicit parameters configuration
            params.heartbeat = 600
            params.blocked_connection_timeout = 300
            params.connection_attempts = 3
            params.retry_delay = 2

            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._channel.basic_qos(prefetch_count=1)

            # Declare the exchange and queue
            logger.info(f"Declaring exchange: {settings.MOTOR_EXCHANGE} (type: direct)")
            self._channel.exchange_declare(
                exchange=settings.MOTOR_EXCHANGE,
                exchange_type='direct',
                durable=True,
            )
            logger.info(f"Declaring queue: {settings.MOTOR_QUEUE}")
            self._channel.queue_declare(
                queue=settings.MOTOR_QUEUE,
                durable=True,
            )
            logger.info(f"Binding queue {settings.MOTOR_QUEUE} to exchange {settings.MOTOR_EXCHANGE} with routing key {settings.MOTOR_ROUTING_KEY}")
            self._channel.queue_bind(
                exchange=settings.MOTOR_EXCHANGE,
                queue=settings.MOTOR_QUEUE,
                routing_key=settings.MOTOR_ROUTING_KEY,
            )

            logger.info(f"Connected to RabbitMQ and declared queue: {settings.MOTOR_QUEUE}")
        except Exception as exc:
            logger.error(f"Failed to connect to RabbitMQ: {exc}", exc_info=True)
            raise

    def close(self) -> None:
        """Gracefully closes open channels and connections."""
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
            if getattr(self.pipeline, "publisher", None) is not None:
                self.pipeline.publisher.close()

    def start_consuming(self) -> None:
        """Starts monitoring the queue and routes items to the callback worker."""
        if not self._channel:
            raise RuntimeError("Not connected to RabbitMQ")

        def callback(
            ch: BlockingChannel,
            method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties,
            body: bytes,
        ) -> None:
            logger.info(f"[CALLBACK TRIGGERED] Received message, delivery_tag: {method.delivery_tag}")
            
            if self._shutdown:
                ch.stop_consuming()
                return
                
            try:
                # Deserialize message
                envelope = MessageEnvelope.from_bytes(body)
                logger.info(f"[CALLBACK] Message ID: {envelope.message_id} deserialized successfully")

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
                logger.info(f"[CALLBACK] Message acknowledged: {method.delivery_tag}")

            except Exception as exc:
                logger.error(f"[CALLBACK ERROR] Error processing message: {exc}", exc_info=True)
                self.failed_count += 1
                # Reject and requeue message
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        try:
            logger.info(f"About to register callback for queue: {settings.MOTOR_QUEUE}")
            self._channel.basic_consume(
                queue=settings.MOTOR_QUEUE,
                on_message_callback=callback,
                auto_ack=False,
            )
            logger.info("Started consuming messages...")
            logger.info("Calling channel.start_consuming() - this will block until messages arrive or shutdown")
            self._channel.start_consuming()
            logger.info("[CONSUMER] start_consuming returned normally")

        except (KeyboardInterrupt, Exception) as exc:
            logger.warning(f"Consumer interrupted: {type(exc).__name__}: {exc}", exc_info=True)
            if self._channel and self._channel.is_open:
                self._channel.stop_consuming()

    def stop_consuming(self) -> None:
        """Sets the shutdown flag and requests an ingestion block stop."""
        self._shutdown = True
        if self._channel and self._channel.is_open:
            self._channel.stop_consuming()
        logger.info(f"Consumer stopped - Processed: {self.processed_count}, Failed: {self.failed_count}")

    def get_stats(self) -> Dict[str, Any]:
        return {"processed": self.processed_count, "failed": self.failed_count}


def run_consumer() -> None:
    """Run the consumer in a loop with error handling."""
    consumer = SensorConsumer()

    def signal_handler(signum: int, frame: Any) -> None:
        logger.info("Received shutdown signal, stopping consumer...")
        consumer._shutdown = True
        if consumer._channel and consumer._channel.is_open:
            consumer._channel.stop_consuming()

    # Register signal handlers AFTER creating consumer
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