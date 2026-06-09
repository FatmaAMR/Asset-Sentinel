"""
db/chroma_client.py
────────────────────
Persistent ChromaDB client — single instance shared across the service.
Supports per-machine collections with auto-create.
"""

from __future__ import annotations  # 1. Postpones evaluation of annotations, fixing the '|' operator issue
import os
import chromadb
# 2. Import the actual type classes for static analysis / type hinting
from chromadb.api.models.Collection import Collection 
from chromadb.api.segment import SegmentAPI as ClientAPI # Chroma's underlying client class type
from config import settings

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"]     = "False"

# 3. Use ClientAPI for the type hint instead of the PersistentClient factory function
_client: ClientAPI | None = None




def get_chroma_client() -> chromadb.PersistentClient:
    """Return (or lazily create) the shared PersistentClient."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_path)
    return _client


def get_chroma_collection(collection_name: str | None = None) -> chromadb.Collection:
    """
    Return the collection for the given name.
    If collection_name is None, falls back to settings.chroma_collection.
    Auto-creates the collection if it doesn't exist.
    """
    name   = collection_name or settings.chroma_collection
    client = get_chroma_client()
    return client.get_or_create_collection(
        name     = name,
        metadata = {"hnsw:space": "cosine"},
    )


def list_collections() -> list[str]:
    """Return names of all existing collections."""
    return [c.name for c in get_chroma_client().list_collections()]


def delete_collection(collection_name: str) -> bool:
    """Delete a collection. Returns True if deleted, False if not found."""
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
        return True
    except Exception:
        return False
