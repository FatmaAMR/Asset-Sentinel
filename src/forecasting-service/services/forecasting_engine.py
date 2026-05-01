import os
import torch
import torch.optim as optim
from models.sentinel_nn import SentinelTransformer
from .adaptation_logic import AutonomousSentinel

class ForecastingEngine:
    def __init__(self, base_weights_path, assets_dir="src/forecasting-service/assets/"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.base_weights = base_weights_path
        self.assets_dir = assets_dir
        self.type_models = {}

    def _get_model_instance(self, machine_type, input_dim):
        """Loads type-specific weights or falls back to base weights."""
        if machine_type not in self.type_models:
            model = SentinelTransformer(input_dim=input_dim, seq_len=64).to(self.device)
            
            type_weights_path = os.path.join(self.assets_dir, f"{machine_type}.pth")
            load_path = type_weights_path if os.path.exists(type_weights_path) else self.base_weights
            
            checkpoint = torch.load(load_path, map_location=self.device)
            # Handle both formats: OrderedDict (direct state_dict) and wrapped format
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            else:
                # Checkpoint is the state_dict directly
                model.load_state_dict(checkpoint)
            self.type_models[machine_type] = model
            
        return self.type_models[machine_type]

    def run_inference(self, machine_id, machine_type, window_data):
        """
        Complete pipeline execution:
        1. Model Routing
        2. OOD Detection
        3. Autonomous Adaptation
        4. RUL Prediction
        """
        # input_dim derived from the second dimension of the window (channels)
        input_dim = window_data.shape[2] 
        model = self._get_model_instance(machine_type, input_dim)
        
        optimizer = optim.Adam(model.parameters(), lr=1e-5)
        adaptor = AutonomousSentinel(model, optimizer, self.device)

        # Monitor and Adapt
        if adaptor.check_ood(window_data):
            adaptor.adapt_to_type(window_data, machine_type)
            # Save updated weights for this specific machine type
            save_path = os.path.join(self.assets_dir, f"{machine_type}.pth")
            torch.save({'model_state_dict': model.state_dict()}, save_path)
            print(f">> Synchronized weights saved for {machine_type}")

        # Final Inference
        model.eval()
        with torch.no_grad():
            input_tensor = torch.tensor(window_data, dtype=torch.float32).to(self.device)
            rul_prediction = model(input_tensor).item()
            
        return rul_prediction
    



    # src/forecasting-service/services/adaptation_logic.py
def check_ood(self, window_data):
    return False  # Force normal inference for testing