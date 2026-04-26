"""
Processing pipeline orchestrates:
  • Data transformation
  • Feature engineering
  • Model inference
  • Result storage
  • Error handling & recovery
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
from pathlib import Path
import numpy as np  # ضفنا numpy هنا

# Add src to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.transformers import SensorTransformer
from models.mock_model import predict, ModelInput, ModelOutput
from services.logic import SensorLogic
from db.connection import get_db_connection

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

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        import time
        start_time = time.time()

        message_id = message.get("message_id", "unknown")
        record = message.get("record", {})
        file_name = record.get("file_name", "unknown")
        window_index = record.get("window_index", 0)

        result = PipelineResult(
            success=False,
            message_id=message_id,
            file_name=file_name,
            window_index=window_index,
        )

        try:
            logger.debug(f"[{message_id}] Stage 1: Extract data")
            column_names = record.get("column_names", [])
            data = record.get("data", {})

            if not data:
                raise ValueError("Empty sensor data")

            logger.debug(f"[{message_id}] Stage 2: Transform features")
            transformed_data = self.transformer.transform(
                data=data,
                column_names=column_names,
            )

            # --- التعديل الجوهري هنا لضبط الـ Shape ---
            logger.debug(f"[{message_id}] Stage 3: Run prediction model")
            
            # الموديل محتاج (50, 9). لو الداتا جاية فلات أو بمقاس مختلف (زي 128)، بنعيد تشكيلها وقصها.
            try:
                # 1. بنحولها لمصفوفة بـ 9 أعمدة (الأعمدة هي الحساسات المختارة)
                reshaped = transformed_data.reshape(-1, 9)
                # 2. بناخد أول 50 صف فقط عشان نطابق WINDOW_SIZE=50
                prepared_window = reshaped[:50, :]
            except Exception as e:
                logger.warning(f"Reshape failed, attempting fallback: {e}")
                # Fallback في حالة وجود نقص في البيانات (تكملة بأصفار مثلاً)
                prepared_window = np.zeros((50, 9))

            model_input = ModelInput(
                machine_id=file_name,
                window=prepared_window, # بعتنا الداتا بالـ shape الصح (50, 9)
            )
            # ------------------------------------------

            model_output = predict(model_input)

            prediction = {
                "predicted_rul": model_output.predicted_rul,
                "failure_type": model_output.failure_type,
                "raw_scores": model_output.raw_scores.tolist(),
            }

            logger.debug(f"[{message_id}] Stage 4: Apply business logic")
            processed_prediction = self.logic.process_prediction(
                prediction=prediction,
                sensor_data=data,
                file_name=file_name,
            )

            logger.debug(f"[{message_id}] Stage 5: Store results")
            self._store_results(
                message_id=message_id,
                file_name=file_name,
                window_index=window_index,
                prediction=processed_prediction,
                raw_data=data,
            )

            result.success = True
            result.prediction = processed_prediction
            logger.info(f"[{message_id}] Pipeline completed successfully")

        except Exception as exc:
            logger.error(f"[{message_id}] Pipeline failed: {exc}", exc_info=True)
            result.success = False
            result.error = str(exc)
            result.error_stage = self._get_current_stage()

        finally:
            result.processing_time_ms = (time.time() - start_time) * 1000
            logger.debug(f"[{message_id}] Total time: {result.processing_time_ms:.2f}ms")

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
                logger.debug(f"Stored result for {message_id}")
        except Exception as exc:
            logger.error(f"Failed to store results: {exc}")

    def _get_current_stage(self) -> str:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            return frame.f_back.f_code.co_name
        return "unknown"