"""
api/rag_router.py
──────────────────
FastAPI router — all RAG endpoints.

Embedding split
───────────────
  PDF / global KB  ──►  PdfEmbedder   (Cohere text 1024-d)
                         collection: "maintenance_manuals"
                         endpoints:  POST /rag/ask
                                     POST /rag/ingest  (no machine_id)
                                     GET  /rag/status  (no machine_id)

  Sensor windows   ──►  SensorEmbedder (Cohere text 1024-d + TS2Vec 256-d = 1280-d)
                         collection: "sensor_{machine_id}"
                         endpoints:  POST /rag/ingest-window
                                     POST /rag/diagnose
                                     POST /rag/machine-query
                                     GET  /rag/status?machine_id=...
"""

import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Query

from schemas.rag_schemas import (
    AskRequest, AskResponse, IngestResponse,
    DiagnoseRequest, DiagnoseResponse, DiagnosisSource,
    DeleteChunksRequest, DeleteChunksResponse,
    ResetRequest, ResetResponse,
    WindowIngestRequest, WindowIngestResponse,
    MachineQueryRequest, MachineQueryResponse, SimilarWindowMatch,
)
from services.pdf_loader      import load_documents, ChunkProfile
from services.service_factory import (
    get_rag_service,
    get_pdf_embedder,
    get_sensor_embedder,
    get_embedder,           # back-compat (used by delete/reset/status with no machine_id)
    get_llm,
    get_diagnose_service,
)
from services.sensor_normalizer import normalize
from services.window_chunker    import window_event_to_chunks
from services.llm_client        import LLMClient
from db.chroma_client           import list_collections
from config                     import settings

logger        = logging.getLogger("rag_router")
router        = APIRouter(prefix="/rag", tags=["RAG"])
KNOWLEDGE_DIR = settings.knowledge_folder


