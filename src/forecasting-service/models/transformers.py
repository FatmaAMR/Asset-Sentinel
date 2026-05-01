# Specialized Time-Series Transformer models (PatchTST/Informer)
"""
Data transformers for sensor data preprocessing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SensorTransformer:
    """Transforms raw sensor data into features for ML models."""

    def __init__(self):
        self.scalers = {}  # Could add scalers if needed

    def transform(self, data: Dict[str, Any], column_names: List[str]) -> np.ndarray:
        """
        Transform sensor data window into a feature matrix.
        Handles windowed time-series data (e.g., 100 timesteps × 24 features).
        """
        try:
            # Convert to numpy array (each column is a time series)
            window_data = []
            for col in column_names:
                col_values = data.get(col, [])
                if isinstance(col_values, (list, np.ndarray)):
                    window_data.append(col_values)
                else:
                    # Single value - expand to match window size
                    window_data.append([col_values])
            
            # Stack columns to get shape (num_timesteps, num_features)
            features = np.array(window_data, dtype=np.float32).T  # Transpose to (timesteps, features)
            
            # Normalize each feature (standardization)
            for i in range(features.shape[1]):
                col_data = features[:, i]
                col_mean = np.nanmean(col_data)
                col_std = np.nanstd(col_data)
                if col_std > 0:
                    features[:, i] = (col_data - col_mean) / col_std
                else:
                    features[:, i] = col_data - col_mean
            
            # Replace NaN values with 0
            features = np.nan_to_num(features, nan=0.0)
            
            logger.debug(f"Transformed window shape: {features.shape}")
            return features

        except Exception as exc:
            logger.error(f"Transformation failed: {exc}")
            raise

    def fit(self, data_list: List[Dict[str, Any]], column_names: List[str]) -> None:
        """
        Fit transformers on training data.
        Placeholder for future ML pipeline integration.
        """
        # Implement fitting logic here if needed (e.g., StandardScaler)
        pass

# Add any existing code from the file below this class if needed