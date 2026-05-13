"""
Forecasting-service imports from shared schemas.
"""

import sys
from pathlib import Path

# Add parent (src) to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# from schemas.models import MessageEnvelope, FileRecord

# __all__ = ["MessageEnvelope", "FileRecord"]

from dataclasses import dataclass, field
from typing import List, Dict, Any
import json

@dataclass
class ForecastingResult:
    machine_id: str
    label: str           # "normal" | "warning" | "critical"
    rul: float           # Remaining Useful Life
    window_sliding: List[Dict[str, Any]] 
    message_id: str
    timestamp: float

    def to_bytes(self) -> bytes:
        return json.dumps({
            "machine_id": self.machine_id,
            "label": self.label,
            "rul": self.rul,
            "window_sliding": self.window_sliding,  # This will now serialize the list of rows
            "message_id": self.message_id,
            "timestamp": self.timestamp,
        }).encode("utf-8")