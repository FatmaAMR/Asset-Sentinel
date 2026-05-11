import os
from dotenv import load_dotenv
from pathlib import Path

# Setup paths
CURRENT_FILE = Path(__file__).resolve()
# Locating the root directory 'Asset-Sentinel'
ROOT_DIR = next(p for p in CURRENT_FILE.parents if p.name == "Asset-Sentinel")
load_dotenv(dotenv_path=ROOT_DIR / ".env")

class Settings:
    # --- RabbitMQ Base Configuration ---
    # Using your CloudAMQP URL from the provided snippet
    RABBITMQ_URL = os.getenv(
        "RABBITMQ_URL",
        "amqps://burraqtq:yFx0LDD76FrrDRFLhd2Wk_R68YfwhG00@cow.rmq2.cloudamqp.com/burraqtq"
    )
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "motor_exchange")
    
    # --- Forecasting Service Queues ---
    RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "motor.raw")
    RABBITMQ_ROUTING_KEY = os.getenv("RABBITMQ_ROUTING_KEY", "motor.raw")
    
    # --- Notification Service Queues (NEW) ---
    # These are specific for the Notification Consumer we built
    RABBITMQ_ALERT_QUEUE = os.getenv("RABBITMQ_ALERT_QUEUE", "motor.alerts")
    RABBITMQ_ALERT_ROUTING_KEY = os.getenv("RABBITMQ_ALERT_ROUTING_KEY", "alert.#")

    # --- External Service Endpoints (NEW) ---
    # Used by the Notification Dispatcher to communicate with other microservices
    CONSULTING_SERVICE_URL = os.getenv("CONSULTING_SERVICE_URL", "http://localhost:8001")
    MANAGERIAL_SERVICE_URL = os.getenv("MANAGERIAL_SERVICE_URL", "http://localhost:8002")

    # --- Database Configuration ---
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shared.db")

    # --- General App Settings ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

    # --- Data Ingestion (Kept for compatibility) ---
    DATA_DIR = os.getenv("DATA_DIR", str(ROOT_DIR / "src" / "raw"))
    WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 128))
    WINDOW_STEP = int(os.getenv("WINDOW_STEP", 64))


    # --- External Service Endpoints (Pulled from .env) ---
    # We provide a default value as a fallback
    CONSULTING_SERVICE_BASE_URL = os.getenv("CONSULTING_SERVICE_URL", "http://localhost:8001")
    MANAGERIAL_SERVICE_BASE_URL = os.getenv("MANAGERIAL_SERVICE_URL", "http://localhost:8001")

    # --- Derived Full Endpoints ---
    @property
    def consulting_api_url(self) -> str:
        return f"{self.CONSULTING_SERVICE_BASE_URL}/suggestion"

    @property
    def managerial_api_url(self) -> str:
        return f"{self.MANAGERIAL_SERVICE_BASE_URL}/staff/all"

settings = Settings()




