import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'raw')

def get_motor_data(file_name):
    file_full_path = os.path.join(DATA_PATH, file_name)
    df = pd.read_csv(file_full_path)
    return {
        "vibration_z": df['Z'].values,
        "current_i1": df['I1'].values,
        "voltage_v1": df['V1'].values
    }