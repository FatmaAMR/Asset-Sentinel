from __future__ import annotations

# ── path setup MUST be first ──────────────────────────────────────────────────
import sys
from pathlib import Path
service_root = Path(__file__).resolve().parent.parent  # notification-service2/
sys.path.insert(0, str(service_root))
sys.path.insert(1, str(service_root.parent))

import asyncio   # all other imports below, unchanged
import json
import sys
from pathlib import Path

# Add local service root so notification-service2/schemas wins over src/schemas
service_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(service_root))

from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import StreamingResponse

from schemas.models import AlertMessage
from services.NotificationDispatcher import NotificationDispatcher
from services.notification_rag_consumer import (
    get_notifications,
    get_stream_info,
    start_consumer,
)

router     = APIRouter()
dispatcher = NotificationDispatcher()


# ── Existing endpoint ─────────────────────────────────────────────────────────

@router.post("/trigger-alert")
async def manual_alert(alert: AlertMessage, background_tasks: BackgroundTasks):
    """Receive an alert (from RabbitMQ consumer or manual POST) and dispatch it."""
    background_tasks.add_task(dispatcher.process_alert, alert)
    return {"status": "Alert processing started"}


# ── RAG Notification polling ──────────────────────────────────────────────────

@router.get("/rag/notifications/{machine_id}")
async def get_machine_notifications(
    machine_id: str,
    limit: int = Query(default=50, ge=1, le=200, description="Max notifications to return"),
):
    """
    Poll the latest diagnosis notifications for a machine.

    The notification-service consumes from the RabbitMQ `consulting.diagnosis`
    exchange and buffers the last 200 events per machine in memory.

    Returns newest-first. Starts the background consumer for this machine_id
    automatically if it is not already running.
    """
    await start_consumer(machine_id)   # idempotent — no-op if already running
    notifications = get_notifications(machine_id, limit=limit)
    return {
        "machine_id":    machine_id,
        "count":         len(notifications),
        "notifications": notifications,
    }


# ── SSE stream ────────────────────────────────────────────────────────────────

@router.get("/rag/notifications/stream/{machine_id}")
async def notification_stream(machine_id: str):
    """
    Server-Sent Events stream — pushes a diagnosis event to the client the
    moment it arrives from RabbitMQ.

    Connect with:
        const src = new EventSource('/rag/notifications/stream/MACHINE_ID');
        src.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    await start_consumer(machine_id)

    # Each SSE connection gets its own asyncio.Queue fed by a watcher task
    # that watches the in-memory store for new entries.
    live_queue: asyncio.Queue = asyncio.Queue(maxsize=64)
    snapshot_size = [len(get_notifications(machine_id, limit=200))]  # baseline

    async def _watcher():
        """Poll the in-memory store every 0.5 s and forward new entries."""
        while True:
            await asyncio.sleep(0.5)
            current = get_notifications(machine_id, limit=200)
            if len(current) > snapshot_size[0]:
                new_items = current[:len(current) - snapshot_size[0]]
                for item in reversed(new_items):   # oldest-first
                    await live_queue.put(item)
                snapshot_size[0] = len(current)

    watcher_task = asyncio.create_task(_watcher())

    async def _event_generator():
        try:
            # Send a heartbeat immediately so the client knows we're alive
            yield "data: {\"type\": \"connected\"}\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(live_queue.get(), timeout=30)
                    yield f"data: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"   # keep-alive comment
        except asyncio.CancelledError:
            pass
        finally:
            watcher_task.cancel()

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",   # disable nginx buffering
            "Access-Control-Allow-Origin": "*",
        },
    )


# ── Stream info ───────────────────────────────────────────────────────────────

@router.get("/rag/notifications/stream/{machine_id}/info")
async def notification_stream_info(machine_id: str):
    """
    Return buffer statistics for the machine's notification stream.

    Response fields:
      buffered      – notifications currently in the in-memory buffer
      total_seen    – all notifications received since process start
      last_event_at – unix timestamp of the most recent notification (null if none)
      buffer_cap    – maximum buffer size (200)
    """
    await start_consumer(machine_id)   # ensure consumer is running
    return {
        "machine_id": machine_id,
        **get_stream_info(machine_id),
    }