"""
db/chroma_client.py
────────────────────
Persistent ChromaDB client — single instance shared across the service.
"""

import os
import chromadb
from config import settings

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"]     = "False"

def get_chroma_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=settings.chroma_path)
    return client.get_or_create_collection(
        name     = settings.chroma_collection,
        metadata = {"hnsw:space": "cosine"},
    )