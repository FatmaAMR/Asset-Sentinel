import sys
import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db.connection import get_motor_data, DATA_PATH
from services.verification import validate_sensor_reading
from services.logic import extract_features, verbalize_status

if __name__ == "__main__":
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

    print(f"\nALL DONE! Results saved to: {output_path}")