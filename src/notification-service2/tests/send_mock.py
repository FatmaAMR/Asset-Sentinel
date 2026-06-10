import pika
import json
import uuid

RABBITMQ_URL = "amqps://burraqtq:yFx0LDD76FrrDRFLhd2Wk_R68YfwhG00@cow.rmq2.cloudamqp.com/burraqtq"
QUEUE_NAME = "motor.alerts"

def send_mock_alert():
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # إنشاء رسالة وهمية مطابقة للموديل بتاعك
    mock_payload = {
        "message_id": f"MSG-{uuid.uuid4().hex[:6]}",
        "machine_id": "ENGINE-001",
        "machine_type": "V6_Industrial",
        "predicted_rul": 42.5,
        "confidence": 0.89,
        "failure_type": "Bearing Wear",
        "alert_level": "Critical"
    }

    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=json.dumps(mock_payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    print(f" [x] Sent Alert: {mock_payload['message_id']}")
    connection.close()

if __name__ == "__main__":
    send_mock_alert()