

import json
import logging
import os

import sys
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone
import pika

# ── 1. Load environment variables ────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# ── 2. Silence internal pika logs ────────────────────────────────────────────
logging.getLogger("pika").setLevel(logging.WARNING)

# ── 3. Configure logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

# ── 4. RabbitMQ config ───────────────────────────────────────────────────────
RABBITMQ_URL              = os.getenv("RABBITMQ_URL")
FORECASTING_EXCHANGE      = os.getenv("FORECASTING_EXCHANGE", "forecasting_exchange")
EQUIPMENT_STATUS_QUEUE    = os.getenv("EQUIPMENT_STATUS_QUEUE", "equipment.status")
EQUIPMENT_STATUS_ROUTING_KEY = os.getenv("EQUIPMENT_STATUS_ROUTING_KEY", "equipment.status")

# ── 5. MongoDB ────────────────────────────────────────────────────────────────
# Import here so startup fails fast if pymongo is missing
try:
    from db.connection import get_collection
except ImportError:
    logger.error("pymongo not installed. Run: pip install pymongo[srv]")
    sys.exit(1)


def _build_document(message_id: str, data: dict) -> dict:
    """Map the incoming RabbitMQ message to a MongoDB document."""
    metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
    labels = data.get("labels", {}) if isinstance(data, dict) else {}

    machine_id = (
        data.get("machine_id")
        or metadata.get("file_name")
        or metadata.get("machine_id")
    )

    rul_value = (
        data.get("rul")
        or data.get("predicted_rul")
        or labels.get("predicted_rul")
    )

    label_value = (
        data.get("label")
        or data.get("alert_level")
        or labels.get("health_state")
        or labels.get("status")
        or labels.get("alert_level")
    )

    return {
        # Required field for MongoDB time-series collection
        "timestamp": datetime.now(timezone.utc),
        "message_id": message_id,
        "machine_id": machine_id,
        "label": label_value,
        "rul": rul_value,
        # Store the full payload for reference
        "raw": data,
    }


def handle_status(ch, method, properties, body) -> None:
    """Process a single RabbitMQ message and persist it to MongoDB."""
    message_id = (properties.message_id or "unknown") if properties else "unknown"
    try:
        data = json.loads(body)

        # ── Persist to MongoDB ────────────────────────────────────────────────
        doc        = _build_document(message_id, data)
        collection = get_collection()
        result     = collection.insert_one(doc)

        logger.info(
            f"[SAVED] mongo_id={result.inserted_id} | "
            f"message={message_id} | "
            f"machine={data.get('machine_id')} | "
            f"label={data.get('label')} | "
            f"rul={data.get('rul')}"
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as exc:
        logger.error(f"Failed to process message {message_id}: {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start() -> None:
    if not RABBITMQ_URL:
        logger.error("RABBITMQ_URL not found in environment!")
        return

    params = pika.URLParameters(RABBITMQ_URL)

    try:
        connection = pika.BlockingConnection(params)
        channel    = connection.channel()

        channel.exchange_declare(
            exchange=FORECASTING_EXCHANGE,
            exchange_type="direct",
            durable=True
        )

        res = channel.queue_declare(queue=EQUIPMENT_STATUS_QUEUE, durable=True)
        channel.queue_bind(
            exchange=FORECASTING_EXCHANGE,
            queue=EQUIPMENT_STATUS_QUEUE,
            routing_key=EQUIPMENT_STATUS_ROUTING_KEY
        )

        initial_count = res.method.message_count
        if initial_count == 0:
            logger.info("Queue is already empty. Exiting.")
            connection.close()
            return

        logger.info(f"[*] Found {initial_count} messages. Saving to MongoDB...")



        
        for method_frame, properties, body in channel.consume(

            queue=EQUIPMENT_STATUS_QUEUE,
            inactivity_timeout=3
        ):
            if method_frame:
                handle_status(channel, method_frame, properties, body)


            else:

                logger.info("Queue empty and timeout reached. Shutting down...")
                break


        channel.cancel()

        connection.close()
        logger.info("✅ Service finished. All messages saved to MongoDB.")

    except Exception as e:
        logger.error(f"Service Error: {e}")


if __name__ == "__main__":
    start()