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