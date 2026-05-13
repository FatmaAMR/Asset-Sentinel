import logging
import pika
from pika.adapters.blocking_connection import BlockingChannel

from config.settings import settings
from schemas.models import ForecastingResult

# --- 1. SILENCE PIKA LOGS ---
logging.getLogger("pika").setLevel(logging.WARNING)
# ----------------------------

logger = logging.getLogger(__name__)

class ForecastingPublisher:
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
            print(f"✅ Connected to RabbitMQ | Exchange: {settings.FORECASTING_EXCHANGE}")

        except Exception as exc:
            logger.error(f"❌ Failed to connect: {exc}")
            raise

    def publish(self, result: ForecastingResult) -> None:
        if not self._channel:
            raise RuntimeError("Not connected to RabbitMQ")

        # Always publish to status
        self._publish_to(
            routing_key=settings.EQUIPMENT_STATUS_ROUTING_KEY,
            result=result,
        )

        # Alerts only for warnings/critical
        if result.label in ("warning", "critical"):
            self._publish_to(
                routing_key=settings.ALERTS_ROUTING_KEY,
                result=result,
            )

    def _publish_to(self, routing_key: str, result: ForecastingResult) -> None:
        try:
            self._channel.basic_publish(
                exchange=settings.FORECASTING_EXCHANGE,
                routing_key=routing_key,
                body=result.to_bytes(),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    message_id=result.message_id,
                    timestamp=int(result.timestamp),
                ),
            )
            self.published_count += 1
            
            # --- 2. CLEAN SUCCESS MESSAGE ---
            print(f"🚀 Published Successfully | ID: {result.message_id} | Key: {routing_key} | Label: {result.label}")
            
        except Exception as exc:
            logger.error(f"❌ Failed to publish {result.message_id}: {exc}")
            raise

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