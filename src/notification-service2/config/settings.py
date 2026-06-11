import os
from pathlib import Path
from dotenv import load_dotenv

CURRENT_FILE = Path(__file__).resolve()
# Walk up until we find the project root (contains .env)
_root_candidates = [p for p in CURRENT_FILE.parents if (p / ".env").exists()]
ROOT_DIR = _root_candidates[0] if _root_candidates else CURRENT_FILE.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")


class Settings:
    # ── RabbitMQ ──────────────────────────────────────────────────────────────
    RABBITMQ_URL      = os.getenv("RABBITMQ_URL",
        "amqps://epnwrxps:FJDX9jCp6ng-bHYxHocDRsYbBqsJ6yP3@cow.rmq2.cloudamqp.com/epnwrxps")
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "motor_exchange")

    # legacy raw queue (kept for compatibility)
    RABBITMQ_QUEUE       = os.getenv("RABBITMQ_QUEUE",       "motor.raw")
    RABBITMQ_ROUTING_KEY = os.getenv("RABBITMQ_ROUTING_KEY", "motor.raw")

    # ── equipment.alerts queue ────────────────────────────────────────────────
    RABBITMQ_ALERT_QUEUE       = os.getenv("RABBITMQ_ALERT_QUEUE",       "equipment.alerts")
    RABBITMQ_ALERT_ROUTING_KEY = os.getenv("RABBITMQ_ALERT_ROUTING_KEY", "equipment.alerts")

    # ── External services ─────────────────────────────────────────────────────
    CONSULTING_SERVICE_BASE_URL = os.getenv("CONSULTING_SERVICE_URL", "http://localhost:8001")
    MANAGERIAL_SERVICE_BASE_URL = os.getenv("MANAGERIAL_SERVICE_URL", "http://localhost:8002")
    WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "ws://localhost:8765/ws/alerts")

    @property
    def consulting_diagnose_url(self) -> str:
        """POST /diagnose  — primary endpoint used by the notification service."""
        return f"{self.CONSULTING_SERVICE_BASE_URL}/rag/diagnose"

    @property
    def consulting_api_url(self) -> str:
        """Legacy RAG endpoint (kept for compatibility)."""
        return f"{self.CONSULTING_SERVICE_BASE_URL}/rag/ask"

    @property
    def managerial_api_url(self) -> str:
        return f"{self.MANAGERIAL_SERVICE_BASE_URL}/api/v1/managerial/staff/all"

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shared.db")

    # ── General ───────────────────────────────────────────────────────────────
    LOG_LEVEL   = os.getenv("LOG_LEVEL",   "INFO")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

    # ── Data ingestion (kept for compatibility) ───────────────────────────────
    DATA_DIR    = os.getenv("DATA_DIR", str(ROOT_DIR / "src" / "raw"))
    WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 64))
    WINDOW_STEP = int(os.getenv("WINDOW_STEP", 64))


settings = Settings()