# ══════════════════════════════════════════════════════════════════════════════
# PDF / global KB endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest):
    """Ask a question against the global PDF knowledge base."""
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        result = await get_rag_service().ask(body.question, top_k=body.top_k)
    except Exception as exc:
        logger.exception("RAG ask failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return AskResponse(
        question = result["question"],
        answer   = result["answer"],
        sources  = result["sources"],
        intent   = "RAG",
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    file:       UploadFile = File(...),
    machine_id: str | None = Query(None, description="Target machine ID; omit for global KB"),
):
    """
    Upload a PDF or TXT file.

    - **machine_id omitted**  → global KB, PdfEmbedder (Cohere text, 1024-d).
    - **machine_id supplied** → machine PDF folder, PdfEmbedder for that machine
      (separate collection "machine_pdf_{machine_id}", Cohere text only).
      Note: sensor window data goes to "sensor_{machine_id}" via /ingest-window.
    """
    fname = file.filename or ""
    if not (fname.lower().endswith(".pdf") or fname.lower().endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")

    profile  = ChunkProfile.MACHINE if machine_id else ChunkProfile.GLOBAL
    save_dir  = os.path.join(KNOWLEDGE_DIR, machine_id) if machine_id else KNOWLEDGE_DIR
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, fname)

    with open(save_path, "wb") as f:
        f.write(await file.read())
    logger.info("Saved '%s' (profile=%s, machine_id=%s).", save_path, profile.value, machine_id)

    try:
        # PDFs always go into PdfEmbedder — global or machine-specific collection
        if machine_id:
            from db.chroma_client import get_chroma_collection
            from services.embedder import PdfEmbedder as _PE
            col = get_chroma_collection(f"pdf_{machine_id}")
            embedder = _PE(col)
        else:
            embedder = get_pdf_embedder()

        chunks = load_documents(save_dir, profile=profile)
        if not chunks:
            return IngestResponse(
                status       = "no_content_found",
                chunks_added = 0,
                total_chunks = embedder.collection.count(),
            )
        result = embedder.build(chunks)
        return IngestResponse(
            status       = "ok",
            chunks_added = result["chunks_added"],
            total_chunks = result["total_chunks"],
        )
    except Exception as exc:
        logger.exception("Ingest failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# Sensor window endpoints  (SensorEmbedder — fused 1280-d)
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/ingest-window", response_model=WindowIngestResponse)
async def ingest_window(body: WindowIngestRequest):
    """
    Receive a machine window event (RUL + sliding-window sensor data) and
    store it in the machine's SENSOR collection using the fused
    Cohere-text + TS2Vec embedding (1280-d).

    Collection used: "sensor_{machine_id}"
    """
    try:
        embedder = get_sensor_embedder(body.machine_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not access sensor collection: {exc}")

    chunks = window_event_to_chunks(body)
    if not chunks:
        raise HTTPException(status_code=422, detail="Window data produced no embeddable chunks.")

    try:
        # Pass raw window_sliding so SensorEmbedder can build the TS2Vec component
        result = embedder.build(chunks, window_sliding=body.window_sliding)
    except Exception as exc:
        logger.exception("Window ingest failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return WindowIngestResponse(
        status        = "ok",
        machine_id    = body.machine_id,
        message_id    = body.message_id,
        chunks_added  = result["chunks_added"],
        total_chunks  = result["total_chunks"],
    )


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(body: DiagnoseRequest):
    """
    Diagnose a live machine window by similarity-searching the machine's
    SENSOR collection (fused 1280-d vectors) and asking the LLM to
    synthesise the most likely fault cause.

    Collection used: "sensor_{machine_id}"
    """
    try:
        svc    = get_diagnose_service(body.machine_id)
        result = await svc.diagnose(
            machine_id     = body.machine_id,
            label          = body.label,
            rul            = body.rul,
            window_sliding = body.window_sliding,
            message_id     = body.message_id,
            timestamp      = body.timestamp,
            top_k          = body.top_k,
        )
    except Exception as exc:
        logger.exception("Diagnose failed for machine '%s': %s", body.machine_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))

    sources = [
        DiagnosisSource(
            file     = s["file"],
            page     = s["page"],
            content  = s["content"],
            distance = s["distance"],
        )
        for s in result["sources"]
    ]
    return DiagnoseResponse(
    machine_id       = result["machine_id"],
    query_text       = result["query_text"],
    fault_cause      = result["fault_cause"],
    extracted_reason = result["extracted_reason"],
    similarity_mode  = result.get("similarity_mode", "sensor_only"),
    sources          = sources,
)  


@router.post("/machine-query", response_model=MachineQueryResponse)
async def machine_query(
    body:       MachineQueryRequest,
    embed_mode: str = Query(
        "sensor_only",
        description=(
            "Which embedding drives similarity: "
            "'sensor_only' (TS2Vec — raw sensor values, default), "
            "'text_only' (Cohere — label/description text), "
            "'fused' (both combined)"
        ),
    ),
):
    """
    Send a live machine window (no reason) and retrieve the most similar
    historically-stored windows from the SENSOR collection (fused 1280-d).

    Collection used: "sensor_{machine_id}"
    """
    from types import SimpleNamespace
    import re

    # Build query chunk text (same path as ingest — reason="" so no annotation bleeds)
    fake_event = SimpleNamespace(
        machine_id     = body.machine_id,
        label          = body.label,
        rul            = body.rul,
        window_sliding = body.window_sliding,
        message_id     = body.message_id,
        timestamp      = body.timestamp,
        reason         = "",
    )
    query_chunks = window_event_to_chunks(fake_event)
    if not query_chunks:
        raise HTTPException(status_code=422, detail="Window data produced no embeddable text.")

    query_text = query_chunks[0]["text"]
    logger.info("machine-query [%s]: %s…", body.machine_id, query_text[:120])

    try:
        embedder = get_sensor_embedder(body.machine_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not access sensor collection: {exc}")

    if embedder.collection.count() == 0:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No sensor data found for machine '{body.machine_id}'. "
                "Please ingest window events first via POST /rag/ingest-window."
            ),
        )

    from services.embedder import EmbedMode
    try:
        mode = EmbedMode(embed_mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid embed_mode '{embed_mode}'. Choose: sensor_only, text_only, fused.",
        )

    # Query with chosen mode
    raw_chunks = embedder.query(
        query_text     = query_text,
        top_k          = body.top_k,
        window_sliding = body.window_sliding,
        mode           = mode,
    )

    if not raw_chunks:
        raise HTTPException(status_code=404, detail="No similar windows found.")

    def _extract_reason(text: str) -> str:
        m = re.search(r"Reason:\s*(.+?)(?:\s*\.|$)", text)
        if m:
            candidate = m.group(1).strip().rstrip(".")
            if candidate and not candidate.startswith("Message"):
                return candidate
        return ""

    matches: list[SimilarWindowMatch] = []
    for rank, chunk in enumerate(raw_chunks, start=1):
        matches.append(SimilarWindowMatch(
            rank          = rank,
            distance      = chunk["distance"],
            source        = chunk["source"],
            stored_reason = _extract_reason(chunk["text"]),
            text_preview  = chunk["text"][:200] + ("…" if len(chunk["text"]) > 200 else ""),
            full_text     = chunk["text"],
        ))

    best = matches[0]
    return MachineQueryResponse(
        machine_id    = body.machine_id,
        message_id    = body.message_id,
        query_text    = query_text,
        best_reason   = best.stored_reason,
        best_distance = best.distance,
        similarity_mode = mode.value,
        matches       = matches,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Shared / admin endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/status")
async def status(
    machine_id:    str | None = Query(None),
    sensor_only:   bool       = Query(False, description="True → inspect sensor collection; False → PDF collection"),
):
    """
    Return collection health.

    - machine_id=None,  sensor_only=False → global PDF KB
    - machine_id=<id>,  sensor_only=False → PDF collection for that machine
    - machine_id=<id>,  sensor_only=True  → sensor collection for that machine
    """
    try:
        if machine_id and sensor_only:
            embedder = get_sensor_embedder(machine_id)
        elif machine_id:
            from db.chroma_client import get_chroma_collection
            from services.embedder import PdfEmbedder as _PE
            embedder = _PE(get_chroma_collection(f"pdf_{machine_id}"))
        else:
            embedder = get_pdf_embedder()

        collection_name = embedder.collection.name
        total           = embedder.collection.count()
        collections     = list_collections()

        chunks_payload: list[dict] = []
        if total > 0:
            raw = embedder.collection.get(include=["documents", "metadatas"])
            for i, doc_id in enumerate(raw["ids"]):
                text     = raw["documents"][i] if raw.get("documents") else ""
                metadata = raw["metadatas"][i]  if raw.get("metadatas") else {}
                chunks_payload.append({
                    "id":           doc_id,
                    "source":       metadata.get("source", ""),
                    "page":         metadata.get("page", 0),
                    "embed_type":   metadata.get("embed_type", ""),
                    "text_preview": text[:120] + ("…" if len(text) > 120 else ""),
                    "text":         text,
                })

        return {
            "status":          "ready",
            "collection":      collection_name,
            "total_chunks":    total,
            "chunks":          chunks_payload,
            "all_collections": collections,
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/chunks")
async def list_chunks(
    machine_id:  str | None = Query(None,  description="Machine ID; omit for global PDF KB"),
    sensor_only: bool       = Query(False, description="True → sensor collection"),
    limit:       int        = Query(100,   ge=1, le=1000),
    offset:      int        = Query(0,     ge=0),
):
    """List chunks with pagination. Use sensor_only=true for sensor collections."""
    try:
        if machine_id and sensor_only:
            embedder = get_sensor_embedder(machine_id)
        elif machine_id:
            from db.chroma_client import get_chroma_collection
            from services.embedder import PdfEmbedder as _PE
            embedder = _PE(get_chroma_collection(f"pdf_{machine_id}"))
        else:
            embedder = get_pdf_embedder()

        collection_name = embedder.collection.name
        total           = embedder.collection.count()
        chunks_payload: list[dict] = []

        if total > 0:
            raw       = embedder.collection.get(include=["documents", "metadatas"])
            all_ids   = raw["ids"]
            all_docs  = raw.get("documents", [])
            all_meta  = raw.get("metadatas", [])
            page_ids  = all_ids[offset : offset + limit]
            page_docs = all_docs[offset : offset + limit] if all_docs else []
            page_meta = all_meta[offset : offset + limit] if all_meta else []

            for i, doc_id in enumerate(page_ids):
                text     = page_docs[i] if page_docs else ""
                metadata = page_meta[i] if page_meta else {}
                chunks_payload.append({
                    "id":           doc_id,
                    "source":       metadata.get("source", ""),
                    "page":         metadata.get("page", 0),
                    "embed_type":   metadata.get("embed_type", ""),
                    "text_preview": text[:120] + ("…" if len(text) > 120 else ""),
                    "text":         text,
                })

        return {
            "collection":   collection_name,
            "total_chunks": total,
            "offset":       offset,
            "limit":        limit,
            "chunks":       chunks_payload,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/documents")
async def list_documents(
    machine_id: str | None = Query(None, description="Omit for global PDF KB"),
):
    """
    Return one entry per unique PDF ingested into the knowledge base.
    Much lighter than /rag/chunks — no chunk text, just file metadata.

    Response shape:
      {
        "collection": "maintenance_manuals",
        "total_documents": 3,
        "documents": [
          {
            "filename":    "20070034949.pdf",
            "title":       "20070034949",
            "chunk_count": 348,
            "pages":       [1, 2, 3, ...],
            "embed_type":  "pdf_cohere"
          },
          ...
        ]
      }
    """
    try:
        if machine_id:
            from db.chroma_client import get_chroma_collection
            from services.embedder import PdfEmbedder as _PE
            embedder = _PE(get_chroma_collection(f"pdf_{machine_id}"))
        else:
            embedder = get_pdf_embedder()

        total = embedder.collection.count()
        if total == 0:
            return {
                "collection":      embedder.collection.name,
                "total_documents": 0,
                "documents":       [],
            }

        # Fetch only metadata — no document text needed
        raw  = embedder.collection.get(include=["metadatas"])
        docs: dict[str, dict] = {}

        for meta in raw.get("metadatas", []):
            source     = meta.get("source", "")
            page       = meta.get("page", 0)
            embed_type = meta.get("embed_type", "")
            if not source:
                continue
            if source not in docs:
                docs[source] = {
                    "filename":    source,
                    "title":       source.replace(".pdf", "").replace("_", " "),
                    "chunk_count": 0,
                    "pages":       set(),
                    "embed_type":  embed_type,
                }
            docs[source]["chunk_count"] += 1
            docs[source]["pages"].add(page)

        # Serialize sets to sorted lists
        result = []
        for d in docs.values():
            result.append({
                "filename":    d["filename"],
                "title":       d["title"],
                "chunk_count": d["chunk_count"],
                "page_count":  len(d["pages"]),
                "embed_type":  d["embed_type"],
            })

        # Sort by filename
        result.sort(key=lambda x: x["filename"])

        return {
            "collection":      embedder.collection.name,
            "total_documents": len(result),
            "documents":       result,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    
    
@router.get("/collections")
async def get_collections():
    """Return all ChromaDB collection names (both PDF and sensor)."""
    try:
        return {"collections": list_collections()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/pdf/{filename}", response_model=DeleteChunksResponse)
async def delete_pdf(
    filename:    str,
    machine_id:  str | None = Query(None),
    sensor_only: bool       = Query(False),
):
    """Remove a file from disk and delete all its chunks from the relevant collection."""
    save_dir  = os.path.join(KNOWLEDGE_DIR, machine_id) if machine_id else KNOWLEDGE_DIR
    file_path = os.path.join(save_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    try:
        if machine_id and sensor_only:
            embedder = get_sensor_embedder(machine_id)
        elif machine_id:
            from db.chroma_client import get_chroma_collection
            from services.embedder import PdfEmbedder as _PE
            embedder = _PE(get_chroma_collection(f"pdf_{machine_id}"))
        else:
            embedder = get_pdf_embedder()

        deleted = embedder.delete_by_source(filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return DeleteChunksResponse(deleted=deleted, collection=embedder.collection.name)


@router.delete("/chunks", response_model=DeleteChunksResponse)
async def delete_chunks(body: DeleteChunksRequest):
    """Delete chunks by filter or IDs from the specified collection."""
    if not body.where and not body.ids:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of: 'where' or 'ids'.",
        )
    try:
        embedder = get_embedder(body.machine_id)
        deleted  = embedder.delete_chunks(where=body.where, ids=body.ids)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return DeleteChunksResponse(deleted=deleted, collection=embedder.collection.name)


@router.post("/reset", response_model=ResetResponse)
async def reset_collection(body: ResetRequest):
    """Wipe ALL chunks in a collection (keeps the collection itself)."""
    try:
        embedder = get_embedder(body.machine_id)
        deleted  = embedder.reset()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return ResetResponse(deleted=deleted, collection=embedder.collection.name)


@router.post("/switch-model")
async def switch_model(model_key: str):
    """Tell master-llm-service to switch its active model."""
    llm = LLMClient()
    try:
        return await llm.switch_model(model_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── SSE notification stream ────────────────────────────────────────────────────

import json as _json
import asyncio as _asyncio
from fastapi.responses import StreamingResponse
from services.notification_bus import subscribe as _subscribe, ensure_queue as _ensure_queue


@router.get("/notifications/stream/{machine_id}")
async def notification_stream(machine_id: str):
    """
    Server-Sent Events stream for diagnosis notifications.
    Subscribe BEFORE calling /diagnose.
    """
    async def _event_generator():
        async with _subscribe(machine_id) as queue:
            while True:
                try:
                    payload = await _asyncio.wait_for(queue.get(), timeout=20.0)
                    yield f"data: {_json.dumps(payload, ensure_ascii=False)}\n\n"
                except _asyncio.TimeoutError:
                    yield ": heartbeat\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type = "text/event-stream",
        headers    = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/notifications/stream/{machine_id}/info")
async def notification_stream_info(machine_id: str):
    from services.notification_bus import _subscribers
    return {"machine_id": machine_id, "active_subscribers": len(_subscribers.get(machine_id, []))}


@router.get("/notifications/{machine_id}")
async def get_notifications(machine_id: str, limit: int = 10):
    """Pull buffered diagnosis notifications from RabbitMQ (without SSE)."""
    import aio_pika
    from services.notification_bus import _queue_name, ensure_queue

    await ensure_queue(machine_id)
    messages   = []
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel = await connection.channel()
        queue   = await channel.declare_queue(
            _queue_name(machine_id),
            durable=True, auto_delete=False, exclusive=False,
        )
        for _ in range(limit):
            msg = await queue.get(fail=False)
            if msg is None:
                break
            async with msg.process():
                try:
                    messages.append(_json.loads(msg.body.decode()))
                except Exception:
                    pass
    finally:
        await connection.close()

    return {"machine_id": machine_id, "count": len(messages), "messages": messages}
