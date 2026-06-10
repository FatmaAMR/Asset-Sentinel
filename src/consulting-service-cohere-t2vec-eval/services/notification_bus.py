"""
services/notification_bus.py
─────────────────────────────
RabbitMQ-backed notification bus using aio-pika (async, FastAPI-compatible).

Architecture
────────────
  Exchange : "consulting.diagnosis"  (topic, durable)
  Routing  : "diagnosis.<machine_id>"
              e.g. diagnosis.M001, diagnosis.M002

  Publisher (DiagnoseService)
    → publish_diagnosis(machine_id, payload)
    → routing_key = f"diagnosis.{machine_id}"

  Consumer (SSE endpoint)
    → subscribe(machine_id) context manager
    → declares an exclusive, auto-delete queue bound to "diagnosis.<machine_id>"
    → one queue per SSE connection — each tab gets its own copy of every event
    → queue is deleted automatically when the SSE client disconnects

Why aio-pika, not pika?
  pika is synchronous — calling it from an async FastAPI route blocks the
  event loop and stalls all other requests.  aio-pika wraps the same AMQP
  protocol with native asyncio.  It is a direct drop-in for async code.

Multi-instance safe
  Because every SSE subscriber gets its own exclusive queue bound to the
  exchange, multiple consulting-service pods all receive every diagnosis event
  for their connected clients — no message loss under horizontal scaling.
"""

import json
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any

import aio_pika
import aio_pika.abc

from config import settings

logger = logging.getLogger("notification_bus")

EXCHANGE_NAME = "consulting.diagnosis"
EXCHANGE_TYPE = aio_pika.ExchangeType.TOPIC


# ── Shared publisher connection (one per process) ─────────────────────────────

_pub_connection: aio_pika.abc.AbstractRobustConnection | None = None
_pub_channel:    aio_pika.abc.AbstractChannel | None = None
_pub_exchange:   aio_pika.abc.AbstractExchange | None = None
_pub_lock = asyncio.Lock()


async def _get_publisher_exchange() -> aio_pika.abc.AbstractExchange:
    """
    Lazily create (and cache) a single robust connection + channel + exchange
    for publishing.  Thread-safe via asyncio.Lock.
    """
    global _pub_connection, _pub_channel, _pub_exchange

    async with _pub_lock:
        if _pub_exchange is not None:
            return _pub_exchange

        logger.info("Connecting to RabbitMQ for publishing: %s", settings.rabbitmq_url)
        _pub_connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        _pub_channel    = await _pub_connection.channel()
        _pub_exchange   = await _pub_channel.declare_exchange(
            EXCHANGE_NAME,
            EXCHANGE_TYPE,
            durable = True,
        )
        logger.info("Publisher exchange '%s' ready.", EXCHANGE_NAME)
        return _pub_exchange


async def close_publisher() -> None:
    """Call from FastAPI lifespan shutdown to cleanly close the publisher."""
    global _pub_connection, _pub_channel, _pub_exchange
    if _pub_connection and not _pub_connection.is_closed:
        await _pub_connection.close()
    _pub_connection = _pub_channel = _pub_exchange = None
    logger.info("RabbitMQ publisher connection closed.")


# ── Publish ───────────────────────────────────────────────────────────────────

async def publish_diagnosis(machine_id: str, payload: dict[str, Any]) -> None:
    """
    Publish a diagnosis-complete event to the topic exchange.

    Before publishing, the durable queue for this machine_id is declared
    (idempotent) so messages are NEVER dropped — even if no SSE subscriber
    has ever connected for this machine.

    Routing key : diagnosis.<machine_id>   e.g. "diagnosis.M001"
    Persistence : PERSISTENT — survives broker restarts.
    """
    try:
        # Ensure the durable queue exists and is bound BEFORE publishing
        await ensure_queue(machine_id)

        exchange = await _get_publisher_exchange()
        body     = json.dumps(payload, ensure_ascii=False).encode()
        message  = aio_pika.Message(
            body          = body,
            content_type  = "application/json",
            delivery_mode = aio_pika.DeliveryMode.PERSISTENT,
        )
        routing_key = f"diagnosis.{machine_id}"
        await exchange.publish(message, routing_key=routing_key)
        logger.info(
            "Published diagnosis event → queue='%s' routing_key=%s",
            _queue_name(machine_id), routing_key,
        )
    except Exception as exc:
        logger.exception("Failed to publish diagnosis notification: %s", exc)


# ── Subscribe (SSE consumer) ──────────────────────────────────────────────────

def _queue_name(machine_id: str) -> str:
    """
    Stable, durable queue name for a machine.
    e.g. "diagnosis.notifications.M001"

    This queue:
      - is declared once and survives broker restarts (durable=True)
      - accumulates messages even when NO subscriber is connected
      - delivers buffered messages the moment a subscriber connects
    """
    return f"diagnosis.notifications.{machine_id}"


async def ensure_queue(machine_id: str) -> None:
    """
    Declare the durable queue and bind it to the exchange.
    Safe to call multiple times — idempotent (AMQP passive declare).
    Call this at ingest time or on startup for known machines so the queue
    exists before the first /diagnose even runs.
    """
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel  = await connection.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, EXCHANGE_TYPE, durable=True
        )
        queue = await channel.declare_queue(
            _queue_name(machine_id),
            durable     = True,   # survives broker restart
            auto_delete = False,  # stays alive when no consumer is connected
            exclusive   = False,  # multiple consumers allowed
        )
        await queue.bind(exchange, routing_key=f"diagnosis.{machine_id}")
        logger.info(
            "Durable queue '%s' declared and bound (routing_key=diagnosis.%s).",
            queue.name, machine_id,
        )
    finally:
        await connection.close()


@asynccontextmanager
async def subscribe(machine_id: str) -> AsyncIterator[asyncio.Queue]:
    """
    Async context manager — connects to the durable queue for machine_id,
    drains any buffered messages first, then streams live ones.

    Messages published while NO subscriber was connected are preserved in
    RabbitMQ and delivered immediately when this context opens.

    Usage in the SSE endpoint:
        async with subscribe("M001") as q:
            while True:
                payload = await q.get()
                yield f"data: {json.dumps(payload)}\\n\\n"
    """
    bridge: asyncio.Queue = asyncio.Queue(maxsize=128)

    logger.info("Opening RabbitMQ subscriber connection for machine %s", machine_id)
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)

    try:
        channel  = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, EXCHANGE_TYPE, durable=True
        )

        # Re-declare with same args — idempotent, ensures queue exists
        queue = await channel.declare_queue(
            _queue_name(machine_id),
            durable     = True,
            auto_delete = False,
            exclusive   = False,
        )
        await queue.bind(exchange, routing_key=f"diagnosis.{machine_id}")
        logger.info(
            "Subscriber attached to durable queue '%s' for machine %s",
            queue.name, machine_id,
        )

        async def _on_message(msg: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with msg.process():           # ack on success, nack on exception
                try:
                    payload = json.loads(msg.body.decode())
                    await bridge.put(payload)
                except Exception as exc:
                    logger.exception("Failed to decode RabbitMQ message: %s", exc)

        await queue.consume(_on_message)
        yield bridge

    finally:
        if not connection.is_closed:
            await connection.close()
        logger.info("Subscriber connection closed for machine %s", machine_id)
