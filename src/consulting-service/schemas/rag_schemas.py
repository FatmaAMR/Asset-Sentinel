"""
schemas/rag_schemas.py
───────────────────────
Pydantic schemas for RAG request / response.
"""

from pydantic import BaseModel
from typing import List, Optional


class AskRequest(BaseModel):
    question: str
    top_k:    int = 4


class SourceRef(BaseModel):
    file:    str
    page:    int
    content: str          # chunk text used to generate the answer


class AskResponse(BaseModel):
    question: str
    answer:   str         # structured markdown: ## Overview / ## Details / ## Summary
    sources:  List[SourceRef]
    intent:   str = "RAG"


class IngestRequest(BaseModel):
    folder: Optional[str] = "./knowledge"


class IngestResponse(BaseModel):
    status:        str
    chunks_added:  int
    total_chunks:  int
