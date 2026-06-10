from fastapi import APIRouter, BackgroundTasks
from schemas.models import AlertMessage
from services.NotificationDispatcher import NotificationDispatcher

router = APIRouter()
dispatcher = NotificationDispatcher()

@router.post("/trigger-alert")
async def manual_alert(alert: AlertMessage, background_tasks: BackgroundTasks):
    # We use background tasks to not block the API
    background_tasks.add_task(dispatcher.process_alert, alert)
    return {"status": "Alert processing started"}