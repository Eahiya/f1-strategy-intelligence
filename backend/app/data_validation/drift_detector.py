"""
F1 Strategy Platform v6.0 - Data Drift Detection
Monitors for data distribution changes that could affect model performance.
"""
import numpy as np
import pandas as pd
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
from scipy import stats


@dataclass
class DriftReport:
    """Report of detected data drift."""
    feature: str
    drift_detected: bool
    drift_score: float  # 0-1, higher = more drift
    method: str
    baseline_stats: Dict
    current_stats: Dict
    timestamp: str
    recommendation: str


class DataDriftDetector:
    """
    Detects when incoming data differs from training data distribution.
    
    Methods:
    - Statistical tests (KS test, Chi-square)
    - Population Stability Index (PSI)
    - Wasserstein distance
    """
    
    def __init__(self, psi_threshold: float = 0.2, ks_threshold: float = 0.05):
        """
        Initialize drift detector.
        
        Args:
            psi_threshold: PSI threshold for drift detection (0.2 = 20%)
            ks_threshold: KS test p-value threshold
        """
        self.psi_threshold = psi_threshold
        self.ks_threshold = ks_threshold
        self.baseline_distributions: Dict[str, np.ndarray] = {}
        self.feature_names: List[str] = []
    
    def fit_baseline(self, data: pd.DataFrame, features: List[str] = None):
        """
        Fit baseline distribution from training data.
        
        Args:
            data: Training DataFrame
            features: Features to monitor (all numeric if None)
        """
        if features is None:
            features = data.select_dtypes(include=[np.number]).columns.tolist()
        
        self.feature_names = features
        
        for feature in features:
            if feature in data.columns:
                self.baseline_distributions[feature] = data[feature].dropna().values
    
    def detect_drift(self, new_data: pd.DataFrame) -> List[DriftReport]:
        """
        Detect drift in new data compared to baseline.
        
        Args:
            new_data: New data to check
        
        Returns:
            List of DriftReport objects
        """
        reports = []
        
        for feature in self.feature_names:
            if feature not in new_data.columns:
                continue
            
            if feature not in self.baseline_distributions:
                continue
            
            baseline = self.baseline_distributions[feature]
            current = new_data[feature].dropna().values
            
            if len(current) == 0:
                continue
            
            # Calculate PSI
            psi_score = self._calculate_psi(baseline, current)
            
            # KS test
            ks_stat, ks_pvalue = stats.ks_2samp(baseline, current)
            
            # Determine drift
            drift_detected = psi_score > self.psi_threshold or ks_pvalue < self.ks_threshold
            
            # Use PSI as primary score
            drift_score = psi_score
            
            # Generate recommendation
            if drift_detected:
                if psi_score > 0.3:
                    recommendation = f"CRITICAL: Retrain model for {feature}"
                elif psi_score > 0.2:
                    recommendation = f"WARNING: Monitor {feature} closely"
                else:
                    recommendation = f"CAUTION: Minor drift in {feature}"
            else:
                recommendation = "No action needed"
            
            report = DriftReport(
                feature=feature,
                drift_detected=drift_detected,
                drift_score=drift_score,
                method="PSI + KS",
                baseline_stats={
                    "mean": float(np.mean(baseline)),
                    "std": float(np.std(baseline)),
                    "min": float(np.min(baseline)),
                    "max": float(np.max(baseline))
                },
                current_stats={
                    "mean": float(np.mean(current)),
                    "std": float(np.std(current)),
                    "min": float(np.min(current)),
                    "max": float(np.max(current))
                },
                timestamp=datetime.now().isoformat(),
                recommendation=recommendation
            )
            
            reports.append(report)
        
        return reports
    
    def _calculate_psi(self, baseline: np.ndarray, current: np.ndarray, 
                       bins: int = 10) -> float:
        """
        Calculate Population Stability Index.
        
        PSI = sum((%Actual - %Expected) * ln(%Actual / %Expected))
        
        Interpretation:
        - PSI < 0.1: No significant change
        - 0.1 ≤ PSI < 0.2: Moderate change
        - PSI ≥ 0.2: Significant change
        """
        # Create bins based on baseline
        min_val = min(baseline.min(), current.min())
        max_val = max(baseline.max(), current.max())
        bin_edges = np.linspace(min_val, max_val, bins + 1)
        
        # Calculate percentages
        baseline_counts, _ = np.histogram(baseline, bins=bin_edges)
        current_counts, _ = np.histogram(current, bins=bin_edges)
        
        # Convert to percentages
        baseline_pct = baseline_counts / len(baseline)
        current_pct = current_counts / len(current)
        
        # Add small constant to avoid division by zero
        baseline_pct = np.maximum(baseline_pct, 0.0001)
        current_pct = np.maximum(current_pct, 0.0001)
        
        # Calculate PSI
        psi_values = (current_pct - baseline_pct) * np.log(current_pct / baseline_pct)
        psi = np.sum(psi_values)
        
        return float(psi)
    
    def get_drift_summary(self, reports: List[DriftReport]) -> Dict:
        """Get summary of drift detection results."""
        if not reports:
            return {
                "total_features": 0,
                "drift_detected": False,
                "features_with_drift": [],
                "max_drift_score": 0,
                "overall_status": "no_data"
            }
        
        drift_features = [r.feature for r in reports if r.drift_detected]
        max_score = max(r.drift_score for r in reports)
        
        # Determine overall status
        if max_score > 0.3:
            status = "critical"
        elif max_score > 0.2:
            status = "warning"
        elif len(drift_features) > 0:
            status = "caution"
        else:
            status = "healthy"
        
        return {
            "total_features": len(reports),
            "drift_detected": len(drift_features) > 0,
            "features_with_drift": drift_features,
            "drift_count": len(drift_features),
            "max_drift_score": max_score,
            "overall_status": status,
            "recommendation": "Retrain models" if status == "critical" else 
                            "Monitor closely" if status == "warning" else 
                            "Continue monitoring"
        }


if __name__ == "__main__":
    # Test drift detection
    print("Testing Data Drift Detector")
    print("=" * 60)
    
    # Create baseline data
    np.random.seed(42)
    baseline_data = pd.DataFrame({
        'lap_time': np.random.normal(85, 5, 1000),
        'tire_age': np.random.uniform(0, 30, 1000),
        'fuel_load': np.random.uniform(20, 50, 1000)
    })
    
    detector = DataDriftDetector()
    detector.fit_baseline(baseline_data)
    
    # Test 1: No drift (similar distribution)
    similar_data = pd.DataFrame({
        'lap_time': np.random.normal(86, 5, 100),  # Slightly shifted
        'tire_age': np.random.uniform(0, 30, 100),
        'fuel_load': np.random.uniform(20, 50, 100)
    })
    
    reports = detector.detect_drift(similar_data)
    summary = detector.get_drift_summary(reports)
    print(f"Test 1 (No major drift): {summary['overall_status']}")
    
    # Test 2: Significant drift
    drifted_data = pd.DataFrame({
        'lap_time': np.random.normal(95, 8, 100),  # Major shift
        'tire_age': np.random.uniform(0, 50, 100),  # Different range
        'fuel_load': np.random.uniform(10, 60, 100)
    })
    
    reports = detector.detect_drift(drifted_data)
    summary = detector.get_drift_summary(reports)
    print(f"Test 2 (Significant drift): {summary['overall_status']}")
    print(f"  Features with drift: {summary['features_with_drift']}")
    print(f"  Max drift score: {summary['max_drift_score']:.3f}")
    
    print("\n✓ Drift detector ready!")
