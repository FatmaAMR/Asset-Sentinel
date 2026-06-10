"""
services/diagnose_service.py
─────────────────────────────
Mirrors RAGService exactly, but for machine fault diagnosis.

Flow
────
  1.  window_event_to_chunks() — build query text via the SAME chunker used at
                                  ingest time so vectors land in the same space.
  2.  embedder.query()         — retrieve top-k similar historical window chunks
  3.  _extract_reason()        — pull the stored "Reason:" field from each chunk
  4.  _build_prompt()          — assemble context + query prompt (reason-focused)
  5.  llm.generate()           — call master-llm-service
  6.  _parse() / _clean()      — strip markdown artefacts from the raw reply
  7.  return dict              — matches the DiagnoseResponse schema, including
                                  `extracted_reason` from the best-matching chunk

Design goals
────────────
  • Chunk text used for querying is identical to ingest chunk text
    (window_event_to_chunks with reason="" so no annotation bleeds in).
  • Prompt asks the LLM to extract + synthesise the `reason` values found in
    the retrieved chunks and return that as the primary answer.
  • extracted_reason in the response is the raw stored reason from chunk rank-1
    (no LLM involvement — deterministic).
  • All LLM interaction lives here, not in the router.
  • The service is stateless — pass embedder + llm at construction time.
  • Easy to unit-test: inject a mock Embedder and a mock LLMClient.
"""

import re
import logging
import time
from dataclasses import dataclass
from types import SimpleNamespace

from services.embedder          import SensorEmbedder, EmbedMode
from services.llm_client        import LLMClient
from services.window_chunker    import window_event_to_chunks
from services.notification_bus  import publish_diagnosis

logger = logging.getLogger("diagnose_service")


# ── Parsed result dataclass ──────────────────────────────────────────────────

@dataclass
class ParsedDiagnosis:
    cause:   str   # primary fault cause / extracted reason sentence
    details: str   # supporting reasoning

    def to_text(self) -> str:
        """Return the best non-empty field for the final response."""
        return (self.cause or self.details).strip()


# ── Service ──────────────────────────────────────────────────────────────────

