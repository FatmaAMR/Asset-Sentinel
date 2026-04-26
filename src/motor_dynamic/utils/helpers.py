"""
Helpers:
  - build_envelope() : wraps a FileRecord in a MessageEnvelope
"""

from __future__ import annotations

from schemas.models import FileRecord, MessageEnvelope


def build_envelope(record: FileRecord) -> MessageEnvelope:
    return MessageEnvelope(record=record)
