from pydantic import BaseModel
from typing import List, Optional


class AlertMessage(BaseModel):
    message_id: str
    machine_id: str
    machine_type: str
    predicted_rul: float
    confidence: float
    failure_type: str
    alert_level: str  # Warning, Critical

class NotificationPayload(BaseModel):
    recipient_email: str
    channel: str
    subject: str
    body: str