"""
SQLite registry — records which files have been fully published.
Prevents re-publishing if the service restarts mid-run.

Now keyed on file_path (absolute path string) instead of file_number,
so any filename works without parsing.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)

DB_URL = "sqlite:///./ingestion_registry.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class FileRegistry(Base):
    __tablename__ = "file_registry"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    # file_key is the absolute path — unique across any directory layout
    file_key          = Column(String,  unique=True, nullable=False, index=True)
    file_name         = Column(String,  nullable=False)
    total_rows        = Column(Integer, default=0)
    windows_published = Column(Integer, default=0)
    ingested_at       = Column(DateTime(timezone=True), nullable=True)
    success           = Column(Boolean, default=True)
    error_message     = Column(String,  nullable=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Registry DB ready (SQLite)")


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def is_already_ingested(session: Session, file_key: str) -> bool:
    row = (
        session.query(FileRegistry)
        .filter(FileRegistry.file_key == file_key, FileRegistry.success == True)
        .first()
    )
    return row is not None


def mark_ingested(
    session: Session,
    file_key: str,
    file_name: str,
    total_rows: int,
    windows_published: int,
    success: bool = True,
    error_message: str | None = None,
) -> None:
    existing = (
        session.query(FileRegistry)
        .filter(FileRegistry.file_key == file_key)
        .first()
    )
    now = datetime.now(timezone.utc)
    if existing:
        existing.windows_published = windows_published
        existing.total_rows        = total_rows
        existing.ingested_at       = now
        existing.success           = success
        existing.error_message     = error_message
    else:
        session.add(FileRegistry(
            file_key=file_key,
            file_name=file_name,
            total_rows=total_rows,
            windows_published=windows_published,
            ingested_at=now,
            success=success,
            error_message=error_message,
        ))
