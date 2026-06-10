import re
import time
import logging
from dataclasses import dataclass
from services.embedder   import Embedder
from services.llm_client import LLMClient

logger = logging.getLogger("rag_service")


@dataclass
class ParsedAnswer:
    overview: str
    details:  str
    summary:  str

    def to_text(self) -> str:
        return self.overview or self.details


class RAGService:

    def __init__(self, embedder: Embedder, llm: LLMClient):
        self.embedder = embedder
        self.llm      = llm

    # ── Main entry point ──────────────────────────────────────────────────────

    async def ask(self, question: str, top_k: int = 4) -> dict:
        t0     = time.perf_counter()
        chunks = self.embedder.query(question, top_k=top_k)
        retrieve_s = time.perf_counter() - t0

        if not chunks:
            return {
                "question":   question,
                "answer":     "No knowledge base available. Please ingest PDF manuals first.",
                "sources":    [],
                "retrieve_s": round(retrieve_s, 4),
                "generate_s": 0.0,
            }

        prompt = self._build_prompt(question, chunks)
        logger.info("Sending to LLM — question: %s", question[:80])

        t0 = time.perf_counter()
        raw_answer = await self.llm.generate(
            prompt=prompt,
            caller="consulting",
            system_prompt=(
                "You are a senior industrial machinery expert. "
                "Your ONLY permitted knowledge source is the excerpts provided in the prompt. "
                "STRICT RULES — violating any rule makes your answer invalid:\n"
                "1. Answer EXCLUSIVELY from the provided excerpts. "
                    "Do not add anything that is not explicitly stated in them.\n"
                "2. If the answer is not in the excerpts, reply with exactly this sentence: "
                    "I could not find this information in the provided documents.\n"
                "3. Do NOT use prior knowledge, general expertise, or assumptions.\n"
                "4. Do NOT use phrases like based on my knowledge or generally speaking.\n"
                "5. Cite the excerpt number for every factual claim, e.g. [Excerpt 2].\n"
                "6. Plain text only — no markdown, no bullet points, no headers."
            ),
            temperature=0.1,
            max_tokens=512,
        )
        generate_s = time.perf_counter() - t0

        parsed = self._parse(raw_answer)
        answer = self._clean(parsed.to_text())

        # One source entry per chunk — do NOT dedup by (source, page) because
        # multiple chunks from the same page are distinct results and collapsing
        # them makes the response return fewer items than the requested top_k.
        seen    = set()
        sources = []
        for c in chunks:
            key = c["text"][:80]   # dedup only exact-duplicate chunk text
            if key not in seen:
                seen.add(key)
                sources.append({
                    "file":     c["source"],
                    "page":     c["page"],
                    "content":  c["text"],
                    "distance": c.get("distance", 1.0),
                })

        return {
            "question":   question,
            "answer":     answer,
            "sources":    sources,
            "retrieve_s": round(retrieve_s, 4),
            "generate_s": round(generate_s, 4),
        }

    # ── Prompt builder, parser, cleaner: unchanged ──────────────────────────

    def _build_prompt(self, question: str, chunks: list[dict]) -> str:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Excerpt {i} — {chunk['source']}, page {chunk['page']}]\n"
                f"{chunk['text']}"
            )
        context = "\n\n".join(context_parts)

        return (
            f"PROVIDED EXCERPTS — your ONLY permitted source:\n"
            f"{'─' * 60}\n"
            f"{context}\n"
            f"{'─' * 60}\n\n"
            f"QUESTION: {question}\n\n"
            f"INSTRUCTIONS:\n"
            f"- Answer using ONLY the excerpts above.\n"
            f"- Cite the excerpt number for every fact, e.g. [Excerpt 1].\n"
            f"- Do NOT add information that is not in the excerpts.\n"
            f"- If the answer is not in the excerpts, reply exactly:\n"
            f"  I could not find this information in the provided documents.\n\n"
            f"ANSWER:"
        )

    def _parse(self, raw: str) -> ParsedAnswer:
        not_found = re.search(r'<not_found>(.*?)</not_found>', raw, re.DOTALL)
        if not_found:
            return ParsedAnswer(overview=not_found.group(1).strip(), details="", summary="")
        return ParsedAnswer(overview="", details=raw.strip(), summary="")

    def _extract_tag(self, text: str, tag: str) -> str:
        match = re.search(rf'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
        return match.group(1).strip() if match else ""

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