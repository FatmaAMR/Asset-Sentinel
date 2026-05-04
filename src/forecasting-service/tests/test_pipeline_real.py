"""
test_pipeline_real.py
---------------------
بيقرأ test_FD001.csv الحقيقي ويشغّل الـ pipeline بالداتا الفعلية
"""

import sys
import numpy as np
import time
import pandas as pd
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
tests_dir    = Path(__file__).resolve().parent   # tests/
service_root = tests_dir.parent                  # forecasting-service/

sys.path.insert(0, str(service_root))

from pipeline import ProcessingPipeline

FEATURE_COLUMNS = [f"sensor_{i}" for i in range(1, 22)]


# ── Load الداتا ───────────────────────────────────────────────────────────────
def load_fd001(path: str) -> pd.DataFrame:
    # بنقرأ أول صف عشان نعرف هو فيه header ولا لا
    sample = pd.read_csv(path, nrows=1, header=None)
    first_val = str(sample.iloc[0, 0]).strip()

    if first_val.lstrip('-').replace('.','',1).isdigit():
        # مفيش header — space separated بدون أسماء
        df = pd.read_csv(path, sep=r"\s+", header=None)
    else:
        # فيه header
        df = pd.read_csv(path)

    print(f"Loaded : {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Machines: {df.iloc[:, 0].nunique()}")
    return df


# ── بناء الـ message ──────────────────────────────────────────────────────────
def build_message(df: pd.DataFrame, unit_id, window_size: int = 64) -> dict:
    machine_df = df[df.iloc[:, 0] == unit_id].tail(window_size)

    # الـ sensors بتبدأ من column رقم 5 (بعد unit_id, time, op1, op2, op3)
    sensor_cols = df.columns[5:26].tolist()

    data = {
        FEATURE_COLUMNS[i]: machine_df.iloc[:, 5 + i].tolist()
        for i in range(min(21, len(sensor_cols)))
    }

    time_max = machine_df.iloc[:, 1].max()
    window_index = int(time_max) if not pd.isna(time_max) else 0

    return {
        "message_id": f"real_test_unit_{unit_id}_{int(time.time())}",
        "machine_type": "base_type",
        "record": {
            "file_name":    f"FD001_unit_{unit_id}",
            "window_index": window_index,
            "column_names": FEATURE_COLUMNS,
            "data":         data,
        }
    }


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    csv_path = service_root.parent / "raw" / "test_FD001.csv"

    if not csv_path.exists():
        print(f"CSV not found at: {csv_path}")
        sys.exit(1)

    df = load_fd001(str(csv_path))

    print("\nInitializing pipeline...")
    pipeline = ProcessingPipeline()
    print("Pipeline ready!")

    unit_ids = sorted(df.iloc[:, 0].unique())[:3]

    for unit_id in unit_ids:
        print(f"\n{'='*60}")
        print(f"Testing Machine: unit_{unit_id}")

        message = build_message(df, unit_id)
        result  = pipeline.process(message)

        print(f"  success        : {result['success']}")
        print(f"  error          : {result['error']}")

        if result["success"] and result["data"]["prediction"]:
            pred = result["data"]["prediction"]
            print(f"  predicted_rul  : {pred.get('predicted_rul', 'N/A')}")
            print(f"  mean_rul       : {pred.get('mean_rul', 'N/A')}")
            print(f"  std_rul        : {pred.get('std_rul', 'N/A')}")
            print(f"  confidence     : {pred.get('confidence', 0):.0%}")
            print(f"  failure_type   : {pred.get('failure_type', 'N/A')}")
            print(f"  alert_level    : {pred.get('alert_level', 'N/A')}")
            print(f"  should_alert   : {pred.get('should_alert', 'N/A')}")
            print(f"  channels       : {pred.get('channels', 'N/A')}")
            print(f"  alert_message  : {pred.get('alert_message', 'N/A')}")
        else:
            print(f"  failed at: {result['data'].get('error_stage', 'unknown')}")
            print(f"  error    : {result['error']}")

        print(f"  time: {result['data']['processing_time_ms']:.2f}ms")
