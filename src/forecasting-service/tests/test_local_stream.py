import os
import sys
import json
import time
from pathlib import Path
import pandas as pd

# Dynamically resolve paths to ensure clean execution from any directory context
current_test_dir = Path(__file__).resolve().parent
project_root = current_test_dir.parent
sys.path.insert(0, str(project_root))

from pipeline import ProcessingPipeline

def run_isolated_full_pipeline_test(csv_filename: str):
    print("=" * 80)
    print(f"[FINAL PIPELINE VALIDATOR] Running Isolated End-to-End Test for: {csv_filename}")
    print("=" * 80)
    
    csv_file_path = current_test_dir / csv_filename
    
    if not csv_file_path.exists():
        print(f"[ERROR] Target file not found at: {csv_file_path}")
        return

    # Read the data and slice the tail to fast-forward straight to failure alerts
    try:
        df_full = pd.read_csv(csv_file_path)
        df_stream = df_full.tail(70).reset_index(drop=True)
        print(f"[DATA SETUP] Sliced the last {len(df_stream)} real cycles from historical log.")
    except Exception as exc:
        print(f"[DATA FAILURE] Error reading CSV asset: {exc}")
        return

    # Initialize the updated production-grade processing pipeline
    try:
        pipeline = ProcessingPipeline()
    except Exception as exc:
        print(f"[LAUNCH FAILURE] Error booting pipeline modules: {exc}")
        return

    machine_id = Path(csv_filename).stem
    machine_type = "base_type"
    
    print(f"\n[LIVE STREAM SIMULATION] Commencing row-by-row execution loop...\n")
    
    for index, row in df_stream.iterrows():
        cycle_number = int(row["time_cycles"]) if "time_cycles" in df_full.columns else (index + 1)
        row_dict = row.to_dict()
        
        # Build the exact Envelope Schema that RabbitMQ traditionally delivers
        mock_envelope = {
            "message_id": f"isolated_test_uuid_{int(time.time())}_{cycle_number:03d}",
            "source": "motor.raw.isolated_test_harness",
            "timestamp": time.time(),
            "machine_type": machine_type,
            "record": {
                "file_name": machine_id,
                "file_index": 1,
                "window_index": cycle_number,
                "column_names": list(row_dict.keys()),
                "data": row_dict
            }
        }
        
        # Pass payload straight into the pipeline core processing block
        # The print statement inside pipeline.py will capture and print the final payload variable automatically
        pipeline.process(mock_envelope)

    print("=" * 80)
    print("[FINAL PIPELINE VALIDATOR] Verification complete. End-to-End lifecycle testing wrapped.")
    print("=" * 80)

if __name__ == "__main__":
    # Test on test_FD001.csv to verify full RUL and Gradient XAI attribution outputs
    run_isolated_full_pipeline_test("test_FD001.csv")