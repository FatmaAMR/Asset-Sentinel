   
import asyncio
import json
import aio_pika
from config import settings
from services.NotificationDispatcher import NotificationDispatcher
from schemas.models import AlertMessage

async def main():
    dispatcher = NotificationDispatcher()
    
    # Connect to RabbitMQ
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    
    async with connection:
        channel = await connection.channel()
        
        # Declare the Alert Queue
        queue = await channel.declare_queue(settings.RABBITMQ_ALERT_QUEUE, durable=True)
        
        print(f"[*] Notification Service started. Waiting for alerts on {settings.RABBITMQ_ALERT_QUEUE}...")

        async with queue.iterator() as queue_iter:
            async def process_message(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        alert = AlertMessage(**data)
                        print(f"[!] Alert Received: {alert.message_id} - Processing...")
                        await dispatcher.process_alert(alert)
                    except Exception as e:
                        print(f"[Error] Failed to process message: {e}")

            # Start consuming
            async for message in queue_iter:
                await process_message(message)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Service Stopped.")