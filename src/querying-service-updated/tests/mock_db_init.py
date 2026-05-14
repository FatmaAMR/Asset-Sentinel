import sqlite3

def initialize_mock_db():
    # Connect to the database file (it will be created if it doesn't exist)
    conn = sqlite3.connect('shared.db')
    cursor = conn.cursor()

    # 1. Create Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            location TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            temperature REAL,
            vibration REAL,
            pressure REAL,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT,
            predicted_rul REAL,
            confidence REAL,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        )
    ''')

    # 2. Insert Mock Data
    assets_data = [
        ('MOTOR_01', 'Main Conveyor Motor', 'Motor', 'Section A'),
        ('PUMP_01', 'Cooling Water Pump', 'Pump', 'Section B'),
        ('BOILER_01', 'High Pressure Boiler', 'Boiler', 'Section C')
    ]
    cursor.executemany('INSERT OR IGNORE INTO assets VALUES (?,?,?,?)', assets_data)

    predictions_data = [
        ('MOTOR_01', 15.5, 0.95),
        ('PUMP_01', 5.2, 0.88),
        ('BOILER_01', 120.0, 0.99)
    ]
    cursor.executemany('INSERT OR IGNORE INTO predictions (asset_id, predicted_rul, confidence) VALUES (?,?,?)', predictions_data)

    conn.commit()
    conn.close()
    print("Mock Database initialized with tables and sample data.")

if __name__ == "__main__":
    initialize_mock_db() 