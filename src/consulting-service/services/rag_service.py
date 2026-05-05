"""
services/rag_service.py
────────────────────────
Core RAG logic:
  1. Query ChromaDB for relevant PDF chunks
  2. Build prompt with retrieved context
  3. Send to local LLM for reasoning
  4. Parse output into structured fields
  5. Return clean answer + source references
"""

import re
import logging
from dataclasses import dataclass
from services.embedder     import Embedder
from services.llama_client import LlamaClient

logger = logging.getLogger("rag_service")


@dataclass
class ParsedAnswer:
    overview: str
    details:  str
    summary:  str

    def to_text(self) -> str:
        """Return the answer as flat plain text."""
        return self.overview or self.details


class RAGService:

    def __init__(self, embedder: Embedder, llama: LlamaClient):
        self.embedder = embedder
        self.llama    = llama

    # ── Main entry point ──────────────────────────────────────────────────────

    async def ask(self, question: str, top_k: int = 4) -> dict:
        chunks = self.embedder.query(question, top_k=top_k)

        if not chunks:
            return {
                "question": question,
                "answer":   "No knowledge base available. Please ingest PDF manuals first.",
                "sources":  [],
            }

        prompt     = self._build_prompt(question, chunks)
        logger.info("Sending to LLM — question: %s", question[:80])
        raw_answer = await self.llama.complete(prompt)

        parsed = self._parse(raw_answer)
        answer = self._clean(parsed.to_text())

        seen    = set()
        sources = []
        for c in chunks:
            key = (c["source"], c["page"])
            if key not in seen:
                seen.add(key)
                sources.append({
                    "file":    c["source"],
                    "page":    c["page"],
                    "content": c["text"],
                })

        return {
            "question": question,
            "answer":   answer,
            "sources":  sources,
        }

    # ── Prompt builder ────────────────────────────────────────────────────────

    def _build_prompt(self, question: str, chunks: list[dict]) -> str:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Excerpt {i} - {chunk['source']}, page {chunk['page']}]\n"
                f"{chunk['text']}"
            )
        context = "\n\n".join(context_parts)

        return f"""You are a senior industrial machinery expert. Answer the question directly and clearly using only the excerpts below.

- Plain text only. No markdown, no symbols, no sections.
- Be concise, accurate, and practical. Include specific values and units from the excerpts.
- Cite facts inline like (Excerpt 1, page 5).
- Do not start with "Based on" or "According to".
- If the answer is not in the excerpts respond with only: <not_found>This information is not covered in the available maintenance manuals.</not_found>
- Never invent information.

Excerpts:
{context}

Question: {question}

Answer:"""

    # ── Output parser ─────────────────────────────────────────────────────────

    def _parse(self, raw: str) -> ParsedAnswer:
        """Extract answer from flat response — no section tags."""
        not_found = re.search(r'<not_found>(.*?)</not_found>', raw, re.DOTALL)
        if not_found:
            return ParsedAnswer(overview=not_found.group(1).strip(), details="", summary="")

        return ParsedAnswer(overview="", details=raw.strip(), summary="")

    def _extract_tag(self, text: str, tag: str) -> str:
        match = re.search(rf'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
        return match.group(1).strip() if match else ""

    # ── Answer cleaner ────────────────────────────────────────────────────────

    def _clean(self, text: str) -> str:
        """Strip any markdown symbols and normalize whitespace."""
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = text.replace('\\n', ' ')
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.replace('\\', '')
        text = re.sub(r'  +', ' ', text)
        return text.strip()