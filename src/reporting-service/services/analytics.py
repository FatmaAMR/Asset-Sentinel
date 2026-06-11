import time
from typing import List, Optional
from datetime import datetime
from schemas.models import MachineAggregatedReport, FactoryReport


async def process_factory_data(raw_data: List[dict], status_filter: Optional[str] = None) -> FactoryReport:
    if not raw_data:
        return FactoryReport(
            report_time=datetime.utcnow().isoformat(),
            total_machines=0,
            critical_machines_count=0,
            active_sensors=0,
            machines_details=[]
        )

    active_sensors = len(raw_data)

    # Group by machine
    machines_data = {}
    for record in raw_data:
        m_id = record["machine_id"]
        if m_id not in machines_data:
            machines_data[m_id] = []
        machines_data[m_id].append(record)

    reports = []
    critical_count = 0

    for m_id, records in machines_data.items():
        # Use the latest record per machine
        latest = sorted(records, key=lambda x: x["timestamp"])[-1]

        # Status comes directly from the pipeline — no recomputation
        status = latest.get("status", "Normal")

        if status_filter and status != status_filter:
            continue

        if status == "Critical":
            critical_count += 1

        report = MachineAggregatedReport(
            machine_id=m_id,
            avg_temperature=latest.get("temperature", 0.0),
            max_temperature=latest.get("temperature", 0.0),
            avg_vibration=latest.get("vibration", 0.0),
            max_vibration=latest.get("vibration", 0.0),
            current_rul_days=latest.get("rul_days", 0),
            status=status,
        )
        reports.append(report)

    return FactoryReport(
        report_time=datetime.utcnow().isoformat(),
        total_machines=len(machines_data),
        critical_machines_count=critical_count,
        active_sensors=active_sensors,
        machines_details=reports
    )


async def get_machine_history(raw_data: List[dict], machine_id: str, limit: int = 50) -> dict:
    machine_records = [r for r in raw_data if r["machine_id"] == machine_id]
    if not machine_records:
        return None
    sorted_records = sorted(machine_records, key=lambda x: x["timestamp"])[-limit:]
    return {"machine_id": machine_id, "limit": limit, "data": sorted_records}


async def get_machine_details(raw_data: List[dict], machine_id: str) -> dict:
    machine_records = [r for r in raw_data if r["machine_id"] == machine_id]
    if not machine_records:
        return None

    latest_record = sorted(machine_records, key=lambda x: x["timestamp"])[-1]
    status = latest_record.get("status", "Normal")

    aggregated = MachineAggregatedReport(
        machine_id=machine_id,
        avg_temperature=latest_record.get("temperature", 0.0),
        max_temperature=latest_record.get("temperature", 0.0),
        avg_vibration=latest_record.get("vibration", 0.0),
        max_vibration=latest_record.get("vibration", 0.0),
        current_rul_days=latest_record.get("rul_days", 0),
        status=status,
    )

    return {
        "machine_id": machine_id,
        "details": aggregated,
        "latest_reading": latest_record,
    }


async def get_active_alerts(raw_data: List[dict], status_filter: Optional[str] = None) -> List[dict]:
    alerts = []
    machines_data = {}
    for record in raw_data:
        m_id = record["machine_id"]
        if m_id not in machines_data:
            machines_data[m_id] = []
        machines_data[m_id].append(record)

    for m_id, records in machines_data.items():
        latest = sorted(records, key=lambda x: x["timestamp"])[-1]
        status = latest.get("status", "Normal")
        rul    = latest.get("rul_days", 0)

        # Only alert on non-Normal machines
        if status == "Normal":
            continue

        severity = status  # "Critical", "Warning", "Scheduled"

        if status_filter and severity != status_filter:
            continue

        if severity == "Critical":
            message = f"Critical: {m_id} has RUL of {rul} days. Immediate inspection required."
        elif severity == "Warning":
            message = f"Warning: {m_id} degradation detected. RUL {rul} days. Monitor closely."
        else:
            message = f"Scheduled maintenance window active for {m_id}."

        alerts.append({
            "alert_id":  f"ALT-{m_id}-{int(time.time())}",
            "machine_id": m_id,
            "severity":   severity,
            "message":    message,
            "timestamp":  latest["timestamp"],
        })

    return alerts