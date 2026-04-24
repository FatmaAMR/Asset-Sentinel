import sys
import os
import json
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db.connection import get_motor_data, DATA_PATH
from services.validation import validate_sensor_reading
from services.logic import extract_features, verbalize_status

def run_validation_tests():
    print(" Running Validation Unit Tests...")
    
    # Test 1: Normal Data
    normal = np.array([1.0, 1.2, 0.9, 1.1, 1.0])
    valid, msg = validate_sensor_reading(normal)
    print(f" - Normal Data Test: {'✅ PASSED' if valid else '❌ FAILED'} ({msg})")

    # Test 2: Stuck Sensor (Zero Variance)
    stuck = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    valid, msg = validate_sensor_reading(stuck)
    print(f" - Stuck Sensor Test: {'✅ PASSED' if not valid and msg == 'Stuck' else '❌ FAILED'} ({msg})")

    # Test 3: Outlier Detection
    outlier = np.array([1.0, 1.1, 0.9, 1.0, 50.0])
    valid, msg = validate_sensor_reading(outlier)
    print(f" - Outlier Test: {'✅ PASSED' if not valid and msg == 'Outlier' else '❌ FAILED'} ({msg})")
    
    print("-" * 50)

if __name__ == "__main__":
  
    run_validation_tests()

    try:
        all_files = [f for f in os.listdir(DATA_PATH) if f.endswith('.csv')]
    except Exception as e:
        print(f"Error: {e}")
        all_files = []

    final_output = []

    for file_name in all_files:
        try:
            data = get_motor_data(file_name)
            v_sample = data['vibration_z'][:100]
            i_sample = data['current_i1'][:100]
            
            is_valid, msg = validate_sensor_reading(v_sample)
            
            if is_valid:
                features = extract_features(v_sample, i_sample)
                text_report = verbalize_status(features)
                
                result_entry = {
                    "file_name": file_name,
                    "metrics": {
                        "vibration_rms": float(features['vibration_rms']),
                        "vibration_kurtosis": float(features['vibration_kurtosis']),
                        "current_mean": float(features['current_mean']),
                        "peak_vibration": float(features['peak_vibration'])
                    },
                    "report": text_report
                }
                final_output.append(result_entry)
                print(f"File: {file_name} | Processed and Added")
            else:
                print(f"File: {file_name} | Skipped: {msg}")
                
        except Exception as e:
            print(f"File: {file_name} | Error: {e}")
        
        print("-" * 50)

    output_path = os.path.join(current_dir, 'final_results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"\n ALL DONE! Results saved to: {output_path}")