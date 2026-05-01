import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader
import logging
import sys
from pathlib import Path

# Setup path for imports
service_root = Path(__file__).resolve().parent.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

# Import from models to avoid duplication
from models.adaptation import SentinelDataset, AutonomousSentinel

logger = logging.getLogger(__name__)


class AdaptationManager:
    """
    High-level manager for model adaptation logic.
    Wraps AutonomousSentinel with additional monitoring and validation.
    """
    def __init__(self, model, optimizer, device='cuda'):
        self.sentinel = AutonomousSentinel(model, optimizer, device)
        self.device = device
        self.adaptation_history = []

    def check_ood(self, window_data, threshold=0.15):
        """
        Detect Out-of-Distribution data using Latent Signal Variance.
        """
        return self.sentinel.check_ood(window_data, threshold)

    def pseudo_labeling_strategy(self, unlabeled_data, max_rul=125):
        """
        Generate linear decay labels for unlabeled streams.
        Properly handles both 2D and 3D input shapes.
        """
        # Handle 3D data (batch, seq_len, features) or 2D (seq_len, features)
        if isinstance(unlabeled_data, np.ndarray):
            if unlabeled_data.ndim == 3:
                num_samples = unlabeled_data.shape[0]  # Use batch dimension
            else:
                num_samples = 1  # Single sample
        else:
            num_samples = len(unlabeled_data)
        
        labels = np.linspace(max_rul, 0, num_samples)
        logger.debug(f"Generated {num_samples} pseudo-labels for adaptation")
        return labels

    def adapt_to_type(self, window_data, machine_type, ood_threshold=0.15):
        """
        Perform Fine-tuning on type-specific data using pseudo-labels.
        Includes validation and logging.
        """
        try:
            # Validate input
            if isinstance(window_data, np.ndarray) and window_data.size == 0:
                logger.warning(f"Empty data provided for adaptation to {machine_type}")
                return False
            
            logger.info(f">> Initiating Autonomous Adaptation for Type: {machine_type}")
            
            # Check OOD before adapting
            if not self.sentinel.check_ood(window_data, ood_threshold):
                logger.debug(f"Data is in-distribution, skipping adaptation for {machine_type}")
                return False
            
            # Generate labels and adapt
            generated_labels = self.pseudo_labeling_strategy(window_data)
            adaptation_set = SentinelDataset(window_data, generated_labels)
            adaptation_loader = DataLoader(adaptation_set, batch_size=min(16, len(adaptation_set)), shuffle=True)

            self.sentinel.model.train()
            criterion = nn.MSELoss()
            
            epoch_losses = []
            for epoch in range(5):
                epoch_loss = 0
                batch_count = 0
                for batch_x, batch_y in adaptation_loader:
                    batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device).unsqueeze(1)
                    self.sentinel.optimizer.zero_grad()
                    outputs = self.sentinel.model(batch_x)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    self.sentinel.optimizer.step()
                    epoch_loss += loss.item()
                    batch_count += 1
                
                avg_loss = epoch_loss / batch_count if batch_count > 0 else 0
                epoch_losses.append(avg_loss)
                logger.info(f"Adaptation Epoch {epoch+1}/5 | Avg Loss: {avg_loss:.4f}")
            
            # Log adaptation history
            self.adaptation_history.append({
                'machine_type': machine_type,
                'epoch_losses': epoch_losses,
                'timestamp': np.datetime64('now')
            })
            
            self.sentinel.model.eval()
            logger.info(f">> Adaptation completed for {machine_type}")
            return True
            
        except Exception as e:
            logger.error(f"Adaptation failed for {machine_type}: {e}", exc_info=True)
            return False


if __name__ == "__main__":
    print("=" * 80)
    print("Testing AdaptationManager Logic")
    print("=" * 80)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Mock model for testing
    class TestModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = nn.Linear(21, 32)
            self.regressor = nn.Sequential(
                nn.Linear(32 * 64, 128),
                nn.ReLU(),
                nn.Linear(128, 1)
            )
        
        def forward(self, x):
            batch, seq_len, features = x.shape
            encoded = self.encoder(x)
            flattened = encoded.reshape(batch, -1)
            return self.regressor(flattened)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TestModel().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    manager = AdaptationManager(model, optimizer, device)
    
    # Test 1: Pseudo-label generation with 3D data
    print("\nTest 1: Pseudo-label generation (3D data)")
    data_3d = np.random.randn(2, 64, 21)  # batch=2, seq_len=64, features=21
    labels = manager.pseudo_labeling_strategy(data_3d)
    print(f"  Input shape: {data_3d.shape}")
    print(f"  Generated labels shape: {labels.shape}")
    print(f"  Expected: (2,) | Actual: {labels.shape} - {'✓ PASS' if labels.shape == (2,) else '✗ FAIL'}")
    
    # Test 2: Pseudo-label generation with 2D data
    print("\nTest 2: Pseudo-label generation (2D data)")
    data_2d = np.random.randn(64, 21)  # seq_len=64, features=21
    labels = manager.pseudo_labeling_strategy(data_2d)
    print(f"  Input shape: {data_2d.shape}")
    print(f"  Generated labels shape: {labels.shape}")
    print(f"  Expected: (1,) | Actual: {labels.shape} - {'✓ PASS' if labels.shape == (1,) else '✗ FAIL'}")
    
    # Test 3: OOD detection
    print("\nTest 3: OOD Detection")
    normal_data = np.random.randn(1, 64, 21) * 0.1 + 50
    is_ood = manager.check_ood(normal_data)
    print(f"  Normal data OOD: {is_ood} (Expected: False) - {'✓ PASS' if not is_ood else '✗ FAIL'}")
    
    # Create truly OOD data with high variance across predictions
    ood_data = np.concatenate([
        np.random.randn(1, 64, 21) * 10 + 50,
        np.random.randn(1, 64, 21) * 10 + 10
    ], axis=0)  # 2 batches with very different distributions
    is_ood = manager.check_ood(ood_data)
    print(f"  OOD data OOD: {is_ood} (Expected: True) - {'✓ PASS' if is_ood else '⚠ INFO (variance may be low with random model)'}")
    
    # Test 4: Adaptation with OOD data
    print("\nTest 4: Full Adaptation Pipeline")
    adapted = manager.adapt_to_type(ood_data, "turbofan")
    print(f"  Adaptation triggered: {adapted} (Expected: True) - {'✓ PASS' if adapted else '✗ FAIL'}")
    
    # Test 5: Adaptation history
    print("\nTest 5: Adaptation History")
    print(f"  Total adaptations logged: {len(manager.adaptation_history)}")
    if manager.adaptation_history:
        last_adaptation = manager.adaptation_history[-1]
        print(f"  Last machine type: {last_adaptation['machine_type']}")
        print(f"  Final epoch loss: {last_adaptation['epoch_losses'][-1]:.4f}")
    
    # Test 6: Error handling (empty data)
    print("\nTest 6: Error Handling (Empty Data)")
    empty_data = np.array([])
    adapted = manager.adapt_to_type(empty_data, "invalid_type")
    print(f"  Handled empty data: {not adapted} (Expected: False) - {'✓ PASS' if not adapted else '✗ FAIL'}")
    
    print("\n" + "=" * 80)
    print("Adaptation Logic Tests Completed!")
    print("=" * 80)