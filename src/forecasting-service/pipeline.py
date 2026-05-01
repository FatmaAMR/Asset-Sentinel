from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
from pathlib import Path
import numpy as np
import torch

# --- 1. Path Configuration (Breaking Circular Imports & Resolving Packages) ---
# Set the forecasting-service directory as the primary root for absolute imports
current_file = Path(__file__).resolve()
service_root = current_file.parent

if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

# --- 2. Absolute Imports ---
# These now work because service_root is in sys.path
from models.transformers import SensorTransformer
from services.forecasting_engine import ForecastingEngine
from services.logic import SensorLogic
from db.connection import get_db_connection
from services.verification import verify
from services.disptcher import dispatch

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
        """
        Orchestrates the data flow from raw input to RUL prediction and dispatching.
        """
        # Malak's Layer: Feature Engineering & Transformation
        self.transformer = transformer or SensorTransformer()
        
        # Mai's Layer: Business Logic & Decision Making
        self.logic = SensorLogic()
        
        self.db = get_db_connection()
        
        # AI Core: Sentinel AI Engine
        # Using absolute path for weight loading stability
        base_weights = service_root / "assets" / "base_model.pth"
        self.engine = ForecastingEngine(base_weights_path=str(base_weights))

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        import time
        start_time = time.time()

        message_id = message.get("message_id", "unknown")
        record = message.get("record", {})
        file_name = record.get("file_name", "unknown")
        window_index = record.get("window_index", 0)
        machine_type = message.get("machine_type", "base_type")

        result = PipelineResult(
            success=False,
            message_id=message_id,
            file_name=file_name,
            window_index=window_index,
        )

        try:
            # --- Stage 1: Data Extraction ---
            logger.debug(f"[{message_id}] Stage 1: Data Extraction")
            column_names = record.get("column_names", [])
            data = record.get("data", {})

            if not data:
                raise ValueError("Empty sensor data received in pipeline")

            # --- Stage 2: Feature Transformation (Malak's Logic) ---
            logger.debug(f"[{message_id}] Stage 2: Feature Transformation")
            transformed_data = self.transformer.transform(
                data=data,
                column_names=column_names,
            )

            # --- Stage 3: Sentinel Inference Preparation ---
            logger.debug(f"[{message_id}] Stage 3: Sentinel Inference Preparation")
            
            # Constraints: Sentinel AI requires (Batch: 1, Sequence: 64, Features: 21)
            try:
                reshaped = transformed_data.reshape(-1, 21)
                
                # Window Handling (Padding for new engines, Truncating for stable ones)
                if reshaped.shape[0] < 64:
                    padding = np.zeros((64 - reshaped.shape[0], 21))
                    prepared_window = np.vstack((padding, reshaped))
                else:
                    prepared_window = reshaped[-64:, :]
                
                # Add Batch dimension
                prepared_window_batch = np.expand_dims(prepared_window, axis=0)
                
            except Exception as e:
                logger.error(f"Shape alignment failed for Transformer: {e}")
                prepared_window_batch = np.zeros((1, 64, 21))

            # Execute Primary RUL Prediction
            predicted_rul = self.engine.run_inference(
                machine_id=file_name,
                machine_type=machine_type,
                window_data=prepared_window_batch
            )

            prediction_payload = {
                "predicted_rul": float(predicted_rul),
                "machine_type": machine_type,
                "status": "monitored"
            }

            # --- Stage 3.5: Advanced Verification & Dispatch (Mai's Logic) ---
            logger.debug(f"[{message_id}] Stage 3.5: Verification & Dispatch")

            # Verification based on model confidence and window variance
            verification = verify(prepared_window, self.engine, machine_type, machine_id=file_name)
            
            # Final Dispatch Decision (Alert Levels)
            decision = dispatch(verification)
            
            # Enrich prediction payload
            prediction_payload.update({
                "mean_rul": float(verification.mean_rul),
                "std_rul": float(verification.std_rul),
                "confidence": float(verification.confidence),
                "failure_type": verification.failure_type,
                "alert_level": decision.alert_level.value,
                "alert_message": decision.message,
                "should_alert": decision.should_alert,
                "channels": decision.channels
            })

            logger.info(
                f"[{message_id}] Decision: {decision.alert_level.value} | "
                f"RUL: {verification.mean_rul:.1f} | Conf: {verification.confidence:.0%}"
            )

            # --- Stage 4: Business Logic ---
            logger.debug(f"[{message_id}] Stage 4: Business Logic")
            processed_prediction = self.logic.process_prediction(
                prediction=prediction_payload,
                sensor_data=data,
                file_name=file_name,
            )

            # --- Stage 5: Persistent Storage ---
            logger.debug(f"[{message_id}] Stage 5: Persistent Storage")
            self._store_results(
                message_id=message_id,
                file_name=file_name,
                window_index=window_index,
                prediction=processed_prediction,
                raw_data=data,
            )

            result.success = True
            result.prediction = processed_prediction
            logger.info(f"[{message_id}] Pipeline execution completed successfully")

        except Exception as exc:
            logger.error(f"[{message_id}] Critical failure: {exc}", exc_info=True)
            result.success = False
            result.error = str(exc)
            result.error_stage = self._get_current_stage()

        finally:
            result.processing_time_ms = (time.time() - start_time) * 1000
            logger.debug(f"[{message_id}] Processing Time: {result.processing_time_ms:.2f}ms")

        return {
            "success": result.success,
            "message_id": result.message_id,
            "error": result.error,
            "data": result.to_dict(),
        }

    def _store_results(self, message_id, file_name, window_index, prediction, raw_data):
        try:
            result_record = {
                "message_id": message_id,
                "file_name": file_name,
                "window_index": window_index,
                "prediction": prediction,
                "raw_data": raw_data,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "processed",
            }
            if self.db:
                self.db.insert_prediction_result(result_record)
        except Exception as exc:
            logger.error(f"Persistence failed: {exc}")

    def _get_current_stage(self) -> str:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            return frame.f_back.f_code.co_name
        return "unknown"

if __name__ == "__main__":
    # Test block to verify imports
    p = ProcessingPipeline()
    print("Pipeline initialized with all absolute imports resolved.")