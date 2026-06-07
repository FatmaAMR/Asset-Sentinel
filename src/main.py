import os
import signal
import subprocess
import sys
from pathlib import Path
import time

BASE = Path(__file__).resolve().parent


def main():
    print("\n" + "=" * 80)
    print("[Master] Starting Asset-Sentinel Pipeline")
    print("=" * 80 + "\n")

    # Step 1: Run motor_dynamic (producer) - publishes messages and exits
    print("[Step 1] Starting Motor Data Ingestion (Producer)...")
    producer = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=BASE / "motor_dynamic",
        env=os.environ.copy(),
    )
    producer.wait()
    print("\n[Step 1] Producer completed. Messages published to RabbitMQ.\n")

    # Small delay to ensure messages are processed
    time.sleep(1)

    # Step 2: Run forecasting-service consumer - stays alive consuming from queue
    print("[Step 2] Starting Forecasting Service Consumer (Consumer)...")
    print("[Step 2] Consumer will process messages from the queue...")
    print("[Step 2] Press Ctrl+C to stop the consumer.\n")

    consumer = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=BASE / "forecasting-service",
        env=os.environ.copy(),
    )

    def _shutdown(signum, frame):
        print("\n\n[Master] Shutting down consumer...")
        if consumer.poll() is None:
            consumer.terminate()
            consumer.wait()
        print("[Master] Consumer stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Keep the main process alive while consumer runs
    consumer.wait()


if __name__ == "__main__":
    main()