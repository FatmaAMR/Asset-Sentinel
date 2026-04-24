"""
mock_model.py
-------------
Mimics the real forecasting model interface.
Returns random RUL so we can build and test the full pipeline
before the real model is ready.

USAGE:
    from models.mock_model import predict

SWAP TO REAL MODEL:
    from models.real_model import predict   # just change this line
"""

import numpy as np
from dataclasses import dataclass


WINDOW_SIZE = 50      
N_FEATURES  = 9      
FAILURE_CLASSES = [
    "phase_removal",
    "mechanical_misalignment",
    "healthy",
]

@dataclass
class ModelInput:
    """
    Represents one inference request.

    machine_id  : unique machine identifier  (str)
    window      : numpy array of shape (WINDOW_SIZE, N_FEATURES)
                  each row = one timestep, each col = one sensor
    """
    machine_id: str
    window: np.ndarray        


@dataclass
class ModelOutput:
    """
    What the model returns for one machine.

    machine_id      : echoed back for routing
    predicted_rul   : Remaining Useful Life in hours  (float)
    failure_type    : best-guess failure category      (str)
    raw_scores      : full probability vector per class (np.ndarray)
    """
    machine_id:    str
    predicted_rul: float
    failure_type:  str
    raw_scores:    np.ndarray


FAILURE_CLASSES = [
    "bearing_failure",
    "overheating",
    "imbalance",
    "lubrication_loss",
    "electrical_fault",
    "no_failure",
]


def predict(model_input: ModelInput) -> ModelOutput:
 
    assert isinstance(model_input.window, np.ndarray), \
        "window must be a numpy array"
    assert model_input.window.shape == (WINDOW_SIZE, N_FEATURES), \
        f"Expected shape ({WINDOW_SIZE}, {N_FEATURES}), got {model_input.window.shape}"

    predicted_rul = float(np.random.uniform(0, 200))


    raw_scores    = np.random.dirichlet(np.ones(len(FAILURE_CLASSES)))
    failure_type  = FAILURE_CLASSES[int(np.argmax(raw_scores))]

    return ModelOutput(
        machine_id    = model_input.machine_id,
        predicted_rul = predicted_rul,
        failure_type  = failure_type,
        raw_scores    = raw_scores,
    )