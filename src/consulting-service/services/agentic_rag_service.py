"""
services/agentic_rag_service.py
────────────────────────────────
Agentic RAG with web search fallback:

  Step 1 — Plan      : LLM breaks question into focused sub-queries
  Step 2 — Retrieve  : Search ChromaDB for each sub-query
  Step 3 — Reflect   : Is context sufficient? (keyword-based, no LLM)
  Step 4 — Retry     : Reformulate and search ChromaDB again (max 2x)
  Step 5 — Web       : If still insufficient, search the web via Tavily
  Step 6 — Answer    : Generate final answer from all collected context
"""

import re
import json
import logging
from dataclasses import dataclass, field
from services.embedder     import Embedder
from services.llama_client import LlamaClient
from config                import settings

logger = logging.getLogger("agentic_rag")

MAX_ITERATIONS      = 2      # ChromaDB retry cycles before falling back to web
DISTANCE_THRESHOLD  = 0.45   # cosine distance — below this = relevant chunk


@dataclass
class AgentState:
    question:     str
    queries:      list[str]  = field(default_factory=list)
    chunks:       list[dict] = field(default_factory=list)
    web_results:  list[dict] = field(default_factory=list)
    iterations:   int        = 0
    sufficient:   bool       = False
    reasoning:    str        = ""
    used_web:     bool       = False


