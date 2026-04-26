import numpy as np

def validate_sensor_reading(window):
    if window is None or len(window) == 0:
        return False, "Empty"
    
    if np.std(window) == 0:
        return False, "Stuck"

    q1 = np.percentile(window, 25)
    q3 = np.percentile(window, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    if np.any((window < lower_bound) | (window > upper_bound)):
        return False, "Outlier"

    return True, "Valid"