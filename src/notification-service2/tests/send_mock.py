import pika
import json
import uuid
import time

RABBITMQ_URL = "amqps://epnwrxps:FJDX9jCp6ng-bHYxHocDRsYbBqsJ6yP3@cow.rmq2.cloudamqp.com/epnwrxps"
EXCHANGE_NAME = "motor_exchange"
ROUTING_KEY = "equipment.alerts"

def make_window():
    """Simulate a 64-step sensor window — replace with real MongoDB data later."""
    return [
        {
            "step": i,
            "rpm": 3600 + (i % 5),
            "temperature_c": 840 + (i * 0.1),
            "vibration_mm_s": 12.4 + (i * 0.05),
            "lubrication_bar": 4.2,
        }
        for i in range(64)
    ]

def send_mock_alert():
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    msg_id = f"MSG-{uuid.uuid4().hex[:6]}"

    mock_payload = {
        # Core identity
        "machine_id":   "TRB-9402",
        "machine_type": "Turbine_Industrial",

        # Prediction fields
        "predicted_rul": 118.5,
        "mean_rul":      120.0,
        "confidence":    0.94,
        "failure_type":  "Bearing Wear",
        "alert":         "Vibration threshold exceeded ISO 10816 Zone C",
        "alert_level":   "CRITICAL",

        # Alerting meta
        "should_alert": True,
        "channels":     ["websocket", "email"],
        "processed_by": "forecasting-service",
        "file_name":    "TRB-9402_window_064.csv",
        "message":      "Critical bearing wear detected on TRB-9402",

        # XAI
        "xai_root_cause_diagnosis": None,

        # Metadata block
        "metadata": {
            "message_id": msg_id,
            "timestamp":  time.time(),
        },

        # The actual sensor window — this becomes window_sliding in /rag/diagnose
        "raw": make_window(),
    }

    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="topic",
        durable=True,
        passive=True,   # don't recreate if it exists
    )
    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key=ROUTING_KEY,
        body=json.dumps(mock_payload),
        properties=pika.BasicProperties(delivery_mode=2),
    )

    print(f"[x] Sent alert {msg_id} for machine TRB-9402")
    connection.close()

if __name__ == "__main__":
    send_mock_alert()