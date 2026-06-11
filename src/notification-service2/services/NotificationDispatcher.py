from __future__ import annotations

import httpx
import logging
import json
from typing import Any, Dict

try:
    import websockets
except ImportError:  # pragma: no cover
    websockets = None

from schemas.models import AlertMessage, DiagnoseRequest, DiagnoseResponse
from utils.helpers import format_notification_body
from config import settings

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    def __init__(self):
        self.diagnose_endpoint  = settings.consulting_diagnose_url
        self.managerial_endpoint = settings.managerial_api_url
        self.websocket_url = settings.WEBSOCKET_URL
        print(f"\n[System] Dispatcher Online.")
        print(f" > Consulting /diagnose : {self.diagnose_endpoint}")
        print(f" > Managerial Source   : {self.managerial_endpoint}")
        print(f" > WebSocket Target    : {self.websocket_url}\n")
        if websockets is None:
            logger.warning("websockets package not installed; WebSocket notifications are disabled.")

    # ── Main entry-point ──────────────────────────────────────────────────────

    async def process_alert(self, alert: AlertMessage) -> None:
        print("=" * 60)
        print(f" [NEW ALERT RECEIVED]")
        print(f" ID: {alert.message_id} | Machine: {alert.machine_id}")
        print("-" * 60)

        # Step 1 — call consulting /diagnose
        print(f"[Step 1] Sending DiagnoseRequest to consulting service …")
        diagnosis = await self._call_consulting_diagnose(alert)
        print(f" > Diagnosis response: {diagnosis}")

        # Step 2 — fetch staff list
        print(f"[Step 2] Fetching staff list …")
        print(f"Recipients count = {len(recipients)}")
        recipients = await self._fetch_system_users()
        print(f" > Staff: {json.dumps(recipients, indent=2)}")

        # Step 3 — build & log notification packages
        print(f"[Step 3] Building notification payloads …")
        suggestion = (
            diagnosis.get("suggestion")
            or diagnosis.get("answer")
            or "Standard inspection required."
        )
        if not recipients:
              await self._push_websocket_notification({
             "message": "Test notification",
            "machine_id": alert.machine_id,
             "rul": alert.mean_rul
       })

        for person in recipients:
            json_payload = format_notification_body(
                alert.machine_id,
                alert.mean_rul,
                suggestion,
            )

            notification_package = {
                "target_user":  person.get("name"),
                "target_email": person.get("email"),
                "notification_display": json_payload,
                "interactive_options": [
                    "Acknowledge & Start Maintenance",
                    "Request Backup Team",
                    "Mute Alert for 1 Hour",
                ],
                "meta_data": {
                    "raw_alert":      alert.dict(),
                    "source_service": "Notification-Service-V1",
                },
            }

            await self._push_websocket_notification(notification_package)

            print(f"\n[Final Output for {person.get('name')}]:")
            print(json.dumps(notification_package, indent=2, default=str))

        print("-" * 60)
        print(f" [COMPLETED] All notifications dispatched for {alert.message_id}")
        print("=" * 60 + "\n")

    # ── Consulting /diagnose ──────────────────────────────────────────────────

    async def _call_consulting_diagnose(self, alert: AlertMessage) -> Dict[str, Any]:
        """
        Map equipment.alerts payload → DiagnoseRequest and POST to /diagnose.

        Field mapping
        -------------
        machine_id     ← alert.machine_id
        label          ← alert.failure_type
        rul            ← alert.mean_rul
        window_sliding ← alert.raw
        message_id     ← alert.metadata.message_id
        timestamp      ← alert.metadata.timestamp
        top_k          ← 1  (as specified)
        """
        request_body = DiagnoseRequest(
            machine_id     = alert.machine_id,
            label          = alert.failure_type,
            rul            = alert.mean_rul,
            window_sliding = alert.raw,
            message_id     = alert.metadata.message_id,
            timestamp      = alert.metadata.timestamp,
            top_k          = 1,
        )

        logger.info(
            "[%s] POST %s  body=%s",
            alert.message_id,
            self.diagnose_endpoint,
            request_body.json(),
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.diagnose_endpoint,
                    json=request_body.dict(),
                    timeout=15.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Consulting /diagnose returned %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            return {"suggestion": "Consulting service returned an error — manual inspection required."}
        except Exception as exc:
            logger.error("Consulting /diagnose unreachable: %s", exc)
            return {"suggestion": "Consulting service offline — standard inspection required."}

    # ── Managerial staff list ─────────────────────────────────────────────────

    async def _fetch_system_users(self) -> list:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.managerial_endpoint, timeout=5.0)
                response.raise_for_status()
                return response.json().get("users", [])
        except Exception as exc:
            logger.error("Managerial API error: %s", exc)
            return []

    async def _push_websocket_notification(self, payload: Dict[str, Any]) -> None:
        print("FUNCTION ENTERED")
        if websockets is None:
            print("[⚠️] WebSocket push skipped: websockets package not installed.")
            logger.warning("WebSocket push skipped because websockets package is not installed.")
            return

        if not self.websocket_url:
            print("[⚠️] WebSocket push skipped: WEBSOCKET_URL not configured.")
            logger.warning("WebSocket push skipped because WEBSOCKET_URL is not configured.")
            return

        try:
            print(f"[📤] Sending WebSocket notification to {self.websocket_url}...")
            async with websockets.connect(self.websocket_url, ping_interval=20, ping_timeout=10) as ws:
                await ws.send(json.dumps(payload))
                print(f"[✅] WebSocket notification sent successfully!")
                logger.info(f"WebSocket notification sent to {self.websocket_url}")
        except Exception as exc:
            print(f"[❌] WebSocket send failed: {type(exc).__name__}: {exc}")
            logger.error(f"Failed to send WebSocket notification: {exc}")
