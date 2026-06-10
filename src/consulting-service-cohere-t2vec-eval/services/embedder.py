"""
services/embedder.py
─────────────────────
Two distinct embedder classes:

  PdfEmbedder    — global knowledge-base PDF/TXT chunks
  ─────────────
  • Cohere text embedding only (1024-d, cosine).
  • input_type="search_document" at ingest, "search_query" at query time.
  • Collection: settings.chroma_collection ("maintenance_manuals").

  SensorEmbedder — per-machine sensor window events
  ──────────────
  Supports THREE embedding modes, selected per-operation:

    SENSOR_ONLY   (default for diagnose / machine-query)
      Vector = TS2Vec 256-d numerical embedding of raw readings.
      Similarity is driven entirely by the actual sensor values —
      temperature trends, vibration patterns, pressure dynamics.
      The Cohere text is stored as the ChromaDB document (for LLM context)
      but does NOT influence the distance calculation.

    TEXT_ONLY
      Vector = Cohere text 1024-d.
      Useful when window_sliding is unavailable or sparse.

    FUSED         (default for ingest — stores both for maximum recall)
      Vector = L2-norm( TS2Vec 256-d || Cohere text 1024-d ) → 1280-d.
      Combines both signals.

  Why SENSOR_ONLY for diagnose?
    The whole point of diagnose is to find historical windows whose SENSOR
    READINGS match the current live readings.  If Cohere text dominates
    (80 % of the 1280-d fused vector), two windows with identical sensor
    values but different label strings can score far apart, while windows
    with the same label but completely different physical readings can score
    close.  SENSOR_ONLY eliminates that distortion and lets the numerical
    temporal features determine similarity.

  Collection name: "sensor_{machine_id}"
"""

from __future__ import annotations

import logging
from enum import Enum

import numpy as np
import cohere
import chromadb

from config import settings
from services.sensor_normalizer import normalize
from services.ts2vec_embedder   import get_ts2vec_encoder, SENSOR_EMBED_DIM

logger = logging.getLogger("embedder")

COHERE_BATCH_LIMIT = 96
COHERE_DIM         = 1024
FUSED_DIM          = COHERE_DIM + SENSOR_EMBED_DIM   # 1280


class EmbedMode(str, Enum):
    SENSOR_ONLY = "sensor_only"   # TS2Vec 256-d  — similarity driven by raw numbers
    TEXT_ONLY   = "text_only"     # Cohere 1024-d — similarity driven by text
    FUSED       = "fused"         # concat + L2-norm → 1280-d


# ── Shared Cohere client ──────────────────────────────────────────────────────

_cohere_client: cohere.Client | None = None


def _get_cohere_client() -> cohere.Client:
    global _cohere_client
    if _cohere_client is None:
        if not settings.cohere_api_key:
            raise RuntimeError(
                "COHERE_API_KEY is not set. Add it to your .env: COHERE_API_KEY=your-key"
            )
        _cohere_client = cohere.Client(api_key=settings.cohere_api_key)
        logger.info("Cohere client initialised (model: %s).", settings.embed_model)
    return _cohere_client


def _embed_text_sync(texts: list[str], input_type: str) -> list[list[float]]:
    """
    Blocking Cohere embed call.
    input_type: "search_document" (ingest) | "search_query" (query)
    """
    response = _get_cohere_client().embed(
        texts           = texts,
        model           = settings.embed_model,
        input_type      = input_type,
        embedding_types = ["float"],
    )
    return response.embeddings.float


# ══════════════════════════════════════════════════════════════════════════════
# PdfEmbedder
# ══════════════════════════════════════════════════════════════════════════════

class PdfEmbedder:
    """Cohere-only embedder for global PDF/TXT knowledge-base chunks."""

    def __init__(self, collection: chromadb.Collection) -> None:
        self.collection = collection

    def build(self, chunks: list[dict]) -> dict:
        if not chunks:
            return {"chunks_added": 0, "total_chunks": self.collection.count()}

        existing   = set(self.collection.get(include=[])["ids"])
        new_chunks = [c for c in chunks if c["id"] not in existing]
        if not new_chunks:
            logger.info("PdfEmbedder: all chunks already stored.")
            return {"chunks_added": 0, "total_chunks": self.collection.count()}

        batch_size = min(settings.embed_batch_size, COHERE_BATCH_LIMIT)
        logger.info("PdfEmbedder: embedding %d chunks into '%s'…", len(new_chunks), self.collection.name)

        for i in range(0, len(new_chunks), batch_size):
            batch  = new_chunks[i : i + batch_size]
            texts  = [c["text"] for c in batch]
            embeds = _embed_text_sync(texts, "search_document")
            self.collection.add(
                ids        = [c["id"] for c in batch],
                documents  = texts,
                embeddings = embeds,
                metadatas  = [{
                    "source":        c["source"],
                    "page":          c["page"],
                    "original_text": c["text"],
                    "embed_type":    "pdf_cohere",
                } for c in batch],
            )

        total = self.collection.count()
        logger.info("PdfEmbedder: '%s' → %d total.", self.collection.name, total)
        return {"chunks_added": len(new_chunks), "total_chunks": total}

    def query(self, question: str, top_k: int | None = None) -> list[dict]:
        top_k = top_k or settings.rag_top_k
        if self.collection.count() == 0:
            return []
        emb = _embed_text_sync([question], "search_query")[0]
        res = self.collection.query(
            query_embeddings = [emb],
            n_results        = min(top_k, self.collection.count()),
            include          = ["documents", "metadatas", "distances"],
        )
        return [
            {
                "text":     doc,
                "source":   res["metadatas"][0][i].get("source", ""),
                "page":     res["metadatas"][0][i].get("page", 0),
                "distance": round(res["distances"][0][i], 4),
            }
            for i, doc in enumerate(res["documents"][0])
        ]

    def delete_by_source(self, source: str) -> int:
        ids = self.collection.get(where={"source": source}, include=[]).get("ids", [])
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)

    def delete_chunks(self, where: dict | None = None, ids: list[str] | None = None) -> int:
        if ids:
            self.collection.delete(ids=ids)
            return len(ids)
        if where:
            found = self.collection.get(where=where, include=[]).get("ids", [])
            if found:
                self.collection.delete(ids=found)
            return len(found)
        return 0

    def reset(self) -> int:
        total = self.collection.count()
        if total:
            self.collection.delete(ids=self.collection.get(include=[])["ids"])
        return total


