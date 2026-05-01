"""Verification Service
--------------------
MATH USED:
  - Mean RUL  : μ = (1/N) Σ RUL_i
  - Std  RUL  : σ = sqrt((1/N) Σ (RUL_i - μ)²)
  - Confidence: C = 1 - (σ / (μ + ε))
"""

import numpy as np
import torch
from dataclasses import dataclass, field
from typing import List, Any


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
    all_predictions: List[float] = field(repr=False)


class StochasticRunner:
    def __init__(self, n_runs: int = N_RUNS):
        self.n_runs = n_runs

    def run(self, machine_id: str, window_data: np.ndarray, engine: Any, machine_type: str) -> List[float]:

        if window_data.ndim == 2:
            input_batch = np.expand_dims(window_data, axis=0)
        else:
            input_batch = window_data

        # ── نجيب الـ model من الـ engine مباشرة ──────────────────────────────
        input_dim = input_batch.shape[2]
        model = engine._get_model_instance(machine_type, input_dim)
        device = engine.device

        # ── نحط الـ model في train() mode عشان الـ Dropout يشتغل ─────────────
        # run_inference بيعمل eval() فبنتخطاه ونشغّل الـ model لوحدنا
        model.train()

        input_tensor = torch.tensor(input_batch, dtype=torch.float32).to(device)

        results = []
        with torch.no_grad():
            for _ in range(self.n_runs):
                # كل run الـ Dropout بيطفي neurons مختلفة → نتيجة مختلفة
                rul = model(input_tensor).item()
                results.append(float(rul))

        # ── نرجعه لـ eval() بعد ما خلصنا ────────────────────────────────────
        model.eval()

        return results


class UncertaintyChecker:
    def check(self, machine_id: str, rul_values_list: List[float]) -> VerificationResult:
        rul_values = np.array(rul_values_list)
        mean_rul   = float(np.mean(rul_values))
        std_rul    = float(np.std(rul_values))
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
            failure_type    = "predictive_maintenance",
            all_predictions = rul_values_list,
        )


def verify(prepared_window: np.ndarray, engine: Any, machine_type: str = "base_type", machine_id: str = "unknown") -> VerificationResult:
    """
    Primary entry point for the pipeline.
    Receives the prepared numpy window (64, 21) directly.
    """
    predictions = StochasticRunner().run(machine_id, prepared_window, engine, machine_type)  
    return UncertaintyChecker().check(machine_id, predictions)
