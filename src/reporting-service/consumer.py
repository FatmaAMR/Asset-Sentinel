

import json
import logging
import os
import signal
import sys
from dotenv import load_dotenv
from pathlib import Path
import pika

# 1. Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# 2. Silence internal pika logs
logging.getLogger("pika").setLevel(logging.WARNING)

# 3. Configure logging format
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
FORECASTING_EXCHANGE = os.getenv("FORECASTING_EXCHANGE", "forecasting_exchange")
EQUIPMENT_STATUS_QUEUE = os.getenv("EQUIPMENT_STATUS_QUEUE", "equipment.status")
EQUIPMENT_STATUS_ROUTING_KEY = os.getenv("EQUIPMENT_STATUS_ROUTING_KEY", "equipment.status")


def handle_status(ch, method, properties, body) -> None:
    """Processes a single message and logs a clean summary."""
    message_id = properties.message_id or "unknown"
    try:
        data = json.loads(body)
        
        # Log only the essential info (Machine ID, Label, and RUL)
        # We skip 'window_sliding' to keep the console clean
        logger.info(
            f"[STATUS] message={message_id} | "
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
        channel = connection.channel()

        channel.exchange_declare(exchange=FORECASTING_EXCHANGE, exchange_type="direct", durable=True)
        
        # Declare the queue and get the initial count
        res = channel.queue_declare(queue=EQUIPMENT_STATUS_QUEUE, durable=True)
        channel.queue_bind(exchange=FORECASTING_EXCHANGE, queue=EQUIPMENT_STATUS_QUEUE, routing_key=EQUIPMENT_STATUS_ROUTING_KEY )

        initial_count = res.method.message_count
        if initial_count == 0:
            logger.info("Queue is already empty. Exiting.")
            connection.close()
            return

        logger.info(f"[*] Found {initial_count} messages. Processing...")

        # We process messages until the generator stops or times out
        # Using a 3-second timeout is usually enough to detect "truly empty"
        for method_frame, properties, body in channel.consume(
            queue=EQUIPMENT_STATUS_QUEUE, 
            inactivity_timeout=3 
        ):
            if method_frame:
                handle_status(channel, method_frame, properties, body)
                
                # We NO LONGER check message_count here. 
                # channel.consume will automatically give us the next message 
                # if one exists.
            else:
                # This triggers ONLY when the queue is empty AND 3 seconds have passed
                logger.info("Queue empty and timeout reached. Shutting down...")
                break

        # Stop consuming and close
        channel.cancel()
        connection.close()
        logger.info("✅ Service finished. All messages captured.")

    except Exception as e:
        logger.error(f"Service Error: {e}")

if __name__ == "__main__":
    start()