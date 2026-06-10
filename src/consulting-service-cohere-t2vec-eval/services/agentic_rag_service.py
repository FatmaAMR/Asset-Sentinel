"""
services/agentic_rag_service.py
────────────────────────────────
Agentic RAG with web search fallback (Direct Question Query version).

  Step 1 — Retrieve  : Search ChromaDB directly for the original question
  Step 2 — Reflect   : Is context sufficient? (distance-based, no LLM)
  Step 3 — Web       : If insufficient, search the web via Tavily
  Step 4 — Answer    : Generate final answer from all collected context
"""

import re
import logging
from dataclasses import dataclass, field

from services.embedder   import Embedder
from services.llm_client import LLMClient
from config import settings

logger = logging.getLogger("agentic_rag")

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_TOKENS         = 512

# Cohere v3 embeddings: good matches have cosine distance < 0.30.
# 0.40 gives a small buffer while still filtering weak hits.
DISTANCE_THRESHOLD = 0.60


# ── State ─────────────────────────────────────────────────────────────────────

@dataclass
class AgentState:
    question:    str
    chunks:      list[dict] = field(default_factory=list)
    web_results: list[dict] = field(default_factory=list)
    sufficient:  bool       = False
    reasoning:   str        = ""
    used_web:    bool       = False


# ── Service ───────────────────────────────────────────────────────────────────

