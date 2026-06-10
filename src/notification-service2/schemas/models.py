from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class AlertMetadata(BaseModel):
    message_id: str
    timestamp: float


class AlertMessage(BaseModel):
    """Matches the equipment.alerts queue payload shape."""
    # Core identity
    machine_id:     str
    machine_type:   str

    # Prediction fields
    predicted_rul:  float
    mean_rul:       float
    confidence:     float
    failure_type:   str
    alert:          str                     # e.g. "Normal" / fault label
    alert_level:    str                     # "SCHEDULED", "WARNING", "CRITICAL"

    # Alerting meta
    should_alert:   bool
    channels:       List[str]
    processed_by:   str
    file_name:      str
    message:        str

    # XAI / root-cause (nullable)
    xai_root_cause_diagnosis: Optional[Any] = None

    # Nested metadata block  →  we promote message_id / timestamp from here
    metadata:       AlertMetadata

    # Raw sliding-window sensor data
    raw:            Any = None              # list of readings or dict

    # Convenience properties so downstream code keeps using .message_id / .timestamp
    @property
    def message_id(self) -> str:            # type: ignore[override]
        return self.metadata.message_id

    @property
    def timestamp(self) -> float:
        return self.metadata.timestamp


class NotificationPayload(BaseModel):
    recipient_email: str
    channel: str
    subject: str
    body: str


# ── Consulting-service /diagnose contract ────────────────────────────────────

class DiagnoseRequest(BaseModel):
    machine_id:     str   = Field(..., description="Unique machine identifier")
    label:          str   = Field(..., description="Predicted fault / condition label")
    rul:            float = Field(..., description="Remaining Useful Life (cycles or hours)")
    window_sliding: Any   = Field(..., description="Sliding-window sensor data")
    message_id:     str   = Field(..., description="Unique event UUID")
    timestamp:      float = Field(..., description="Unix timestamp of the event")
    top_k:          int   = Field(1,   description="Number of similar historical cases to retrieve")


class DiagnoseResponse(BaseModel):
    """Minimal contract — extend as the consulting API evolves."""
    diagnosis:  Optional[str] = None
    suggestion: Optional[str] = None
    similar_cases: Optional[List[Any]] = None
    raw:        Optional[Any] = None
