"""
PyTorch-based LSTM Lap Time Predictor.
Wrapped to match scikit-learn API for easy integration.
"""
import numpy as np
import pandas as pd
import warnings

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    warnings.warn("PyTorch is not available. LSTM models will not work.")


class PyTorchLSTM(nn.Module if TORCH_AVAILABLE else object):
    """Core LSTM Neural Network Architecture."""
    def __init__(self, input_size, hidden_size=64, num_layers=2):
        super(PyTorchLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layer
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True, 
            dropout=0.2 if num_layers > 1 else 0
        )
        
        # Fully connected layer
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x shape: (batch, seq_len, features)
        out, (h_n, c_n) = self.lstm(x)
        
        # We want the output of the last time step
        out = out[:, -1, :] 
        out = self.fc(out)
        return out


class SklearnLSTMWrapper:
    """
    Wrapper class to make the PyTorch LSTM model conform to the
    Scikit-Learn regressor API (`fit`, `predict`, `feature_importances_`).
    """
    def __init__(self, hidden_size=64, num_layers=2, learning_rate=0.005, epochs=15, batch_size=32):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for the LSTM model.")
            
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.feature_importances_ = None

    def fit(self, X, y):
        if isinstance(X, (pd.DataFrame, pd.Series)):
            X = X.values
        if isinstance(y, (pd.DataFrame, pd.Series)):
            y = y.values
            
        # Mock feature importances (equal weights) since LSTM doesn't have it natively
        self.feature_importances_ = np.ones(X.shape[1]) / X.shape[1]

        # Reshape to (batch_size, seq_len, features) -> (batch_size, 1, features)
        X_tensor = torch.tensor(X, dtype=torch.float32).unsqueeze(1)
        y_tensor = torch.tensor(y, dtype=torch.float32).unsqueeze(1)

        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        # Initialize model
        self.model = PyTorchLSTM(
            input_size=X.shape[1], 
            hidden_size=self.hidden_size, 
            num_layers=self.num_layers
        )
        
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

        # Training loop
        self.model.train()
        for epoch in range(self.epochs):
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()

        return self

    def predict(self, X):
        if not self.model:
            raise ValueError("Model has not been trained yet. Call `fit` first.")
            
        if isinstance(X, (pd.DataFrame, pd.Series)):
            X = X.values
            
        X_tensor = torch.tensor(X, dtype=torch.float32).unsqueeze(1)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_tensor)
            
        return outputs.squeeze().numpy()


if __name__ == "__main__":
    if TORCH_AVAILABLE:
        print("Testing LSTM Wrapper...")
        # Generate random mock data
        X_mock = np.random.rand(100, 15)
        y_mock = np.random.rand(100) * 100
        
        # Initialize and train
        wrapper = SklearnLSTMWrapper(epochs=5)
        wrapper.fit(X_mock, y_mock)
        
        # Predict
        preds = wrapper.predict(X_mock)
        print("Predictions shape:", preds.shape)
        print("Predictions sample:", preds[:5])
        print("LSTM Wrapper tests passed successfully.")
    else:
        print("PyTorch not installed, skipping test.")
