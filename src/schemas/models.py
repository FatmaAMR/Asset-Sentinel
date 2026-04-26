"""
Shared data models for MessageEnvelope and FileRecord.
Used by motor_dynamic (producer) and forecasting-service (consumer).
"""

from __future__ import annotations

from typing import Any, Dict, List
from dataclasses import dataclass, field
import json
from datetime import datetime
import uuid


@dataclass
class FileRecord:
    """Represents a windowed chunk of sensor data from a file."""
    file_name: str
    file_index: int
    window_index: int
    column_names: List[str]
    data: Dict[str, Any]
    window_size: int = 128

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_name": self.file_name,
            "file_index": self.file_index,
            "window_index": self.window_index,
            "column_names": self.column_names,
            "data": self.data,
            "window_size": self.window_size,
        }


@dataclass
class MessageEnvelope:
    """Wrapper for messages sent via RabbitMQ."""
    message_id: str
    source: str
    timestamp: float
    record: FileRecord

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "source": self.source,
            "timestamp": self.timestamp,
            "record": self.record.to_dict(),
        }

    def to_bytes(self) -> bytes:
        """Serialize to JSON bytes for RabbitMQ."""
        return json.dumps(self.to_dict()).encode("utf-8")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MessageEnvelope:
        """Deserialize from dict."""
        record_data = data.get("record", {})
        record = FileRecord(
            file_name=record_data.get("file_name"),
            file_index=record_data.get("file_index"),
            window_index=record_data.get("window_index"),
            column_names=record_data.get("column_names", []),
            data=record_data.get("data", {}),
            window_size=record_data.get("window_size", 128),
        )
        return cls(
            message_id=data.get("message_id"),
            source=data.get("source"),
            timestamp=data.get("timestamp"),
            record=record,
        )
    @classmethod
    def from_bytes(cls, data: bytes) -> MessageEnvelope:
        import json
        obj = json.loads(data.decode("utf-8"))
        return cls.from_dict(obj)


@dataclass
class IngestionResult:
    """Result of ingestion run."""
    published: int = 0
    failed: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)