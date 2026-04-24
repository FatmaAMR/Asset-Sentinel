
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

from models.mock_model import ModelInput, ModelOutput, predict


# ── Config ────────────────────────────────────────────────────────────────────
N_RUNS        = 10      # how many stochastic passes per inference
NOISE_STD     = 0.01    # std of Gaussian noise added to input  (normalised units)
EPSILON       = 1e-6    # avoid division by zero in confidence formula


@dataclass
class VerificationResult:
    machine_id:      str
    mean_rul:        float
    std_rul:         float
    confidence:      float
    failure_type:    str
    all_predictions: List[ModelOutput] = field(repr=False)


class StochasticRunner:
  
    def __init__(self, n_runs: int = N_RUNS, noise_std: float = NOISE_STD):
        self.n_runs    = n_runs
        self.noise_std = noise_std

    def run(self, model_input: ModelInput) -> List[ModelOutput]:
     
        results = []
        for _ in range(self.n_runs):
            # add tiny Gaussian noise to simulate input uncertainty
            noisy_window = model_input.window + np.random.normal(
                loc=0.0, scale=self.noise_std, size=model_input.window.shape
            )
            noisy_input = ModelInput(
                machine_id=model_input.machine_id,
                window=noisy_window
            )
            results.append(predict(noisy_input))
        return results


class UncertaintyChecker:
   

    def check(self, predictions: List[ModelOutput]) -> VerificationResult:
        rul_values = np.array([p.predicted_rul for p in predictions])

        mean_rul = float(np.mean(rul_values))
        std_rul  = float(np.std(rul_values))

        raw_confidence = 1.0 - (std_rul / (mean_rul + EPSILON))
        confidence     = float(np.clip(raw_confidence, 0.0, 1.0))

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

def verify(model_input: ModelInput) -> VerificationResult:
 
    runner  = StochasticRunner(n_runs=10, noise_std=0.01) 
    checker = UncertaintyChecker()

    predictions = runner.run(model_input)
    return checker.check(predictions)

