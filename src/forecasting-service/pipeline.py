import numpy as np
from models import mock_model       
from services import verification
from services import disptcher


def run_pipeline(machine_id: str, raw_window: np.ndarray, industry: str = "default"):

    model_input = mock_model.ModelInput(machine_id=machine_id, window=raw_window)

    v = verification.verify(model_input)

    config = disptcher.ThresholdConfig.get_default()
    d = disptcher.dispatch(v, config=config)

    return v, d


if __name__ == "__main__":
    print("=" * 65)
    print("SENTINEL — Pipeline Smoke Test")
    print("=" * 65)

    test_cases = [
        ("machine_01", "default"),
        ("machine_02", "aviation"),
        ("machine_03", "conveyor"),
    ]

    for machine_id, industry in test_cases:
        raw_window = np.random.rand(50, 9)
        v, d = run_pipeline(machine_id, raw_window, industry)

        print(f"\nMachine   : {v.machine_id}  [{industry}]")
        print(f"Mean RUL  : {v.mean_rul:.1f}h  |  Std: {v.std_rul:.2f}h")
        print(f"Confidence: {v.confidence:.0%}")
        print(f"Failure   : {v.failure_type}")
        print(f"Decision  : {d.alert_level.value}")
        print(f"Channels  : {d.channels}")
        print(f"Message   : {d.message}")
        print("-" * 65)