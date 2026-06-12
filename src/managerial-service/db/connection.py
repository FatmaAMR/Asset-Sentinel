import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

MONGO_URL = os.getenv("DB_URL")
if not MONGO_URL:
    raise ValueError("DB_URL not found in .env")

client = AsyncIOMotorClient(MONGO_URL)
db = client["Asset-Sentinel"]

def get_collection(name: str):
    return db[name]