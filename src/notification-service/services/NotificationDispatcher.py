# import httpx
# import logging
# import json
# from schemas.models import AlertMessage
# from utils.helpers import format_notification_body

# logger = logging.getLogger(__name__)

# class NotificationDispatcher:
#     def __init__(self):
#         # Use settings for URLs
#         from config import settings
#         self.consulting_url = settings.CONSULTING_SERVICE_URL
#         self.managerial_url = settings.MANAGERIAL_SERVICE_URL

#     async def process_alert(self, alert: AlertMessage):
#         suggestion = await self._get_proactive_suggestion(alert.failure_type, alert.machine_id)
#         recipients = await self._get_notified_staff(alert.machine_id, alert.alert_level)
        
#         for person in recipients:
#             # Generate JSON body for Frontend
#             json_body = format_notification_body(alert.machine_id, alert.predicted_rul, suggestion)
#             await self._send_notification(person, alert, json_body)

#     async def _send_notification(self, person: dict, alert: AlertMessage, json_body: dict):
#         # This JSON is what the Frontend or Socket service will consume
#         notification_package = {
#             "recipient": person['email'],
#             "channel": person['channel'],
#             "alert_data": alert.dict(),
#             "display_content": json_body
#         }
        
#         logger.info(f"Notification prepared for {person['email']}: {json.dumps(notification_package)}")
#         # Integration point for actual SMTP or WebSocket push
#         return notification_package

#     async def _get_proactive_suggestion(self, failure_type: str, machine_id: str) -> str:
#         try:
#             async with httpx.AsyncClient() as client:
#                 response = await client.get(f"{self.consulting_url}/{failure_type}")
#                 return response.json().get("suggestion", "Check machine immediately.")
#         except Exception as e:
#             logger.error(f"Consulting Service unavailable: {e}")
#             return "No specific suggestion available."

#     async def _get_notified_staff(self, machine_id: str, alert_level: str) -> list:
#         try:
#             async with httpx.AsyncClient() as client:
#                 response = await client.get(f"{self.managerial_url}/{machine_id}/staff?level={alert_level}")
#                 return response.json().get("staff", [])
#         except Exception as e:
#             logger.error(f"Managerial Service unavailable: {e}")
#             return []

#     async def _send_notification(self, person: dict, alert: AlertMessage, suggestion: str):
#         # Logic to trigger email, SMS, or Dashboard update
#         logger.info(f"Notification sent to {person['email']} via {person['channel']}")
#         print(f"--- ALERT: {alert.alert_level} ---")
#         print(f"To: {person['name']} | Machine: {alert.machine_id}")
#         print(f"Suggestion: {suggestion}")


import httpx
import logging
import json
from schemas.models import AlertMessage
from utils.helpers import format_notification_body
from config import settings

logger = logging.getLogger(__name__)

class NotificationDispatcher:
    def __init__(self):
        self.consulting_endpoint = settings.consulting_api_url
        self.managerial_endpoint = settings.managerial_api_url
        print(f"\n[System] Dispatcher Online.")
        print(f" > Consulting Source: {self.consulting_endpoint}")
        print(f" > Managerial Source: {self.managerial_endpoint}\n")

    async def process_alert(self, alert: AlertMessage):
        print("="*60)
        print(f" [NEW ALERT RECEIVED]")
        print(f" ID: {alert.message_id} | Machine: {alert.machine_id}")
        print("-"*60)

        # 1. Consulting Service Step
        print(f"[Step 1] Requesting Expert Suggestion for: {alert.failure_type}")
        suggestion = await self._fetch_suggestion(alert.failure_type)
        print(f" > API Response (Suggestion): {suggestion}")

        # 2. Managerial Service Step
        print(f"[Step 2] Requesting Staff List for Machine: {alert.machine_id}")
        recipients = await self._fetch_system_users()
        print(f" > API Response (Staff): {json.dumps(recipients, indent=2)}")

        # 3. Final Formatting & Suggestions
        print(f"[Step 3] Constructing Final JSON Payload...")
        
        for person in recipients:
            # Generate the base notification
            json_payload = format_notification_body(
                alert.machine_id, 
                alert.predicted_rul, 
                suggestion
            )
            
            # Adding Interactive Quick Responses for the Frontend
            quick_responses = [
                "Acknowledge & Start Maintenance",
                "Request Backup Team",
                "Mute Alert for 1 Hour"
            ]

            notification_package = {
                "target_user": person['name'],
                "target_email": person['email'],
                "notification_display": json_payload,
                "interactive_options": quick_responses,
                "meta_data": {
                    "raw_alert": alert.dict(),
                    "source_service": "Notification-Service-V1"
                }
            }

            # Printing the full final structure to see the results
            print(f"\n[Final Output for {person['name']}]:")
            print(json.dumps(notification_package, indent=2))
        
        print("-"*60)
        print(f" [COMPLETED] All notifications dispatched for {alert.message_id}")
        print("="*60 + "\n")

    async def _fetch_suggestion(self, failure_type: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.consulting_endpoint}/{failure_type}"
                response = await client.get(url, timeout=5.0)
                return response.json().get("suggestion", "Check machine immediately.")
        except Exception as e:
            logger.error(f"Consulting API Error: {e}")
            return "Standard inspection required (Service Offline)."

    async def _fetch_system_users(self) -> list:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.managerial_endpoint, timeout=5.0)
                return response.json().get("users", [])
        except Exception as e:
            logger.error(f"Managerial API Error: {e}")
            return []

    async def _dispatch_output(self, person: dict, alert: AlertMessage, json_body: dict):
        # This method is now integrated into the loop above for visual clarity
        pass