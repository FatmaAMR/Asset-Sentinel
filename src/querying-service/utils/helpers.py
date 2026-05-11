# Base template for SQL generation
SQL_SYSTEM_TEMPLATE = """
You are a SQL expert for an industrial predictive maintenance system.
Convert the user's natural language question into a valid SQL query.

Database Schema:
{schema}

Return ONLY the SQL query code. Do not include any explanations or markdown blocks.
"""

# Dynamic Schema definition
CURRENT_DATABASE_SCHEMA = """
- assets (id, name, type, location, install_date)
- sensor_readings (id, asset_id, timestamp, temperature, vibration, pressure)
- maintenance_logs (id, asset_id, technician_name, maintenance_date, issue_found, parts_replaced)
- predictions (id, asset_id, predicted_rul, confidence)
"""