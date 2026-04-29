import torch
import torch.nn as nn

class SentinelTransformer(nn.Module):
    """
    Core AI Architecture for Sentinel AI.
    Specialized Time-Series Transformer for RUL Prediction.
    """
    def __init__(self, input_dim, seq_len, num_heads=4, num_layers=3, d_model=64):
        super(SentinelTransformer, self).__init__()
        
        self.input_projection = nn.Linear(input_dim, d_model)
        self.pos_embedding = nn.Parameter(torch.zeros(1, seq_len, d_model))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=num_heads,
            dim_feedforward=d_model*4,
            dropout=0.1,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.regressor = nn.Sequential(
            nn.Flatten(),
            nn.Linear(d_model * seq_len, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1)
        )

    def forward(self, x):
        x = self.input_projection(x)
        x = x + self.pos_embedding
        x = self.transformer_encoder(x)
        return self.regressor(x)