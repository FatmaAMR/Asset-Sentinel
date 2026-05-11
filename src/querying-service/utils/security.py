import re

class SQLValidator:
    # We only allow SELECT queries for the Querying Service
    ALLOWED_KEYWORDS = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
    FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", "ALTER", "--", ";"]

    @staticmethod
    def is_safe(sql_query: str) -> bool:
        # 1. Must be a SELECT statement
        if not SQLValidator.ALLOWED_KEYWORDS.match(sql_query):
            return False
        
        # 2. Must not contain forbidden destructive commands
        upper_query = sql_query.upper()
        for forbidden in SQLValidator.FORBIDDEN_KEYWORDS:
            if forbidden in upper_query:
                return False
        
        return True