class AgenticRAGService:

    def __init__(self, embedder: Embedder, llm: LLMClient) -> None:
        self.embedder = embedder
        self.llm      = llm

    # ── Main entry point ──────────────────────────────────────────────────────

    async def ask(self, question: str, top_k: int | None = None) -> dict:
        top_k = top_k or settings.rag_top_k
        state = AgentState(question=question)

        # Step 1 — ChromaDB retrieve
        self._retrieve_from_db(state, top_k)

        # Step 2 — Reflect
        if not state.chunks:
            logger.warning("No chunks found in knowledge base.")
        else:
            self._reflect(state)
            logger.info("Sufficiency check — sufficient: %s | %s", state.sufficient, state.reasoning)

        # Step 3 — Web fallback
        if not state.sufficient and settings.search_fallback:
            logger.info("Context insufficient — falling back to web search.")
            await self._retrieve_from_web(state)
            state.used_web = True

        # Step 4 — Answer
        if not state.chunks and not state.web_results:
            return {
                "question":   question,
                "answer":     "No relevant information found in manuals or web.",
                "sources":    [],
                "iterations": 1,
                "used_web":   False,
            }

        raw_answer = await self._answer(state)
        answer     = self._clean(raw_answer)
        sources    = self._build_sources(state)

        # Track if any web sources from the DB or Tavily fallback were actually delivered
        has_web_sources = any(s["type"] == "web" for s in sources)

        return {
            "question":   question,
            "answer":     answer,
            "sources":    sources,
            "iterations": 1,
            "used_web":   has_web_sources,
        }

    # ── Step 1: Retrieve from ChromaDB ────────────────────────────────────────

    def _retrieve_from_db(self, state: AgentState, top_k: int) -> None:
        seen_keys = {(c["source"], c["page"], c["text"][:50]) for c in state.chunks}

        results = self.embedder.query(state.question, top_k=top_k)
        for chunk in results:
            key = (chunk["source"], chunk["page"], chunk["text"][:50])
            if key not in seen_keys:
                seen_keys.add(key)
                state.chunks.append(chunk)

    # ── Step 2: Reflect (distance-based, no LLM) ──────────────────────────────

    def _reflect(self, state: AgentState) -> None:
        """
        Judge sufficiency from cosine distance scores alone — fast, no LLM.
        A chunk is 'relevant' when its distance is below DISTANCE_THRESHOLD.
        """
        if not state.chunks:
            state.sufficient = False
            state.reasoning  = "No chunks retrieved."
            return

        relevant = [c for c in state.chunks if c.get("distance", 1.0) < DISTANCE_THRESHOLD]

        if len(relevant) >= 2:
            state.sufficient = True
            state.reasoning  = (
                f"{len(relevant)} relevant chunks found (distance < {DISTANCE_THRESHOLD})."
            )
        else:
            state.sufficient = False
            state.reasoning  = (
                f"Only {len(relevant)} relevant chunks — need more context."
            )

    # ── Step 3: Web search fallback ───────────────────────────────────────────

    async def _retrieve_from_web(self, state: AgentState) -> None:
        if not settings.tavily_api_key:
            logger.warning("TAVILY_API_KEY not set — skipping web search.")
            return
        try:
            from tavily import TavilyClient           # pip install tavily-python
            client   = TavilyClient(api_key=settings.tavily_api_key)
            response = client.search(
                query               = state.question,
                search_depth        = "advanced",
                max_results         = 1,
                include_raw_content = False,
            )
            for r in response.get("results", []):
                state.web_results.append({
                    "title":   r.get("title", ""),
                    "url":     r.get("url", ""),
                    "content": r.get("content", ""),
                })
            logger.info("Web search returned %d results.", len(state.web_results))
        except ImportError:
            logger.error("tavily-python not installed. Run: pip install tavily-python")
        except Exception as exc:
            logger.error("Web search failed: %s", exc)

    # ── Step 4: Answer ────────────────────────────────────────────────────────

    async def _answer(self, state: AgentState) -> str:
        context_parts: list[str] = []

        # Enumerate DB chunks and dynamically tag context labels for the LLM
        for i, chunk in enumerate(state.chunks, 1):
            is_web = (
                chunk.get("type") == "web" or 
                "url" in chunk or 
                not str(chunk["source"]).lower().endswith(".pdf")
            )
            label = f"Web Source {i}" if is_web else f"Manual Excerpt {i}"
            meta  = f" - {chunk['source']}" + (f", page {chunk['page']}" if not is_web else "")
            
            context_parts.append(f"[{label}{meta}]\n{chunk['text']}")

        # Enumerate fallback Tavily search results
        start_idx = len(state.chunks) + 1
        for i, r in enumerate(state.web_results, start_idx):
            context_parts.append(
                f"[Web Source {i} - {r['title']} ({r['url']})]\n"
                f"{r['content']}"
            )

        context = "\n\n".join(context_parts)
        
        # Check if any web elements are parsed so the system label accurately guides the LLM
        any_web = any(
            c.get("type") == "web" or 
            "url" in c or 
            not str(c["source"]).lower().endswith(".pdf") 
            for c in state.chunks
        ) or bool(state.web_results)
        
        source_label = "manual excerpts and web sources" if any_web else "manual excerpts"

        prompt = (
            f"You are a senior industrial machinery expert. "
            f"Answer the question using only the {source_label} below.\n\n"
            "- Plain text only. No markdown, no symbols, no LaTeX, no math formulas.\n"
            "- Be concise, accurate, and practical. Include specific values and units.\n"
            "- Cite manual facts like (Manual Excerpt 1, page 5) and web facts like (Web Source 2).\n"
            '- Do not start with "Based on" or "According to".\n'
            "- If the answer cannot be found in any source respond with only: "
            "This information is not covered in the available sources.\n"
            "- Never invent information.\n\n"
            f"Sources:\n{context}\n\n"
            f"Question: {state.question}\n\n"
            "Answer:"
        )

        return await self.llm.generate(
            prompt=prompt,
            caller="consulting",
            system_prompt=(
                "You are a senior industrial machinery expert. "
                "Your ONLY permitted knowledge source is the excerpts provided in the prompt. "
                "Plain text only — no markdown, no bullet points, no headers."
            ),
            temperature=0.1,
            max_tokens=MAX_TOKENS,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_sources(self, state: AgentState) -> list[dict]:
        seen:    set[tuple]  = set()
        sources: list[dict]  = []

        # 1. Process chunks from ChromaDB (Splitting out mixed manuals & web assets)
        for c in state.chunks:
            key = (c["source"], c["page"])
            if key not in seen:
                seen.add(key)
                
                # Check extension/metadata to handle non-pdf data seamlessly
                is_web = (
                    c.get("type") == "web" or 
                    "url" in c or 
                    not str(c["source"]).lower().endswith(".pdf")
                )
                
                if is_web:
                    sources.append({
                        "type":    "web",
                        "file":    c["source"],
                        "page":    0,
                        "content": c["text"],
                        "url":     c.get("url", ""),
                    })
                else:
                    sources.append({
                        "type":    "manual",
                        "file":    c["source"],
                        "page":    c["page"],
                        "content": c["text"],
                    })

        # 2. Process results pulled from fallback web execution
        for r in state.web_results:
            sources.append({
                "type":    "web",
                "file":    r["title"],
                "page":    0,
                "content": r["content"],
                "url":     r["url"],
            })

        return sources

    def _clean(self, text: str) -> str:
        """Strip LaTeX, markdown, and extra whitespace from the answer."""
        text = re.sub(r"\\\[.*?\\\]",       "",  text, flags=re.DOTALL)
        text = re.sub(r"\\\(.*?\\\)",       "",  text, flags=re.DOTALL)
        text = re.sub(r"\\[a-zA-Z]+\{.*?\}", "", text, flags=re.DOTALL)
        text = re.sub(r"\\[a-zA-Z]+",       "",  text)
        text = re.sub(r"#{1,6}\s*",         "",  text)
        text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"`(.+?)`",            r"\1", text)
        text = re.sub(r"^\s*[-*+]\s+",      "",  text, flags=re.MULTILINE)
        text = text.replace("\\n", " ").replace("\\t", " ").replace("\\", "")
        text = re.sub(r"\n+",  " ", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()