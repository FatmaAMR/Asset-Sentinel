from __future__ import annotations
import os
import logging
import time
import sys
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
except ImportError as e:
    sys.path.insert(0, str(service_root))
    from services.forecasting_engine import ForecastingEngine
    from services.logic import SensorLogic
    from services.verification import SensorValidator
    from services.disptcher import dispatch, ThresholdConfig, AlertLevel

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
        
        self.fleet_historical_buffers: Dict[str, List[np.ndarray]] = {}
        print("[System Launcher] V3 Core LSTM Components Successfully Integrated.")

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        start_time_ms = time.time()
        
        message_id = message.get("message_id", "unknown")
        record = message.get("record", {})
        machine_id = record.get("file_name", "unknown_asset")
        machine_type = message.get("machine_type", "base_type")
        
        print(f"\n>>> [Pipeline Input Received] Message ID: {message_id} | Tracking ID: {machine_id}")

        try:
            # Step 1: Real-time Feature Extraction and Normalization via telemetry_scaler
            raw_telemetry_packet = record.get("data", {})
            scaled_row, errors = self.validator.process_and_scale_features(raw_telemetry_packet)
            
            if errors or scaled_row is None:
                raise ValueError(f"Feature processing architecture exceptions raised: {errors}")

            # Step 2: Manage Sliding Window Buffers per individual Asset ID
            if machine_id not in self.fleet_historical_buffers:
                self.fleet_historical_buffers[machine_id] = []
                
            self.fleet_historical_buffers[machine_id].append(scaled_row)
            
            if len(self.fleet_historical_buffers[machine_id]) > 64:
                self.fleet_historical_buffers[machine_id].pop(0)

            # Step 3: Handle Zero-Padding structures during early initial start-up loops
            current_history_len = len(self.fleet_historical_buffers[machine_id])
            current_window_stack = np.array(self.fleet_historical_buffers[machine_id])
            
            if current_history_len < 64:
                pad_width = 64 - current_history_len
                padding = np.zeros((pad_width, len(self.validator.ACTIVE_FEATURES)))
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

            # Step 5: Automated Post-Alert XAI Diagnostic Triggers Loop Condition
            xai_diagnostic_payload = None
            
            PRODUCTION_THRESHOLD = 45.0
            if predicted_rul <= PRODUCTION_THRESHOLD and current_history_len >= 64:
                print(f"  > 🚨 [CRITICAL ALERT TRIGGERED] Safety Bound Breached! Extracting Gradient Saliency...")
                
                # Fetch the active trained neural model instance from engine dynamically
                active_model_nn = self.engine._get_model_instance(machine_type, len(self.validator.ACTIVE_FEATURES))
                
                # CRUCIAL FIX: Pass active_model_nn as the first parameter
                xai_result = self.validator.execute_xai_root_cause_analysis(
                    model_engine=active_model_nn, 
                    window_matrix=prepared_window, 
                    threshold_value=PRODUCTION_THRESHOLD
                )
                xai_diagnostic_payload = asdict(xai_result)
                print(f"  > XAI Isolation Complete. Primary Target Source: {xai_diagnostic_payload['mapped_mechanical_subsystem']}")
                
            # Step 6: Package Response payloads for Downstream Brokers
            prediction_payload = {
                "predicted_rul": float(predicted_rul),
                "machine_id": machine_id,
                "machine_type": machine_type,
                "confidence": 0.99 if current_history_len >= 64 else 0.40,  # High production score for locked sequences
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
            
            return {
                "success": True,
                "message_id": message_id,
                "error": None,
                "payload": processed_prediction
            }

        except Exception as exc:
            logger.error(f"[Pipeline Runtime Failure] Process aborted: {str(exc)}")
            return {
                "success": False,
                "message_id": message_id,
                "error": str(exc),
                "payload": None
            }