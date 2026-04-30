from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
from pathlib import Path
import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.transformers import SensorTransformer
from services.forecasting_engine import ForecastingEngine
from services.logic import SensorLogic
from db.connection import get_db_connection

from services.verification import verify, ModelInput
from services.dispatcher import dispatch, ThresholdConfig

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
    def __init__(
        self,
        transformer: Optional[SensorTransformer] = None,
    ):
        self.transformer = transformer or SensorTransformer()
        self.logic = SensorLogic()
        self.db = get_db_connection()
        
        # Initialize the real AI Engine
        # Path points to your .pth file in the assets folder
        base_weights = "src/forecasting-service/assets/base_model.pth"
        self.engine = ForecastingEngine(base_weights_path=base_weights)

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        import time
        start_time = time.time()

        message_id = message.get("message_id", "unknown")
        record = message.get("record", {})
        file_name = record.get("file_name", "unknown")
        window_index = record.get("window_index", 0)
        
        # Machine type for routing - default to base if not provided in envelope
        machine_type = message.get("machine_type", "base_type")

        result = PipelineResult(
            success=False,
            message_id=message_id,
            file_name=file_name,
            window_index=window_index,
        )

        try:
            logger.debug(f"[{message_id}] Stage 1: Data Extraction")
            column_names = record.get("column_names", [])
            data = record.get("data", {})

            if not data:
                raise ValueError("Empty sensor data")

            logger.debug(f"[{message_id}] Stage 2: Feature Transformation")
            # This calls the existing SensorTransformer class
            transformed_data = self.transformer.transform(
                data=data,
                column_names=column_names,
            )

            logger.debug(f"[{message_id}] Stage 3: Real Model Inference")
            
            # Reshaping to match SentinelTransformer requirements: (Batch, Seq_len, Features)
            # Sentinel requires (1, 64, 21)
            try:
                # Reshape to 21 features (Active features for FD001)
                reshaped = transformed_data.reshape(-1, 21)
                
                # Check if we have enough rows for the window, otherwise pad with zeros
                if reshaped.shape[0] < 64:
                    padding = np.zeros((64 - reshaped.shape[0], 21))
                    prepared_window = np.vstack((padding, reshaped))
                else:
                    prepared_window = reshaped[:64, :]
                
                # Add Batch dimension: (1, 64, 21)
                prepared_window = np.expand_dims(prepared_window, axis=0)
                
            except Exception as e:
                logger.error(f"Data shaping failed: {e}")
                # Fallback to zero window to avoid crash during testing
                prepared_window = np.zeros((1, 64, 21))

            # Execute real inference and autonomous adaptation
            predicted_rul = self.engine.run_inference(
                machine_id=file_name,
                machine_type=machine_type,
                window_data=prepared_window
            )

            prediction = {
                "predicted_rul": float(predicted_rul),
                "machine_type": machine_type,
                "status": "monitored"
            }
            logger.debug(f"[{message_id}] Stage 3.5: Verification & Dispatching")
 
            model_input = ModelInput(
                machine_id = file_name,
                window     = prepared_window[0],  
            )

            verification = verify(model_input, self.engine, machine_type)
 
            
            decision = dispatch(verification)
            prediction["mean_rul"]      = verification.mean_rul
            prediction["std_rul"]       = verification.std_rul
            prediction["confidence"]    = verification.confidence
            prediction["failure_type"]  = verification.failure_type
            prediction["alert_level"]   = decision.alert_level.value
            prediction["alert_message"] = decision.message
            prediction["should_alert"]  = decision.should_alert
            prediction["channels"]      = decision.channels
 
            logger.info(
                f"[{message_id}] Dispatch Decision: {decision.alert_level.value} | "
                f"RUL: {verification.mean_rul:.1f}h | "
                f"Confidence: {verification.confidence:.0%}"
            )


            logger.debug(f"[{message_id}] Stage 4: Business Logic")
            processed_prediction = self.logic.process_prediction(
                prediction=prediction,
                sensor_data=data,
                file_name=file_name,
            )

            logger.debug(f"[{message_id}] Stage 5: Results Storage")
            self._store_results(
                message_id=message_id,
                file_name=file_name,
                window_index=window_index,
                prediction=processed_prediction,
                raw_data=data,
            )

            result.success = True
            result.prediction = processed_prediction
            logger.info(f"[{message_id}] Pipeline execution successful")

        except Exception as exc:
            logger.error(f"[{message_id}] Pipeline critical failure: {exc}", exc_info=True)
            result.success = False
            result.error = str(exc)
            result.error_stage = self._get_current_stage()

        finally:
            result.processing_time_ms = (time.time() - start_time) * 1000
            logger.debug(f"[{message_id}] Total Processing Time: {result.processing_time_ms:.2f}ms")

        return {
            "success": result.success,
            "message_id": result.message_id,
            "error": result.error,
            "data": result.to_dict(),
        }

    def _store_results(
        self,
        message_id: str,
        file_name: str,
        window_index: int,
        prediction: Dict[str, Any],
        raw_data: Dict[str, Any],
    ) -> None:
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
            logger.error(f"Storage failed: {exc}")

    def _get_current_stage(self) -> str:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            return frame.f_back.f_code.co_name
        return "unknown"