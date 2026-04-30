
"""Verification Service
--------------------
MATH USED:
  - Mean RUL  : μ = (1/N) Σ RUL_i
  - Std  RUL  : σ = sqrt((1/N) Σ (RUL_i - μ)²)
  - Confidence: C = 1 - (σ / (μ + ε))   ← coefficient of variation inverted
                    clamped to [0, 1]
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List

from models.sentinel_nn import ModelInput, ModelOutput, predict


N_RUNS  = 20       
EPSILON = 1e-6     

@dataclass
class VerificationResult:
    machine_id:      str    
    mean_rul:        float  
    std_rul:         float  
    confidence:      float  
    failure_type:    str    
    all_predictions: List[ModelOutput] = field(repr=False)  



class StochasticRunner:
    def __init__(self, n_runs: int = N_RUNS):
        self.n_runs = n_runs

    def run(self, model_input: ModelInput, engine: Any, machine_type: str) -> List[ModelOutput]:
        results = []
        for _ in range(self.n_runs):
            predicted_rul = engine.run_inference(
                machine_id=model_input.machine_id,
                machine_type=machine_type,
                window_data=np.expand_dims(model_input.window, axis=0)
            )
      
            results.append(ModelOutput(
                machine_id=model_input.machine_id,
                predicted_rul=float(predicted_rul),
                failure_type="unknown" 
            ))
        return results






class UncertaintyChecker:


    def check(self, predictions: List[ModelOutput]) -> VerificationResult:

        rul_values = np.array([p.predicted_rul for p in predictions])

        mean_rul = float(np.mean(rul_values))
  

        std_rul = float(np.std(rul_values))

        confidence = float(np.clip(
            1.0 - (std_rul / (mean_rul + EPSILON)),
            0.0,
            1.0
        ))

        failure_counts = {}
        for p in predictions:
            failure_counts[p.failure_type] = failure_counts.get(p.failure_type, 0) + 1
        failure_type = max(failure_counts, key=failure_counts.get)

        return VerificationResult(
            machine_id      = predictions[0].machine_id,
            mean_rul        = mean_rul,
            std_rul         = std_rul,
            confidence      = confidence,
            failure_type    = failure_type,
            all_predictions = predictions,
        )


def verify(model_input: ModelInput, engine: Any, machine_type: str = "base_type") -> VerificationResult:
  
    predictions = StochasticRunner().run(model_input, engine, machine_type)
    return UncertaintyChecker().check(predictions)