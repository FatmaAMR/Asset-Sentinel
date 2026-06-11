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


# Map pipeline alert_level/label → frontend status strings
_STATUS_MAP = {
    "HEALTHY":  "Normal",
    "NORMAL":   "Normal",
    "WARNING":  "Warning",
    "CRITICAL": "Critical",
    "SCHEDULED": "Scheduled",
}

def _safe_float(val, fallback=0.0) -> float:
    """Handle MongoDB $numberDouble special objects and plain floats."""
    if isinstance(val, dict):
        v = val.get("$numberDouble", fallback)
        try:
            return float(v)
        except (TypeError, ValueError):
            return fallback
    try:
        return float(val)
    except (TypeError, ValueError):
        return fallback

def get_mock_influx_data() -> list:
    """
    Read pre-computed predictions from MongoDB (written by the pipeline).
    Fields used directly from the document — no recomputation:
      machine_id  → doc.machine_id
      rul_days    → doc.rul  (predicted RUL from the model)
      status      → doc.label / doc.raw.alert_level  (pipeline output)
      timestamp   → doc.timestamp
    temperature/vibration kept as 0 since they're not meaningful display
    values — status and RUL come from the model, not raw sensors.
    """
    try:
        collection = get_collection()
        documents  = list(collection.find({}, {"_id": 0}))

        mapped = []
        for doc in documents:
            machine_id = doc.get("machine_id")
            rul        = doc.get("rul", 0)
            timestamp  = doc.get("timestamp")

            if hasattr(timestamp, "isoformat"):
                timestamp = timestamp.isoformat()
            else:
                timestamp = str(timestamp)

            # Status comes from the pipeline — trust it directly
            raw         = doc.get("raw", {})
            alert_level = (
                doc.get("label")
                or raw.get("alert_level")
                or raw.get("alert")
                or "HEALTHY"
            ).upper()
            status = _STATUS_MAP.get(alert_level, "Normal")

            # confidence from the model (0–1), stored for future use
            confidence = raw.get("confidence", None)

            # Compute avg temperature (s_4) and avg vibration (s_9) from raw arrays
            raw_inner = raw.get("raw", {})
            s4_arr = [_safe_float(v) for v in raw_inner.get("s_4", []) if v is not None]
            s9_arr = [_safe_float(v) for v in raw_inner.get("s_9", []) if v is not None]
            avg_temp = round(sum(s4_arr) / len(s4_arr), 2) if s4_arr else 0.0
            avg_vibe = round(sum(s9_arr) / len(s9_arr), 2) if s9_arr else 0.0

            mapped.append({
                "machine_id":            machine_id,
                "timestamp":             timestamp,
                "temperature":           avg_temp,
                "vibration":             avg_vibe,
                "rul_days":              int(rul),
                "status":                status,
                "confidence":            confidence,
                "scheduled_maintenance": raw.get("scheduled_maintenance", False),
            })

        return mapped

    except Exception as e:
        print(f"[MongoDB] Failed to fetch data: {e}")
        return []