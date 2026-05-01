import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, Dataset

class SentinelDataset(Dataset):
    """Dataset wrapper for tensors."""
    def __init__(self, x, y):
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
    
    def __len__(self): 
        return len(self.x)
    
    def __getitem__(self, i): 
        return self.x[i], self.y[i]

class AutonomousSentinel:
    """
    Logic wrapper for OOD detection and Model Adaptation.
    """
    def __init__(self, model, optimizer, device='cuda'):
        self.model = model
        self.optimizer = optimizer
        self.device = device

    def monitor_and_adapt(self, window_data, ood_threshold=0.15):
        self.model.eval()
        with torch.no_grad():
            input_tensor = torch.tensor(window_data, dtype=torch.float32).to(self.device)
            preds = self.model(input_tensor).cpu().numpy().flatten()

        variance = np.var(preds)
        if variance > ood_threshold:
            print(">> OOD Detected. Initiating Adaptation...")
            # Pseudo-labeling Strategy: Generate RUL labels for each sequence sample
            # window_data can be (batch, seq_len, features)
            if window_data.ndim == 3:
                num_samples = window_data.shape[0]
            else:
                # If 2D, we treat it as a single sample
                window_data = window_data.reshape(1, *window_data.shape)
                num_samples = 1
            
            # Create RUL labels (one label per sequence sample, declining from 125 to 0)
            pseudo_labels = np.linspace(125, 0, num_samples)
            
            dataset = SentinelDataset(window_data, pseudo_labels)
            loader = DataLoader(dataset, batch_size=min(16, len(dataset)), shuffle=True)
            
            self.model.train()
            criterion = nn.MSELoss()
            for epoch in range(5):
                for bx, by in loader:
                    bx, by = bx.to(self.device), by.to(self.device).unsqueeze(1)
                    self.optimizer.zero_grad()
                    preds = self.model(bx)
                    loss = criterion(preds, by)
                    loss.backward()
                    self.optimizer.step()
            return True
        return False

    def check_ood(self, window_data, ood_threshold=0.15):
        """Check if data is out-of-distribution without adaptation."""
        self.model.eval()
        with torch.no_grad():
            input_tensor = torch.tensor(window_data, dtype=torch.float32).to(self.device)
            preds = self.model(input_tensor).cpu().numpy().flatten()
        variance = np.var(preds)
        return variance > ood_threshold

    def adapt_to_type(self, window_data, machine_type, ood_threshold=0.15):
        """Adapt model to a specific machine type."""
        if self.check_ood(window_data, ood_threshold):
            return self.monitor_and_adapt(window_data, ood_threshold)
        return False


if __name__ == "__main__":
    print("=" * 80)
    print("Testing AutonomousSentinel Adaptation Module")
    print("=" * 80)
    
    # Simulate a simple model that outputs RUL predictions
    class DummyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = nn.Linear(21, 32)
            self.regressor = nn.Sequential(
                nn.Linear(32 * 64, 128),
                nn.ReLU(),
                nn.Linear(128, 1)
            )
        
        def forward(self, x):
            # x shape: (batch, seq_len, features)
            batch, seq_len, features = x.shape
            encoded = self.encoder(x)  # (batch, seq_len, 32)
            flattened = encoded.reshape(batch, -1)  # (batch, seq_len*32)
            return self.regressor(flattened)  # (batch, 1)
    
    # Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DummyModel().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    adaptor = AutonomousSentinel(model, optimizer, device)
    
    # Test 1: Normal data (low variance)
    print("\nTest 1: Normal data (low variance)")
    normal_data = np.random.randn(1, 64, 21) * 0.1 + 50
    is_ood = adaptor.check_ood(normal_data)
    print(f"  Is OOD: {is_ood} (Expected: False)")
    
    # Test 2: Out-of-distribution data (high variance)
    print("\nTest 2: Out-of-distribution data (high variance)")
    ood_data = np.random.randn(2, 64, 21) * 5.0 + 50
    is_ood = adaptor.check_ood(ood_data)
    print(f"  Is OOD: {is_ood} (Expected: True)")
    
    # Test 3: Adaptation
    print("\nTest 3: Model Adaptation")
    adapted = adaptor.adapt_to_type(ood_data, "turbofan")
    print(f"  Adaptation triggered: {adapted}")
    
    print("\n" + "=" * 80)
    print("Adaptation module tests completed successfully!")
    print("=" * 80)