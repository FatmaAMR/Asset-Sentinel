import pika
import json
import uuid
import sys
from pathlib import Path

# --- تظبيط المسارات عشان يشوف مجلد core ---
current_file = Path(__file__).resolve()
# بنرجع لورا مرتين عشان نوصل لمجلد notification-service
project_root = current_file.parent.parent 

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    # تعديل الـ import ليكون مطابق لمكان ملف الـ settings
    from config import settings
except ImportError as e:
    print(f"[Error] Cannot find core.config. Ensure you are running from notification-service directory. Details: {e}")
    sys.exit(1)

def send_test_alert():
    # استخدام الإعدادات من ملف الـ config
    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
    channel = connection.channel()

    test_alert = {
        "message_id": f"TEST-{uuid.uuid4().hex[:6]}",
        "machine_id": "TURBINE-001",
        "machine_type": "Gas_Turbine",
        "predicted_rul": 45.5,
        "confidence": 0.92,
        "failure_type": "Bearing Wear", # جربي تغيري دي لـ Bearing Wear عشان تشوفي الـ Mock suggestion
        "alert_level": "Critical"
    }

    channel.basic_publish(
        exchange='',
        routing_key=settings.RABBITMQ_ALERT_QUEUE,
        body=json.dumps(test_alert),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print(f" [x] Sent Test Alert: {test_alert['message_id']}")
    print(f" [x] Target Queue: {settings.RABBITMQ_ALERT_QUEUE}")
    connection.close()

if __name__ == "__main__":
    send_test_alert()