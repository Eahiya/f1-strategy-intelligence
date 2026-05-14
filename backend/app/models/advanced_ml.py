"""
Advanced ML Models with XGBoost, LightGBM, and feature engineering.
Includes model persistence and cross-validation.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from pathlib import Path
import joblib
import warnings

# Try to import gradient boosting libraries
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    warnings.warn("XGBoost not available, falling back to Random Forest")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    warnings.warn("LightGBM not available")

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


class FeatureEngineer:
    """
    Advanced feature engineering for F1 race data.
    Creates polynomial, interaction, and domain-specific features.
    """
    
    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive feature set for ML models.
        
        Args:
            df: Input DataFrame with raw race data
            
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        
        # 1. Polynomial features for tire age (non-linear degradation)
        df['tire_age_log'] = np.log1p(df['tire_age'])
        df['tire_age_exp'] = np.exp(df['tire_age'] / 10)
        
        # 2. Fuel-related features
        df['fuel_per_lap'] = df['fuel_load'] / (df['total_laps'] - df['lap_number'] + 1)
        df['fuel_burn_rate'] = df['fuel_load'].diff().fillna(0)
        
        # 3. Interaction features
        df['tire_weather'] = df['tire_age'] * df['weather_encoded']
        df['temp_degradation'] = df['track_temperature'] * df['tire_age_squared']
        
        # 4. Racing context features
        df['race_pace'] = df.groupby('race_id')['lap_time'].transform('mean')
        df['pace_deviation'] = df['lap_time'] - df['race_pace']
        
        # 5. Driver performance features
        df['driver_avg_pace'] = df.groupby('driver_id')['lap_time'].transform('mean')
        df['driver_consistency_score'] = df.groupby('driver_id')['lap_time'].transform('std')
        
        # 6. Stint optimization features
        df['stint_optimal'] = (
            (df['tire_compound'] == 'soft') & (df['tire_age'] <= 20) |
            (df['tire_compound'] == 'medium') & (df['tire_age'] <= 35) |
            (df['tire_compound'] == 'hard') & (df['tire_age'] <= 50)
        ).astype(int)
        
        # 7. Track evolution (rubbering in)
        df['track_evolution'] = np.sqrt(df['lap_number']) * 0.02
        
        # 8. Tire degradation acceleration (second derivative)
        df['degradation_accel'] = df.groupby(['race_id', 'driver_id', 'stint_number'])['tire_degradation'].diff().diff().fillna(0)
        
        # 9. Weather impact composite
        df['weather_impact'] = (
            df['weather_encoded'] * 0.5 + 
            (df['track_temperature'] - 35) / 20 * 0.3 +
            df['humidity'] * 0.2
        )
        
        # 10. Pit window indicator
        df['in_pit_window'] = (
            (df['race_progress'] > 0.25) & (df['race_progress'] < 0.75)
        ).astype(int)
        
        return df
    
    @staticmethod
    def get_lap_time_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Get feature matrix and target for lap time prediction."""
        feature_cols = [
            # Core features
            'tire_age', 'tire_age_squared', 'tire_age_log', 'tire_age_exp',
            'fuel_load', 'fuel_effect', 'fuel_per_lap',
            'track_temperature', 'air_temperature',
            'weather_encoded', 'humidity', 'wind_speed',
            
            # Engineered features
            'tire_weather', 'temp_degradation', 'track_evolution',
            'weather_impact', 'stint_progress', 'race_progress',
            'in_pit_window', 'stint_optimal',
            
            # Driver features
            'driver_consistency', 'driver_pace_skill', 'driver_tire_management',
            
            # Context
            'grip_level', 'safety_car_active'
        ]
        
        # Add encoded categorical features
        if 'circuit_encoded' in df.columns:
            feature_cols.append('circuit_encoded')
        if 'tire_compound_encoded' in df.columns:
            feature_cols.append('tire_compound_encoded')
        
        # Filter to available columns
        available_cols = [c for c in feature_cols if c in df.columns]
        
        X = df[available_cols].fillna(0)
        y = df['lap_time']
        
        return X, y
    
    @staticmethod
    def get_degradation_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Get feature matrix and target for tire degradation prediction."""
        feature_cols = [
            'tire_age', 'tire_age_squared', 'tire_age_log',
            'track_temperature', 'weather_encoded',
            'temp_degradation', 'degradation_accel',
            'driver_tire_management', 'stint_progress',
            'weather_impact', 'grip_level'
        ]
        
        if 'tire_compound_encoded' in df.columns:
            feature_cols.append('tire_compound_encoded')
        if 'circuit_encoded' in df.columns:
            feature_cols.append('circuit_encoded')
        
        available_cols = [c for c in feature_cols if c in df.columns]
        
        X = df[available_cols].fillna(0)
        y = df['tire_degradation']
        
        return X, y


class AdvancedLapTimePredictor:
    """
    Advanced lap time predictor with ensemble methods and hyperparameter optimization.
    """
    
    def __init__(self, model_type: str = 'xgboost'):
        """
        Initialize predictor.
        
        Args:
            model_type: 'xgboost', 'lightgbm', 'random_forest', 'gradient_boosting'
        """
        self.model_type = model_type
        self.model = None
        self.feature_engineer = FeatureEngineer()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.metrics = {}
        self.feature_importance = {}
        
    def _create_model(self):
        """Create the ML model based on type."""
        if self.model_type == 'xgboost' and XGBOOST_AVAILABLE:
            return xgb.XGBRegressor(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                reg_alpha=0.1,
                reg_lambda=1.0
            )
        elif self.model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
            return lgb.LGBMRegressor(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                reg_alpha=0.1,
                reg_lambda=1.0,
                verbose=-1
            )
        elif self.model_type == 'gradient_boosting':
            return GradientBoostingRegressor(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )
        else:  # random_forest fallback
            return RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=3,
                random_state=42,
                n_jobs=-1
            )
    
    def train(self, df: pd.DataFrame, cv_folds: int = 5) -> Dict:
        """
        Train the model with cross-validation.
        
        Args:
            df: Training DataFrame
            cv_folds: Number of cross-validation folds
            
        Returns:
            Training metrics dictionary
        """
        # Feature engineering
        df_engineered = self.feature_engineer.create_features(df)
        X, y = self.feature_engineer.get_lap_time_features(df_engineered)
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Create and train model
        self.model = self._create_model()
        self.model.fit(X_train_scaled, y_train)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train,
            cv=KFold(n_splits=cv_folds, shuffle=True, random_state=42),
            scoring='neg_mean_squared_error'
        )
        cv_rmse = np.sqrt(-cv_scores.mean())
        
        # Test set evaluation
        y_pred = self.model.predict(X_test_scaled)
        
        self.metrics = {
            'cv_rmse': cv_rmse,
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'test_mae': mean_absolute_error(y_test, y_pred),
            'test_r2': r2_score(y_test, y_pred),
            'cv_std': np.sqrt(cv_scores.std()),
            'mean_pct_error': np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        }
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = dict(zip(X.columns, self.model.feature_importances_))
        
        self.is_trained = True
        
        return self.metrics
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predict lap times."""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        df_engineered = self.feature_engineer.create_features(df)
        X, _ = self.feature_engineer.get_lap_time_features(df_engineered)
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict(X_scaled)
    
    def save(self, path: str):
        """Save model to disk."""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'metrics': self.metrics,
            'feature_importance': self.feature_importance,
            'is_trained': self.is_trained,
            'model_type': self.model_type
        }, path)
        
    def load(self, path: str):
        """Load model from disk."""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.metrics = data['metrics']
        self.feature_importance = data['feature_importance']
        self.is_trained = data['is_trained']
        self.model_type = data.get('model_type', 'random_forest')


