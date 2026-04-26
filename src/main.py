import os
import signal
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

SERVICES = [
    ("motor_dynamic", "main.py"),
    ("forecasting-service", "main.py"),
]


def start_process(service_dir: str, script_name: str):
    return subprocess.Popen(
        [sys.executable, script_name],
        cwd=BASE / service_dir,
        env=os.environ.copy(),
    )


def main():
    procs = [start_process(dir_, script) for dir_, script in SERVICES]

    def _shutdown(signum, frame):
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    for proc in procs:
        proc.wait()


if __name__ == "__main__":
    main()