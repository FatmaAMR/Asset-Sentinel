from datetime import datetime

def format_notification_body(machine_id: str, rul: float, suggestion: str) -> dict:
    return {
        "title": "Machine Health Alert",
        "machine_id": machine_id,
        "estimated_rul": round(rul, 2),
        "action_required": suggestion,
        "urgency": "High",
        "timestamp": datetime.utcnow().isoformat()
    }