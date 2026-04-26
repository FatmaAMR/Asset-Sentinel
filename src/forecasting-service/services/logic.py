"""
Business logic for sensor data processing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict
import numpy as np

logger = logging.getLogger(__name__)


class SensorLogic:
    """Applies business rules to predictions."""

    def process_prediction(
        self,
        prediction: Dict[str, Any],
        sensor_data: Dict[str, Any],
        file_name: str,
    ) -> Dict[str, Any]:
        """
        Apply business logic to raw prediction.
        """
        try:
            # Example: Flag high vibration as critical
            vibration = sensor_data.get("vibration", 0)
            if vibration > 80:
                prediction["alert"] = "High vibration detected"
            else:
                prediction["alert"] = "Normal"

            # Add metadata
            prediction["processed_by"] = "SensorLogic"
            prediction["file_name"] = file_name

            logger.debug(f"Processed prediction: {prediction}")
            return prediction

        except Exception as exc:
            logger.error(f"Logic processing failed: {exc}")
            raise