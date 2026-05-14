"""Lap Time Prediction Model using Random Forest Regression."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib

from app.core.config import CIRCUITS, TIRE_COMPOUNDS


class LapTimePredictor:
    """
    Model B: Lap Time Predictor
    
    Predicts lap time based on:
    - Tire age and compound
    - Circuit characteristics
    - Fuel load
    - Lap number
    """
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            min_samples_split=3,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        self.is_trained = False
        self.metrics = {}
        self.feature_importance = None
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """
        Train the lap time prediction model.
        
        Args:
            X: Features (tire_age, circuit, fuel, etc.)
            y: Target (lap time in seconds)
            
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
            'mae': mean_absolute_error(y_test, y_pred),
            'r2': r2_score(y_test, y_pred),
            'mean_pct_error': np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        }
        
        # Feature importance
        self.feature_importance = dict(zip(
            X.columns, 
            self.model.feature_importances_
        ))
        
        self.is_trained = True
        
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict lap times for given inputs.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Predicted lap times in seconds
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        return self.model.predict(X)
    
    def predict_lap(self, circuit_encoded: int, tire_encoded: int,
                   lap_number: int, tire_age: int, tire_age_sq: float,
                   fuel_load: float, fuel_effect: float, 
                   stint_progress: float, total_laps: int) -> float:
        """
        Predict a single lap time.
        
        Args:
            Various encoded features
            
        Returns:
            Predicted lap time in seconds
        """
        features = np.array([[circuit_encoded, tire_encoded, lap_number,
                            tire_age, tire_age_sq, fuel_load, fuel_effect,
                            stint_progress, total_laps]])
        
        return self.model.predict(features)[0]
    
    def simulate_stint(self, circuit: str, tire: str, start_lap: int,
                       stint_length: int, initial_fuel: float,
                       encoded_values: dict = None) -> list:
        """
        Simulate a full stint lap by lap.
        
        Args:
            circuit: Circuit name
            tire: Tire compound
            start_lap: Starting lap number
            stint_length: Number of laps in stint
            initial_fuel: Starting fuel load
            encoded_values: Pre-computed encodings (optional)
            
        Returns:
            List of predicted lap times
        """
        if encoded_values is None:
            # Use simplified formula-based prediction
            base_time = CIRCUITS[circuit]["base_lap_time"]
            tire_pace = TIRE_COMPOUNDS[tire]["base_pace"]
            deg_rate = TIRE_COMPOUNDS[tire]["degradation_rate"]
            
            lap_times = []
            for i in range(stint_length):
                # lap = start_lap + i
                tire_age = i + 1
                
                # Base lap time
                time = base_time + tire_pace
                
                # Tire degradation
                degradation = deg_rate * (tire_age ** 1.5)
                time += degradation
                
                # Fuel effect
                fuel_remaining = initial_fuel * (1 - i / stint_length)
                time += fuel_remaining * 0.08
                
                # Random variation
                noise = np.random.normal(0, 0.2)
                time += noise
                
                lap_times.append(round(time, 3))
            
            return lap_times
        else:
            # Use ML model for prediction
            lap_times = []
            for i in range(stint_length):
                features = self._create_features(
                    circuit, tire, start_lap + i, i + 1,
                    initial_fuel, stint_length, encoded_values
                )
                time = self.predict(features)[0]
                lap_times.append(round(time, 3))
            
            return lap_times
    
    def _create_features(self, circuit: str, tire: str, lap: int,
                        tire_age: int, fuel: float, stint_len: int,
                        encoded: dict) -> pd.DataFrame:
        """Create feature DataFrame for single prediction."""
        data = {
            'circuit_encoded': [encoded['circuit_encoded']],
            'tire_compound_encoded': [encoded['tire_encoded']],
            'lap_number': [lap],
            'tire_age': [tire_age],
            'tire_age_sq': [tire_age ** 2],
            'fuel_load': [fuel * (1 - tire_age / stint_len)],
            'fuel_effect': [fuel * 0.08 * (1 - tire_age / stint_len)],
            'stint_progress': [tire_age / stint_len],
            'total_laps': [CIRCUITS[circuit]['laps']]
        }
        return pd.DataFrame(data)
    
    def get_feature_importance(self) -> dict:
        """Return feature importance as dictionary."""
        return self.feature_importance or {}
    
    def save(self, path: str):
        """Save model to disk."""
        joblib.dump({
            'model': self.model,
            'metrics': self.metrics,
            'feature_importance': self.feature_importance,
            'is_trained': self.is_trained
        }, path)
    
    def load(self, path: str):
        """Load model from disk."""
        data = joblib.load(path)
        self.model = data['model']
        self.metrics = data['metrics']
        self.feature_importance = data['feature_importance']
        self.is_trained = data['is_trained']


if __name__ == "__main__":
    # Test the model
    from app.services.data_generator import generate_dataset
    from app.services.data_pipeline import F1DataPipeline
    
    # Generate data
    df = generate_dataset(num_samples=1000)
    
    # Prepare data
    pipeline = F1DataPipeline()
    (X_lt, y_lt), _ = pipeline.prepare_for_training(df)
    
    # Train model
    model = LapTimePredictor()
    metrics = model.train(X_lt, y_lt)
    
    print("Lap Time Predictor Training Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\nFeature Importance:")
    for feature, importance in model.get_feature_importance().items():
        print(f"  {feature}: {importance:.4f}")
