import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, Dataset

class SentinelDataset(Dataset):
    """Dataset wrapper for tensors."""
    def __init__(self, x, y):
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
    def __len__(self): return len(self.x)
    def __getitem__(self, i): return self.x[i], self.y[i]

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
            # Pseudo-labeling Strategy
            pseudo_labels = np.linspace(125, 0, len(window_data))
            dataset = SentinelDataset(window_data, pseudo_labels)
            loader = DataLoader(dataset, batch_size=16, shuffle=True)
            
            self.model.train()
            criterion = nn.MSELoss()
            for _ in range(5):
                for bx, by in loader:
                    bx, by = bx.to(self.device), by.to(self.device).unsqueeze(1)
                    self.optimizer.zero_grad()
                    loss = criterion(self.model(bx), by)
                    loss.backward()
                    self.optimizer.step()
            return True
        return False