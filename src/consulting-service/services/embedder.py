"""
services/embedder.py
─────────────────────
Embeds PDF chunks using sentence-transformers and stores in ChromaDB.
All settings come from config.py / .env
"""

import logging
import chromadb
from sentence_transformers import SentenceTransformer
from config import settings

logger = logging.getLogger("embedder")


class Embedder:

    def __init__(self, collection: chromadb.Collection):
        self.collection = collection
        logger.info("Loading embedding model: %s", settings.embed_model)
        self.model = SentenceTransformer(settings.embed_model)
        logger.info("Embedding model ready.")

    def build(self, chunks: list[dict]) -> dict:
        """Embed and store chunks. Skips already-stored ones."""
        if not chunks:
            return {"chunks_added": 0, "total_chunks": self.collection.count()}

        existing_ids = set(self.collection.get(include=[])["ids"])
        new_chunks   = [c for c in chunks if c["id"] not in existing_ids]

        if not new_chunks:
            logger.info("All chunks already embedded — nothing to add.")
            return {"chunks_added": 0, "total_chunks": self.collection.count()}

        logger.info("Embedding %d new chunks...", len(new_chunks))

        batch_size = settings.embed_batch_size
        for i in range(0, len(new_chunks), batch_size):
            batch  = new_chunks[i : i + batch_size]
            texts  = [c["text"] for c in batch]
            embeds = self.model.encode(texts, show_progress_bar=False).tolist()

            self.collection.add(
                ids        = [c["id"]     for c in batch],
                documents  = [c["text"]   for c in batch],
                embeddings = embeds,
                metadatas  = [{"source": c["source"], "page": c["page"]} for c in batch],
            )
            logger.info("  Stored batch %d/%d",
                        i // batch_size + 1,
                        (len(new_chunks) - 1) // batch_size + 1)

        total = self.collection.count()
        logger.info("Knowledge base ready — %d total chunks.", total)
        return {"chunks_added": len(new_chunks), "total_chunks": total}

    def query(self, question: str, top_k: int | None = None) -> list[dict]:
        """Embed question and return top_k most relevant chunks."""
        top_k = top_k or settings.rag_top_k

        if self.collection.count() == 0:
            logger.warning("Knowledge base is empty.")
            return []

        embedding = self.model.encode(question).tolist()
        results   = self.collection.query(
            query_embeddings = [embedding],
            n_results        = min(top_k, self.collection.count()),
            include          = ["documents", "metadatas", "distances"],
        )

        return [
            {
                "text":     doc,
                "source":   results["metadatas"][0][i]["source"],
                "page":     results["metadatas"][0][i]["page"],
                "distance": round(results["distances"][0][i], 4),
            }
            for i, doc in enumerate(results["documents"][0])
        ]
