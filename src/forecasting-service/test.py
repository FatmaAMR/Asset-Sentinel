"""
Test script for ForecastingPublisher.
"""

import time
import uuid
import logging
from schemas.models import ForecastingResult
from utils.publisher import ForecastingPublisher

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def make_window_data(rows: int = 50) -> list:
    """Generate fake 50 rows of sensor data."""
    return [
        {
            "timestamp": time.time() + i,
            "temperature": 75.0 + i * 0.5,
            "vibration": 0.3 + i * 0.01,
            "current": 10.0 + i * 0.1,
            "pressure": 1.2 + i * 0.05,
        }
        for i in range(rows)
    ]


def make_result(machine_id: str, label: str, rul: float) -> ForecastingResult:
    """Factory to build a ForecastingResult with fake window data."""
    return ForecastingResult(
        machine_id=machine_id,
        label=label,
        rul=rul,
        window_sliding=make_window_data(),
        message_id=str(uuid.uuid4()),
        timestamp=time.time(),
    )


def run_tests():
    publisher = ForecastingPublisher()

    try:
        publisher.connect()
        logger.info("Publisher connected ✓")

        cases = [
            ("normal",   make_result("M001", "normal",   500.0)),
            ("warning",  make_result("M002", "warning",  120.5)),
            ("critical", make_result("M003", "critical",  10.0)),
        ]

        for name, result in cases:
            logger.info(f"── Testing [{name}] ──────────────────────")
            publisher.publish(result=result)  # removed the stray window_data= kwarg
            logger.info(f"   message_id={result.message_id} | rul={result.rul} | label={result.label}")

        logger.info(f"── Stats: {publisher.get_stats()} ──────────")
        # normal  → 1 publish (status only)
        # warning → 2 publishes (status + alerts)
        # critical→ 2 publishes (status + alerts)
        # expected total: 5
        assert publisher.get_stats()["published"] == 5, "Publish count mismatch!"
        logger.info("All assertions passed ✓")

    except Exception as exc:
        logger.error(f"Test failed: {exc}")
        raise

    finally:
        publisher.close()
        logger.info("Publisher closed ✓")


if __name__ == "__main__":
    run_tests()