# ══════════════════════════════════════════════════════════════════════════════
# SensorEmbedder
# ══════════════════════════════════════════════════════════════════════════════

class SensorEmbedder:
    """
    Fused embedder for per-machine sensor window events.

    Ingest  → FUSED mode   : stores Cohere(1024) + TS2Vec(256) = 1280-d vector.
    Diagnose / machine-query → SENSOR_ONLY mode : queries with TS2Vec 256-d only.

    The stored vector is always FUSED (1280-d) so a single collection supports
    both modes.  At query time, SENSOR_ONLY pads the Cohere slot with zeros,
    which zeroes out the text contribution and lets the TS2Vec 256-d slot
    alone drive the cosine distance.

    Collection name convention: "sensor_{machine_id}"
    """

    def __init__(self, collection: chromadb.Collection) -> None:
        self.collection = collection
        self._ts2vec    = get_ts2vec_encoder()

    # ── Vector builders ────────────────────────────────────────────────────────

    def _ts2vec_vec(self, window_sliding: object) -> np.ndarray:
        """256-d TS2Vec numerical embedding, L2-normalised."""
        v    = self._ts2vec.encode(window_sliding)   # float32 (256,)
        norm = np.linalg.norm(v)
        return (v / norm) if norm > 1e-8 else v

    def _cohere_vec(self, text: str, input_type: str) -> np.ndarray:
        """1024-d Cohere text embedding, L2-normalised."""
        v    = np.array(_embed_text_sync([text], input_type)[0], dtype=np.float32)
        norm = np.linalg.norm(v)
        return (v / norm) if norm > 1e-8 else v

    def _build_vector(
        self,
        text:           str,
        window_sliding: object | None,
        input_type:     str,
        mode:           EmbedMode,
    ) -> list[float]:
        """
        Build the stored/query vector according to the chosen EmbedMode.

        SENSOR_ONLY  → [zeros(1024) | ts2vec(256)]   (1280-d, text slot = 0)
        TEXT_ONLY    → [cohere(1024) | zeros(256)]   (1280-d, sensor slot = 0)
        FUSED        → [cohere(1024) | ts2vec(256)]  (1280-d, both active)

        All three produce a 1280-d vector so the same collection is compatible
        with all modes.  Cosine distance on a zero-padded slot ignores that slot,
        giving pure TS2Vec similarity for SENSOR_ONLY and pure Cohere similarity
        for TEXT_ONLY — without needing separate collections.
        """
        if mode == EmbedMode.SENSOR_ONLY:
            if window_sliding is None:
                logger.warning(
                    "SensorEmbedder SENSOR_ONLY requested but window_sliding is None — "
                    "falling back to TEXT_ONLY."
                )
                mode = EmbedMode.TEXT_ONLY
            else:
                ts_part     = self._ts2vec_vec(window_sliding)       # (256,)
                cohere_part = np.zeros(COHERE_DIM, dtype=np.float32) # (1024,) zeros
                fused       = np.concatenate([cohere_part, ts_part]) # (1280,)
                # Already normalised (ts_part is unit-norm, cohere is zeros)
                return fused.tolist()

        if mode == EmbedMode.TEXT_ONLY:
            cohere_part  = self._cohere_vec(text, input_type)        # (1024,)
            sensor_part  = np.zeros(SENSOR_EMBED_DIM, dtype=np.float32)
            fused        = np.concatenate([cohere_part, sensor_part])
            return fused.tolist()

        # FUSED
        cohere_part = self._cohere_vec(text, input_type)
        if window_sliding is not None:
            ts_part = self._ts2vec_vec(window_sliding)
        else:
            ts_part = np.zeros(SENSOR_EMBED_DIM, dtype=np.float32)
        # Both parts are already individually L2-normalised — do NOT jointly
        # re-normalise here.  Joint re-norm scales the ts2vec slot down by
        # ~1/√2, which causes SENSOR_ONLY queries (zeros | ts2vec) to score
        # 0.293 distance instead of 0.0 against the same window.
        fused = np.concatenate([cohere_part, ts_part])
        return fused.tolist()

    # ── Ingest (FUSED — stores both signals) ──────────────────────────────────

    def build(self, chunks: list[dict], window_sliding: object | None = None) -> dict:
        """
        Store sensor window chunks using FUSED mode (Cohere + TS2Vec, 1280-d).

        Storing FUSED means the collection supports all three query modes:
          • SENSOR_ONLY queries zero out the Cohere slot → pure TS2Vec similarity
          • TEXT_ONLY   queries zero out the TS2Vec slot → pure Cohere similarity
          • FUSED       queries use both slots
        """
        if not chunks:
            return {"chunks_added": 0, "total_chunks": self.collection.count()}

        existing   = set(self.collection.get(include=[])["ids"])
        new_chunks = [c for c in chunks if c["id"] not in existing]
        if not new_chunks:
            logger.info("SensorEmbedder: all chunks already stored.")
            return {"chunks_added": 0, "total_chunks": self.collection.count()}

        logger.info(
            "SensorEmbedder: ingesting %d chunks into '%s' [FUSED 1280-d]…",
            len(new_chunks), self.collection.name,
        )

        for chunk in new_chunks:
            norm_text = normalize(chunk["text"])
            vec = self._build_vector(
                text           = norm_text,
                window_sliding = window_sliding,
                input_type     = "search_document",
                mode           = EmbedMode.FUSED,
            )
            self.collection.add(
                ids        = [chunk["id"]],
                documents  = [norm_text],
                embeddings = [vec],
                metadatas  = [{
                    "source":        chunk["source"],
                    "page":          chunk["page"],
                    "original_text": chunk["text"],
                    "embed_type":    "sensor_fused",
                }],
            )

        total = self.collection.count()
        logger.info("SensorEmbedder: '%s' → %d total.", self.collection.name, total)
        return {"chunks_added": len(new_chunks), "total_chunks": total}

    # ── Query ──────────────────────────────────────────────────────────────────

    def query(
        self,
        query_text:     str,
        top_k:          int | None    = None,
        window_sliding: object | None = None,
        mode:           EmbedMode     = EmbedMode.SENSOR_ONLY,
    ) -> list[dict]:
        """
        Find the top-k most similar historical sensor windows.

        Parameters
        ----------
        query_text     : normalised text of the current window (from window_event_to_chunks)
        window_sliding : raw sensor readings list[dict] for the TS2Vec component
        mode           : which embedding drives similarity
            SENSOR_ONLY (default) — similarity = TS2Vec cosine on raw numbers
                                     → finds windows with matching sensor dynamics
            TEXT_ONLY             — similarity = Cohere cosine on normalised text
                                     → finds windows with matching labels/descriptions
            FUSED                 — both signals contribute
        top_k          : number of results to return

        Returns
        -------
        list[dict] with keys: text, source, page, distance, similarity_mode
        """
        top_k = top_k or settings.rag_top_k
        if self.collection.count() == 0:
            logger.warning("SensorEmbedder: collection '%s' is empty.", self.collection.name)
            return []

        if mode == EmbedMode.SENSOR_ONLY and window_sliding is None:
            logger.warning(
                "SENSOR_ONLY query but window_sliding=None — falling back to TEXT_ONLY."
            )
            mode = EmbedMode.TEXT_ONLY

        logger.info(
            "SensorEmbedder.query [%s] mode=%s top_k=%d",
            self.collection.name, mode.value, top_k,
        )

        vec = self._build_vector(
            text           = normalize(query_text),
            window_sliding = window_sliding,
            input_type     = "search_query",
            mode           = mode,
        )

        res = self.collection.query(
            query_embeddings = [vec],
            n_results        = min(top_k, self.collection.count()),
            include          = ["documents", "metadatas", "distances"],
        )

        return [
            {
                "text":            doc,
                "source":          res["metadatas"][0][i].get("source", ""),
                "page":            res["metadatas"][0][i].get("page", 0),
                "distance":        round(res["distances"][0][i], 4),
                "similarity_mode": mode.value,
            }
            for i, doc in enumerate(res["documents"][0])
        ]

    # ── Helpers ────────────────────────────────────────────────────────────────

    def delete_by_source(self, source: str) -> int:
        ids = self.collection.get(where={"source": source}, include=[]).get("ids", [])
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)

    def delete_chunks(self, where: dict | None = None, ids: list[str] | None = None) -> int:
        if ids:
            self.collection.delete(ids=ids)
            return len(ids)
        if where:
            found = self.collection.get(where=where, include=[]).get("ids", [])
            if found:
                self.collection.delete(ids=found)
            return len(found)
        return 0

    def reset(self) -> int:
        total = self.collection.count()
        if total:
            self.collection.delete(ids=self.collection.get(include=[])["ids"])
        return total


# Back-compat alias
Embedder = PdfEmbedder