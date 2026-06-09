"""
schemas/rag_schemas.py
───────────────────────
Pydantic schemas for RAG request / response.
"""

from __future__ import annotations
import json
from pydantic import BaseModel, Field, model_validator
from typing import Any, List, Optional


# ── Ask ───────────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str
    top_k:    int = 4


class SourceRef(BaseModel):
    file:    str
    page:    int
    content: str


class AskResponse(BaseModel):
    question: str
    answer:   str
    sources:  List[SourceRef]
    intent:   str = "RAG"


# ── Ingest (file upload) ──────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    folder: Optional[str] = "./knowledge"


class IngestResponse(BaseModel):
    status:        str
    chunks_added:  int
    total_chunks:  int


# ── Window ingest ─────────────────────────────────────────────────────────────

class WindowIngestRequest(BaseModel):
    """
    Payload sent by the prediction service after every inference window.

    Fields mirror the producer's call:
        machine_id=machine_id,
        label=label,
        rul=rul,
        window_sliding=make_window_data(),
        message_id=str(uuid.uuid4()),
        timestamp=time.time(),
        reason=reason,
    """
    machine_id:     str  = Field(...,  description="Unique machine identifier")
    label:          str  = Field(...,  description="Predicted fault / condition label")
    rul:            float = Field(..., description="Remaining Useful Life (cycles or hours)")
    window_sliding: Any  = Field(...,  description="Sliding-window sensor data — list of readings or dict")
    message_id:     str  = Field(...,  description="Unique event UUID")
    timestamp:      float = Field(..., description="Unix timestamp of the event")
    reason:         str  = Field("",   description="Free-text annotation / reason for this window")

    @model_validator(mode="before")
    @classmethod
    def _decode_window_sliding(cls, values: Any) -> Any:
        """
        If window_sliding arrived as a JSON string (double-encoded by the client),
        decode it transparently so downstream code always sees a list/dict.
        """
        if isinstance(values, dict):
            ws = values.get("window_sliding")
            if isinstance(ws, str):
                try:
                    values["window_sliding"] = json.loads(ws)
                except json.JSONDecodeError:
                    pass  # leave as-is; Pydantic will surface the type error
        return values


class WindowIngestResponse(BaseModel):
    status:       str
    machine_id:   str
    message_id:   str
    chunks_added: int
    total_chunks: int


# ── Diagnose ──────────────────────────────────────────────────────────────────

class DiagnoseRequest(BaseModel):
    """
    Mirrors WindowIngestRequest so the diagnose path uses window_event_to_chunks()
    identically to the ingest path — same chunk text → same vector space.
    """
    machine_id:     str   = Field(...,  description="Unique machine identifier")
    label:          str   = Field(...,  description="Predicted fault / condition label")
    rul:            float = Field(...,  description="Remaining Useful Life (cycles or hours)")
    window_sliding: Any   = Field(...,  description="Sliding-window sensor data — list of readings or dict")
    message_id:     str   = Field(...,  description="Unique event UUID")
    timestamp:      float = Field(...,  description="Unix timestamp of the event")
    top_k:          int   = Field(5,    description="Number of similar historical cases to retrieve")

    @model_validator(mode="before")
    @classmethod
    def _decode_window_sliding(cls, values: Any) -> Any:
        """
        If window_sliding arrived as a JSON string (double-encoded by the client),
        decode it transparently so downstream code always sees a list/dict.
        """
        if isinstance(values, dict):
            ws = values.get("window_sliding")
            if isinstance(ws, str):
                try:
                    values["window_sliding"] = json.loads(ws)
                except json.JSONDecodeError:
                    pass
        return values


class DiagnosisSource(BaseModel):
    file:     str
    page:     int
    content:  str
    distance: float


class DiagnoseResponse(BaseModel):
    machine_id:       str
    query_text:       str           # chunk text sent to embedder (window_event_to_chunks output)
    fault_cause:      str           # LLM diagnosis
    extracted_reason: str           # reason extracted from the best-matching retrieved chunk
    similarity_mode:  str           # which embedding drove similarity: sensor_only | text_only | fused
    sources:          List[DiagnosisSource]


# ── Delete / Reset ────────────────────────────────────────────────────────────

class DeleteChunksRequest(BaseModel):
    machine_id: Optional[str]       = Field(None, description="Target machine collection; None = global")
    where:      Optional[dict]      = Field(None, description="ChromaDB metadata filter")
    ids:        Optional[List[str]] = Field(None, description="Explicit chunk IDs to delete")


class DeleteChunksResponse(BaseModel):
    deleted:    int
    collection: str


class ResetRequest(BaseModel):
    machine_id: Optional[str] = Field(None, description="Machine collection to reset; None = global")


class ResetResponse(BaseModel):
    deleted:    int
    collection: str


# ── Machine Query (no reason — returns most-similar stored reason) ────────────

class MachineQueryRequest(BaseModel):
    """
    Send a live window snapshot (no reason/annotation) and retrieve the
    most similar historical window chunk together with its stored reason.

    Mirrors the ingest-window payload but omits `reason` — the service
    will find it for you from the best-matching stored chunk.
    """
    machine_id:     str   = Field(...,  description="Unique machine identifier")
    label:          str   = Field(...,  description="Predicted fault / condition label")
    rul:            float = Field(...,  description="Remaining Useful Life (cycles or hours)")
    window_sliding: Any   = Field(...,  description="Sliding-window sensor data — list of readings or dict")
    message_id:     str   = Field(...,  description="Unique event UUID")
    timestamp:      float = Field(...,  description="Unix timestamp of the event")
    top_k:          int   = Field(5,    description="How many similar chunks to retrieve")

    @model_validator(mode="before")
    @classmethod
    def _decode_window_sliding(cls, values: Any) -> Any:
        if isinstance(values, dict):
            ws = values.get("window_sliding")
            if isinstance(ws, str):
                try:
                    values["window_sliding"] = json.loads(ws)
                except json.JSONDecodeError:
                    pass
        return values


class SimilarWindowMatch(BaseModel):
    """One matching historical window chunk."""
    rank:           int
    distance:       float
    source:         str
    stored_reason:  str   = Field(...,  description="The reason/annotation stored at ingest time")
    text_preview:   str   = Field(...,  description="First 200 chars of the matched chunk text")
    full_text:      str   = Field(...,  description="Complete matched chunk text")


class MachineQueryResponse(BaseModel):
    machine_id:      str
    message_id:      str
    query_text:      str                  = Field(..., description="Normalised query sent to the vector store")
    best_reason:     str                  = Field(..., description="Reason from the single most-similar stored chunk")
    best_distance:   float
    similarity_mode: str                  = Field(..., description="sensor_only | text_only | fused")
    matches:         list[SimilarWindowMatch]
