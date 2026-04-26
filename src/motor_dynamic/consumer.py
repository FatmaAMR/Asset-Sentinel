import json
import logging
import sys
import csv
import os

import pika
import pika.exceptions

from config.settings import settings
from schemas.models import MessageEnvelope

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("consumer")

# Configuration for output
OUTPUT_FILE = "consumed_motor_data.csv"

def _process(envelope: MessageEnvelope) -> None:
    """
    Writes the envelope record data into a CSV file.
    """
    rec = envelope.record
    file_exists = os.path.isfile(OUTPUT_FILE)

    with open(OUTPUT_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if new file
        if not file_exists:
            writer.writerow(["file_name", "window_index", "column_name", "values"])

        # Log to console
        logger.info(f"Processing {rec.file_name} | Window {rec.window_index}")

        # Store signals: we flatten them or store them as list strings
        for col_name, values in rec.signals.items():
            writer.writerow([rec.file_name, rec.window_index, col_name, json.dumps(values)])

def main() -> None:
    params = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        virtual_host=settings.RABBITMQ_VHOST,
        credentials=pika.PlainCredentials(
            settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
        ),
        heartbeat=600,
    )

    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Ensure queue exists
    queue_state = channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True, passive=True)
    
    # Get initial message count
    message_count = queue_state.method.message_count
    if message_count == 0:
        logger.info("Queue is empty. Nothing to consume.")
        return

    logger.info(f"Starting consumption. {message_count} messages in queue.")

    consumed_count = 0
    
    # ── Loop until the queue is empty ────────────────────────────────────────
    while True:
        # basic_get is better for "one-off" or "finish-when-empty" tasks
        method_frame, header_frame, body = channel.basic_get(queue=settings.RABBITMQ_QUEUE, auto_ack=False)
        
        if method_frame:
            try:
                data = json.loads(body.decode("utf-8"))
                envelope = MessageEnvelope(**data)
                
                _process(envelope)
                
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                consumed_count += 1
            except Exception as exc:
                logger.error(f"Failed to process message: {exc}")
                channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=False)
        else:
            # No more messages left in the queue
            logger.info(f"Queue empty. Finished consuming {consumed_count} messages.")
            break

    if connection and not connection.is_closed:
        connection.close()

if __name__ == "__main__":
    main()