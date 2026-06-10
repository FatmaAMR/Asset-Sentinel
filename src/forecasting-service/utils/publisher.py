import json
import logging
import ssl
import time
from typing import Any, Dict

import certifi
import pika
from pika.adapters.blocking_connection import BlockingChannel

from config.settings import settings

# --- 1. SILENCE PIKA LOGS ---
logging.getLogger("pika").setLevel(logging.WARNING)
# ----------------------------

logger = logging.getLogger(__name__)


class ForecastingPublisher:

    def __init__(self):
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self.published_count = 0

        # Create a secure SSL context using certifi's fallback bundle
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def connect(self) -> None:
        """Establishes connection bypass for Windows certificate store."""
        try:
            params = pika.URLParameters(settings.RABBITMQ_URL)

            # Inject the safe context to prevent the ASN1 crash
            params.ssl_options = pika.SSLOptions(context=self._ssl_context)

            # Standard stability parameters
            params.heartbeat = 600
            params.blocked_connection_timeout = 300
            params.connection_attempts = 3
            params.retry_delay = 2

            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()

            self._channel.exchange_declare(
                exchange=settings.FORECASTING_EXCHANGE,
                exchange_type="direct",
                durable=True,
            )

            # Queue 1: Equipment Status
            self._channel.queue_declare(
                queue=settings.EQUIPMENT_STATUS_QUEUE,
                durable=True,
            )
            self._channel.queue_bind(
                exchange=settings.FORECASTING_EXCHANGE,
                queue=settings.EQUIPMENT_STATUS_QUEUE,
                routing_key=settings.EQUIPMENT_STATUS_ROUTING_KEY,
            )

            # Queue 2: Alerts
            self._channel.queue_declare(
                queue=settings.ALERTS_QUEUE,
                durable=True,
            )
            self._channel.queue_bind(
                exchange=settings.FORECASTING_EXCHANGE,
                queue=settings.ALERTS_QUEUE,
                routing_key=settings.ALERTS_ROUTING_KEY,
            )

            # Clean Info Log
            print(
                f"✅ Connected to RabbitMQ | Exchange: {settings.FORECASTING_EXCHANGE}"
            )

        except Exception as exc:
            logger.error(f"❌ Failed to connect: {exc}")
            raise

    def publish(self, payload: Dict[str, Any]) -> None:
        if not self._channel:
            raise RuntimeError("Not connected to RabbitMQ")

        # Always publish the full status payload
        self._publish_to(
            routing_key=settings.EQUIPMENT_STATUS_ROUTING_KEY,
            payload=payload,
            queue_name=settings.EQUIPMENT_STATUS_QUEUE,
        )

        # Publish to the alerts queue only when should_alert is explicitly false
        if self._should_publish_alert(payload):
            self._publish_to(
                routing_key=settings.ALERTS_ROUTING_KEY,
                payload=payload,
                queue_name=settings.ALERTS_QUEUE,
            )

    def _should_publish_alert(self, payload: Dict[str, Any]) -> bool:
        # Publish to alerts only when `should_alert` is explicitly True
        labels = payload.get("labels")
        if isinstance(labels, dict) and "should_alert" in labels:
            return labels.get("should_alert") is True
        return payload.get("should_alert") is True

    def _serialize_payload(self, payload: Dict[str, Any]) -> bytes:
        return json.dumps(payload).encode("utf-8")

    def _publish_to(
        self, routing_key: str, payload: Dict[str, Any], queue_name: str
    ) -> None:
        try:
            body = self._serialize_payload(payload)
            message_id = payload.get("metadata", {}).get(
                "message_id", payload.get("message_id", "unknown")
            )
            labels = payload.get("labels")
            should_alert = (
                labels.get("should_alert")
                if isinstance(labels, dict)
                else payload.get("should_alert")
            )

            self._channel.basic_publish(
                exchange=settings.FORECASTING_EXCHANGE,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    message_id=message_id,
                    timestamp=self._extract_timestamp(payload),
                ),
            )
            self.published_count += 1
            print(
                f"🚀 Published Successfully | Queue: {queue_name} | ID: {message_id} | RoutingKey: {routing_key} | should_alert: {should_alert}"
            )

        except Exception as exc:
            logger.error(f"❌ Failed to publish {message_id}: {exc}")
            raise

    def _extract_timestamp(self, payload: Dict[str, Any]) -> int:
        raw_timestamp = payload.get("metadata", {}).get("timestamp", 0)
        if isinstance(raw_timestamp, (int, float)):
            return int(raw_timestamp)

        try:
            return int(float(raw_timestamp))
        except (TypeError, ValueError):
            return int(time.time())

    def close(self) -> None:
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
            if self._connection and not self._connection.is_closed:
                self._connection.close()
            print("🔌 Connection closed.")
        except Exception as exc:
            logger.warning(f"Error closing: {exc}")
        finally:
            self._channel = None
            self._connection = None

    def get_stats(self) -> dict:
        return {"published": self.published_count}