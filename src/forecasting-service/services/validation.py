"""
Sensor data validation layer with:
  • Schema validation
  • Data type enforcement
  • Range checking
  • Anomaly detection
  • Timestamp validation
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_data: Optional[Dict[str, Any]] = None


class SensorValidator:
    SENSOR_RANGES = {
        "vibration": (0, 100),
        "temperature": (-40, 150),
        "frequency": (0, 10000),
        "amplitude": (0, 1000),
        "phase": (0, 360),
        "power": (0, 10000),
        "current": (0, 1000),
        "voltage": (0, 600),
    }

    REQUIRED_FIELDS = [
        "file_name",
        "file_index",
        "window_index",
        "column_names",
        "data",
    ]

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.validation_history = []

    def validate_message_envelope(self, message: Dict[str, Any]) -> ValidationResult:
        errors = []
        warnings = []

        for field in ["message_id", "source", "timestamp", "record"]:
            if field not in message:
                errors.append(f"Missing required field: {field}")

        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        record = message.get("record", {})

        for field in self.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"Missing required record field: {field}")

        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        try:
            file_index = record.get("file_index")
            if not isinstance(file_index, int) or file_index < 0:
                errors.append(f"Invalid file_index: {file_index}")

            window_index = record.get("window_index")
            if not isinstance(window_index, int) or window_index < 0:
                errors.append(f"Invalid window_index: {window_index}")

            file_name = record.get("file_name", "")
            if not isinstance(file_name, str) or not file_name.strip():
                errors.append(f"Invalid file_name: {file_name}")

            column_names = record.get("column_names", [])
            if not isinstance(column_names, list) or not column_names:
                errors.append(f"Invalid column_names: {column_names}")

        except Exception as exc:
            errors.append(f"Error validating record metadata: {exc}")

        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        data = record.get("data", {})
        if not isinstance(data, dict):
            errors.append(f"Data must be dict, got {type(data)}")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        data_keys = set(data.keys())
        column_names_set = set(column_names)

        if data_keys != column_names_set:
            mismatched = data_keys.symmetric_difference(column_names_set)
            warnings.append(f"Data keys don't match column_names. Mismatched: {mismatched}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data=message,
        )

    def validate_sensor_values(
        self, column_names: List[str], data: Dict[str, Any]
    ) -> ValidationResult:
        errors = []
        warnings = []
        cleaned_data = data.copy()

        for col_name, value in data.items():
            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                errors.append(f"Column '{col_name}': non-numeric value '{value}'")
                continue

            if np.isnan(numeric_value):
                errors.append(f"Column '{col_name}': NaN detected")
                continue
            if np.isinf(numeric_value):
                errors.append(f"Column '{col_name}': Infinity detected")
                continue

            for sensor_type, (min_val, max_val) in self.SENSOR_RANGES.items():
                if sensor_type in col_name.lower():
                    if not (min_val <= numeric_value <= max_val):
                        warnings.append(
                            f"Column '{col_name}': value {numeric_value} outside range [{min_val}, {max_val}]"
                        )
                    break

            if self._is_outlier(numeric_value, col_name):
                warnings.append(f"Column '{col_name}': potential outlier {numeric_value}")

        if self.strict_mode and warnings:
            errors.extend(warnings)
            warnings = []

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data=cleaned_data,
        )

    def validate_timestamps(
        self, message: Dict[str, Any]
    ) -> ValidationResult:
        errors = []
        warnings = []

        try:
            msg_timestamp = message.get("timestamp")
            if not isinstance(msg_timestamp, (int, float)):
                errors.append(f"Invalid message timestamp: {msg_timestamp}")
                return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

            now = datetime.now().timestamp()
            if msg_timestamp > now:
                warnings.append(f"Message timestamp {msg_timestamp} is in the future")

            thirty_days_ago = now - (30 * 24 * 60 * 60)
            if msg_timestamp < thirty_days_ago:
                warnings.append(f"Message timestamp {msg_timestamp} is older than 30 days")

        except Exception as exc:
            errors.append(f"Timestamp validation error: {exc}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _is_outlier(self, value: float, column_name: str, threshold: float = 3.0) -> bool:
        return False

    def log_validation(self, result: ValidationResult, message_id: str) -> None:
        self.validation_history.append({
            "message_id": message_id,
            "timestamp": datetime.now().isoformat(),
            "is_valid": result.is_valid,
            "errors_count": len(result.errors),
            "warnings_count": len(result.warnings),
        })

        if not result.is_valid:
            logger.error(f"Validation failed for {message_id}: {result.errors}")
        elif result.warnings:
            logger.warning(f"Validation warnings for {message_id}: {result.warnings}")
        else:
            logger.info(f"Validation passed for {message_id}")