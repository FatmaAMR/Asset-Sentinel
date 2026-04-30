"""Verification Service
--------------------
MATH USED:
  - Mean RUL  : μ = (1/N) Σ RUL_i
  - Std  RUL  : σ = sqrt((1/N) Σ (RUL_i - μ)²)
  - Confidence: C = 1 - (σ / (μ + ε))
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Any

# --- Fixed Imports: Removed missing classes from sentinel_nn ---
# We no longer import ModelInput, ModelOutput, or predict because they don't exist in sentinel_nn.py
from models.sentinel_nn import SentinelTransformer

N_RUNS  = 20       
EPSILON = 1e-6     

@dataclass
class VerificationResult:
    machine_id:      str    
    mean_rul:        float  
    std_rul:         float  
    confidence:      float  
    failure_type:    str    
    all_predictions: List[float] = field(repr=False) # Changed to store raw float RULs

class StochasticRunner:
    def __init__(self, n_runs: int = N_RUNS):
        self.n_runs = n_runs

    def run(self, machine_id: str, window_data: np.ndarray, engine: Any, machine_type: str) -> List[float]:
        results = []
        # Ensure window_data is (1, 64, 21) for the engine
        if window_data.ndim == 2:
            input_batch = np.expand_dims(window_data, axis=0)
        else:
            input_batch = window_data

        for _ in range(self.n_runs):
            # The engine handles the stochastic inference (e.g., if dropout is enabled)
            predicted_rul = engine.run_inference(
                machine_id=machine_id,
                machine_type=machine_type,
                window_data=input_batch
            )
            results.append(float(predicted_rul))
        return results

class UncertaintyChecker:
    def check(self, machine_id: str, rul_values_list: List[float]) -> VerificationResult:
        rul_values = np.array(rul_values_list)
        mean_rul = float(np.mean(rul_values))
        std_rul = float(np.std(rul_values))

        # Calculate confidence based on variance
        confidence = float(np.clip(
            1.0 - (std_rul / (mean_rul + EPSILON)),
            0.0,
            1.0
        ))

        return VerificationResult(
            machine_id      = machine_id,
            mean_rul        = mean_rul,
            std_rul         = std_rul,
            confidence      = confidence,
            failure_type    = "predictive_maintenance", # General type since specific labels are removed
            all_predictions = rul_values_list,
        )

def verify(prepared_window: np.ndarray, engine: Any, machine_type: str = "base_type", machine_id: str = "unknown") -> VerificationResult:
    """
    Primary entry point for the pipeline. 
    Receives the prepared numpy window (64, 21) directly.
    """
    # 1. Run multiple inferences to capture variance
    predictions = StochasticRunner().run(machine_id, prepared_window, engine, machine_type)
    
    # 2. Calculate metrics and return result
    return UncertaintyChecker().check(machine_id, predictions)