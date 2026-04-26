"""
Forecasting-service configuration settings.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")


class Settings:
    # RabbitMQ
    RABBITMQ_URL = os.getenv(
        "RABBITMQ_URL",
        "amqps://burraqtq:yFx0LDD76FrrDRFLhd2Wk_R68YfwhG00@cow.rmq2.cloudamqp.com/burraqtq"
    )
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "motor_exchange")
    RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "motor.raw")
    RABBITMQ_ROUTING_KEY = os.getenv("RABBITMQ_ROUTING_KEY", "motor.raw")
    RABBITMQ_DLX_QUEUE = os.getenv("RABBITMQ_DLX_QUEUE", "motor.raw.dlx")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shared.db")

    # General
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    STRICT_VALIDATION = os.getenv("STRICT_VALIDATION", "false").lower() == "true"


settings = Settings()