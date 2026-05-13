"""
Forecasting-service configuration settings.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")


class Settings:
    # RabbitMQ Connection (CloudAMQP)
    RABBITMQ_URL = os.getenv(
        "RABBITMQ_URL",
        "amqps://burraqtq:yFx0LDD76FrrDRFLhd2Wk_R68YfwhG00@cow.rmq2.cloudamqp.com/burraqtq"
    )

    # Consuming from motor_dynamic
    MOTOR_EXCHANGE = os.getenv("MOTOR_EXCHANGE", "motor_exchange")
    MOTOR_QUEUE = os.getenv("MOTOR_QUEUE", "motor.raw")
    MOTOR_ROUTING_KEY = os.getenv("MOTOR_ROUTING_KEY", "motor.raw")
    MOTOR_DLX_QUEUE = os.getenv("MOTOR_DLX_QUEUE", "motor.raw.dlx")

    # Publishing → status (direct)
    FORECASTING_EXCHANGE = os.getenv("FORECASTING_EXCHANGE", "forecasting_exchange")
    EQUIPMENT_STATUS_QUEUE = os.getenv("EQUIPMENT_STATUS_QUEUE", "equipment.status")
    EQUIPMENT_STATUS_ROUTING_KEY = os.getenv("EQUIPMENT_STATUS_ROUTING_KEY", "equipment.status")

    # Publishing → alerts notifications (direct)
    ALERTS_QUEUE = os.getenv("ALERTS_NOTIFICATIONS_QUEUE", "equipment.alerts")
    ALERTS_ROUTING_KEY = os.getenv("ALERTS_NOTIFICATIONS_ROUTING_KEY", "equipment.alerts")

    # # Publishing → alerts rag (direct)
    # ALERTS_RAG_QUEUE = os.getenv("ALERTS_RAG_QUEUE", "alerts.rag")
    # ALERTS_RAG_ROUTING_KEY = os.getenv("ALERTS_RAG_ROUTING_KEY", "alerts.rag")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shared.db")

    # General
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    STRICT_VALIDATION = os.getenv("STRICT_VALIDATION", "false").lower() == "true"


settings = Settings()