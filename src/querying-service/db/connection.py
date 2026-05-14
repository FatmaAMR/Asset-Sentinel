import sqlite3
import httpx
import logging

logger = logging.getLogger(__name__)

MANAGERIAL_BASE_URL = "http://localhost:8002/api/v1/managerial"

# Internal (no auth) endpoint for staff
ENDPOINTS = {
    "assets":     f"{MANAGERIAL_BASE_URL}/assets/",
    "staff":      f"{MANAGERIAL_BASE_URL}/staff/all",
    "thresholds": f"{MANAGERIAL_BASE_URL}/thresholds/",
}


class DatabaseManager:
    def __init__(self):
        # In-memory SQLite — rebuilt fresh on every query from live managerial data
        self.conn = None

    # ------------------------------------------------------------------
    # Public interface (same signature as before — nothing else changes)
    # ------------------------------------------------------------------
    def execute_query(self, sql_query: str):
        try:
            db = self._build_in_memory_db()
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            db.close()
            return result
        except Exception as e:
            raise Exception(f"Database Execution Error: {str(e)}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_in_memory_db(self) -> sqlite3.Connection:
        """Fetch live data from managerial service and load into in-memory SQLite."""
        conn = sqlite3.connect(":memory:")

        assets     = self._fetch(ENDPOINTS["assets"])
        staff      = self._fetch_staff()          # wrapped response → list
        thresholds = self._fetch(ENDPOINTS["thresholds"])

        self._load_table(conn, "assets",     assets,     [
            "asset_id", "machine_type", "location_floor",
            "location_section", "specifications", "status"
        ])
        self._load_table(conn, "staff",      staff,      [
            "name", "email", "role"
        ])
        self._load_table(conn, "thresholds", thresholds, [
            "rule_id", "machine_type", "warning_limit",
            "critical_limit", "updated_by_staff_id"
        ])

        return conn

    def _fetch(self, url: str) -> list:
        """GET a URL that returns a plain JSON list."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Could not fetch {url}: {e}")
            return []

    def _fetch_staff(self) -> list:
        """GET /staff/all which returns {'users': [...]}."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(ENDPOINTS["staff"])
                response.raise_for_status()
                data = response.json()
                return data.get("users", []) if isinstance(data, dict) else data
        except Exception as e:
            logger.warning(f"Could not fetch staff: {e}")
            return []

    def _load_table(self, conn: sqlite3.Connection, table: str,
                    rows: list, columns: list):
        """Create table and insert rows into in-memory SQLite."""
        if not rows:
            # Create empty table so SQL queries don't fail on missing tables
            cols_def = ", ".join(f"{c} TEXT" for c in columns)
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols_def})")
            conn.commit()
            return

        # Derive columns from actual data keys (safer than hardcoded list)
        actual_cols = list(rows[0].keys())
        cols_def    = ", ".join(f"{c} TEXT" for c in actual_cols)
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols_def})")

        placeholders = ", ".join("?" for _ in actual_cols)
        for row in rows:
            values = [str(row.get(c, "")) for c in actual_cols]
            conn.execute(
                f"INSERT INTO {table} ({', '.join(actual_cols)}) VALUES ({placeholders})",
                values
            )
        conn.commit()
        logger.info(f"[DB] Loaded {len(rows)} rows into table '{table}'")