class DiagnoseService:
    """
    Stateful service — holds an Embedder and LLMClient.
    One instance per machine is created on demand via service_factory.
    """

    SYSTEM_PROMPT = (
        "You are a senior industrial maintenance engineer with expertise in "
        "predictive fault detection. "
        "You will be given current sensor readings for a machine and a set of "
        "similar historical fault cases retrieved from the knowledge base. "
        "Each historical case includes a stored 'Reason' annotation that "
        "describes why the fault occurred.\n"
        "Your task:\n"
        "  1. Extract and synthesise the most relevant reason(s) from the "
        "historical cases — prioritise the closest match (lowest distance).\n"
        "  2. Confirm or refine the extracted reason by referencing the current "
        "sensor values.\n"
        "  3. Return the extracted fault reason as a single concise sentence.\n"
        "Plain text only, no markdown, no bullet points."
    )

    def __init__(self, embedder: SensorEmbedder, llm: LLMClient) -> None:
        self.embedder = embedder
        self.llm      = llm

    # ── Main entry point ──────────────────────────────────────────────────────

    async def diagnose(
        self,
        machine_id:     str,
        label:          str,
        rul:            float,
        window_sliding: object,
        message_id:     str,
        timestamp:      float,
        top_k:          int = 5,
    ) -> dict:
        """
        Run the full diagnose pipeline and return a result dict compatible
        with DiagnoseResponse.

        Parameters
        ----------
        machine_id     : machine identifier
        label          : fault label from the prediction model
        rul            : remaining useful life value
        window_sliding : raw sensor window — list or dict
        message_id     : unique event UUID
        timestamp      : unix timestamp
        top_k          : number of similar historical chunks to retrieve

        Returns
        -------
        {
            "machine_id":       str,
            "query_text":       str,   # window chunk text (same as ingest path)
            "fault_cause":      str,   # LLM-synthesised reason
            "extracted_reason": str,   # raw reason from best-matching chunk
            "sources":          list[{"file", "page", "content", "distance"}],
        }
        """
        # 1. Build query text using the SAME chunker as ingest-window.
        #    message_id and timestamp are passed through but window_chunker
        #    no longer includes them in the chunk text, so the same sensor
        #    window always produces the same embedding vector.
        fake_event = SimpleNamespace(
            machine_id     = machine_id,
            label          = label,
            rul            = rul,
            window_sliding = window_sliding,
            message_id     = message_id,
            timestamp      = timestamp,
            reason         = "",   # omit — querying, not annotating
        )
        query_chunks = window_event_to_chunks(fake_event)
        query_text   = query_chunks[0]["text"] if query_chunks else ""
        logger.info("DiagnoseService [%s] — query: %s…", machine_id, query_text[:120])

        # 2. Retrieve similar chunks
        # Pass raw window_sliding so SensorEmbedder builds the fused
        # Cohere-text + TS2Vec query vector (1280-d) — not text-only.
        chunks = self.embedder.query(
            query_text     = query_text,
            top_k          = top_k,
            window_sliding = window_sliding,
            mode           = EmbedMode.SENSOR_ONLY,   # similarity driven by raw sensor values
        )

        # 3. No history found → short-circuit
        if not chunks:
            logger.warning("DiagnoseService [%s] — collection is empty.", machine_id)
            return {
                "machine_id":       machine_id,
                "query_text":       query_text,
                "fault_cause":      (
                    f"No historical data found for machine '{machine_id}'. "
                    "Please ingest window events first."
                ),
                "extracted_reason": "",
                "sources":          [],
            }

        # 4. Extract stored reason from each chunk (deterministic, no LLM)
        extracted_reason = self._extract_reason(chunks[0]["text"])  # rank-1 chunk

        # 5. Build prompt (reason-extraction focused)
        prompt = self._build_prompt(machine_id, query_text, chunks)
        logger.debug("DiagnoseService prompt (first 300 chars): %s", prompt[:300])

        # 6. Call LLM
        try:
            raw = await self.llm.generate(
                prompt        = prompt,
                caller        = "consulting",
                system_prompt = self.SYSTEM_PROMPT,
                temperature   = 0.15,
                max_tokens    = 512,
            )
        except Exception as exc:
            logger.exception("DiagnoseService LLM call failed: %s", exc)
            raise

        # 7. Parse + clean
        parsed      = self._parse(raw)
        fault_cause = self._clean(parsed.to_text())

        # 8. Build source list (deduped by source+page, ordered by distance)
        seen    = set()
        sources = []
        for chunk in chunks:
            key = (chunk["source"], chunk["page"])
            if key not in seen:
                seen.add(key)
                sources.append({
                    "file":     chunk["source"],
                    "page":     chunk["page"],
                    "content":  chunk["text"],
                    "distance": chunk["distance"],
                })

        result = {
            "machine_id":       machine_id,
            "query_text":       query_text,
            "fault_cause":      fault_cause,
            "extracted_reason": extracted_reason,
            "similarity_mode":  EmbedMode.SENSOR_ONLY.value,
            "sources":          sources,
        }

        # ── 9. Publish to RabbitMQ so all SSE subscribers are notified
        await publish_diagnosis(machine_id, {
            "type":             "diagnosis_complete",
            "machine_id":       machine_id,
            "message_id":       message_id,
            "extracted_reason": extracted_reason,
            "fault_cause":      fault_cause,
            "timestamp":        timestamp,
            "notified_at":      time.time(),
        })

        return result

    # ── Reason extractor (deterministic) ─────────────────────────────────────

    @staticmethod
    def _extract_reason(text: str) -> str:
        """
        Pull the stored 'Reason: <value>.' field from a chunk that was produced
        by window_event_to_chunks().  Returns empty string if absent.
        """
        m = re.search(r"Reason:\s*(.+?)(?:\s*\.|$)", text)
        if m:
            candidate = m.group(1).strip().rstrip(".")
            # Guard against accidentally matching the next field label
            if candidate and not candidate.startswith("Message"):
                return candidate
        return ""

    # ── Prompt builder ────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        machine_id: str,
        query_text: str,
        chunks:     list[dict],
    ) -> str:
        """
        Assemble the diagnose prompt.

        Structure:
          [Historical Cases — each includes the stored Reason annotation]
          Current Readings
          Task: extract + confirm the most likely reason
          Diagnosis:
        """
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            stored_reason = self._extract_reason(chunk["text"])
            reason_line   = f"  Stored reason: {stored_reason}" if stored_reason else ""
            context_parts.append(
                f"[Case {i} — {chunk['source']}, page {chunk['page']} "
                f"| distance: {chunk['distance']:.4f}]{reason_line}\n"
                f"{chunk['text']}"
            )
        context = "\n\n".join(context_parts)

        return (
            f"Historical fault cases from the knowledge base "
            f"(each contains a stored 'Reason' annotation):\n"
            f"{context}\n\n"
            f"Current sensor readings for machine '{machine_id}':\n"
            f"{query_text}\n\n"
            f"Extract the most likely fault reason from the historical cases above "
            f"and confirm it against the current sensor values. "
            f"Return the extracted reason as a single concise sentence.\n\n"
            f"Diagnosis:"
        )

    # ── Output parser ─────────────────────────────────────────────────────────

    def _parse(self, raw: str) -> ParsedDiagnosis:
        """
        Extract structured fields if the LLM used XML tags; otherwise treat
        the whole response as the diagnosis detail.
        """
        cause_match = re.search(r"<cause>(.*?)</cause>", raw, re.DOTALL)
        if cause_match:
            cause  = cause_match.group(1).strip()
            detail = re.sub(r"<cause>.*?</cause>", "", raw, flags=re.DOTALL).strip()
            return ParsedDiagnosis(cause=cause, details=detail)
        return ParsedDiagnosis(cause="", details=raw.strip())

    # ── Markdown / artefact cleaner ───────────────────────────────────────────

    def _clean(self, text: str) -> str:
        """Strip markdown artefacts — mirrors RAGService._clean()."""
        text = re.sub(r"#{1,6}\s*", "", text)
        text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = text.replace("\\n", " ")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.replace("\\", "")
        text = re.sub(r"  +", " ", text)
        return text.strip()

