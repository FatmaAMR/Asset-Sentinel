from pymongo import MongoClient
from pymongo.collection import Collection
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")

MONGO_URL       = os.getenv("DB_URL")
DATABASE_NAME   = os.getenv("DB_NAME", "Sentinel")
COLLECTION_NAME = os.getenv("DB_COLLECTION", "cmapss_sensor_data")

# Single client instance reused across the app
_client: MongoClient = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URL)
    return _client


def get_collection() -> Collection:
    return get_client()[DATABASE_NAME][COLLECTION_NAME]