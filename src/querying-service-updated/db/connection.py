import sqlite3
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

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
            # Fetch all documents from MongoDB
            documents = list(self.collection.find({}, {"_id": 0}))

            if not documents:
                return []

            # Build in-memory SQLite from MongoDB documents
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

        # Flatten documents — drop nested dicts/lists, keep scalar fields
        flat_docs = []
        for doc in documents:
            flat = {}
            for k, v in doc.items():
                if isinstance(v, (str, int, float, bool)) or v is None:
                    flat[k] = v
                elif hasattr(v, "isoformat"):  # datetime
                    flat[k] = v.isoformat()
                # skip nested dicts/lists (e.g. raw, window_sliding)
            flat_docs.append(flat)

        if not flat_docs:
            return conn

        # Create table from first document's keys
        columns = list(flat_docs[0].keys())
        cols_def = ", ".join(f'"{c}" TEXT' for c in columns)
        conn.execute(f"CREATE TABLE IF NOT EXISTS assets ({cols_def})")

        placeholders = ", ".join("?" for _ in columns)
        for doc in flat_docs:
            values = [str(doc.get(c, "")) for c in columns]
            conn.execute(
                f'INSERT INTO assets ({", ".join(f"{chr(34)}{c}{chr(34)}" for c in columns)}) VALUES ({placeholders})',
                values
            )

        conn.commit()
        logger.info(f"[DB] Loaded {len(flat_docs)} documents into in-memory table 'assets'")
        return conn