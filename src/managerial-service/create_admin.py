import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import uuid
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

MONGO_URL = os.getenv("DB_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["Asset-Sentinel"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    col = db["staff"]
    
    email = "mai@sentinel.com"
    
    if await col.find_one({"email": email}):
        print(f"Admin {email} already exists.")
        return

    doc = {
        "staff_id":   f"EMP-{uuid.uuid4().hex[:4].upper()}",
        "full_name":  "Mai",
        "role":       "Admin",
        "email":      email,
        "password":   pwd_context.hash("123456"),
        "created_at": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    await col.insert_one(doc)
    doc.pop("_id", None)
    print(f"Admin created: {doc}")

asyncio.run(create_admin())