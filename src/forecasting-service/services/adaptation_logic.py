import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, Dataset

class SentinelDataset(Dataset):
    def __init__(self, x, y):
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
    def __len__(self): return len(self.x)
    def __getitem__(self, i): return self.x[i], self.y[i]

class AutonomousSentinel:
    def __init__(self, model, optimizer, device='cuda'):
        self.model = model
        self.optimizer = optimizer
        self.device = device

    def check_ood(self, window_data, threshold=0.15):
        """
        Detect Out-of-Distribution data using Latent Signal Variance.
        Toggle the hardcoded return for manual testing of the adaptation flow.
        """
        self.model.eval()
        with torch.no_grad():
            input_tensor = torch.tensor(window_data, dtype=torch.float32).to(self.device)
            preds = self.model(input_tensor).cpu().numpy().flatten()
        
        variance_score = np.var(preds)
        is_ood_detected = variance_score > threshold
        
        # Manual Override for Testing: Change to True to force adaptation
        # return True 
        return is_ood_detected

    def pseudo_labeling_strategy(self, unlabeled_data, max_rul=125):
        """Generate linear decay labels for unlabeled streams."""
        num_samples = len(unlabeled_data)
        return np.linspace(max_rul, 0, num_samples)

    def adapt_to_type(self, window_data, machine_type):
        """Perform Fine-tuning on type-specific data using pseudo-labels."""
        print(f">> Initiating Autonomous Adaptation for Type: {machine_type}")
        
        generated_labels = self.pseudo_labeling_strategy(window_data)
        adaptation_set = SentinelDataset(window_data, generated_labels)
        adaptation_loader = DataLoader(adaptation_set, batch_size=16, shuffle=True)

        self.model.train()
        criterion = nn.MSELoss()
        
        for epoch in range(5):
            epoch_loss = 0
            for batch_x, batch_y in adaptation_loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device).unsqueeze(1)
                self.optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()
                epoch_loss += loss.item()
            
            print(f"Adaptation Epoch {epoch+1} | Loss: {epoch_loss/len(adaptation_loader):.4f}")
        
        return True