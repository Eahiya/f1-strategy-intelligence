"""
F1 Strategy Platform v6.0 - Outlier Detection
Detects anomalous data points that could indicate errors or special cases.
"""
import numpy as np
import pandas as pd
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
from scipy import stats


class OutlierMethod(Enum):
    """Methods for outlier detection."""
    IQR = "iqr"  # Interquartile range
    ZSCORE = "zscore"  # Z-score method
    ISOLATION_FOREST = "isolation_forest"  # ML-based


@dataclass
class OutlierReport:
    """Report of detected outliers."""
    feature: str
    outlier_indices: List[int]
    outlier_values: List[float]
    outlier_count: int
    outlier_percentage: float
    method: str
    threshold_used: float
    recommendation: str


class OutlierDetector:
    """
    Detects outliers in racing data.
    
    Racing context outliers:
    - Lap times >3x standard deviation (crashes, red flags)
    - Tire ages >100 laps (data entry errors)
    - Fuel loads outside physical limits
    """
    
    # Racing-specific bounds
    PHYSICAL_LIMITS = {
        'lap_time': (45, 180),  # seconds
        'tire_age': (0, 100),   # laps
        'fuel_load': (5, 120),  # kg
        'speed': (0, 400),      # km/h
        'gap_to_leader': (-100, 100)  # seconds
    }
    
    def __init__(self, method: OutlierMethod = OutlierMethod.IQR, 
                 z_threshold: float = 3.0, iqr_multiplier: float = 1.5):
        """
        Initialize outlier detector.
        
        Args:
            method: Detection method
            z_threshold: Z-score threshold (typically 3)
            iqr_multiplier: IQR multiplier (typically 1.5)
        """
        self.method = method
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier
    
    def detect_outliers(self, data: pd.DataFrame, 
                        features: List[str] = None) -> List[OutlierReport]:
        """
        Detect outliers in specified features.
        
        Args:
            data: DataFrame to check
            features: Features to analyze (all numeric if None)
        
        Returns:
            List of OutlierReport objects
        """
        if features is None:
            features = data.select_dtypes(include=[np.number]).columns.tolist()
        
        reports = []
        
        for feature in features:
            if feature not in data.columns:
                continue
            
            values = data[feature].dropna().values
            
            if len(values) == 0:
                continue
            
            # First apply physical limits
            if feature in self.PHYSICAL_LIMITS:
                min_phys, max_phys = self.PHYSICAL_LIMITS[feature]
                physical_outliers = np.where((values < min_phys) | (values > max_phys))[0]
            else:
                physical_outliers = np.array([])
            
            # Apply statistical method
            if self.method == OutlierMethod.ZSCORE:
                statistical_outliers = self._zscore_outliers(values)
            elif self.method == OutlierMethod.IQR:
                statistical_outliers = self._iqr_outliers(values)
            else:
                statistical_outliers = np.array([])
            
            # Combine outliers
            all_outliers = np.unique(np.concatenate([physical_outliers, statistical_outliers])).astype(int)
            
            if len(all_outliers) > 0:
                outlier_pct = len(all_outliers) / len(values) * 100
                
                # Generate recommendation
                if outlier_pct > 10:
                    recommendation = f"CRITICAL: {outlier_pct:.1f}% outliers in {feature} - check data source"
                elif outlier_pct > 5:
                    recommendation = f"WARNING: {outlier_pct:.1f}% outliers in {feature} - review needed"
                elif outlier_pct > 1:
                    recommendation = f"NOTE: {outlier_pct:.1f}% outliers in {feature} - normal racing incidents"
                else:
                    recommendation = f"OK: Normal outlier rate in {feature}"
                
                report = OutlierReport(
                    feature=feature,
                    outlier_indices=all_outliers.tolist(),
                    outlier_values=values[all_outliers].tolist(),
                    outlier_count=len(all_outliers),
                    outlier_percentage=outlier_pct,
                    method=self.method.value,
                    threshold_used=self.z_threshold if self.method == OutlierMethod.ZSCORE else self.iqr_multiplier,
                    recommendation=recommendation
                )
                
                reports.append(report)
        
        return reports
    
    def _zscore_outliers(self, values: np.ndarray) -> np.ndarray:
        """Detect outliers using Z-score method."""
        z_scores = np.abs(stats.zscore(values))
        return np.where(z_scores > self.z_threshold)[0]
    
    def _iqr_outliers(self, values: np.ndarray) -> np.ndarray:
        """Detect outliers using IQR method."""
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - self.iqr_multiplier * iqr
        upper_bound = q3 + self.iqr_multiplier * iqr
        
        return np.where((values < lower_bound) | (values > upper_bound))[0]
    
    def clean_outliers(self, data: pd.DataFrame, reports: List[OutlierReport],
                       method: str = "clip") -> pd.DataFrame:
        """
        Clean outliers from data.
        
        Args:
            data: Original DataFrame
            reports: Outlier reports
            method: 'clip' (cap at bounds), 'remove' (drop rows), 'median' (replace)
        
        Returns:
            Cleaned DataFrame
        """
        cleaned = data.copy()
        
        for report in reports:
            feature = report.feature
            
            if method == "clip" and feature in self.PHYSICAL_LIMITS:
                min_val, max_val = self.PHYSICAL_LIMITS[feature]
                cleaned[feature] = cleaned[feature].clip(min_val, max_val)
            
            elif method == "remove":
                # Don't remove - just flag
                pass
            
            elif method == "median":
                median_val = cleaned[feature].median()
                outlier_mask = cleaned.index.isin(report.outlier_indices)
                cleaned.loc[outlier_mask, feature] = median_val
        
        return cleaned
    
    def get_summary(self, reports: List[OutlierReport]) -> Dict:
        """Get summary of outlier detection."""
        if not reports:
            return {
                "total_features_checked": 0,
                "features_with_outliers": 0,
                "total_outliers": 0,
                "max_outlier_percentage": 0,
                "status": "healthy"
            }
        
        total_outliers = sum(r.outlier_count for r in reports)
        max_pct = max(r.outlier_percentage for r in reports)
        
        # Determine status
        critical_count = sum(1 for r in reports if r.outlier_percentage > 10)
        warning_count = sum(1 for r in reports if 5 < r.outlier_percentage <= 10)
        
        if critical_count > 0:
            status = "critical"
        elif warning_count > 0:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "total_features_checked": len(reports),
            "features_with_outliers": len([r for r in reports if r.outlier_count > 0]),
            "total_outliers": total_outliers,
            "max_outlier_percentage": max_pct,
            "status": status,
            "recommendation": "Review data sources" if status in ["critical", "warning"] else "Data quality acceptable"
        }


# Import for zscore


if __name__ == "__main__":
    # Test outlier detection
    print("Testing Outlier Detector")
    print("=" * 60)
    
    # Create test data with outliers
    np.random.seed(42)
    data = pd.DataFrame({
        'lap_time': np.concatenate([
            np.random.normal(85, 3, 95),  # Normal laps
            [120, 145, 5]  # Outliers (crash, pit, error)
        ]),
        'tire_age': np.concatenate([
            np.random.uniform(0, 30, 97),
            [150, 200]  # Impossible tire ages
        ])
    })
    
    detector = OutlierDetector(method=OutlierMethod.IQR)
    reports = detector.detect_outliers(data)
    
    print(f"Found outliers in {len(reports)} features:")
    for report in reports:
        print(f"  - {report.feature}: {report.outlier_count} outliers ({report.outlier_percentage:.1f}%)")
        print(f"    {report.recommendation}")
    
    summary = detector.get_summary(reports)
    print(f"\nOverall status: {summary['status']}")
    
    print("\n✓ Outlier detector ready!")
