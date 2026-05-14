"""Data pipeline for cleaning and preprocessing F1 data."""
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


class F1DataPipeline:
    """Pipeline for F1 data processing and feature engineering."""
    
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.fitted = False
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean raw F1 data:
        - Handle missing values
        - Remove outliers
        - Normalize lap times per circuit
        """
        df = df.copy()
        
        # Handle missing values
        df = df.dropna(subset=['lap_time', 'circuit', 'tire_compound'])
        
        # Fill missing numeric values with median
        numeric_cols = ['lap_number', 'tire_age', 'fuel_load']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
        
        # Remove unrealistic lap times (outliers)
        df = df.groupby('circuit', group_keys=False).apply(
            lambda x: x[(x['lap_time'] >= x['lap_time'].quantile(0.01)) & 
                       (x['lap_time'] <= x['lap_time'].quantile(0.99))]
        ).reset_index(drop=True)
        
        # Normalize lap times per circuit (z-score)
        df['lap_time_normalized'] = df.groupby('circuit')['lap_time'].transform(
            lambda x: (x - x.mean()) / x.std()
        )
        
        return df
    
    def encode_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Encode categorical features:
        - Label encode circuit names
        - Label encode tire compounds
        """
        df = df.copy()
        categorical_cols = ['circuit', 'tire_compound']
        
        for col in categorical_cols:
            if col not in df.columns:
                continue
                
            if fit:
                self.label_encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            else:
                if col in self.label_encoders:
                    df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
        
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create additional features for ML models:
        - Tire degradation rate
        - Stint progress
        - Lap time delta from base
        """
        df = df.copy()
        
        # Tire degradation rate (change from previous lap)
        df['degradation_rate'] = df.groupby(['circuit', 'tire_compound'])['lap_time'].diff()
        df['degradation_rate'] = df['degradation_rate'].fillna(0)
        
        # Stint progress (percentage through stint)
        if 'stint_length' in df.columns:
            df['stint_progress'] = df['lap_number'] / df['stint_length']
        else:
            df['stint_progress'] = 0.5  # default
        
        # Tire age squared (degradation is non-linear)
        df['tire_age_sq'] = df['tire_age'] ** 2
        
        # Fuel effect (linear with lap number)
        df['fuel_effect'] = df['fuel_load'] * (1 - df['lap_number'] / df['total_laps'])
        
        return df
    
    def prepare_for_training(self, df: pd.DataFrame) -> tuple:
        """
        Full pipeline: clean, encode, engineer features.
        Returns X, y for lap time prediction and X, y for degradation prediction.
        """
        df = self.clean_data(df)
        df = self.encode_features(df, fit=True)
        df = self.engineer_features(df)
        
        # Features for lap time prediction
        lap_time_features = [
            'circuit_encoded', 'tire_compound_encoded', 'lap_number',
            'tire_age', 'tire_age_sq', 'fuel_load', 'fuel_effect',
            'stint_progress', 'total_laps'
        ]
        
        # Features for degradation prediction
        degradation_features = [
            'circuit_encoded', 'tire_compound_encoded', 'tire_age',
            'tire_age_sq', 'stint_progress'
        ]
        
        # Ensure all features exist
        lap_time_features = [f for f in lap_time_features if f in df.columns]
        degradation_features = [f for f in degradation_features if f in df.columns]
        
        X_lap_time = df[lap_time_features]
        y_lap_time = df['lap_time']
        
        X_degradation = df[degradation_features]
        y_degradation = df['tire_degradation'] if 'tire_degradation' in df.columns else df['degradation_rate']
        
        self.fitted = True
        
        return (X_lap_time, y_lap_time), (X_degradation, y_degradation)
    
    def transform_single(self, circuit: str, tire: str, lap: int, 
                        tire_age: int, fuel: float, total_laps: int) -> pd.DataFrame:
        """Transform a single prediction input."""
        data = {
            'circuit': [circuit],
            'tire_compound': [tire],
            'lap_number': [lap],
            'tire_age': [tire_age],
            'fuel_load': [fuel],
            'total_laps': [total_laps],
            'stint_length': [total_laps],  # Assume full race
            'lap_time': [0]  # Placeholder
        }
        
        df = pd.DataFrame(data)
        df = self.encode_features(df, fit=False)
        df = self.engineer_features(df)
        
        return df


def load_and_prepare_data(data_path: str = "data/f1_race_data.csv") -> tuple:
    """Convenience function to load and prepare data."""
    df = pd.read_csv(data_path)
    pipeline = F1DataPipeline()
    return pipeline.prepare_for_training(df), pipeline
