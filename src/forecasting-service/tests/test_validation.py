# filepath: c:\Users\malak\Asset-Sentinel\src\forecasting-service\tests\test_validation.py
import pytest
from services.validation import SensorValidator, ValidationResult


def test_validate_message_envelope_valid():
    validator = SensorValidator()
    message = {
        "message_id": "123",
        "source": "motor_dynamic",
        "timestamp": 1234567890.0,
        "record": {
            "file_name": "test.csv",
            "file_index": 1,
            "window_index": 0,
            "column_names": ["vibration", "temperature"],
            "data": {"vibration": 10.0, "temperature": 50.0},
        },
    }
    result = validator.validate_message_envelope(message)
    assert result.is_valid
    assert not result.errors


def test_validate_sensor_values_out_of_range():
    validator = SensorValidator()
    result = validator.validate_sensor_values(
        ["vibration"], {"vibration": 150.0}  # Above range
    )
    assert not result.is_valid or result.warnings  # Depends on strict_mode