class AgenticRAGService:

    def __init__(self, embedder: Embedder, llama: LlamaClient):
        self.embedder = embedder
        self.llama    = llama

    # ── Main entry point ──────────────────────────────────────────────────────

    async def ask(self, question: str, top_k: int | None = None) -> dict:
        top_k = top_k or settings.rag_top_k
        state = AgentState(question=question)

        # Step 1 — Plan
        state.queries = await self._plan(question)
        logger.info("Planned queries: %s", state.queries)

        # Steps 2-4 — ChromaDB retrieve → reflect → retry loop
        while state.iterations < MAX_ITERATIONS:
            state.iterations += 1
            self._retrieve_from_db(state, top_k)

            if not state.chunks:
                logger.warning("No chunks found in knowledge base.")
                break

            # Reflect using distance scores — no LLM call needed
            self._reflect(state)
            logger.info("Iteration %d — sufficient: %s | %s",
                        state.iterations, state.sufficient, state.reasoning)

            if state.sufficient:
                break

            if state.iterations < MAX_ITERATIONS:
                state.queries = await self._reformulate(state)

        # Step 5 — Web fallback if still not sufficient
        if not state.sufficient and settings.search_fallback:
            logger.info("Context insufficient — falling back to web search.")
            await self._retrieve_from_web(state)
            state.used_web = True

        # Step 6 — Answer
        if not state.chunks and not state.web_results:
            return {
                "question":   question,
                "answer":     "No relevant information found in manuals or web.",
                "sources":    [],
                "iterations": state.iterations,
                "used_web":   False,
            }

        raw_answer = await self._answer(state)
        answer     = self._clean(raw_answer)
        sources    = self._build_sources(state)

        return {
            "question":   question,
            "answer":     answer,
            "sources":    sources,
            "iterations": state.iterations,
            "used_web":   state.used_web,
        }

    # ── Step 1: Plan ──────────────────────────────────────────────────────────

    async def _plan(self, question: str) -> list[str]:
        prompt = f"""List 1 to 3 short search queries to find information about the question below.
Return a JSON array only. Example: ["vibration limits", "measurement method"]
Question: {question}
JSON:"""

        try:
            raw     = await self.llama.complete(prompt)
            queries = self._extract_json_array(raw)
            if queries:
                return queries[:3]
        except Exception as e:
            logger.warning("Query planning failed (%s) — using original question.", e)

        return [question]

    # ── Step 2: Retrieve from ChromaDB ────────────────────────────────────────

    def _retrieve_from_db(self, state: AgentState, top_k: int) -> None:
        seen_keys = {(c["source"], c["page"], c["text"][:50]) for c in state.chunks}

        for query in state.queries:
            results = self.embedder.query(query, top_k=top_k)
            for chunk in results:
                key = (chunk["source"], chunk["page"], chunk["text"][:50])
                if key not in seen_keys:
                    seen_keys.add(key)
                    state.chunks.append(chunk)

    # ── Step 3: Reflect (distance-based, no LLM) ──────────────────────────────

    def _reflect(self, state: AgentState) -> None:
        """
        Use cosine distance scores to judge sufficiency — fast, no LLM call.
        A chunk with distance < DISTANCE_THRESHOLD is considered relevant.
        """
        if not state.chunks:
            state.sufficient = False
            state.reasoning  = "No chunks retrieved."
            return

        relevant = [c for c in state.chunks if c.get("distance", 1.0) < DISTANCE_THRESHOLD]

        if len(relevant) >= 2:
            state.sufficient = True
            state.reasoning  = f"{len(relevant)} relevant chunks found (distance < {DISTANCE_THRESHOLD})."
        else:
            state.sufficient = False
            state.reasoning  = f"Only {len(relevant)} relevant chunks — need more context."

    # ── Step 4: Reformulate ───────────────────────────────────────────────────

    async def _reformulate(self, state: AgentState) -> list[str]:
        prompt = f"""The previous search did not find enough information.
Original question: {state.question}
Previous queries that failed: {state.queries}
Generate 1 to 2 new different search queries. Return a JSON array only.
JSON:"""

        try:
            raw     = await self.llama.complete(prompt)
            queries = self._extract_json_array(raw)
            if queries:
                return queries[:2]
        except Exception as e:
            logger.warning("Reformulation failed (%s) — stopping loop.", e)
            state.sufficient = True

        return state.queries

    # ── Step 5: Web search fallback ───────────────────────────────────────────

    async def _retrieve_from_web(self, state: AgentState) -> None:
        if not settings.tavily_api_key:
            logger.warning("TAVILY_API_KEY not set — skipping web search.")
            return
        try:
            from tavily import TavilyClient
            client   = TavilyClient(api_key=settings.tavily_api_key)
            response = client.search(
                query               = state.question,
                search_depth        = "advanced",
                max_results         = 5,
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
        except Exception as e:
            logger.error("Web search failed: %s", e)

    # ── Step 6: Answer ────────────────────────────────────────────────────────

    async def _answer(self, state: AgentState) -> str:
        context_parts = []

        for i, chunk in enumerate(state.chunks, 1):
            context_parts.append(
                f"[Manual Excerpt {i} - {chunk['source']}, page {chunk['page']}]\n"
                f"{chunk['text']}"
            )

        for i, r in enumerate(state.web_results, 1):
            context_parts.append(
                f"[Web Source {i} - {r['title']} ({r['url']})]\n"
                f"{r['content']}"
            )

        context      = "\n\n".join(context_parts)
        source_label = "manual excerpts and web sources" if state.used_web else "manual excerpts"

        prompt = f"""You are a senior industrial machinery expert. Answer the question using only the {source_label} below.

- Plain text only. No markdown, no symbols, no LaTeX, no math formulas.
- Be concise, accurate, and practical. Include specific values and units.
- Cite manual facts like (Manual Excerpt 1, page 5) and web facts like (Web Source 2).
- Do not start with "Based on" or "According to".
- If the answer cannot be found in any source respond with only: This information is not covered in the available sources.
- Never invent information.

Sources:
{context}

Question: {state.question}

Answer:"""

        return await self.llama.complete(prompt)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_json_array(self, text: str) -> list[str]:
        """Extract a JSON array from anywhere in the model response."""
        text  = re.sub(r'```(?:json)?|```', '', text)
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if not match:
            return []
        data = json.loads(match.group())
        if isinstance(data, list) and all(isinstance(q, str) for q in data):
            return data
        return []

    def _build_sources(self, state: AgentState) -> list[dict]:
        seen    = set()
        sources = []

        for c in state.chunks:
            key = (c["source"], c["page"])
            if key not in seen:
                seen.add(key)
                sources.append({
                    "type":    "manual",
                    "file":    c["source"],
                    "page":    c["page"],
                    "content": c["text"],
                })

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
        text = re.sub(r'\\\[.*?\\\]', '', text, flags=re.DOTALL)
        text = re.sub(r'\\\(.*?\\\)', '', text, flags=re.DOTALL)
        text = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\\[a-zA-Z]+', '', text)
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = text.replace('\\n', ' ').replace('\\t', ' ')
        text = text.replace('\\', '')
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()