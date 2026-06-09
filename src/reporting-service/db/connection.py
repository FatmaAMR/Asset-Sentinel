from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import CollectionInvalid
from pymongo.uri_parser import parse_uri
import os
import certifi
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

MONGO_URL       = os.getenv("DB_URL")
DATABASE_NAME   = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("DB_COLLECTION", "equipment_status")

_client: MongoClient | None = None
_collection: Collection | None = None


def _get_database_name() -> str:
    if DATABASE_NAME:
        return DATABASE_NAME

    if not MONGO_URL:
        raise ValueError("DB_URL is required to determine the MongoDB database name.")

    parsed = parse_uri(MONGO_URL)
    database = parsed.get("database")
    if database:
        return database

    return "Sentinel"


def _ensure_time_series_collection(client: MongoClient, db_name: str, collection_name: str) -> Collection:
    db = client[db_name]
    if collection_name in db.list_collection_names():
        return db[collection_name]

    try:
        return db.create_collection(
            collection_name,
            timeseries={
                "timeField": "timestamp",
                "metaField": "machine_id",
                "granularity": "seconds",
            },
        )
    except CollectionInvalid:
        return db[collection_name]


def get_client() -> MongoClient:
    global _client
    if _client is None:
        if not MONGO_URL:
            raise ValueError("DB_URL is not configured in the environment.")
        _client = MongoClient(MONGO_URL, tlsCAFile=certifi.where())
    return _client


def get_collection() -> Collection:
    global _collection
    if _collection is None:
        client = get_client()
        db_name = _get_database_name()
        _collection = _ensure_time_series_collection(client, db_name, COLLECTION_NAME)
    return _collection


def get_mock_influx_data() -> list:
    """
    Fetch documents from MongoDB and map them to the flat format
    that analytics.py expects:
      { machine_id, timestamp, temperature, vibration, rul_days }
    """
    try:
        collection = get_collection()
        documents  = list(collection.find({}, {"_id": 0}))

        mapped = []
        for doc in documents:
            machine_id = doc.get("machine_id")
            rul        = doc.get("rul", 0)
            timestamp  = doc.get("timestamp")

            # Convert datetime to isoformat string if needed
            if hasattr(timestamp, "isoformat"):
                timestamp = timestamp.isoformat()
            else:
                timestamp = str(timestamp)

            # Pull sensor readings from raw.window_sliding last entry
            temperature = 0.0
            vibration   = 0.0
            raw = doc.get("raw", {})
            window = raw.get("window_sliding", [])
            if window:
                last = window[-1]
                temperature = float(last.get("temperature", 0.0))
                vibration   = float(last.get("vibration",   0.0))

            mapped.append({
                "machine_id":  machine_id,
                "timestamp":   timestamp,
                "temperature": temperature,
                "vibration":   vibration,
                "rul_days":    int(rul),
            })

        return mapped

    except Exception as e:
        print(f"[MongoDB] Failed to fetch data: {e}")
        return []