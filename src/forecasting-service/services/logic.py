import numpy as np

def extract_features(v_sample, i_sample):
    features = {
        'vibration_rms': np.sqrt(np.mean(v_sample**2)),
        'vibration_kurtosis': float(np.mean((v_sample - np.mean(v_sample))**4) / (np.std(v_sample)**4 + 1e-6)),
        'current_mean': np.mean(i_sample),
        'peak_vibration': np.max(np.abs(v_sample))
    }
    return features

def verbalize_status(features):
    rms = features['vibration_rms']
    kurt = features['vibration_kurtosis']
    curr = features['current_mean']
    
    status_msg = f"Motor operating with RMS vibration {rms:.4f}. "
    if kurt > 1:
        status_msg += "High peakiness detected. "
    else:
        status_msg += "Vibration distribution is stable. "
    status_msg += f"Avg current: {curr:.4f}A."
    
    return status_msg