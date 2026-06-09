"""
services/rag_service.py
────────────────────────
Core RAG logic:
  1. Query ChromaDB for relevant PDF chunks
  2. Build prompt with retrieved context
  3. Send to master-llm-service via LLMClient
  4. Parse output into structured fields
  5. Return clean answer + source references
"""

import re
import logging
from dataclasses import dataclass
from services.embedder  import Embedder
from services.llm_client   import LLMClient          # ← was LlamaClient

logger = logging.getLogger("rag_service")


@dataclass
class ParsedAnswer:
    overview: str
    details:  str
    summary:  str

    def to_text(self) -> str:
        return self.overview or self.details


class RAGService:

    def __init__(self, embedder: Embedder, llm: LLMClient):   # ← was llama: LlamaClient
        self.embedder = embedder
        self.llm      = llm                                    # ← was self.llama

    # ── Main entry point ──────────────────────────────────────────────────────

    async def ask(self, question: str, top_k: int = 4) -> dict:
        chunks = self.embedder.query(question, top_k=top_k)

        if not chunks:
            return {
                "question": question,
                "answer":   "No knowledge base available. Please ingest PDF manuals first.",
                "sources":  [],
            }

        prompt = self._build_prompt(question, chunks)
        logger.info("Sending to LLM — question: %s", question[:80])

        raw_answer = await self.llm.generate(         # ← was self.llama.complete(prompt)
            prompt=prompt,
            caller="consulting",
            system_prompt=(
                "You are a senior industrial machinery expert. "
                "Answer using only the provided excerpts. "
                "Plain text only, no markdown."
            ),
            temperature=0.2,                          # low = factual/consistent
            max_tokens=1024,
        )

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

        return (
            f"Excerpts:\n{context}\n\n"           # system_prompt carries the rules,
            f"Question: {question}\n\n"            # so prompt is just context + question
            f"Answer:"
        )

    # ── Output parser ─────────────────────────────────────────────────────────

    def _parse(self, raw: str) -> ParsedAnswer:
        not_found = re.search(r'<not_found>(.*?)</not_found>', raw, re.DOTALL)
        if not_found:
            return ParsedAnswer(overview=not_found.group(1).strip(), details="", summary="")
        return ParsedAnswer(overview="", details=raw.strip(), summary="")

    def _extract_tag(self, text: str, tag: str) -> str:
        match = re.search(rf'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
        return match.group(1).strip() if match else ""

    # ── Answer cleaner ────────────────────────────────────────────────────────

    def _clean(self, text: str) -> str:
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = text.replace('\\n', ' ')
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.replace('\\', '')
        text = re.sub(r'  +', ' ', text)
        return text.strip()