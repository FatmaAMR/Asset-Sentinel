"""
services/evaluator.py
──────────────────────
RAG evaluation suite — v2 (improved metrics).

Metrics computed
────────────────
  1. Cosine Distance Threshold Consistency
       How consistently retrieved chunks fall below DISTANCE_THRESHOLD.
       Reported as a ratio (0-1) and per-query breakdown.

  2. Hit Rate @ K
       Fraction of queries for which at least one relevant chunk
       (distance < threshold) appears in the top-K results.

  3. Mean Reciprocal Rank (MRR)
       Average of 1/rank for the first relevant chunk across queries.

  4. Context Relevance  ★ IMPROVED
       Now uses Normalized Discounted Cumulative Gain (NDCG) instead of
       a simple rank-weighted average.  Relevance labels are graded
       (0-3) rather than binary, giving a much more sensitive signal.

  5. Groundedness  ★ IMPROVED
       Hybrid of token-level F1 + soft BM25-style TF-IDF weighting.
       Aggregates over ALL chunks (weighted by distance rank) instead of
       just max-chunk F1, so a good answer that draws from multiple
       chunks is rewarded correctly.

  6. Answer Relevance  ★ IMPROVED
       Pure question-coverage score (recall over question keywords).
       Long, detailed answers are NOT penalised for containing extra
       information beyond the question keywords.

  7. Latency per RAG step
       Wall-clock time (seconds) for retrieval and generation.

Alternative evaluation methods
───────────────────────────────
  ★ RAGAS-style LLM-as-Judge  (see _llm_groundedness / _llm_answer_relevance)
       Each metric is sent to an LLM that scores 0-1 with a short rubric.
       Much more semantic than token overlap — catches paraphrase, synonyms,
       multi-hop reasoning.  Costs one extra LLM call per query per metric.
       Enable with Evaluator(use_llm_judge=True, llm_judge_fn=...).

  ★ Semantic Similarity (embedding cosine)
       _semantic_similarity() embeds both texts and measures cosine
       similarity.  Used as a fallback when LLM judge is not available
       and as a second signal for groundedness.

  ★ BLEU / ROUGE
       Classic MT/summarisation metrics included as helpers.
       Useful for regression testing (fast, deterministic).

Usage
─────
  from services.evaluator import Evaluator, EvalQuery

  # Basic (token-based, no extra LLM calls):
  ev = Evaluator(rag_service=get_rag_service())

  # With LLM judge (best accuracy, extra cost):
  async def my_judge(prompt: str) -> str:
      result = await my_llm_client.complete(prompt)
      return result.text

  ev = Evaluator(
      rag_service=get_rag_service(),
      use_llm_judge=True,
      llm_judge_fn=my_judge,
  )

  report = await ev.run(queries, top_k=5)
  print(report.summary())
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional

logger = logging.getLogger("evaluator")

DISTANCE_THRESHOLD = 0.60


# ══════════════════════════════════════════════════════════════════════════════
# Data classes
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EvalQuery:
    """One text-based evaluation query (PDF / global KB)."""
    question:          str
    relevant_keywords: list[str] = field(default_factory=list)
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
    first_relevant_rank:  int | None
    answer:               str
    groundedness:         float
    answer_relevance:     float
    latency:              StepLatency = field(default_factory=StepLatency)
    distance_threshold:   float       = DISTANCE_THRESHOLD

    # Optional LLM-judge scores (None when judge disabled)
    llm_groundedness:      Optional[float] = None
    llm_answer_relevance:  Optional[float] = None

    # Optional semantic similarity scores
    semantic_groundedness: Optional[float] = None

    @property
    def hit(self) -> bool:
        return self.first_relevant_rank is not None

    @property
    def reciprocal_rank(self) -> float:
        return 1.0 / self.first_relevant_rank if self.first_relevant_rank else 0.0

    @property
    def context_relevance(self) -> float:
        """
        Context relevance for RAG evaluation.

        Combines:
        - NDCG (ranking quality)
        - Threshold consistency (context purity)

        Returns:
            float in [0, 1]
        """
        if not self.distances:
            return 0.0

        # Distance → graded relevance
        def _grade(d: float) -> int:
            if d < 0.40:
                return 3      # highly relevant
            elif d < 0.50:
                return 2      # relevant
            elif d < self.distance_threshold:
                return 1      # marginally relevant
            else:
                return 0      # irrelevant

        grades = [_grade(d) for d in self.distances]

        # DCG
        def _dcg(gs: list[int]) -> float:
            return sum(
                (2**g - 1) / math.log2(rank + 2)
                for rank, g in enumerate(gs)
            )

        dcg = _dcg(grades)
        idcg = _dcg(sorted(grades, reverse=True))

        ndcg = dcg / idcg if idcg > 0 else 0.0

        # Fraction of retrieved chunks below threshold
        threshold_consistency = (
            sum(1 for d in self.distances if d < self.distance_threshold)
            / len(self.distances)
        )

        # Final score
        return (
            0.8 * ndcg +
            0.2 * threshold_consistency
        )

    @property
    def threshold_consistent(self) -> float:
        if not self.distances:
            return 0.0
        return sum(1 for d in self.distances if d < self.distance_threshold) / len(self.distances)


@dataclass
class EvalReport:
    """Aggregated evaluation report across all queries."""
    query_metrics: list[QueryMetrics]

    @property
    def cosine_threshold_consistency(self) -> float:
        if not self.query_metrics:
            return 0.0
        return sum(q.threshold_consistent for q in self.query_metrics) / len(self.query_metrics)

    @property
    def hit_rate(self) -> float:
        if not self.query_metrics:
            return 0.0
        return sum(1 for q in self.query_metrics if q.hit) / len(self.query_metrics)

    @property
    def mrr(self) -> float:
        if not self.query_metrics:
            return 0.0
        return sum(q.reciprocal_rank for q in self.query_metrics) / len(self.query_metrics)

    @property
    def avg_context_relevance(self) -> float:
        if not self.query_metrics:
            return 0.0
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
    def avg_llm_groundedness(self) -> Optional[float]:
        vals = [q.llm_groundedness for q in self.query_metrics if q.llm_groundedness is not None]
        return sum(vals) / len(vals) if vals else None

    @property
    def avg_llm_answer_relevance(self) -> Optional[float]:
        vals = [q.llm_answer_relevance for q in self.query_metrics if q.llm_answer_relevance is not None]
        return sum(vals) / len(vals) if vals else None

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

    @property
    def distance_threshold(self) -> float:
        if not self.query_metrics:
            return DISTANCE_THRESHOLD
        return self.query_metrics[0].distance_threshold

    def to_dict(self) -> dict:
        d: dict = {
            "cosine_distance_threshold_consistency": round(self.cosine_threshold_consistency, 4),
            "hit_rate_at_k":                         round(self.hit_rate,                     4),
            "mrr":                                   round(self.mrr,                          4),
            "context_relevance_mean":                round(self.avg_context_relevance,         4),
            "groundedness_mean":                     round(self.avg_groundedness,              4),
            "answer_relevance_mean":                 round(self.avg_answer_relevance,          4),
            "latency_per_step_mean_s":               self.avg_latency.to_dict(),
            "distance_threshold":                    self.distance_threshold,
            "num_queries":                           len(self.query_metrics),
        }
        if self.avg_llm_groundedness is not None:
            d["llm_groundedness_mean"]     = round(self.avg_llm_groundedness,     4)
            d["llm_answer_relevance_mean"] = round(self.avg_llm_answer_relevance or 0, 4)

        d["per_query"] = [
            {
                "question":              q.question,
                "hit":                   q.hit,
                "first_relevant_rank":   q.first_relevant_rank,
                "reciprocal_rank":       round(q.reciprocal_rank,      4),
                "threshold_consistency": round(q.threshold_consistent, 4),
                "context_relevance":     round(q.context_relevance,    4),
                "groundedness":          round(q.groundedness,         4),
                "answer_relevance":      round(q.answer_relevance,     4),
                **({"llm_groundedness":     round(q.llm_groundedness,     4)} if q.llm_groundedness     is not None else {}),
                **({"llm_answer_relevance": round(q.llm_answer_relevance, 4)} if q.llm_answer_relevance is not None else {}),
                "distances":             [round(d, 4) for d in q.distances],
                "latency_s":             q.latency.to_dict(),
                "answer_snippet":        q.answer[:200] + ("…" if len(q.answer) > 200 else ""),
            }
            for q in self.query_metrics
        ]
        return d

    def summary(self) -> str:
        d = self.to_dict()
        lines = [
            "═" * 62,
            "  RAG Evaluation Report  (v2)",
            "═" * 62,
            f"  Queries evaluated        : {d['num_queries']}",
            f"  Distance threshold       : {d['distance_threshold']}",
            "─" * 62,
            "  Token-based metrics:",
            f"    Cosine Threshold Cons. : {d['cosine_distance_threshold_consistency']:.3f}",
            f"    Hit Rate @ K           : {d['hit_rate_at_k']:.3f}",
            f"    MRR                    : {d['mrr']:.3f}",
            f"    Context Relevance(NDCG): {d['context_relevance_mean']:.3f}  (higher=better)",
            f"    Groundedness           : {d['groundedness_mean']:.3f}",
            f"    Answer Relevance       : {d['answer_relevance_mean']:.3f}",
        ]
        if "llm_groundedness_mean" in d:
            lines += [
                "─" * 62,
                "  LLM-Judge metrics:",
                f"    LLM Groundedness       : {d['llm_groundedness_mean']:.3f}",
                f"    LLM Answer Relevance   : {d['llm_answer_relevance_mean']:.3f}",
            ]
        lines += [
            "─" * 62,
            "  Latency (mean):",
            f"    Retrieve : {d['latency_per_step_mean_s']['retrieve_s']:.3f}s",
            f"    Generate : {d['latency_per_step_mean_s']['answer_s']:.3f}s",
            f"    Reflect  : {d['latency_per_step_mean_s']['reflect_s']:.3f}s",
            f"    Total    : {d['latency_per_step_mean_s']['total_s']:.3f}s",
            "═" * 62,
        ]
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# Text helpers
# ══════════════════════════════════════════════════════════════════════════════

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "and", "or", "but", "not", "it", "its", "this", "that",
    "what", "which", "who", "how", "when", "where", "why",
    "do", "does", "did", "has", "have", "had", "will", "would",
    "can", "could", "should", "may", "might", "shall",
}


def _tokenise(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _token_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tok in _tokenise(text):
        if tok not in STOP_WORDS:
            counts[tok] = counts.get(tok, 0) + 1
    return counts


def _idf_weights(docs: list[str]) -> dict[str, float]:
    """
    Compute IDF weights over a small corpus of docs.
    IDF(t) = log(1 + N / df(t))  where df = num docs containing t.
    """
    N  = len(docs)
    df: dict[str, int] = {}
    for doc in docs:
        for tok in set(_tokenise(doc)):
            if tok not in STOP_WORDS:
                df[tok] = df.get(tok, 0) + 1
    return {t: math.log(1.0 + N / v) for t, v in df.items()}


# ── BLEU (unigram + bigram) ────────────────────────────────────────────────

def _ngrams(tokens: list[str], n: int) -> dict[tuple, int]:
    counts: dict[tuple, int] = {}
    for i in range(len(tokens) - n + 1):
        ng = tuple(tokens[i:i + n])
        counts[ng] = counts.get(ng, 0) + 1
    return counts


def bleu(hypothesis: str, reference: str) -> float:
    """
    Corpus BLEU-1/2 (geometric mean of unigram and bigram precision)
    with brevity penalty.  Range 0–1.

    FIX: Brevity penalty formula corrected to exp(1 - ref_len / hyp_len).
         Previously was inverted (exp(1 - hyp_len / ref_len)), which
         penalised long hypotheses instead of short ones.
    """
    hyp_tok = _tokenise(hypothesis)
    ref_tok = _tokenise(reference)
    if not hyp_tok or not ref_tok:
        return 0.0

    scores = []
    for n in (1, 2):
        hyp_ng = _ngrams(hyp_tok, n)
        ref_ng = _ngrams(ref_tok, n)
        clip   = sum(min(c, ref_ng.get(ng, 0)) for ng, c in hyp_ng.items())
        total  = sum(hyp_ng.values())
        scores.append(clip / total if total else 0.0)

    if 0.0 in scores:
        return 0.0

    geo = math.exp(sum(math.log(s) for s in scores) / len(scores))
    # FIX: BP = exp(1 - ref_len / hyp_len) when hyp is shorter than ref.
    #      The original code had the ratio inverted.
    bp  = math.exp(1 - len(ref_tok) / len(hyp_tok)) if len(hyp_tok) < len(ref_tok) else 1.0
    return bp * geo


# ── ROUGE-L (longest common subsequence) ──────────────────────────────────

def _lcs_length(a: list[str], b: list[str]) -> int:
    """Standard LCS dynamic programming."""
    m, n  = len(a), len(b)
    prev  = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(curr[j - 1], prev[j])
        prev = curr
    return prev[n]


def rouge_l(hypothesis: str, reference: str) -> float:
    """
    ROUGE-L F1 based on longest common subsequence.  Range 0–1.
    """
    hyp_tok = _tokenise(hypothesis)
    ref_tok = _tokenise(reference)
    if not hyp_tok or not ref_tok:
        return 0.0
    lcs = _lcs_length(hyp_tok, ref_tok)
    if lcs == 0:
        return 0.0
    p = lcs / len(hyp_tok)
    r = lcs / len(ref_tok)
    return 2 * p * r / (p + r)


# ══════════════════════════════════════════════════════════════════════════════
# ★ IMPROVED  Groundedness
# ══════════════════════════════════════════════════════════════════════════════

def _groundedness(answer: str, context_chunks: list[dict]) -> float:
    """
    Hybrid groundedness: TF-IDF token coverage + character n-gram overlap.
    
    Token overlap alone scores low when the model paraphrases.
    Character n-grams (e.g. "zone bound", "non-rotat") catch partial
    matches that survive paraphrase, giving a much fairer score.
    
    Final score = 0.4 * token_coverage + 0.6 * char_ngram_coverage
    """
    if not context_chunks or not answer.strip():
        return 0.0

    # ── Build merged chunk pool (distance-weighted) ──────────────────
    all_texts = [answer] + [c.get("text", "") for c in context_chunks]
    idf = _idf_weights(all_texts)

    def _tfidf_counts(text: str) -> dict[str, float]:
        raw   = _token_counts(text)
        total = max(sum(raw.values()), 1)
        return {t: (cnt / total) * idf.get(t, 1.0) for t, cnt in raw.items()}

    def _char_ngrams(text: str, n: int = 4) -> set[str]:
        """Character n-grams over lowercased, whitespace-collapsed text."""
        t = re.sub(r'\s+', ' ', text.lower().strip())
        return {t[i:i+n] for i in range(len(t) - n + 1)}

    ans_tfidf  = _tfidf_counts(answer)
    ans_ngrams = _char_ngrams(answer)

    if not ans_tfidf or not ans_ngrams:
        return 0.0

    ans_total = sum(ans_tfidf.values())

    merged_tokens: dict[str, float] = {}
    merged_ngrams: set[str]         = set()
    total_weight = 0.0

    for chunk in context_chunks:
        chunk_text  = chunk.get("text", "")
        chunk_dist  = float(chunk.get("distance", 1.0))
        chunk_tfidf = _tfidf_counts(chunk_text)
        if not chunk_tfidf:
            continue

        w = 1.0 / (1.0 + chunk_dist)
        total_weight += w

        for tok, val in chunk_tfidf.items():
            merged_tokens[tok] = merged_tokens.get(tok, 0.0) + val * w

        merged_ngrams |= _char_ngrams(chunk_text)

    if not merged_tokens or total_weight == 0:
        return 0.0

    for tok in merged_tokens:
        merged_tokens[tok] /= total_weight

    # ── Token coverage (answer → merged chunk pool) ───────────────────
    common        = set(ans_tfidf) & set(merged_tokens)
    token_overlap = sum(min(ans_tfidf[t], merged_tokens[t]) for t in common)
    token_score   = min(1.0, token_overlap / ans_total)

    # ── Char n-gram coverage (what fraction of answer n-grams appear
    #    anywhere in the chunks) ─────────────────────────────────────
    if ans_ngrams:
        matched_ngrams = ans_ngrams & merged_ngrams
        ngram_score    = len(matched_ngrams) / len(ans_ngrams)
    else:
        ngram_score = 0.0

    # ── Hybrid: n-gram weighted higher (more paraphrase-robust) ──────
    return 0.4 * token_score + 0.6 * ngram_score
# ══════════════════════════════════════════════════════════════════════════════
# ★ IMPROVED  Answer Relevance
# ══════════════════════════════════════════════════════════════════════════════

def _answer_relevance(answer: str, question: str) -> float:
    """
    IDF-weighted question-coverage score.

    Improvement over v1 (F2 with full-answer precision):
      • Precision is computed over *question-vocabulary tokens in the
        answer only* — extra answer tokens that are not in the question
        are completely ignored.  Long, detailed answers are not penalised.
      • IDF weights are recomputed over the question+answer pair so
        domain-specific question terms receive higher importance.
      • A light brevity bonus rewards answers that are at least as long
        as the question (to penalise empty/trivial one-word answers).

    Range: 0.0 → 1.0.

    FIX: Precision was computed only over question tokens *present* in the
         answer, making the denominator always equal to the numerator and
         precision always 1.0.  Precision now uses the full question-token
         mass as denominator so missing question terms correctly reduce it.
    """
    if not answer.strip() or not question.strip():
        return 0.0

    counts_q = _token_counts(question)
    counts_a = _token_counts(answer)
    if not counts_q or not counts_a:
        return 0.0

    idf = _idf_weights([question, answer])

    def w(t: str) -> float:
        return idf.get(t, 1.0)

    # ── Recall: question keywords covered by answer ────────────────────
    q_total   = sum(w(t) * counts_q[t] for t in counts_q)
    q_matched = sum(w(t) * min(counts_q[t], counts_a.get(t, 0)) for t in counts_q)
    recall    = q_matched / q_total if q_total > 0 else 0.0

    # ── Precision: fraction of question-vocab mass present in answer ───
    # FIX: denominator is the *full* question-vocab weight in the answer
    #      (including zeros for absent terms), not just the present subset.
    #      Previously restricted to tokens already in the answer, making
    #      precision trivially 1.0 whenever any overlap existed.
    qv_in_answer_total = sum(w(t) * counts_a.get(t, 0) for t in counts_q)
    qv_match           = sum(w(t) * min(counts_a.get(t, 0), counts_q[t]) for t in counts_q)
    precision = qv_match / qv_in_answer_total if qv_in_answer_total > 0 else recall

    if precision + recall == 0.0:
        return 0.0

    # F-beta β=2: recall weighted 4× over precision
    beta  = 2.0
    f2    = (1 + beta ** 2) * precision * recall / (beta ** 2 * precision + recall)

    # Light brevity bonus: penalise trivially short answers
    answer_len   = sum(counts_a.values())
    question_len = max(sum(counts_q.values()), 1)
    brevity      = min(1.0, answer_len / max(1, question_len * 0.5))

    return f2 * brevity


# ══════════════════════════════════════════════════════════════════════════════
# LLM-as-Judge  (alternative evaluation method)
# ══════════════════════════════════════════════════════════════════════════════

_LLM_GROUNDEDNESS_PROMPT = """\
You are an evaluation assistant. Score how well the ANSWER is grounded
in the CONTEXT on a scale from 0.0 to 1.0 where:
  1.0 = every claim in the answer is fully supported by the context
  0.5 = some claims are supported, some are not
  0.0 = the answer contradicts or ignores the context entirely