class AdvancedTireDegradationModel:
    """
    Advanced tire degradation model with gradient boosting.
    """
    
    def __init__(self, model_type: str = 'xgboost'):
        self.model_type = model_type
        self.model = None
        self.feature_engineer = FeatureEngineer()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.metrics = {}
        
    def _create_model(self):
        """Create the ML model."""
        if self.model_type == 'xgboost' and XGBOOST_AVAILABLE:
            return xgb.XGBRegressor(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.08,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
            return lgb.LGBMRegressor(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.08,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
        else:
            return RandomForestRegressor(
                n_estimators=150,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
    
    def train(self, df: pd.DataFrame, cv_folds: int = 5) -> Dict:
        """Train the model with cross-validation."""
        df_engineered = self.feature_engineer.create_features(df)
        X, y = self.feature_engineer.get_degradation_features(df_engineered)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model = self._create_model()
        self.model.fit(X_train_scaled, y_train)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train,
            cv=KFold(n_splits=cv_folds, shuffle=True, random_state=42),
            scoring='neg_mean_squared_error'
        )
        
        y_pred = self.model.predict(X_test_scaled)
        
        self.metrics = {
            'cv_rmse': np.sqrt(-cv_scores.mean()),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'test_mae': mean_absolute_error(y_test, y_pred),
            'test_r2': r2_score(y_test, y_pred)
        }
        
        self.is_trained = True
        return self.metrics
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predict tire degradation."""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        df_engineered = self.feature_engineer.create_features(df)
        X, _ = self.feature_engineer.get_degradation_features(df_engineered)
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict(X_scaled)
    
    def save(self, path: str):
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'metrics': self.metrics,
            'is_trained': self.is_trained
        }, path)
    
    def load(self, path: str):
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.metrics = data['metrics']
        self.is_trained = data['is_trained']


class ModelEnsemble:
    """
    Ensemble of multiple models for robust predictions.
    """
    
    def __init__(self, models: List[str] = None):
        """
        Initialize ensemble.
        
        Args:
            models: List of model types to include
        """
        if models is None:
            models = ['xgboost', 'random_forest']
            if LIGHTGBM_AVAILABLE:
                models.append('lightgbm')
        
        self.models = {}
        self.weights = {}
        
        for model_type in models:
            self.models[model_type] = AdvancedLapTimePredictor(model_type)
    
    def train(self, df: pd.DataFrame):
        """Train all models in ensemble."""
        for name, model in self.models.items():
            print(f"Training {name}...")
            metrics = model.train(df)
            # Weight by inverse RMSE (better models get higher weight)
            self.weights[name] = 1.0 / (metrics['test_rmse'] + 0.001)
            print(f"  RMSE: {metrics['test_rmse']:.4f}")
        
        # Normalize weights
        total_weight = sum(self.weights.values())
        self.weights = {k: v/total_weight for k, v in self.weights.items()}
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Weighted ensemble prediction."""
        predictions = []
        weights = []
        
        for name, model in self.models.items():
            if model.is_trained:
                pred = model.predict(df)
                predictions.append(pred)
                weights.append(self.weights[name])
        
        # Weighted average
        predictions = np.array(predictions)
        weights = np.array(weights).reshape(-1, 1)
        
        return np.average(predictions, axis=0, weights=weights.flatten())
    
    def save(self, base_path: str):
        """Save all models."""
        Path(base_path).mkdir(parents=True, exist_ok=True)
        for name, model in self.models.items():
            model.save(f"{base_path}/{name}_model.joblib")
        joblib.dump(self.weights, f"{base_path}/ensemble_weights.joblib")
    
    def load(self, base_path: str):
        """Load all models."""
        for name, model in self.models.items():
            model.load(f"{base_path}/{name}_model.joblib")
        self.weights = joblib.load(f"{base_path}/ensemble_weights.joblib")


# Model persistence utilities
def save_all_models(
    lap_time_model: AdvancedLapTimePredictor,
    degradation_model: AdvancedTireDegradationModel,
    output_dir: str = "ml_models"
):
    """Save all trained models."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    lap_time_model.save(f"{output_dir}/lap_time_model.joblib")
    degradation_model.save(f"{output_dir}/tire_degradation_model.joblib")
    
    print(f"Models saved to {output_dir}/")


def load_all_models(
    input_dir: str = "ml_models"
) -> Tuple[AdvancedLapTimePredictor, AdvancedTireDegradationModel]:
    """Load all trained models."""
    lap_time_model = AdvancedLapTimePredictor()
    lap_time_model.load(f"{input_dir}/lap_time_model.joblib")
    
    degradation_model = AdvancedTireDegradationModel()
    degradation_model.load(f"{input_dir}/tire_degradation_model.joblib")
    
    return lap_time_model, degradation_model


if __name__ == "__main__":
    # Test the advanced ML models
    from app.services.data_generator import load_or_generate_data
    
    print("Loading dataset...")
    df = load_or_generate_data(large=True)
    
    print("\n" + "="*60)
    print("Testing Advanced Lap Time Predictor")
    print("="*60)
    
    # Test each model type
    for model_type in ['random_forest', 'xgboost', 'lightgbm']:
        try:
            print(f"\n{model_type.upper()}:")
            predictor = AdvancedLapTimePredictor(model_type=model_type)
            metrics = predictor.train(df, cv_folds=3)
            
            for metric, value in metrics.items():
                print(f"  {metric}: {value:.4f}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*60)
    print("Testing Tire Degradation Model")
    print("="*60)
    
    deg_model = AdvancedTireDegradationModel(model_type='xgboost')
    metrics = deg_model.train(df, cv_folds=3)
    
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
