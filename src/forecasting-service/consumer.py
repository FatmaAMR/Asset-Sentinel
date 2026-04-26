import pika
import json
import numpy as np
import os
import sys

# تأمين المسارات عشان الـ Imports تشتغل صح
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.validation import validate_sensor_reading
from services.logic import extract_features, verbalize_status

def on_message_received(ch, method, properties, body):
    try:
        # 1. فك التشفير والتأكد إنها JSON
        payload = json.loads(body.decode('utf-8'))
        
        # لو الداتا جاية كـ String جوه الـ payload، بنفكها تاني
        if isinstance(payload, str):
            payload = json.loads(payload)

        file_name = payload.get("file_name", "unknown")
        raw_data = payload.get("data", [])

        if not raw_data or len(raw_data) == 0:
            print(f" [!] {file_name}: No data received or empty list.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # تأكدي إن أول عنصر هو Dictionary فعلاً
        first_row = raw_data
        if isinstance(first_row, str): # لو باعتين JSON String جوه الـ List
            import ast
            first_row = ast.literal_eval(first_row)
            
        keys = list(first_row.keys())
        v_col, i_col = keys, keys
        
        # تحويل الداتا لـ Arrays
        v_sample = np.array([float(row[v_col]) for row in raw_data])
        i_sample = np.array([float(row[i_col]) for row in raw_data])

        # التشغيل (Validation + Logic)
        is_valid, msg = validate_sensor_reading(v_sample)
        
        if is_valid:
            features = extract_features(v_sample, i_sample)
            report = verbalize_status(features)
            print(f" [✅] Processed {file_name}: {report}")
        else:
            print(f" [⚠️] {file_name} Skipped: {msg}")

    except Exception as e:
        print(f" [❌] Error processing message: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    # الـ URL بتاعك من CloudAMQP
    cloud_url = "amqps://burraqtq:yFx0LDD76FrrDRFLhd2Wk_R68YfwhG00@cow.rmq2.cloudamqp.com/burraqtq"
    
    params = pika.URLParameters(cloud_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    
    # تعريف الـ Queue
    channel.queue_declare(queue='sensor_data_queue', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='sensor_data_queue', on_message_callback=on_message_received)

    print(' [*] Forecasting Service is connected to CLOUD and waiting for messages...')
    print(' [*] Press CTRL+C to exit.')
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()