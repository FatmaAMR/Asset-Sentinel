from typing import List, Optional
from datetime import datetime
from schemas.models import MachineAggregatedReport, FactoryReport

async def process_factory_data(raw_data: List[dict], status_filter: Optional[str] = None) -> FactoryReport:
    """
    المحرك التحليلي: بياخد الداتا الخام ويحولها لتقارير مع إمكانية الفلترة.
    """
    if not raw_data:
        return FactoryReport(
            report_time=datetime.utcnow().isoformat(),
            total_machines=0,
            critical_machines_count=0,
            machines_details=[]
        )

    machines_data = {}
    for record in raw_data:
        m_id = record["machine_id"]
        if m_id not in machines_data:
            machines_data[m_id] = []
        machines_data[m_id].append(record)
        
    reports = []
    critical_count = 0
    
    for m_id, records in machines_data.items():
        temps = [r["temperature"] for r in records]
        vibes = [r["vibration"] for r in records]
        current_rul = records[-1]["rul_days"]
        
        max_temp = max(temps)
        max_vibe = max(vibes)
        
        # اللوجيك بتاع تحديد الحالة
        status = "Normal"
        if current_rul < 15 or max_temp > 90:
            status = "Critical"
            critical_count += 1
        elif current_rul < 30 or max_temp > 85:
            status = "Warning"
            
        # تطبيق الفلتر لو المستخدم طلبه (مثلاً عايز الـ Critical بس)
        if status_filter and status != status_filter:
            continue

        report = MachineAggregatedReport(
            machine_id=m_id,
            avg_temperature=round(sum(temps) / len(temps), 2),
            max_temperature=max_temp,
            avg_vibration=round(sum(vibes) / len(vibes), 2),
            max_vibration=max_vibe,
            current_rul_days=current_rul,
            status=status
        )
        reports.append(report)
        
    return FactoryReport(
        report_time=datetime.utcnow().isoformat(),
        total_machines=len(machines_data),
        critical_machines_count=critical_count,
        machines_details=reports
    )
# ضيف الدوال دي تحت دالة process_factory_data

async def get_machine_history(raw_data: List[dict], machine_id: str, limit: int = 50) -> dict:
    # فلترة الداتا عشان نجيب مكنة معينة بس
    machine_records = [r for r in raw_data if r["machine_id"] == machine_id]
    if not machine_records:
        return None
    # ترتيب زمني وناخد آخر قراءات حسب الـ limit
    sorted_records = sorted(machine_records, key=lambda x: x["timestamp"])[-limit:]
    return {"machine_id": machine_id, "limit": limit, "data": sorted_records}


async def get_machine_details(raw_data: List[dict], machine_id: str) -> dict:
    machine_records = [r for r in raw_data if r["machine_id"] == machine_id]
    if not machine_records:
        return None

    temps = [r["temperature"] for r in machine_records]
    vibes = [r["vibration"] for r in machine_records]
    latest_record = sorted(machine_records, key=lambda x: x["timestamp"])[-1]
    
    current_rul = latest_record["rul_days"]
    max_temp = max(temps)

    status = "Normal"
    if current_rul < 15 or max_temp > 90:
        status = "Critical"
    elif current_rul < 30 or max_temp > 85:
        status = "Warning"

    aggregated = MachineAggregatedReport(
        machine_id=machine_id,
        avg_temperature=round(sum(temps) / len(temps), 2),
        max_temperature=max_temp,
        avg_vibration=round(sum(vibes) / len(vibes), 2),
        max_vibration=max(vibes),
        current_rul_days=current_rul,
        status=status
    )

    return {
        "machine_id": machine_id,
        "details": aggregated,
        "latest_reading": latest_record
    }


async def get_active_alerts(raw_data: List[dict], status_filter: Optional[str] = None) -> List[dict]:
    # توليد تنبيهات بناءً على أحدث قراءة لكل مكنة
    alerts = []
    machines_data = {}
    for record in raw_data:
        m_id = record["machine_id"]
        if m_id not in machines_data:
            machines_data[m_id] = []
        machines_data[m_id].append(record)

    import time
    for m_id, records in machines_data.items():
        latest = sorted(records, key=lambda x: x["timestamp"])[-1]
        temp = latest["temperature"]
        rul = latest["rul_days"]

        severity = None
        message = ""
        # لوكيج التنبيهات (ده اللي هييجي من موديل LLM لفاطمة بعدين)
        if rul < 15 or temp > 90:
            severity = "Critical"
            message = f"High priority alert: Temperature is {temp}°C, RUL is {rul} days. Please check cooling system."
        elif rul < 30 or temp > 85:
            severity = "Warning"
            message = f"Warning: Temperature is rising ({temp}°C). Monitor closely."

        if severity:
            if status_filter and severity != status_filter:
                continue
            alerts.append({
                "alert_id": f"ALT-{m_id}-{int(time.time())}",
                "machine_id": m_id,
                "severity": severity,
                "message": message,
                "timestamp": latest["timestamp"]
            })
    return alerts