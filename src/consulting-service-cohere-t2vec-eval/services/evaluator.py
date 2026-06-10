"""
services/evaluator.py
──────────────────────
RAG + Agentic evaluation suite.

Metrics computed
────────────────
  1. Cosine Distance Threshold Consistency
       How consistently retrieved chunks fall below DISTANCE_THRESHOLD.
       Reported as a ratio (0-1) and per-query breakdown.

  2. Hit Rate @ K
       Fraction of queries for which at least one relevant chunk (distance < threshold)
       appears in the top-K results.

  3. Mean Reciprocal Rank (MRR)
       Average of 1/rank for the first relevant chunk across queries.

  4. Context Relevance
       Average cosine distance of retrieved chunks — lower = more relevant.
       Computed per-query and aggregated.

  5. Groundedness
       Keyword-overlap ratio between the LLM answer and the retrieved context.
       Measures how much of the answer is grounded in the supplied chunks.

  6. Answer Relevance
       Keyword-overlap ratio between the LLM answer and the original question.
       High relevance = answer actually addresses the question.

  7. Latency per Agent Step
       Wall-clock time (seconds) for each step: plan, retrieve, reflect, answer.
       Returned as a dict and a total.

Window format support
─────────────────────
  Both formats are handled transparently everywhere:
    • Row-wise  : [{"temp": 72, "vibration": 4.1}, {"temp": 74, ...}, ...]
    • Columnar  : {"temp": [72, 74, ...], "vibration": [4.1, 4.3, ...]}

  Call `normalise_window(window_sliding)` to convert either to row-wise list
  before passing to chunkers / embedders.

Usage
─────
  from services.evaluator import Evaluator, EvalQuery

  queries = [
      EvalQuery(
          question="What causes bearing fault?",
          relevant_keywords=["bearing", "temperature", "vibration"],
      )
  ]
  ev = Evaluator(embedder=get_pdf_embedder(), llm=get_llm())
  report = await ev.run(queries, top_k=5)
  print(report.summary())

  # For sensor / window evaluation:
  from services.evaluator import WindowEvalQuery
  wq = WindowEvalQuery(
      machine_id="pump_01",
      window_sliding=[{"temperature": 72, "vibration": 4.1}],  # or columnar dict
      label="Bearing Fault",
      rul=142.0,
      expected_keywords=["bearing", "temperature"],
  )
  wreport = await ev.run_window([wq], embedder=get_sensor_embedder("pump_01"))
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("evaluator")

# ── Mirrors agentic_rag_service.DISTANCE_THRESHOLD ────────────────────────────
DISTANCE_THRESHOLD = 0.60


# ══════════════════════════════════════════════════════════════════════════════
# Window format normaliser  (fixes both {[]} and [{}])
# ══════════════════════════════════════════════════════════════════════════════

def normalise_window(window_sliding: Any) -> list[dict]:
    """
    Accept EITHER window format and always return row-wise list[dict].

    Formats handled
    ───────────────
      Row-wise  (already correct):
        [{"temp": 72, "vib": 4.1}, {"temp": 74, "vib": 4.3}, ...]

      Columnar  (transposed):
        {"temp": [72, 74, ...], "vib": [4.1, 4.3, ...]}

      Mixed / scalar:
        {"temp": 72}          → [{"temp": 72}]
        "some string"         → []
        None                  → []
    """
    if window_sliding is None:
        return []

    # ── Row-wise list ──────────────────────────────────────────────────────
    if isinstance(window_sliding, list):
        out: list[dict] = []
        for item in window_sliding:
            if isinstance(item, dict):
                out.append(item)
            # non-dict items in the list are skipped gracefully
        return out

    # ── Columnar dict ──────────────────────────────────────────────────────
    if isinstance(window_sliding, dict):
        # Check if any value is a list/tuple — that signals columnar layout
        if any(isinstance(v, (list, tuple)) for v in window_sliding.values()):
            max_len = max(
                (len(v) for v in window_sliding.values() if isinstance(v, (list, tuple))),
                default=1,
            )
            rows: list[dict] = []
            for i in range(max_len):
                row: dict = {}
                for col, vals in window_sliding.items():
                    if isinstance(vals, (list, tuple)):
                        row[col] = vals[i] if i < len(vals) else None
                    else:
                        row[col] = vals  # scalar — broadcast to every row
                rows.append(row)
            return rows
        else:
            # Scalar-only dict → single step
            return [window_sliding]

    return []


# ══════════════════════════════════════════════════════════════════════════════
# Data classes
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EvalQuery:
    """One text-based evaluation query (PDF / global KB)."""
    question:          str
    relevant_keywords: list[str] = field(default_factory=list)
    # If you know the ground-truth answer, supply it for grounding checks
    reference_answer:  str       = ""


@dataclass
class WindowEvalQuery:
    """One sensor-window evaluation query."""
    machine_id:        str
    window_sliding:    Any                      # [{}] or {[]} — both accepted
    label:             str       = ""
    rul:               float     = 0.0
    message_id:        str       = "eval_msg"
    timestamp:         float     = field(default_factory=time.time)
    expected_keywords: list[str] = field(default_factory=list)
    reference_answer:  str       = ""


@dataclass
class StepLatency:
    plan:     float = 0.0
    retrieve: float = 0.0
    reflect:  float = 0.0
    answer:   float = 0.0

    @property
    def total(self) -> float:
        return self.plan + self.retrieve + self.reflect + self.answer

    def to_dict(self) -> dict:
        return {
            "plan_s":     round(self.plan,     4),
            "retrieve_s": round(self.retrieve, 4),
            "reflect_s":  round(self.reflect,  4),
            "answer_s":   round(self.answer,   4),
            "total_s":    round(self.total,    4),
        }


@dataclass
class QueryMetrics:
    question:             str
    chunks_retrieved:     int
    distances:            list[float]
    first_relevant_rank:  int | None   # 1-indexed; None if no hit
    answer:               str
    groundedness:         float        # 0-1
    answer_relevance:     float        # 0-1
    latency:              StepLatency  = field(default_factory=StepLatency)

    @property
    def hit(self) -> bool:
        return self.first_relevant_rank is not None

    @property
    def reciprocal_rank(self) -> float:
        return 1.0 / self.first_relevant_rank if self.first_relevant_rank else 0.0

    @property
    def context_relevance(self) -> float:
        """Average cosine distance of retrieved chunks (lower = better)."""
        return sum(self.distances) / len(self.distances) if self.distances else 1.0

    @property
    def threshold_consistent(self) -> float:
        """Fraction of retrieved chunks with distance < DISTANCE_THRESHOLD."""
        if not self.distances:
            return 0.0
        return sum(1 for d in self.distances if d < DISTANCE_THRESHOLD) / len(self.distances)


@dataclass
class EvalReport:
    """Aggregated evaluation report across all queries."""
    query_metrics: list[QueryMetrics]

    # ── Aggregate metrics ──────────────────────────────────────────────────

    @property
    def cosine_threshold_consistency(self) -> float:
        """Average fraction of chunks below DISTANCE_THRESHOLD across queries."""
        if not self.query_metrics:
            return 0.0
        return sum(q.threshold_consistent for q in self.query_metrics) / len(self.query_metrics)

    @property
    def hit_rate(self) -> float:
        """Hit Rate @ K — fraction of queries with ≥1 relevant chunk in top-K."""
        if not self.query_metrics:
            return 0.0
        return sum(1 for q in self.query_metrics if q.hit) / len(self.query_metrics)

    @property
    def mrr(self) -> float:
        """Mean Reciprocal Rank across all queries."""
        if not self.query_metrics:
            return 0.0
        return sum(q.reciprocal_rank for q in self.query_metrics) / len(self.query_metrics)

    @property
    def avg_context_relevance(self) -> float:
        """Mean context relevance (mean cosine distance — lower = better)."""
        if not self.query_metrics:
            return 1.0
        return sum(q.context_relevance for q in self.query_metrics) / len(self.query_metrics)

    @property
    def avg_groundedness(self) -> float:
        if not self.query_metrics:
            return 0.0
        return sum(q.groundedness for q in self.query_metrics) / len(self.query_metrics)

    @property
    def avg_answer_relevance(self) -> float:
        if not self.query_metrics:
            return 0.0
        return sum(q.answer_relevance for q in self.query_metrics) / len(self.query_metrics)

    @property
    def avg_latency(self) -> StepLatency:
        if not self.query_metrics:
            return StepLatency()
        n = len(self.query_metrics)
        return StepLatency(
            plan     = sum(q.latency.plan     for q in self.query_metrics) / n,
            retrieve = sum(q.latency.retrieve for q in self.query_metrics) / n,
            reflect  = sum(q.latency.reflect  for q in self.query_metrics) / n,
            answer   = sum(q.latency.answer   for q in self.query_metrics) / n,
        )

    # ── Serialise ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "cosine_distance_threshold_consistency": round(self.cosine_threshold_consistency, 4),
            "hit_rate_at_k":                         round(self.hit_rate,                     4),
            "mrr":                                   round(self.mrr,                          4),
            "context_relevance_mean":                round(self.avg_context_relevance,         4),
            "groundedness_mean":                     round(self.avg_groundedness,              4),
            "answer_relevance_mean":                 round(self.avg_answer_relevance,          4),
            "latency_per_agent_step_mean_s":         self.avg_latency.to_dict(),
            "distance_threshold":                    DISTANCE_THRESHOLD,
            "num_queries":                           len(self.query_metrics),
            "per_query": [
                {
                    "question":                    q.question,
                    "hit":                         q.hit,
                    "first_relevant_rank":         q.first_relevant_rank,
                    "reciprocal_rank":             round(q.reciprocal_rank,        4),
                    "threshold_consistency":       round(q.threshold_consistent,   4),
                    "context_relevance":           round(q.context_relevance,      4),
                    "groundedness":                round(q.groundedness,           4),
                    "answer_relevance":            round(q.answer_relevance,       4),
                    "distances":                   [round(d, 4) for d in q.distances],
                    "latency_s":                   q.latency.to_dict(),
                    "answer_snippet":              q.answer[:200] + ("…" if len(q.answer) > 200 else ""),
                }
                for q in self.query_metrics
            ],
        }

    def summary(self) -> str:
        d = self.to_dict()
        lines = [
            "═" * 60,
            "  RAG Evaluation Report",
            "═" * 60,
            f"  Queries evaluated        : {d['num_queries']}",
            f"  Distance threshold       : {d['distance_threshold']}",
            "─" * 60,
            f"  Cosine Threshold Consist.: {d['cosine_distance_threshold_consistency']:.3f}",
            f"  Hit Rate @ K             : {d['hit_rate_at_k']:.3f}",
            f"  MRR                      : {d['mrr']:.3f}",
            f"  Context Relevance (avg)  : {d['context_relevance_mean']:.3f}  (lower=better)",
            f"  Groundedness (avg)       : {d['groundedness_mean']:.3f}",
            f"  Answer Relevance (avg)   : {d['answer_relevance_mean']:.3f}",
            "─" * 60,
            "  Latency per Agent Step (mean):",
            f"    Plan     : {d['latency_per_agent_step_mean_s']['plan_s']:.3f}s",
            f"    Retrieve : {d['latency_per_agent_step_mean_s']['retrieve_s']:.3f}s",
            f"    Reflect  : {d['latency_per_agent_step_mean_s']['reflect_s']:.3f}s",
            f"    Answer   : {d['latency_per_agent_step_mean_s']['answer_s']:.3f}s",
            f"    Total    : {d['latency_per_agent_step_mean_s']['total_s']:.3f}s",
            "═" * 60,
        ]
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# Keyword-overlap helpers
# ══════════════════════════════════════════════════════════════════════════════

def _tokenise(text: str) -> set[str]:
    """Lower-case word tokens, stripping punctuation."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _overlap_ratio(text_a: str, text_b: str) -> float:
    """
    Symmetric keyword-overlap ratio:
        |A ∩ B| / |A ∪ B|   (Jaccard-like, ignoring stop-words)

    Returns 0.0 if either set is empty.
    """
    STOP = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "and", "or", "but", "not", "it", "its", "this", "that",
    }
    tokens_a = _tokenise(text_a) - STOP
    tokens_b = _tokenise(text_b) - STOP
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union        = tokens_a | tokens_b
    return len(intersection) / len(union)


