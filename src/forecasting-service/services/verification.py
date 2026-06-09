from __future__ import annotations
import os
import sys
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import torch
import torch.nn as nn  # <-- This line fixes the "nn is not defined" error
import joblib


try:
    import numpy
    sys.modules['numpy._core'] = numpy
except ImportError:
    pass

logger = logging.getLogger(__name__)

@dataclass
class XAIDiagnosticResult:
    status: str
    threshold_breached_limit: float
    isolated_root_cause_sensor: str
    statistical_divergence_magnitude: float
    mapped_mechanical_subsystem: str
    prescriptive_action: str


class SensorValidator:
    STANDARDIZED_RANGE = (-4.0, 4.0)
    
    ACTIVE_FEATURES = [
        's_1', 's_2', 's_3', 's_4', 's_5', 's_6', 's_7', 's_8', 's_9', 's_10',
        's_11', 's_12', 's_13', 's_14', 's_15', 's_16', 's_17', 's_18', 's_19', 's_20', 's_21'
    ]

    SENSOR_MAPPING_NASA = {
        "s_1": "Fan Inlet Total Temperature", "s_2": "LPC Outlet Total Temperature", "s_3": "HPC Outlet Total Temperature",
        "s_4": "LPT Outlet Total Temperature", "s_5": "Fan Inlet Total Pressure", "s_6": "Bypass Duct Total Pressure",
        "s_7": "HPT Outlet Total Pressure", "s_8": "Physical Fan Speed", "s_9": "Physical Core Speed",
        "s_10": "Engine Pressure Ratio (P50/P2) Static", "s_11": "HPC Outlet Static Pressure", "s_12": "HPC Outlet Total Pressure ratio",
        "s_13": "LPT Outlet Total Pressure ratio", "s_14": "Engine Pressure Ratio (P50/P2) Total", "s_15": "HPC Outlet Static Pressure ratio",
        "s_16": "Bleed Enthalpy", "s_17": "HPC Real Speed", "s_18": "HPC Demanded Speed",
        "s_19": "HPC Demanded Corrected Speed", "s_20": "HPT Inlet Static Pressure", "s_21": "LPT Inlet Static Pressure"
    }

    def __init__(self, scaler_path: Optional[str] = None, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.scaler = None
        
        if scaler_path and os.path.exists(scaler_path):
            try:
                self.scaler = joblib.load(scaler_path)
                logger.info(f"[XAI-Verification] Loaded updated telemetry standard scaler from {scaler_path}")
            except Exception as e:
                logger.error(f"[XAI-Verification] Failed loading file via joblib: {str(e)}. Falling back to inline safe instance.")
                self._apply_inline_fallback()
        else:
            logger.warning("[XAI-Verification] Telemetry target scaler not found. Initializing runtime baseline safe instance.")
            self._apply_inline_fallback()

    def _apply_inline_fallback(self):
        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler()
        mock_means = np.zeros(21)
        mock_vars = np.ones(21)
        self.scaler.mean_ = mock_means
        self.scaler.var_ = mock_vars
        self.scaler.scale_ = np.sqrt(mock_vars)
        self.scaler.n_features_in_ = 21

    def process_and_scale_features(self, raw_data: Dict[str, Any]) -> Tuple[Optional[np.ndarray], List[str]]:
        errors = []
        extracted_row = []

        for feature in self.ACTIVE_FEATURES:
            if feature in raw_data:
                try:
                    val = raw_data[feature][0] if isinstance(raw_data[feature], list) else raw_data[feature]
                    extracted_row.append(float(val))
                except (ValueError, TypeError, IndexError):
                    errors.append(f"Non-numeric format captured for feature: {feature}")
            else:
                if self.scaler is not None and hasattr(self.scaler, 'mean_'):
                    feature_idx = self.ACTIVE_FEATURES.index(feature)
                    extracted_row.append(self.scaler.mean_[feature_idx])
                else:
                    extracted_row.append(0.0)

        if errors:
            return None, errors

        row_array = np.array(extracted_row).reshape(1, -1)
        
        if self.scaler is not None:
            scaled_row = self.scaler.transform(row_array)
            return scaled_row.flatten(), errors
        return row_array.flatten(), errors

    def execute_xai_root_cause_analysis(self, model_engine: nn.Module, window_matrix: np.ndarray, threshold_value: float = 45.0) -> XAIDiagnosticResult:
        model_engine.eval()
        device = next(model_engine.parameters()).device
        
        # Force PyTorch to compute gradients specifically for this XAI execution block
        with torch.enable_grad():
            # Clear any residual gradients from previous server inferences
            model_engine.zero_grad()
            
            input_tensor = torch.tensor(window_matrix, dtype=torch.float32).unsqueeze(0).to(device)
            input_tensor.requires_grad = True
            
            output = model_engine(input_tensor)
            output.backward()
            
            # Detach explicitly from computation graph to prevent production memory leaks
            gradients = input_tensor.grad.detach().squeeze(0).abs().cpu().numpy()
            
            # Clear gradients again after extraction to keep memory fully optimized
            model_engine.zero_grad()
            
        channel_attribution_scores = np.mean(gradients, axis=0)
        
        sorted_triggers = sorted(
            [(self.ACTIVE_FEATURES[i], float(channel_attribution_scores[i])) for i in range(len(self.ACTIVE_FEATURES))],
            key=lambda item: item[1], reverse=True
        )
        
        primary_fault_sensor = sorted_triggers[0][0]
        primary_fault_score = sorted_triggers[0][1]
        physical_subsystem = self.SENSOR_MAPPING_NASA.get(primary_fault_sensor, "Unknown Asset Subsystem")

        return XAIDiagnosticResult(
            status="CRITICAL HEALTH BREACH DETECTED",
            threshold_breached_limit=threshold_value,
            isolated_root_cause_sensor=primary_fault_sensor,
            statistical_divergence_magnitude=round(float(primary_fault_score), 6), # Will now print the true float gradient score!
            mapped_mechanical_subsystem=physical_subsystem,
            prescriptive_action=f"Immediate inspection required on {physical_subsystem}. Telemetry gradients report critical structural degradation anomalies."
        )