import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# --- 1. Setup Environment Paths ---
current_file = Path(__file__).resolve()
# Root of the service (forecasting-service)
service_root = current_file.parents[1] 
# Root of the project (Asset-Sentinel)
project_root = current_file.parents[3] 

# Inject paths in order
sys.path.insert(0, str(service_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

# --- 2. Absolute Import ---
try:
    # Importing from the injected service_root
    from pipeline import ProcessingPipeline
    print("Environment setup complete. Pipeline loaded.")
except ImportError as e:
    print(f"Initialization Error: {e}")
    sys.exit(1)

def test_inference_from_csv():
    # Correct path to your CSV file
    csv_path = service_root / "data" / "raw" / "test_FD001.csv"
    
    if not csv_path.exists():
        print(f"Data file not found at: {csv_path}")
        return

    try:
        col_names = ['unit_nr', 'time_cycles', 'os_1', 'os_2', 'os_3'] + [f's_{i}' for i in range(1, 22)]
        df = pd.read_csv(str(csv_path), sep=r'\s+', header=None, names=col_names)
        
        sample_window = df[df['unit_nr'] == 1].tail(64)
        sensor_features = [f's_{i}' for i in range(1, 22)]
        
        if len(sample_window) < 64:
            print(f"Error: Not enough rows. Found {len(sample_window)}.")
            return

        window_data = sample_window[sensor_features].values.flatten().tolist()
        
        mock_message = {
            "message_id": "test_normal_run_001",
            "source": "engine_unit_1",
            "record": {
                "file_name": "test_FD001.csv",
                "window_index": 1,
                "column_names": sensor_features,
                "data": {f"sensor_{i}": val for i, val in enumerate(window_data)}
            },
            "machine_type": "high_pressure_turbine"
        }

        print(">> Initializing Pipeline (This takes time to load Torch)...")
        pipeline = ProcessingPipeline()
        
        print(">> Running RUL Prediction...")
        response = pipeline.process(mock_message)

        if response.get("success"):
            prediction = response["data"]["prediction"]
            print("\n" + "="*45)
            print(" ✅ SUCCESS: RUL PREDICTED")
            print("="*45)
            print(f" Predicted RUL : {prediction['predicted_rul']:.2f} Hours")
            print("="*45)
        else:
            print(f"\nPipeline Failed: {response.get('error')}")

    except Exception as e:
        print(f"\nTest Error: {e}")

if __name__ == "__main__":
    test_inference_from_csv()