def _groundedness(answer: str, context_chunks: list[dict]) -> float:
    """
    Measure how grounded the answer is in the retrieved context.

    Score = max keyword-overlap between the answer and any single chunk text.
    Taking the max (rather than mean) rewards the case where at least one chunk
    closely matches the answer — which is the expected RAG behaviour.
    """
    if not context_chunks or not answer.strip():
        return 0.0
    scores = [_overlap_ratio(answer, c.get("text", "")) for c in context_chunks]
    return max(scores) if scores else 0.0


def _answer_relevance(answer: str, question: str) -> float:
    """Keyword-overlap between answer and question."""
    return _overlap_ratio(answer, question)


# ══════════════════════════════════════════════════════════════════════════════
# Evaluator
# ══════════════════════════════════════════════════════════════════════════════

class Evaluator:
    """
    Runs the full evaluation suite against a live embedder + LLM.

    Parameters
    ----------
    embedder : PdfEmbedder | SensorEmbedder — pre-constructed embedder
    llm      : LLMClient
    """

    def __init__(self, embedder, llm) -> None:
        self.embedder = embedder
        self.llm      = llm

    # ── Text / PDF evaluation ──────────────────────────────────────────────

    async def run(
        self,
        queries: list[EvalQuery],
        top_k:   int = 5,
    ) -> EvalReport:
        """
        Evaluate all EvalQuery instances and return an EvalReport.

        Each query goes through the full agentic pipeline with per-step timing.
        """
        all_metrics: list[QueryMetrics] = []

        for eq in queries:
            qm = await self._evaluate_one(eq, top_k=top_k)
            all_metrics.append(qm)

        return EvalReport(query_metrics=all_metrics)

    async def _evaluate_one(self, eq: EvalQuery, top_k: int) -> QueryMetrics:
        latency = StepLatency()

        # ── Step 1: Plan ──────────────────────────────────────────────────
        t0 = time.perf_counter()
        queries = await self._plan(eq.question)
        latency.plan = time.perf_counter() - t0

        # ── Step 2: Retrieve ──────────────────────────────────────────────
        t0 = time.perf_counter()
        chunks = self._retrieve(queries, top_k=top_k)
        latency.retrieve = time.perf_counter() - t0

        # ── Step 3: Reflect ───────────────────────────────────────────────
        t0 = time.perf_counter()
        distances = [c.get("distance", 1.0) for c in chunks]
        first_relevant_rank = self._first_relevant_rank(distances)
        latency.reflect = time.perf_counter() - t0

        # ── Step 4 / 6: Answer ────────────────────────────────────────────
        t0 = time.perf_counter()
        answer = await self._answer(eq.question, chunks)
        latency.answer = time.perf_counter() - t0

        # ── Metrics ───────────────────────────────────────────────────────
        groundedness     = _groundedness(answer, chunks)
        answer_relevance = _answer_relevance(answer, eq.question)

        return QueryMetrics(
            question            = eq.question,
            chunks_retrieved    = len(chunks),
            distances           = distances,
            first_relevant_rank = first_relevant_rank,
            answer              = answer,
            groundedness        = groundedness,
            answer_relevance    = answer_relevance,
            latency             = latency,
        )

    # ── Window / sensor evaluation ─────────────────────────────────────────

    async def run_window(
        self,
        queries:  list[WindowEvalQuery],
        embedder: "SensorEmbedder",          # type: ignore[name-defined]
        top_k:    int = 5,
    ) -> EvalReport:
        """
        Evaluate window queries using a SensorEmbedder.

        window_sliding can be either [{}] or {[]} — both are normalised.
        """
        all_metrics: list[QueryMetrics] = []

        for wq in queries:
            qm = await self._evaluate_window_one(wq, embedder=embedder, top_k=top_k)
            all_metrics.append(qm)

        return EvalReport(query_metrics=all_metrics)

    async def _evaluate_window_one(
        self,
        wq:       WindowEvalQuery,
        embedder: "SensorEmbedder",          # type: ignore[name-defined]
        top_k:    int,
    ) -> QueryMetrics:
        from services.window_chunker import window_event_to_chunks
        from types import SimpleNamespace

        latency = StepLatency()

        # Normalise window format (handles both [{}] and {[]})
        t0 = time.perf_counter()
        norm_window = normalise_window(wq.window_sliding)
        fake_event  = SimpleNamespace(
            machine_id     = wq.machine_id,
            label          = wq.label,
            rul            = wq.rul,
            window_sliding = norm_window,
            message_id     = wq.message_id,
            timestamp      = wq.timestamp,
            reason         = "",
        )
        query_chunks = window_event_to_chunks(fake_event)
        query_text   = query_chunks[0]["text"] if query_chunks else ""
        latency.plan = time.perf_counter() - t0

        # Retrieve
        t0     = time.perf_counter()
        chunks = embedder.query(
            query_text     = query_text,
            top_k          = top_k,
            window_sliding = norm_window,
        )
        latency.retrieve = time.perf_counter() - t0

        # Reflect
        t0 = time.perf_counter()
        distances           = [c.get("distance", 1.0) for c in chunks]
        first_relevant_rank = self._first_relevant_rank(distances)
        latency.reflect     = time.perf_counter() - t0

        # Answer (diagnosis prompt)
        t0     = time.perf_counter()
        answer = await self._diagnose_answer(
            machine_id = wq.machine_id,
            query_text = query_text,
            chunks     = chunks,
        )
        latency.answer = time.perf_counter() - t0

        groundedness     = _groundedness(answer, chunks)
        answer_relevance = _answer_relevance(
            answer,
            f"{wq.label} {' '.join(wq.expected_keywords)}"
        )

        return QueryMetrics(
            question            = f"[Window] {wq.machine_id}: {wq.label}",
            chunks_retrieved    = len(chunks),
            distances           = distances,
            first_relevant_rank = first_relevant_rank,
            answer              = answer,
            groundedness        = groundedness,
            answer_relevance    = answer_relevance,
            latency             = latency,
        )

    # ── Internal helpers ───────────────────────────────────────────────────

    async def _plan(self, question: str) -> list[str]:
        import re as _re
        prompt = (
            "Write one short, precise search query to find information about the question below.\n"
            "Return the query as plain text only -- no lists, no JSON, no extra words.\n"
            f"Question: {question}\nSearch query:"
        )
        try:
            raw = await self.llm.generate(prompt, max_tokens=512)
            raw = _re.sub(r"```.*?```", "", raw, flags=_re.DOTALL).strip()
            if raw:
                return [raw.splitlines()[0].strip()]
        except Exception as exc:
            logger.warning("Evaluator._plan failed (%s) -- using original question.", exc)
        return [question]

    def _retrieve(self, queries: list[str], top_k: int) -> list[dict]:
        seen:   set[tuple]  = set()
        chunks: list[dict]  = []
        for q in queries:
            for chunk in self.embedder.query(q, top_k=top_k):
                key = (chunk.get("source"), chunk.get("page"), chunk.get("text", "")[:50])
                if key not in seen:
                    seen.add(key)
                    chunks.append(chunk)
        return chunks

    @staticmethod
    def _first_relevant_rank(distances: list[float]) -> int | None:
        for rank, dist in enumerate(distances, start=1):
            if dist < DISTANCE_THRESHOLD:
                return rank
        return None

    async def _answer(self, question: str, chunks: list[dict]) -> str:
        context = "\n\n".join(
            f"[Chunk {i} — {c.get('source', 'unknown')}, p.{c.get('page', 0)}]\n{c.get('text', '')}"
            for i, c in enumerate(chunks, 1)
        )
        prompt = (
            "You are an industrial maintenance expert. Answer using only the provided sources.\n"
            "Plain text only. Be concise.\n\n"
            f"Sources:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        )
        try:
            return await self.llm.generate(prompt, max_tokens=512)
        except Exception as exc:
            logger.warning("Evaluator._answer failed: %s", exc)
            return ""

    async def _diagnose_answer(
        self,
        machine_id: str,
        query_text: str,
        chunks:     list[dict],
    ) -> str:
        context = "\n\n".join(
            f"[Historical Case {i} — distance {c.get('distance', '?')}]\n{c.get('text', '')}"
            for i, c in enumerate(chunks, 1)
        )
        prompt = (
            f"Machine: {machine_id}\nCurrent sensor snapshot:\n{query_text}\n\n"
            f"Similar historical cases:\n{context}\n\n"
            "Identify the most likely fault reason in one concise sentence."
        )
        try:
            return await self.llm.generate(prompt, max_tokens=512)
        except Exception as exc:
            logger.warning("Evaluator._diagnose_answer failed: %s", exc)
            return ""


# ══════════════════════════════════════════════════════════════════════════════
# Standalone FastAPI router  (mount at /eval)
# ══════════════════════════════════════════════════════════════════════════════

try:
    from fastapi import APIRouter as _APIRouter
    from pydantic import BaseModel as _BaseModel, Field as _Field
    from typing import Optional as _Optional

    eval_router = _APIRouter(prefix="/eval", tags=["Evaluation"])

    class _TextEvalRequest(_BaseModel):
        questions: list[str] = _Field(..., description="Questions to evaluate")
        top_k:     int       = _Field(5,   description="Chunks to retrieve per query")

    class _WindowEvalRequest(_BaseModel):
        machine_id:     str   = _Field(..., description="Machine to query")
        window_sliding: object = _Field(..., description="[{}] or {[]} format both accepted")
        label:          str   = _Field("",  description="Fault label")
        rul:            float = _Field(0.0, description="Remaining useful life")
        top_k:          int   = _Field(5,   description="Chunks to retrieve")

    @eval_router.post("/text")
    async def eval_text(body: _TextEvalRequest):
        """
        Evaluate text queries against the global PDF knowledge base.
        Returns all 7 metrics.
        """
        from services.service_factory import get_pdf_embedder, get_llm
        ev      = Evaluator(embedder=get_pdf_embedder(), llm=get_llm())
        queries = [EvalQuery(question=q) for q in body.questions]
        report  = await ev.run(queries, top_k=body.top_k)
        return report.to_dict()

    @eval_router.post("/window")
    async def eval_window(body: _WindowEvalRequest):
        """
        Evaluate a sensor window query.
        Accepts both [{}] and {[]} formats for window_sliding.
        Returns all 7 metrics.
        """
        from services.service_factory import get_sensor_embedder, get_llm
        ev    = Evaluator(embedder=get_sensor_embedder(body.machine_id), llm=get_llm())
        wq    = WindowEvalQuery(
            machine_id     = body.machine_id,
            window_sliding = body.window_sliding,  # normalised inside Evaluator
            label          = body.label,
            rul            = body.rul,
        )
        report = await ev.run_window(
            [wq],
            embedder=get_sensor_embedder(body.machine_id),
            top_k=body.top_k,
        )
        return report.to_dict()

except ImportError:
    # FastAPI not available in this environment — skip router registration
    eval_router = None  # type: ignore[assignment]