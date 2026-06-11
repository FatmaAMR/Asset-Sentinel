import sqlite3
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

MONGO_URL       = os.getenv("DB_URL")
DATABASE_NAME   = os.getenv("DB_NAME", "Sentinel")
COLLECTION_NAME = os.getenv("DB_COLLECTION", "cmapss_sensor_data")

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.mongo_client = MongoClient(MONGO_URL)
        self.collection = self.mongo_client[DATABASE_NAME][COLLECTION_NAME]

    def execute_query(self, sql_query: str):
        try:
            documents = list(self.collection.find({}, {"_id": 0}))

            if not documents:
                return []

            # Keep only the latest document per machine
            latest_per_machine = {}
            for doc in documents:
                machine_id = doc.get("machine_id")
                if not machine_id:
                    continue
                ts = doc.get("timestamp")

                # Normalize timestamp to a comparable numeric value
                if hasattr(ts, "timestamp"):        # datetime object
                    ts_val = ts.timestamp()
                elif isinstance(ts, (int, float)):  # unix timestamp
                    ts_val = float(ts)
                elif isinstance(ts, str):           # ISO string
                    ts_val = ts
                else:
                    ts_val = 0

                if machine_id not in latest_per_machine:
                    latest_per_machine[machine_id] = (ts_val, doc)
                else:
                    existing_ts_val = latest_per_machine[machine_id][0]
                    if ts_val > existing_ts_val:
                        latest_per_machine[machine_id] = (ts_val, doc)

            documents = [v[1] for v in latest_per_machine.values()]
            print(f"[DEBUG] Unique machines after dedup: {len(documents)}")
            logger.info(f"[DB] Deduplicated to {len(documents)} machines (latest per machine)")

            conn = self._build_in_memory_db(documents)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            conn.close()
            return result

        except Exception as e:
            raise Exception(f"Database Execution Error: {str(e)}")

    def _build_in_memory_db(self, documents: list) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")

        flat_docs = []
        for doc in documents:
            flat = {}
            for k, v in doc.items():
                if isinstance(v, (str, int, float, bool)) or v is None:
                    flat[k] = v
                elif hasattr(v, "isoformat"):
                    flat[k] = v.isoformat()
                elif isinstance(v, dict) and k == "raw":
                    raw = v
                    flat["should_alert"] = str(raw.get("should_alert", False))
                    flat["alert_level"]  = str(raw.get("alert_level", ""))
                    flat["confidence"]   = str(raw.get("confidence", ""))
                    flat["failure_type"] = str(raw.get("failure_type", ""))
                # skip other nested dicts/lists
            flat_docs.append(flat)

        if not flat_docs:
            return conn

        all_keys = list(dict.fromkeys(k for doc in flat_docs for k in doc.keys()))
        cols_def = ", ".join(f'"{c}" TEXT' for c in all_keys)
        conn.execute(f"CREATE TABLE IF NOT EXISTS assets ({cols_def})")

        placeholders = ", ".join("?" for _ in all_keys)
        for doc in flat_docs:
            values = [
                str(doc.get(c)) if doc.get(c) is not None else ""
                for c in all_keys
            ]
            conn.execute(
                f'INSERT INTO assets ({", ".join(f"{chr(34)}{c}{chr(34)}" for c in all_keys)}) VALUES ({placeholders})',
                values
            )

        conn.commit()
        logger.info(f"[DB] Loaded {len(flat_docs)} documents into in-memory table 'assets'")
        return conn