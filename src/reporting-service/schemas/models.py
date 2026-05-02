from pydantic import BaseModel
from typing import List

class SensorData(BaseModel):
    timestamp: str
    machine_id: str
    temperature: float
    vibration: float
    rul_days: int

class MachineAggregatedReport(BaseModel):
    machine_id: str
    avg_temperature: float
    max_temperature: float
    avg_vibration: float
    max_vibration: float
    current_rul_days: int
    status: str             # "Normal", "Warning", "Critical"

class FactoryReport(BaseModel):
    report_time: str
    total_machines: int
    critical_machines_count: int
    machines_details: List[MachineAggregatedReport]
    # ضيف الكلاسات دي تحت FactoryReport

class Alert(BaseModel):
    alert_id: str
    machine_id: str
    severity: str
    message: str
    timestamp: str

class MachineHistoryResponse(BaseModel):
    machine_id: str
    limit: int
    data: List[SensorData]

class MachineDetailsResponse(BaseModel):
    machine_id: str
    details: MachineAggregatedReport
    latest_reading: SensorData