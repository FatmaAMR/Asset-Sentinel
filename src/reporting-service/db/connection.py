import random
from datetime import datetime, timedelta
import asyncio

# حولنا الدالة لـ async
async def get_mock_influx_data(machine_count: int = 5, records_per_machine: int = 24):
    """
    محاكاة لجلب البيانات بشكل غير متزامن (Async).
    """
    # بنعمل "sleep" بسيط عشان نحاكي وقت استجابة الداتا بيز
    await asyncio.sleep(0.1) 
    
    mock_data = []
    current_time = datetime.utcnow()

    for machine_id in range(1, machine_count + 1):
        machine_name = f"Machine_{machine_id}"
        base_rul = random.randint(5, 100)

        for hour in range(records_per_machine):
            record_time = current_time - timedelta(hours=hour)
            temperature = round(random.uniform(65, 90.5cd ../..), 2)
            vibration = round(random.uniform(0.5, 3.5), 2)

            mock_data.append({
                "timestamp": record_time.isoformat(),
                "machine_id": machine_name,
                "temperature": temperature,
                "vibration": vibration,
                "rul_days": base_rul
            })
            
    return sorted(mock_data, key=lambda x: x["timestamp"])