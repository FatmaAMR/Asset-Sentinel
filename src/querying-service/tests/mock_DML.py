import sqlite3
from datetime import datetime, timedelta

def populate_extended_mock_data():
    conn = sqlite3.connect('shared.db')
    cursor = conn.cursor()

    # 1. Create Tables (Adding maintenance_logs for relational queries)
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            location TEXT,
            install_date DATE
        );

        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT,
            timestamp DATETIME,
            temperature REAL,
            vibration REAL,
            pressure REAL,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT,
            technician_name TEXT,
            maintenance_date DATE,
            issue_found TEXT,
            parts_replaced TEXT,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        );

        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT,
            predicted_rul REAL,
            confidence REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        );
    ''')

    # 2. Insert Diverse Assets
    assets = [
        ('MTR_001', 'Primary Conveyor Motor', 'Motor', 'North Wing', '2023-01-15'),
        ('MTR_002', 'Secondary Fan Motor', 'Motor', 'South Wing', '2023-05-10'),
        ('PMP_001', 'Coolant Pump A', 'Pump', 'Basement', '2022-11-20'),
        ('PMP_002', 'Oil Pressure Pump', 'Pump', 'Section B', '2024-02-01'),
        ('BLR_001', 'Steam Boiler', 'Boiler', 'Power House', '2021-08-12')
    ]
    cursor.executemany('INSERT OR IGNORE INTO assets VALUES (?,?,?,?,?)', assets)

    # 3. Insert Maintenance Logs (To track "Who" and "When")
    maintenance = [
        ('MTR_001', 'Ahmed Hani', '2026-03-10', 'Overheating', 'Bearings'),
        ('MTR_001', 'Malak Ali', '2026-05-01', 'Standard Checkup', 'None'),
        ('PMP_001', 'Andrew Maher', '2026-04-15', 'Leakage', 'Seal Kit'),
        ('BLR_001', 'Shaimaa Soliman', '2026-01-20', 'Low Pressure', 'Safety Valve')
    ]
    cursor.executemany('INSERT OR IGNORE INTO maintenance_logs (asset_id, technician_name, maintenance_date, issue_found, parts_replaced) VALUES (?,?,?,?,?)', maintenance)

    # 4. Insert Varied Predictions
    predictions = [
        ('MTR_001', 14.2, 0.92),
        ('MTR_002', 45.8, 0.85),
        ('PMP_001', 3.5, 0.98), # High risk
        ('PMP_002', 88.0, 0.75),
        ('BLR_001', 12.0, 0.94)
    ]
    cursor.executemany('INSERT OR IGNORE INTO predictions (asset_id, predicted_rul, confidence) VALUES (?,?,?)', predictions)

    conn.commit()
    conn.close()
    print("Extended Mock Database initialized successfully.")

if __name__ == "__main__":
    populate_extended_mock_data()