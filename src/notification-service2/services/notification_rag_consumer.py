"""
services/notification_rag_consumer.py
──────────────────────────────────────
Bridges the RabbitMQ `consulting.diagnosis` exchange into an in-process
store so the REST polling endpoints can serve notifications without
holding open a long-lived HTTP connection to the consulting service.

Architecture
────────────
  RabbitMQ (consulting.diagnosis exchange)
      └─► notification-service durable queue  "notif.diagnosis.<machine_id>"
              └─► in-memory ring buffer  _store[machine_id]  (last 200 events)
                      └─► GET /rag/notifications/{machine_id}   (polling)
                          GET /rag/notifications/stream/{machine_id}  (SSE)
                          GET /rag/notifications/stream/{machine_id}/info

How to use
──────────
1.  Call `await start_consumer(machine_id)` once per machine you care about
    (e.g. at startup or when a machine first appears).
2.  The background task keeps consuming until the process exits.
3.  The REST endpoints call `get_notifications(machine_id)` to read the store.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from typing import Any

import aio_pika
import aio_pika.abc

from config.settings import settings   # adjust import to match your settings path

logger = logging.getLogger("notification_rag_consumer")

# ── Constants ─────────────────────────────────────────────────────────────────

EXCHANGE_NAME  = "consulting.diagnosis"
EXCHANGE_TYPE  = aio_pika.ExchangeType.TOPIC
BUFFER_SIZE    = 200          # max notifications kept per machine in memory
_CONSUMERS: dict[str, asyncio.Task] = {}   # machine_id → running Task


# ── In-memory store ───────────────────────────────────────────────────────────

class _MachineStore:
    """Ring-buffer + metadata for one machine."""

    def __init__(self) -> None:
        self.buffer:       deque[dict] = deque(maxlen=BUFFER_SIZE)
        self.total_seen:   int         = 0
        self.last_event_at: float | None = None

    def push(self, payload: dict) -> None:
        payload.setdefault("received_at", time.time())
        self.buffer.appendleft(payload)   # newest first
        self.total_seen   += 1
        self.last_event_at = payload["received_at"]

    def latest(self, limit: int = 50) -> list[dict]:
        return list(self.buffer)[:limit]

    def info(self) -> dict:
        return {
            "buffered":      len(self.buffer),
            "total_seen":    self.total_seen,
            "last_event_at": self.last_event_at,
            "buffer_cap":    BUFFER_SIZE,
        }


_store: dict[str, _MachineStore] = {}


def _get_store(machine_id: str) -> _MachineStore:
    if machine_id not in _store:
        _store[machine_id] = _MachineStore()
    return _store[machine_id]


# ── Public read API (used by REST endpoints) ──────────────────────────────────

def get_notifications(machine_id: str, limit: int = 50) -> list[dict]:
    """Return the latest `limit` notifications for a machine (newest first)."""
    return _get_store(machine_id).latest(limit)


def get_stream_info(machine_id: str) -> dict:
    """Return buffer statistics for a machine."""
    return _get_store(machine_id).info()


# ── Background consumer ───────────────────────────────────────────────────────

def _queue_name(machine_id: str) -> str:
    return f"notif.diagnosis.{machine_id}"


async def _consume(machine_id: str) -> None:
    """
    Long-running coroutine: connects to RabbitMQ, declares a durable queue
    bound to `diagnosis.<machine_id>`, and feeds messages into _store.
    """
    store = _get_store(machine_id)
    routing_key = f"diagnosis.{machine_id}"

    logger.info("[%s] Starting RabbitMQ consumer (queue=%s)", machine_id, _queue_name(machine_id))

    while True:   # reconnect loop
        try:
            conn = await aio_pika.connect_robust(settings.rabbitmq_url)
            async with conn:
                channel  = await conn.channel()
                await channel.set_qos(prefetch_count=20)

                exchange = await channel.declare_exchange(
                    EXCHANGE_NAME, EXCHANGE_TYPE, durable=True
                )
                queue = await channel.declare_queue(
                    _queue_name(machine_id),
                    durable     = True,
                    auto_delete = False,
                    exclusive   = False,
                )
                await queue.bind(exchange, routing_key=routing_key)
                logger.info("[%s] Queue ready, consuming…", machine_id)

                async with queue.iterator() as it:
                    async for message in it:
                        async with message.process():
                            try:
                                payload = json.loads(message.body.decode())
                                store.push(payload)
                                logger.debug(
                                    "[%s] Stored notification (total=%d)",
                                    machine_id, store.total_seen,
                                )
                            except Exception as exc:
                                logger.exception("[%s] Decode error: %s", machine_id, exc)

        except asyncio.CancelledError:
            logger.info("[%s] Consumer cancelled.", machine_id)
            return
        except Exception as exc:
            logger.warning("[%s] Consumer error, retrying in 5 s: %s", machine_id, exc)
            await asyncio.sleep(5)


async def start_consumer(machine_id: str) -> None:
    """
    Start a background consumer for machine_id (idempotent — safe to call
    multiple times for the same machine).
    """
    if machine_id in _CONSUMERS and not _CONSUMERS[machine_id].done():
        return   # already running
    task = asyncio.create_task(_consume(machine_id), name=f"consumer-{machine_id}")
    _CONSUMERS[machine_id] = task
    logger.info("[%s] Consumer task started.", machine_id)


async def stop_all_consumers() -> None:
    """Call from FastAPI lifespan shutdown."""
    for machine_id, task in _CONSUMERS.items():
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    _CONSUMERS.clear()
    logger.info("All notification consumers stopped.")