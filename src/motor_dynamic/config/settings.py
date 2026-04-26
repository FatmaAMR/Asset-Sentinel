"""
Central config — all values come from environment variables or .env file.

The ONLY value you should ever need to change is DATA_DIR.
Everything else has sensible defaults.
"""

from __future__ import annotations
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── CHANGE THIS PATH ──────────────────────────────────────────────────────
    DATA_DIR: str =r'C:\Users\user\Downloads\grad project'

    # ── RabbitMQ ──────────────────────────────────────────────────────────────
    RABBITMQ_HOST:        str = "localhost"
    RABBITMQ_PORT:        int = 5672
    RABBITMQ_USER:        str = "guest"
    RABBITMQ_PASSWORD:    str = "guest"
    RABBITMQ_VHOST:       str = "/"
    RABBITMQ_EXCHANGE:    str = "motor_data"
    RABBITMQ_ROUTING_KEY: str = "raw"
    RABBITMQ_QUEUE:       str = "motor.raw"
    RABBITMQ_DLX_QUEUE:   str = "motor.failed"

    # ── Publisher behaviour ───────────────────────────────────────────────────
    WINDOW_SIZE: int = Field(default=1024, description="Samples per message window")
    WINDOW_STEP: int = Field(default=1024, description="Hop between windows")
    MAX_RETRIES: int = 3

    # ── File discovery ────────────────────────────────────────────────────────
    # Comma-separated list of extensions to pick up (no dots, case-insensitive)
    FILE_EXTENSIONS: str = "csv,txt"

    # ── CSV / TXT parsing ─────────────────────────────────────────────────────
    # Leave blank → auto-detect delimiter from first line of each file
    CSV_DELIMITER: str = ""

    # Set to false if your files have no header row
    HAS_HEADER: bool = True

    # ── Helpers ───────────────────────────────────────────────────────────────
    @property
    def extensions(self) -> List[str]:
        """Return cleaned list of extensions, e.g. ['csv', 'txt']."""
        return [e.strip().lower().lstrip(".") for e in self.FILE_EXTENSIONS.split(",") if e.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
