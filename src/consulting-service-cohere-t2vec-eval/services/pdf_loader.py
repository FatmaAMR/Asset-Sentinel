"""
services/pdf_loader.py
───────────────────────
Reads PDFs (and .txt files) from a folder, extracts text page by page,
and splits into overlapping chunks ready for embedding.

Chunk sizes differ by context:
  • Global knowledge base  → larger chunks (denser reference text)
  • Per-machine collection → smaller chunks (precise fault matching)
"""

import os
import logging
import pdfplumber
import re
from enum import Enum

logger = logging.getLogger("pdf_loader")


# ── Chunk profiles ────────────────────────────────────────────────────────────

class ChunkProfile(str, Enum):
    GLOBAL  = "global"   # large chunks for reference manuals / standards
    MACHINE = "machine"  # small chunks for machine-specific fault records


_CHUNK_CONFIG: dict[ChunkProfile, dict] = {
    ChunkProfile.GLOBAL: {
        "size":    800,   # characters per chunk — richer context per hit
        "overlap": 100,   # generous overlap so concepts don't split badly
    },
    ChunkProfile.MACHINE: {
        "size":    400,   # smaller → more targeted fault matching
        "overlap": 60,
    },
}


# ── Public loader ─────────────────────────────────────────────────────────────

def load_documents(folder: str, profile: ChunkProfile = ChunkProfile.GLOBAL) -> list[dict]:
    """
    Walk *folder*, read every PDF and TXT file, return a flat list of chunks.

    Each chunk:
    {
        "id":     unique string  (filename_pN_chunkIndex  OR  filename_chunkIndex),
        "source": "motor_manual.pdf",
        "page":   3,          # 0 for .txt files
        "text":   "...chunk text...",
    }

    Args:
        folder:  Directory to scan.
        profile: ChunkProfile.GLOBAL or ChunkProfile.MACHINE — controls chunk size.
    """
    if not os.path.isdir(folder):
        logger.warning("Knowledge folder not found: %s", folder)
        return []

    cfg         = _CHUNK_CONFIG[profile]
    chunk_size  = cfg["size"]
    overlap     = cfg["overlap"]

    chunks: list[dict] = []
    all_files = os.listdir(folder)

    pdf_files = [f for f in all_files if f.lower().endswith(".pdf")]
    txt_files = [f for f in all_files if f.lower().endswith(".txt")]

    if not pdf_files and not txt_files:
        logger.warning("No PDF or TXT files found in: %s", folder)
        return []

    logger.info(
        "Loading from '%s' with profile=%s (chunk_size=%d, overlap=%d) — "
        "%d PDF(s), %d TXT(s)",
        folder, profile.value, chunk_size, overlap, len(pdf_files), len(txt_files),
    )

    # ── PDFs ──────────────────────────────────────────────────────────────────
    for filename in pdf_files:
        filepath = os.path.join(folder, filename)
        logger.info("Loading PDF: %s", filename)
        try:
            with pdfplumber.open(filepath) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text or len(text.strip()) < 50:
                        continue
                    page_chunks = _chunk_text(text.strip(), chunk_size, overlap)
                    for i, chunk_text in enumerate(page_chunks):
                        chunks.append({
                            "id":     f"{filename}_p{page_num}_{i}",
                            "source": filename,
                            "page":   page_num + 1,
                            "text":   _clean_text(chunk_text),
                        })
        except Exception as exc:
            logger.error("Failed to load PDF %s: %s", filename, exc)

    # ── TXT files ─────────────────────────────────────────────────────────────
    for filename in txt_files:
        filepath = os.path.join(folder, filename)
        logger.info("Loading TXT: %s", filename)
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
            if len(raw.strip()) < 20:
                logger.warning("Skipping nearly-empty TXT file: %s", filename)
                continue
            file_chunks = _chunk_text(raw.strip(), chunk_size, overlap)
            for i, chunk_text in enumerate(file_chunks):
                chunks.append({
                    "id":     f"{filename}_chunk{i}",
                    "source": filename,
                    "page":   0,          # TXT has no pages
                    "text":   _clean_text(chunk_text),
                })
        except Exception as exc:
            logger.error("Failed to load TXT %s: %s", filename, exc)

    logger.info(
        "Total chunks extracted: %d  (PDFs: %d, TXTs: %d)",
        len(chunks), len(pdf_files), len(txt_files),
    )
    return chunks


# ── Backwards-compat alias (used in main.py / other places) ──────────────────

def load_pdfs(folder: str) -> list[dict]:
    """
    Legacy alias → loads with the GLOBAL profile.
    Kept so existing callers (main.py startup ingest) don't break.
    """
    return load_documents(folder, profile=ChunkProfile.GLOBAL)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split *text* into overlapping chunks of *size* characters."""
    chunks = []
    start  = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


def _clean_text(text: str) -> str:
    """Clean raw extracted text before storing in ChromaDB."""
    text = re.sub(r'\n+',   ' ', text)   # newlines → single space
    text = re.sub(r'\s{2,}', ' ', text)  # collapse multiple spaces
    text = re.sub(r'- ',     '',  text)  # remove hyphenated line breaks
    return text.strip()
