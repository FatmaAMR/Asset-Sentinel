"""
Pydantic models for the dynamic motor fault ingestion pipeline.

FileRecord      — one windowed slice from any CSV/TXT file, with dynamic columns
MessageEnvelope — exact JSON published to RabbitMQ
IngestionResult — summary returned by IngestionService.run()
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class FileRecord(BaseModel):
    """
    One window of sensor readings from a single data file.

    Columns are stored dynamically in `signals`:
        {"col_0": [1.2, 3.4, ...], "col_1": [...], ...}

    Column names come from the file header when present, or are auto-generated
    as col_0, col_1, … when the file has no header row.
    """

    # ── File identity ─────────────────────────────────────────────────────────
    file_index:  int   = Field(..., description="Zero-based index among discovered files")
    file_name:   str   = Field(..., description="Original filename (no directory)")
    file_path:   str   = Field(..., description="Absolute path")

    # ── Window location ───────────────────────────────────────────────────────
    window_index: int = Field(default=0)
    row_start:    int = Field(..., description="First row index of this window")
    row_end:      int = Field(..., description="Last row index of this window")

    # ── Dynamic signal columns ────────────────────────────────────────────────
    # Keys = column names from the file header (or col_0, col_1, …)
    # Values = list of floats for the window
    signals: Dict[str, List[float]] = Field(
        default_factory=dict,
        description="All numeric columns from the file, keyed by column name",
    )

    # ── Column metadata ───────────────────────────────────────────────────────
    column_names:  List[str] = Field(default_factory=list, description="Ordered column names")
    column_count:  int       = Field(default=0)
    has_header:    bool      = Field(default=True, description="Whether the file had a header row")

    @property
    def window_size(self) -> int:
        if not self.signals:
            return 0
        return len(next(iter(self.signals.values())))


class MessageEnvelope(BaseModel):
    """Exact JSON body sent to RabbitMQ motor.raw queue."""

    message_id:   str = Field(default_factory=lambda: str(uuid4()))
    source:       str = "local_files"
    published_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    record: FileRecord

    def to_bytes(self) -> bytes:
        return self.model_dump_json().encode("utf-8")


class IngestionResult(BaseModel):
    published: int = 0
    failed:    int = 0
    skipped:   int = 0
    errors:    List[str] = Field(default_factory=list)
