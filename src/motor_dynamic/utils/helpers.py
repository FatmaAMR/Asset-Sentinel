"""
Helpers:
  - build_envelope() : wraps a FileRecord in a MessageEnvelope
"""

from __future__ import annotations
import uuid
import time
from schemas.models import FileRecord, MessageEnvelope


def build_envelope(record: FileRecord) -> MessageEnvelope:
    """
    Wraps a FileRecord into a complete MessageEnvelope with metadata.
    """
    return MessageEnvelope(
        message_id = str(uuid.uuid4()),    # بيولد رقم فريد للرسالة
        source     = "motor_dynamic",      # بيحدد مصدر البيانات
        timestamp  = time.time(),          # بيسجل وقت الإرسال
        record     = record                # بيحط بيانات الـ window
    )