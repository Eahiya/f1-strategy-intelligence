"""Tire Degradation Prediction Model using Random Forest."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

from app.core.config import TIRE_COMPOUNDS


class TireDegradationModel:
    """
    Model A: Tire Degradation Predictor
    
    Predicts how much a tire will degrade (lap time increase) based on:
    - Tire compound
    - Tire age (laps on tire)
    - Circuit characteristics
    """
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        self.is_trained = False
        self.metrics = {}
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """
        Train the tire degradation model.
        
        Args:
            X: Features (circuit, tire, tire_age, etc.)
            y: Target (tire degradation in seconds)
            
        Returns:
            Training metrics
        """
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        self.metrics = {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred),
            'mean_absolute_error': np.mean(np.abs(y_test - y_pred))
        }
        
        self.is_trained = True
        
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict tire degradation for given inputs.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Predicted degradation in seconds
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        return self.model.predict(X)
    
    def predict_single(self, circuit_encoded: int, tire_encoded: int, 
                     tire_age: int, tire_age_sq: float = None, 
                     stint_progress: float = None) -> float:
        """
        Predict degradation for a single tire state.
        
        Args:
            circuit_encoded: Encoded circuit ID
            tire_encoded: Encoded tire compound ID
            tire_age: Number of laps on tire
            tire_age_sq: Tire age squared (optional)
            stint_progress: Progress through stint (optional)
            
        Returns:
            Predicted degradation in seconds
        """
        if tire_age_sq is None:
            tire_age_sq = tire_age ** 2
        if stint_progress is None:
            stint_progress = 0.5
            
        features = np.array([[circuit_encoded, tire_encoded, tire_age, 
                            tire_age_sq, stint_progress]])
        
        return self.model.predict(features)[0]
    
    def get_degradation_curve(self, circuit: str, tire: str, max_laps: int = 40) -> list:
        """
        Generate a full degradation curve for a tire stint.
        
        Args:
            circuit: Circuit name (must be encoded externally)
            tire: Tire compound (must be encoded externally)
            max_laps: Maximum laps to simulate
            
        Returns:
            List of degradation values per lap
        """
        curve = []
        
        for lap in range(1, max_laps + 1):
            # These need to be provided encoded
            # This is a simplified version - actual usage requires encoded values
            degradation = 0.04 * lap + 0.001 * lap ** 2  # Simplified formula
            
            if tire == "soft":
                degradation *= 1.5
            elif tire == "hard":
                degradation *= 0.6
                
            curve.append(round(degradation, 3))
        
        return curve
    
    def should_pit(self, current_degradation: float, tire_age: int, 
                   tire: str, circuit: str) -> bool:
        """
        Rule-based decision on whether to pit based on degradation.
        
        Args:
            current_degradation: Current degradation in seconds
            tire_age: Laps on current tire
            tire: Tire compound
            circuit: Circuit name
            
        Returns:
            True if should pit, False otherwise
        """
        from app.core.config import STRATEGY_CONFIG
        
        # Hard threshold - degradation too high
        if current_degradation > STRATEGY_CONFIG["degradation_threshold"]:
            return True
        
        # Tire age threshold
        optimal_laps = TIRE_COMPOUNDS[tire]["optimal_laps"]
        if tire_age >= optimal_laps * 1.2:  # 20% buffer
            return True
        
        # Absolute max stint length
        if tire_age >= STRATEGY_CONFIG["max_stint_length"]:
            return True
        
        return False
    
    def save(self, path: str):
        """Save model to disk."""
        joblib.dump({
            'model': self.model,
            'metrics': self.metrics,
            'is_trained': self.is_trained
        }, path)
    
    def load(self, path: str):
        """Load model from disk."""
        data = joblib.load(path)
        self.model = data['model']
        self.metrics = data['metrics']
        self.is_trained = data['is_trained']


if __name__ == "__main__":
    # Test the model
    from app.services.data_generator import generate_dataset
    from app.services.data_pipeline import F1DataPipeline
    
    # Generate data
    df = generate_dataset(num_samples=1000)
    
    # Prepare data
    pipeline = F1DataPipeline()
    (_, y_lt), (X_deg, y_deg) = pipeline.prepare_for_training(df)
    
    # Train model
    model = TireDegradationModel()
    metrics = model.train(X_deg, y_deg)
    
    print("Tire Degradation Model Training Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # Test prediction
    sample = X_deg.iloc[:5]
    predictions = model.predict(sample)
    print(f"\nSample predictions: {predictions}")
