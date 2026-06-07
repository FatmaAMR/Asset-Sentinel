"""
Test script to verify queue publishing logic without running the full AI pipeline.
Simulates successful predictions and publishes to both queues.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from utils.publisher import ForecastingPublisher


def generate_mock_payload(should_alert: bool, predicted_rul: float = 85.26) -> dict:
    """Generate a mock status payload matching pipeline format."""
    message_id = str(uuid4())
    return {
        "metadata": {
            "message_id": message_id,
            "file_name": "test_machine.csv",
            "timestamp": datetime.utcnow().isoformat()
        },
        "processed_data": {
            "sensor_1": [1.2, 3.4, 5.6],
            "sensor_2": [2.3, 4.5, 6.7],
        },
        "labels": {
            "predicted_rul": predicted_rul,
            "health_state": "HEALTHY" if predicted_rul > 100 else "WARNING" if predicted_rul > 50 else "CRITICAL",
            "confidence": 0.9377952820865684,
            "should_alert": should_alert
        }
    }


def print_payload(payload: dict) -> None:
    """Pretty print the payload."""
    print("\n" + "=" * 80)
    print("  > Broker Payload Structure:")
    print(json.dumps(payload, indent=4))
    print("=" * 80 + "\n")


def main():
    print("\n[Test] Starting Mock Queue Publisher Test...")
    print(f"[Test] Connecting to RabbitMQ: {settings.RABBITMQ_URL[:50]}...")

    publisher = ForecastingPublisher()

    try:
        publisher.connect()

        test_cases = [
            ("HEALTHY (should_alert=false)", generate_mock_payload(should_alert=False, predicted_rul=150.0)),
            ("WARNING (should_alert=false)", generate_mock_payload(should_alert=False, predicted_rul=60.0)),
            ("CRITICAL (should_alert=true)", generate_mock_payload(should_alert=True, predicted_rul=10.0)),
        ]

        for test_name, payload in test_cases:
            print(f"\n{'─' * 80}")
            print(f"[Test Case] {test_name}")
            print_payload(payload)
            
            print(f"[Publishing] Sending to queues...")
            publisher.publish(payload)
            print(f"[Success] Published\n")

        print(f"\n{'═' * 80}")
        print(f"[Test Summary]")
        print(f"  Total Published: {publisher.get_stats()['published']}")
        print(f"  Expected: 5 messages")
        print(f"    - Test 1 (HEALTHY): 1x status + 1x alerts = 2 messages")
        print(f"    - Test 2 (WARNING): 1x status + 1x alerts = 2 messages")
        print(f"    - Test 3 (CRITICAL): 1x status (no alerts, should_alert=true) = 1 message")
        print(f"  Match: {'✅ YES' if publisher.get_stats()['published'] == 5 else '❌ NO'}")
        print(f"{'═' * 80}\n")

    except Exception as exc:
        print(f"[Error] {exc}")
        raise

    finally:
        publisher.close()
        print("[Test] Connection closed.")


if __name__ == "__main__":
    main()
