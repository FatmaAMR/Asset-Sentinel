from __future__ import annotations

import logging
import time
import sys
import json
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import numpy as np
import torch

current_file = Path(__file__).resolve()
service_root = current_file.parent

if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

try:
    from models.transformers import SensorTransformer
    from services.forecasting_engine import ForecastingEngine
    from services.logic import SensorLogic
    from services.verification import verify
    from services.disptcher import dispatch
except ImportError as e:
    print(f"[Error] Failed to import real modules: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PipelineResult:
    success: bool
    message_id: str
    file_name: str
    window_index: int
    prediction: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_stage: Optional[str] = None
    processing_time_ms: float = 0.0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ProcessingPipeline:
    def __init__(self, transformer: Optional[SensorTransformer] = None):
        print("[System] Initializing Sentinel AI Pipeline Components...")
        
        self.transformer = transformer or SensorTransformer()
        self.logic = SensorLogic()
        
        base_weights = service_root / "assets" / "base_model.pth"
        self.engine = ForecastingEngine(base_weights_path=str(base_weights))
        
        print(f"[System] All real components loaded. Model weights: {base_weights.name}")

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        message_id = message.get("message_id", "unknown")
        record = message.get("record", {})
        file_name = record.get("file_name", "unknown")
        window_index = record.get("window_index", 0)
        machine_type = message.get("machine_type", "base_type")

        print(f"\n--- [Pipeline Start] Message ID: {message_id} ---")

        result = PipelineResult(
            success=False,
            message_id=message_id,
            file_name=file_name,
            window_index=window_index,
        )

        try:
            print(f"[Step 1/5] Extraction | Input: {file_name} | Window: {window_index}")
            column_names = record.get("column_names", [])
            data = record.get("data", {})

            if not data:
                raise ValueError("Empty sensor data received in pipeline")
            print(f"  > Status: Extracted {len(column_names)} columns successfully.")

            print("[Step 2/5] Transformation | Applying SensorTransformer logic")
            transformed_data = self.transformer.transform(
                data=data,
                column_names=column_names,
            )
            print(f"  > Status: Transformation complete. Data shape: {transformed_data.shape}")

            print("[Step 3/5] AI Inference | Preparing window for Sentinel AI (64, 21)")
            reshaped = transformed_data.reshape(-1, 21)
            if reshaped.shape[0] < 64:
                padding = np.zeros((64 - reshaped.shape[0], 21))
                prepared_window = np.vstack((padding, reshaped))
                print(f"  > Info: Padded sequence from {reshaped.shape[0]} to 64")
            else:
                prepared_window = reshaped[-64:, :]
                print(f"  > Info: Truncated sequence to last 64 readings")
            
            prepared_window_batch = np.expand_dims(prepared_window, axis=0)

            predicted_rul = self.engine.run_inference(
                machine_id=file_name,
                machine_type=machine_type,
                window_data=prepared_window_batch
            )
            print(f"  > Status: Sentinel AI Prediction Output: {predicted_rul:.2f} units")

            print("[Step 4/5] Verification & Logic | Validating health and business rules")
            verification = verify(prepared_window, self.engine, machine_type, machine_id=file_name)
            decision = dispatch(verification)
            
            prediction_payload = {
                "predicted_rul": float(predicted_rul),
                "machine_type": machine_type,
                "mean_rul": float(verification.mean_rul),
                "confidence": float(verification.confidence),
                "alert_level": decision.alert_level.value,
                "alert_message": decision.message,
                "should_alert": decision.should_alert
            }

            processed_prediction = self.logic.process_prediction(
                prediction=prediction_payload,
                sensor_data=data,
                file_name=file_name,
            )
            print(f"  > Status: Alert Level set to [{decision.alert_level.value}].")

            print("[Step 5/5] Broker | Generating Dispatch Payload")
            self._prepare_broker_payload(message_id, file_name, processed_prediction, data)

            result.success = True
            result.prediction = processed_prediction

        except Exception as exc:
            print(f"[CRITICAL ERROR] Stage: {self._get_current_stage()} | Details: {exc}")
            result.success = False
            result.error = str(exc)
            result.error_stage = self._get_current_stage()

        finally:
            result.processing_time_ms = (time.time() - start_time) * 1000
            print(f"--- [Pipeline End] Total Time: {result.processing_time_ms:.2f}ms ---\n")

        return {
            "success": result.success,
            "message_id": result.message_id,
            "error": result.error,
            "data": result.to_dict(),
        }

    def _prepare_broker_payload(self, message_id: str, file_name: str, prediction: Dict, raw_data: Dict):
        status_payload = {
            "metadata": {
                "message_id": message_id,
                "file_name": file_name,
                "timestamp": datetime.utcnow().isoformat()
            },
            "processed_data": raw_data,
            "labels": {
                "predicted_rul": prediction.get("predicted_rul"),
                "health_state": prediction.get("alert_level"),
                "confidence": prediction.get("confidence"),
                "should_alert": prediction.get("should_alert")
            }
        }
        
        # Display the formatted payload for verification
        print("  > Broker Payload Structure:")
        print(json.dumps(status_payload, indent=4))
        
        # TODO: Integration point for colleague
        # broker_service.publish(queue='equipment_status', body=status_payload)

    def _get_current_stage(self) -> str:
        import inspect
        return inspect.currentframe().f_back.f_code.co_name

if __name__ == "__main__":
    try:
        pipeline = ProcessingPipeline()
        sample_input = {
            "message_id": "TEST-12345",
            "machine_type": "Industrial_Engine_V1",
            "record": {
                "file_name": "machine_001.csv",
                "window_index": 100,
                "column_names": [f"sensor_{i}" for i in range(21)],
                "data": {f"sensor_{i}": [np.random.rand()] for i in range(21)}
            }
        }
        final_result = pipeline.process(sample_input)
    except Exception as e:
        print(f"Failed to run pipeline: {e}")