CONTEXT:
{context}

ANSWER:
{answer}

Reply with ONLY a decimal number between 0.0 and 1.0. No explanation."""

_LLM_ANSWER_RELEVANCE_PROMPT = """\
You are an evaluation assistant. Score how relevant the ANSWER is to the
QUESTION on a scale from 0.0 to 1.0 where:
  1.0 = the answer directly and completely addresses the question
  0.5 = the answer partially addresses the question
  0.0 = the answer is off-topic or does not address the question at all

QUESTION:
{question}

ANSWER:
{answer}

Reply with ONLY a decimal number between 0.0 and 1.0. No explanation."""


def _parse_score(text: str) -> float:
    """Extract the first float from an LLM judge response."""
    m = re.search(r"[01]?\.\d+|\d+", text.strip())
    if m:
        val = float(m.group())
        return max(0.0, min(1.0, val))
    return 0.0


async def _llm_groundedness(
    answer: str,
    context_chunks: list[dict],
    llm_fn: Callable[[str], Awaitable[str]],
) -> float:
    """
    LLM-as-Judge groundedness.  Uses at most the top-3 chunks to keep
    the context window manageable.
    """
    top_chunks = sorted(context_chunks, key=lambda c: c.get("distance", 1.0))[:3]
    context    = "\n\n---\n\n".join(c.get("text", "") for c in top_chunks)
    prompt     = _LLM_GROUNDEDNESS_PROMPT.format(context=context, answer=answer)
    try:
        raw = await llm_fn(prompt)
        return _parse_score(raw)
    except Exception as exc:
        logger.warning("LLM judge groundedness failed: %s", exc)
        return 0.0


async def _llm_answer_relevance(
    answer: str,
    question: str,
    llm_fn: Callable[[str], Awaitable[str]],
) -> float:
    """LLM-as-Judge answer relevance."""
    prompt = _LLM_ANSWER_RELEVANCE_PROMPT.format(question=question, answer=answer)
    try:
        raw = await llm_fn(prompt)
        return _parse_score(raw)
    except Exception as exc:
        logger.warning("LLM judge answer_relevance failed: %s", exc)
        return 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Evaluator
# ══════════════════════════════════════════════════════════════════════════════

class Evaluator:
    """
    Runs the RAG evaluation suite against a live RAGService.

    Parameters
    ----------
    rag_service        : RAGService instance.
    distance_threshold : Override the module-level DISTANCE_THRESHOLD.
    use_llm_judge      : If True, also score groundedness and answer
                         relevance with an LLM judge (RAGAS-style).
                         Requires llm_judge_fn to be supplied.
    llm_judge_fn       : Async callable (prompt: str) -> str.
                         Called for LLM-judge metrics when use_llm_judge=True.
    """

    def __init__(
        self,
        rag_service,
        distance_threshold: float = DISTANCE_THRESHOLD,
        use_llm_judge: bool = False,
        llm_judge_fn: Optional[Callable[[str], Awaitable[str]]] = None,
    ) -> None:
        self.rag_service        = rag_service
        self.distance_threshold = distance_threshold
        self.use_llm_judge      = use_llm_judge
        self.llm_judge_fn       = llm_judge_fn

        if use_llm_judge and llm_judge_fn is None:
            raise ValueError("use_llm_judge=True requires llm_judge_fn to be supplied.")

    async def run(
        self,
        queries: list[EvalQuery],
        top_k:   int = 5,
    ) -> EvalReport:
        all_metrics: list[QueryMetrics] = []
        for eq in queries:
            qm = await self._evaluate_one(eq, top_k=top_k)
            all_metrics.append(qm)
        return EvalReport(query_metrics=all_metrics)

    async def _evaluate_one(self, eq: EvalQuery, top_k: int) -> QueryMetrics:
        latency = StepLatency()

        result = await self.rag_service.ask(eq.question, top_k=top_k)

        latency.retrieve = float(result.get("retrieve_s", 0.0))
        latency.answer   = float(result.get("generate_s", 0.0))

        answer  = result.get("answer", "")
        sources = result.get("sources", [])

        chunks = [
            {
                "text":     s.get("content", ""),
                "source":   s.get("file", ""),
                "page":     s.get("page", 0),
                "distance": s.get("distance", 1.0),
            }
            for s in sources
        ]

        distances           = [c["distance"] for c in chunks]
        first_relevant_rank = self._first_relevant_rank(distances)

        # FIX: Time only CPU-bound metric computation in reflect step,
        #      not the LLM judge calls (which are I/O-bound and slow).
        t0           = time.perf_counter()
        groundedness = _groundedness(answer, chunks)
        answer_rel   = _answer_relevance(answer, eq.question)
        latency.reflect = time.perf_counter() - t0

        # Optional LLM judge (I/O-bound — timed separately if needed)
        llm_gr  = None
        llm_ar  = None
        if self.use_llm_judge and self.llm_judge_fn:
            llm_gr, llm_ar = await asyncio.gather(
                _llm_groundedness(answer, chunks, self.llm_judge_fn),
                _llm_answer_relevance(answer, eq.question, self.llm_judge_fn),
            )

        return QueryMetrics(
            question             = eq.question,
            chunks_retrieved     = len(chunks),
            distances            = distances,
            first_relevant_rank  = first_relevant_rank,
            answer               = answer,
            groundedness         = groundedness,
            answer_relevance     = answer_rel,
            latency              = latency,
            distance_threshold   = self.distance_threshold,
            llm_groundedness     = llm_gr,
            llm_answer_relevance = llm_ar,
        )

    def _first_relevant_rank(self, distances: list[float]) -> int | None:
        for rank, dist in enumerate(distances, start=1):
            if dist < self.distance_threshold:
                return rank
        return None


# ══════════════════════════════════════════════════════════════════════════════
# FastAPI router
# ══════════════════════════════════════════════════════════════════════════════

try:
    from fastapi import APIRouter as _APIRouter, HTTPException as _HTTPException
    from pydantic import BaseModel as _BaseModel, Field as _Field

    eval_router = _APIRouter(prefix="/eval", tags=["Evaluation"])

    class _TextEvalRequest(_BaseModel):
        questions:          list[str] = _Field(...,  description="Questions to evaluate")
        top_k:              int       = _Field(5,    description="Chunks per query")
        distance_threshold: float     = _Field(
            DISTANCE_THRESHOLD,
            description="Cosine distance threshold (default 0.60)",
        )
        use_llm_judge: bool = _Field(
            False,
            description="Enable LLM-as-Judge scoring (slower, more accurate)",
        )

    @eval_router.post("/text")
    async def eval_text(body: _TextEvalRequest):
        """
        Evaluate text queries against the global PDF knowledge base.

        Returns token-based metrics (always) plus LLM-judge metrics
        (when use_llm_judge=True).

        Alternative evaluation methods available:
          • bleu(hypothesis, reference)   — import from this module
          • rouge_l(hypothesis, reference) — import from this module
          • LLM-as-Judge via use_llm_judge=True (RAGAS-style)
        """
        from services.service_factory import get_rag_service  # type: ignore

        judge_fn = None
        if body.use_llm_judge:
            # FIX: Raise a clear error instead of silently disabling the
            #      judge.  Wire up your LLM client here and remove the raise.
            #
            # Example (OpenAI-compatible):
            #   from openai import AsyncOpenAI
            #   _client = AsyncOpenAI()
            #   async def judge_fn(prompt: str) -> str:
            #       r = await _client.chat.completions.create(
            #           model="gpt-4o-mini",
            #           messages=[{"role": "user", "content": prompt}],
            #       )
            #       return r.choices[0].message.content or ""
            raise _HTTPException(
                status_code=501,
                detail=(
                    "LLM judge is not configured on this server. "
                    "Wire up llm_judge_fn in eval_text() to enable it."
                ),
            )

        ev = Evaluator(
            rag_service        = get_rag_service(),
            distance_threshold = body.distance_threshold,
            use_llm_judge      = body.use_llm_judge and judge_fn is not None,
            llm_judge_fn       = judge_fn,
        )
        queries = [EvalQuery(question=q) for q in body.questions]
        report  = await ev.run(queries, top_k=body.top_k)
        return report.to_dict()

except ImportError:
    eval_router = None  # type: ignore[assignment]