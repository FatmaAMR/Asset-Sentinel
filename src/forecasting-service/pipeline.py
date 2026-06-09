from __future__ import annotations
import os
import logging
import time
import sys
import re
import json
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

current_file = Path(__file__).resolve()
service_root = current_file.parent

try:
    from services.forecasting_engine import ForecastingEngine
    from services.logic import SensorLogic
    from services.verification import SensorValidator
    from services.disptcher import dispatch, ThresholdConfig, AlertLevel
    from utils.publisher import ForecastingPublisher
except ImportError as e:
    sys.path.insert(0, str(service_root))
    from services.forecasting_engine import ForecastingEngine
    from services.logic import SensorLogic
    from services.verification import SensorValidator
    from services.disptcher import dispatch, ThresholdConfig, AlertLevel
    from utils.publisher import ForecastingPublisher

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    def __init__(self):
        print("[System Launcher] Booting Up Sentinel AI Production Pipeline Context...")
        
        current_service_dir = Path(__file__).resolve().parent
        
        # UPDATED PATHS: Direct integration linking to the elite Version 3 assets
        base_weights = current_service_dir / "assets" / "sentinel_v3_weights.pth"
        scaler_file = current_service_dir / "assets" / "telemetry_scaler.joblib"
        
        print(f"[System Path Check] Loading Production LSTM Weights from: {base_weights}")
        print(f"[System Path Check] Loading Production Standard Scaler from: {scaler_file}")
        
        # Initialize Updated Core Services
        self.validator = SensorValidator(scaler_path=str(scaler_file))
        self.engine = ForecastingEngine(base_weights_path=str(base_weights), assets_dir=str(current_service_dir / "assets"))
        self.logic = SensorLogic()
        self.publisher = ForecastingPublisher()
        try:
            self.publisher.connect()
        except Exception as exc:
            logger.error(f"Unable to connect ForecastingPublisher: {exc}")
            self.publisher = None
        
        self.fleet_historical_buffers: Dict[str, List[np.ndarray]] = {}
        print("[System Launcher] V3 Core LSTM Components Successfully Integrated.")

    @staticmethod
    def _format_machine_id(candidate: Any) -> Optional[str]:
        if candidate is None:
            return None

        if isinstance(candidate, list) and candidate:
            candidate = candidate[0]

        candidate_str = str(candidate).strip()
        if not candidate_str:
            return None

        if re.match(r'^(machine|device)[-_]', candidate_str, re.I):
            return candidate_str

        digits = re.search(r'\d+', candidate_str)
        if digits:
            return f"machine-{digits.group(0)}"

        return candidate_str

    @staticmethod
    def _find_unit_candidate(raw_data: Any) -> Optional[Any]:
        if isinstance(raw_data, dict):
            for key, value in raw_data.items():
                normalized_key = str(key).lower()
                if normalized_key in {
                    "unit_nr",
                    "unit_no",
                    "unit_id",
                    "unit",
                    "machine_id",
                    "machine",
                    "asset_id",
                    "asset",
                }:
                    if value is not None:
                        return value

                if normalized_key.startswith(("unit", "machine", "asset")) and value is not None:
                    if re.search(r"\d+", str(value)):
                        return value

                found = ProcessingPipeline._find_unit_candidate(value)
                if found is not None:
                    return found
        elif isinstance(raw_data, list):
            for item in raw_data:
                found = ProcessingPipeline._find_unit_candidate(item)
                if found is not None:
                    return found

        return None

    @staticmethod
    def _extract_machine_id_from_raw(raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract machine ID from raw sensor data payload."""
        if not raw_data or not isinstance(raw_data, dict):
            return None

        candidate = ProcessingPipeline._find_unit_candidate(raw_data)
        return ProcessingPipeline._format_machine_id(candidate)

    @staticmethod
    def _extract_machine_id_from_file_name(file_name: str) -> Optional[str]:
        if not file_name or not isinstance(file_name, str):
            return None

        file_stem = Path(file_name).stem
        if not file_stem:
            return None

        if re.match(r'^(machine|device)[-_]', file_stem, re.I):
            return file_stem

        digits = re.search(r'\d+', file_stem)
        if digits:
            return f"machine-{digits.group(0)}"

        return file_stem

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        start_time_ms = time.time()
        
        message_id = message.get("message_id", "unknown")
        record = message.get("record", {})
        machine_type = message.get("machine_type", "base_type")
        raw_telemetry_packet = record.get("data", {})
        
        # Extract machine_id from raw sensor data first, fallback to normalized file_name
        machine_id = (
            self._extract_machine_id_from_raw(raw_telemetry_packet)
            or self._extract_machine_id_from_file_name(record.get("file_name", ""))
            or "unknown_asset"
        )

        print(f"\n>>> [Pipeline Input Received] Message ID: {message_id} | Tracking ID: {machine_id}")

        try:

            scaled_row, errors = self.validator.process_and_scale_features(raw_telemetry_packet)

            if errors or scaled_row is None:
                raise ValueError(f"Feature processing architecture exceptions raised: {errors}")

            expected_features = len(self.validator.ACTIVE_FEATURES)
            if scaled_row.shape[0] != expected_features:
                raise ValueError(
                    f"Feature vector length mismatch: expected {expected_features}, got {scaled_row.shape[0]}"
                )

            if machine_id not in self.fleet_historical_buffers:
                self.fleet_historical_buffers[machine_id] = []

            self.fleet_historical_buffers[machine_id].append(scaled_row)

            if len(self.fleet_historical_buffers[machine_id]) > 64:
                self.fleet_historical_buffers[machine_id].pop(0)


            current_history_len = len(self.fleet_historical_buffers[machine_id])
            current_window_stack = np.array(self.fleet_historical_buffers[machine_id], dtype=np.float32)
            if current_history_len < 64:
                pad_width = 64 - current_history_len
                padding = np.zeros((pad_width, expected_features), dtype=np.float32)
                prepared_window = np.vstack((padding, current_window_stack))
            else:
                prepared_window = current_window_stack

            # Expand dims to lock standard 3D tensor serialization layout: [1, 64, 21]
            prepared_window_batch = np.expand_dims(prepared_window, axis=0)

            # Step 4: Run Elite V3 LSTM Core Forecasting Engine
            predicted_rul = self.engine.run_inference(
                machine_type=machine_type,
                window_data=prepared_window_batch
            )
            print(f"  > AI Core Inference Response: Predicted RUL = {predicted_rul:.2f} Cycles.")

            xai_diagnostic_payload = None
            PRODUCTION_THRESHOLD = 45.0
            if predicted_rul <= PRODUCTION_THRESHOLD and current_history_len >= 64:
                print(f"  > 🚨 [CRITICAL ALERT TRIGGERED] Safety Bound Breached! Extracting Gradient Saliency...")
                active_model_nn = self.engine._get_model_instance(machine_type, expected_features)
                xai_result = self.validator.execute_xai_root_cause_analysis(
                    model_engine=active_model_nn,
                    window_matrix=prepared_window,
                    threshold_value=PRODUCTION_THRESHOLD
                )
                xai_diagnostic_payload = asdict(xai_result)
                print(f"  > XAI Isolation Complete. Primary Target Source: {xai_diagnostic_payload['mapped_mechanical_subsystem']}")

            prediction_payload = {
                "predicted_rul": float(predicted_rul),
                "machine_id": machine_id,
                "machine_type": machine_type,
                "confidence": 0.99 if current_history_len >= 64 else 0.40,
                "alert_level": "CRITICAL" if (predicted_rul <= PRODUCTION_THRESHOLD and current_history_len >= 64) else "HEALTHY",
                "xai_root_cause_diagnosis": xai_diagnostic_payload
            }

            processed_prediction = self.logic.process_prediction(
                prediction=prediction_payload,
                sensor_data=raw_telemetry_packet,
                file_name=machine_id
            )

            processing_time = (time.time() - start_time_ms) * 1000
            print(f">>> [Pipeline Complete] Output Payload Compiled in {processing_time:.2f}ms.\n")
            
            # -------------------------------------------------------------------------
            # SNEAK PEEK FOR INTEGRATION DEVELOPERS (PRINT FOR VERIFICATION)
            # -------------------------------------------------------------------------
            print("=" * 60)
            print(f"[AI ENGINE BROADCAST] Compiled Payload Ready for Broker Integration:")
            print("=" * 60)
            print(json.dumps(processed_prediction, indent=4))
            print("=" * 60 + "\n")
            # -------------------------------------------------------------------------
            
            try:
                dispatch_decision = dispatch(processed_prediction)
                processed_prediction.update(
                    mean_rul=dispatch_decision.mean_rul,
                    failure_type=dispatch_decision.failure_type,
                    message=dispatch_decision.message,
                    should_alert=dispatch_decision.should_alert,
                    channels=dispatch_decision.channels,
                    alert_level=dispatch_decision.alert_level.value,
                )
            except Exception as exc:
                logger.warning(f"Dispatch decision generation failed: {exc}")

            processed_prediction.setdefault("metadata", {})
            processed_prediction["metadata"].update(
                message_id=message_id,
                timestamp=int(time.time()),
            )
            processed_prediction.setdefault("labels", {})
            processed_prediction["labels"]["should_alert"] = processed_prediction.get("should_alert", False)
            
            # Include raw sensor data for downstream consumer extraction
            processed_prediction.setdefault("raw", {})
            processed_prediction["raw"] = raw_telemetry_packet

            self._publish_equipment_status(processed_prediction)

            return {
                "success": True,
                "message_id": message_id,
                "error": None,
                "payload": processed_prediction,
                "data": {
                    "prediction": processed_prediction,
                    "processing_time_ms": processing_time,
                    "error_stage": None,
                },
            }

        except Exception as exc:
            logger.error(f"[Pipeline Runtime Failure] Process aborted: {str(exc)}")
            return {
                "success": False,
                "message_id": message_id,
                "error": str(exc),
                "payload": None
            }

    def _publish_equipment_status(self, payload: Dict[str, Any]) -> None:
        if not self.publisher:
            logger.warning("ForecastingPublisher not initialized; skipping equipment status publish.")
            return

        try:
            self.publisher.publish(payload)
        except Exception as exc:
            logger.error(f"Failed to publish equipment status payload: {exc}")
