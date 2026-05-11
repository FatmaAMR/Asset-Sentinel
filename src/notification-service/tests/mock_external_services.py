import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Asset-Sentinel Mock Services")

@app.get("/suggestion/{failure_type}")
async def get_suggestion(failure_type: str):
    """
    Temporary endpoint simulating the Consulting Service.
    Returns a fixed suggestion based on the failure type.
    """
    return {
        "failure_type": failure_type,
        "suggestion": f"Standard procedure for {failure_type.replace('_', ' ')}: Inspect components and recalibrate sensors."
    }

@app.get("/staff/all")
async def get_all_users():
    """
    Temporary endpoint simulating the Managerial Service.
    Returns all registered system users to receive the broadcast.
    """
    return {
        "users": [
            {"name": "Admin User", "email": "admin@sentinel.ai", "channel": "Dashboard"},
            {"name": "Senior Engineer", "email": "eng.fatma@sentinel.ai", "channel": "Dashboard"},
            {"name": "Maintenance Lead", "email": "lead@sentinel.ai", "channel": "Dashboard"}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)