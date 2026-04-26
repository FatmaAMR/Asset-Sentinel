"""
Database connection for motor_dynamic (producer).
Manages file ingestion registry to prevent duplicate processing.
"""

import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config.settings import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class FileRegistry(Base):
    """Track which files have been successfully ingested."""
    __tablename__ = "file_registry"

    id = Column(Integer, primary_key=True, index=True)
    file_key = Column(String, unique=True, index=True)  # Full file path
    file_name = Column(String, index=True)
    total_rows = Column(Integer, default=0)
    windows_published = Column(Integer, default=0)
    success = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class DatabaseConnection:
    """Manages DB connections for producer."""

    def __init__(self, db_url: str = settings.DATABASE_URL):
        self.engine = create_engine(db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized at {db_url}")

    def get_session(self) -> Session:
        return self.SessionLocal()

    def close(self):
        self.engine.dispose()


# Singleton instance
_db_connection: Optional[DatabaseConnection] = None


def init_db() -> DatabaseConnection:
    """Initialize database connection."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def get_session() -> Session:
    """Get a database session."""
    db = init_db()
    return db.get_session()


def is_already_ingested(session: Session, file_key: str) -> bool:
    """Check if file was already ingested successfully."""
    record = session.query(FileRegistry).filter(
        FileRegistry.file_key == file_key,
        FileRegistry.success == True
    ).first()
    return record is not None


def mark_ingested(
    session: Session,
    file_key: str,
    file_name: str,
    total_rows: int,
    windows_published: int,
    success: bool,
    error_message: Optional[str] = None,
) -> None:
    """Mark a file as ingested."""
    record = session.query(FileRegistry).filter(
        FileRegistry.file_key == file_key
    ).first()

    if record:
        record.total_rows = total_rows
        record.windows_published = windows_published
        record.success = success
        record.error_message = error_message
    else:
        record = FileRegistry(
            file_key=file_key,
            file_name=file_name,
            total_rows=total_rows,
            windows_published=windows_published,
            success=success,
            error_message=error_message,
        )
        session.add(record)

    session.commit()
    logger.debug(f"Marked {file_name} as {'successful' if success else 'failed'}")