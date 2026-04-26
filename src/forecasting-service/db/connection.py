"""
Database connection for forecasting-service (consumer).
Manages storage of prediction results.
"""

import logging
from typing import Optional
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class PredictionResult(Base):
    """Stores processed prediction results."""
    __tablename__ = "prediction_results"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True)
    file_name = Column(String, index=True)
    window_index = Column(Integer)
    prediction = Column(Text)  # JSON string
    raw_data = Column(Text)  # JSON string
    status = Column(String, default="processed")
    timestamp = Column(DateTime, default=datetime.utcnow)


class DatabaseConnection:
    """Manages DB connections for consumer."""

    def __init__(self, db_url: str = settings.DATABASE_URL):
        self.engine = create_engine(db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized at {db_url}")

    def get_session(self) -> Session:
        return self.SessionLocal()

    def insert_prediction_result(self, result: dict) -> None:
        """Insert a prediction result."""
        session = self.get_session()
        try:
            record = PredictionResult(
                message_id=result["message_id"],
                file_name=result["file_name"],
                window_index=result["window_index"],
                prediction=str(result["prediction"]),
                raw_data=str(result["raw_data"]),
                status=result.get("status", "processed"),
            )
            session.add(record)
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error(f"Failed to insert result: {exc}")
            raise
        finally:
            session.close()

    def close(self):
        self.engine.dispose()


# Singleton instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """Get a database connection instance."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection