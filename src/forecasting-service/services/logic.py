import numpy as np
from scipy.stats import kurtosis

def extract_features(vibration_window, current_window):
    return {
        "vibration_rms": np.sqrt(np.mean(np.square(vibration_window))),
        "vibration_kurtosis": kurtosis(vibration_window),
        "current_mean": np.mean(np.abs(current_window)),
        "peak_vibration": np.max(np.abs(vibration_window))
    }
def verbalize_status(features):
    rms = features['vibration_rms']
    kurt = features['vibration_kurtosis']
    curr = features['current_mean']
    
    status_msg = f"The motor is operating with an RMS vibration of {rms:.4f}. "
    
    if kurt > 1:
        status_msg += "High peakiness (Kurtosis) detected, suggesting potential impulsive shocks. "
    else:
        status_msg += "Vibration distribution appears stable. "
        
    status_msg += f"Average current consumption is {curr:.4f}A."
    
    return status_msg