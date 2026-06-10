"""
Configuration settings for motor_dynamic producer service.
"""

import os
from dotenv import load_dotenv
from pathlib import Path


CURRENT_FILE = Path(__file__).resolve()
ROOT_DIR = next(p for p in CURRENT_FILE.parents if p.name == "Asset-Sentinel")
load_dotenv(dotenv_path=ROOT_DIR / ".env")


class Settings:
    DATA_DIR = os.getenv(
        "DATA_DIR",
        str(ROOT_DIR / "src" / "raw"), 
    )
    print(f"Files inside raw folder: {os.listdir(DATA_DIR)}")
    RABBITMQ_URL = os.getenv(
        "RABBITMQ_URL",
        "amqps://epnwrxps:FJDX9jCp6ng-bHYxHocDRsYbBqsJ6yP3@cow.rmq2.cloudamqp.com/epnwrxps"
    )
    RABBITMQ_EXCHANGE = os.getenv("MOTOR_EXCHANGE", "motor_exchange")
    RABBITMQ_QUEUE = os.getenv("MOTOR_QUEUE", "motor.raw")
    RABBITMQ_ROUTING_KEY = os.getenv("MOTOR_ROUTING_KEY", "motor.raw")
    RABBITMQ_DLX_QUEUE = os.getenv("MOTOR_DLX_QUEUE", "motor.raw.dlx")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shared.db")

    extensions = os.getenv("EXTENSIONS", "csv,txt").split(",")
    HAS_HEADER = os.getenv("HAS_HEADER", "true").lower() == "true"
    CSV_DELIMITER = os.getenv("CSV_DELIMITER", ",")
    WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 64))
    WINDOW_STEP = int(os.getenv("WINDOW_STEP", 64))

    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()