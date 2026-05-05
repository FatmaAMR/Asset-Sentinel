"""
services/pdf_loader.py
───────────────────────
Reads PDFs from a folder, extracts text page by page,
and splits into overlapping chunks ready for embedding.
"""

import os
import logging
import pdfplumber
import re

logger = logging.getLogger("pdf_loader")

# Chunk tuning — adjust if answers feel too narrow or too broad
CHUNK_SIZE    = 500   # characters per chunk
CHUNK_OVERLAP = 50    # overlap between consecutive chunks


def load_pdfs(folder: str) -> list[dict]:
    """
    Walk folder, read every PDF, return list of chunks.

    Each chunk:
    {
        "id":     unique string  (filename_pN_chunkIndex),
        "source": "motor_manual.pdf",
        "page":   3,
        "text":   "...chunk text...",
    }
    """
    if not os.path.isdir(folder):
        logger.warning("Knowledge folder not found: %s", folder)
        return []

    chunks = []
    pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]

    if not pdf_files:
        logger.warning("No PDF files found in: %s", folder)
        return []

    for filename in pdf_files:
        filepath = os.path.join(folder, filename)
        logger.info("Loading: %s", filename)

        try:
            with pdfplumber.open(filepath) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()

                    # Skip empty or near-empty pages
                    if not text or len(text.strip()) < 50:
                        continue

                    # Split page text into overlapping chunks
                    page_chunks = _chunk_text(text.strip(), CHUNK_SIZE, CHUNK_OVERLAP)

                    for i, chunk_text in enumerate(page_chunks):
                        chunks.append({
                            "id":     f"{filename}_p{page_num}_{i}",
                            "source": filename,
                            "page":   page_num + 1,
                           "text":   _clean_text(chunk_text),
                        })

        except Exception as exc:
            logger.error("Failed to load %s: %s", filename, exc)

    logger.info("Total chunks extracted: %d from %d PDFs", len(chunks), len(pdf_files))
    return chunks


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks of `size` characters."""
    chunks = []
    start  = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks
def _clean_text(text: str) -> str:
    """Clean raw PDF text before storing in ChromaDB."""
    text = re.sub(r'\n+', ' ', text)          # newlines → single space
    text = re.sub(r'\s{2,}', ' ', text)       # collapse multiple spaces
    text = re.sub(r'- ', '', text)             # remove hyphenated line breaks
    return text.strip()