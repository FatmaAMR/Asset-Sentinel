import sqlite3
from config.settings import settings

class DatabaseManager:
    def __init__(self):
        # Strip the 'sqlite:///' part if you are using simple sqlite3 library
        self.db_path = settings.DATABASE_URL.replace("sqlite:///", "")

    def execute_query(self, sql_query: str):
        try:
            conn = sqlite3.connect(self.db_path)
            # This allows accessing columns by name like a dictionary
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            
            # Convert Row objects to list of dictionaries
            result = [dict(row) for row in rows]
            
            conn.close()
            return result
        except Exception as e:
            raise Exception(f"Database Execution Error: {str(e)}")