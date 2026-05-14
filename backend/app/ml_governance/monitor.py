"""
F1 Strategy Platform v6.0 - ML Model Monitor
Tracks model performance over time and detects model drift.
"""
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from app.auth.models import Base


class PredictionLog(Base):
    """Database table for prediction logging."""
    __tablename__ = "prediction_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Model info
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    
    # Input/Output
    input_features = Column(JSON, nullable=False)
    prediction = Column(Float, nullable=False)
    prediction_confidence = Column(Float, nullable=True)
    
    # Ground truth (if available later)
    actual_value = Column(Float, nullable=True)
    error = Column(Float, nullable=True)  # prediction - actual
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, nullable=True)
    circuit = Column(String(50), nullable=True)
    
    # Performance
    inference_time_ms = Column(Float, nullable=True)
    
    # Drift tracking
    feature_drift_scores = Column(JSON, nullable=True)
    data_drift_detected = Column(String, default="false")


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a model."""
    model_name: str
    model_version: str
    total_predictions: int
    avg_prediction: float
    avg_confidence: float
    avg_inference_time_ms: float
    mse: Optional[float]  # Mean squared error (if ground truth available)
    mae: Optional[float]  # Mean absolute error
    drift_detected: bool
    recommendations: List[str]


class PredictionLogger:
    """Logs all predictions for monitoring and auditing."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def log_prediction(
        self,
        model_name: str,
        model_version: str,
        input_features: Dict,
        prediction: float,
        confidence: Optional[float] = None,
        inference_time_ms: Optional[float] = None,
        user_id: Optional[int] = None,
        circuit: Optional[str] = None,
        feature_drift: Optional[Dict] = None
    ) -> PredictionLog:
        """Log a single prediction."""
        log = PredictionLog(
            model_name=model_name,
            model_version=model_version,
            input_features=input_features,
            prediction=prediction,
            prediction_confidence=confidence,
            inference_time_ms=inference_time_ms,
            user_id=user_id,
            circuit=circuit,
            feature_drift_scores=feature_drift,
            data_drift_detected="true" if feature_drift else "false"
        )
        
        self.db.add(log)
        self.db.commit()
        
        return log
    
    def update_ground_truth(self, log_id: int, actual_value: float):
        """Update prediction with actual value (for accuracy tracking)."""
        log = self.db.query(PredictionLog).filter(PredictionLog.id == log_id).first()
        if log:
            log.actual_value = actual_value
            log.error = log.prediction - actual_value
            self.db.commit()


class ModelMonitor:
    """Monitors model performance and detects degradation."""
    
    def __init__(self, db_session, drift_detector=None):
        self.db = db_session
        self.drift_detector = drift_detector
    
    def get_performance_metrics(
        self,
        model_name: str,
        version: Optional[str] = None,
        hours: int = 24
    ) -> ModelPerformanceMetrics:
        """
        Get performance metrics for a model.
        
        Args:
            model_name: Model name
            version: Specific version (all if None)
            hours: Time window in hours
        
        Returns:
            ModelPerformanceMetrics
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db.query(PredictionLog).filter(
            PredictionLog.model_name == model_name,
            PredictionLog.timestamp >= start_time
        )
        
        if version:
            query = query.filter(PredictionLog.model_version == version)
        
        logs = query.all()
        
        if not logs:
            return ModelPerformanceMetrics(
                model_name=model_name,
                model_version=version or "all",
                total_predictions=0,
                avg_prediction=0,
                avg_confidence=0,
                avg_inference_time_ms=0,
                mse=None,
                mae=None,
                drift_detected=False,
                recommendations=["No predictions in time window"]
            )
        
        predictions = [log.prediction for log in logs]
        confidences = [log.prediction_confidence for log in logs if log.prediction_confidence]
        inference_times = [log.inference_time_ms for log in logs if log.inference_time_ms]
        
        # Calculate accuracy metrics if ground truth available
        logs_with_truth = [log for log in logs if log.actual_value is not None]
        if logs_with_truth:
            errors = [log.error for log in logs_with_truth]
            mse = np.mean([e**2 for e in errors])
            mae = np.mean([abs(e) for e in errors])
        else:
            mse = None
            mae = None
        
        # Check for drift
        drift_detected = any(log.data_drift_detected == "true" for log in logs)
        
        # Generate recommendations
        recommendations = []
        
        if len(logs) < 10:
            recommendations.append("Low prediction volume - consider if model is being used")
        
        if mae and mae > 5.0:
            recommendations.append(f"High MAE ({mae:.2f}s) - model may need retraining")
        
        if drift_detected:
            recommendations.append("Data drift detected - investigate input distributions")
        
        if confidences and np.mean(confidences) < 0.7:
            recommendations.append("Low average confidence - model uncertainty is high")
        
        if inference_times and np.mean(inference_times) > 500:
            recommendations.append("Slow inference (>500ms) - consider model optimization")
        
        if not recommendations:
            recommendations.append("Model performing within expected parameters")
        
        return ModelPerformanceMetrics(
            model_name=model_name,
            model_version=version or "all",
            total_predictions=len(logs),
            avg_prediction=np.mean(predictions),
            avg_confidence=np.mean(confidences) if confidences else 0,
            avg_inference_time_ms=np.mean(inference_times) if inference_times else 0,
            mse=mse,
            mae=mae,
            drift_detected=drift_detected,
            recommendations=recommendations
        )
    
    def detect_model_drift(self, model_name: str, baseline_hours: int = 168, 
                         current_hours: int = 24) -> Dict:
        """
        Detect if model predictions have drifted from baseline.
        
        Args:
            model_name: Model to check
            baseline_hours: Hours of baseline data (default 1 week)
            current_hours: Hours of recent data (default 1 day)
        
        Returns:
            Drift detection results
        """
        now = datetime.utcnow()
        
        # Get baseline predictions
        baseline_start = now - timedelta(hours=baseline_hours)
        baseline_end = now - timedelta(hours=current_hours)
        
        baseline_logs = self.db.query(PredictionLog).filter(
            PredictionLog.model_name == model_name,
            PredictionLog.timestamp >= baseline_start,
            PredictionLog.timestamp < baseline_end
        ).all()
        
        # Get recent predictions
        current_start = now - timedelta(hours=current_hours)
        current_logs = self.db.query(PredictionLog).filter(
            PredictionLog.model_name == model_name,
            PredictionLog.timestamp >= current_start
        ).all()
        
        if len(baseline_logs) < 10 or len(current_logs) < 10:
            return {
                "model_name": model_name,
                "drift_detected": False,
                "message": "Insufficient data for drift detection",
                "baseline_count": len(baseline_logs),
                "current_count": len(current_logs)
            }
        
        baseline_preds = [log.prediction for log in baseline_logs]
        current_preds = [log.prediction for log in current_logs]
        
        # Statistical test for distribution shift
        from scipy import stats
        ks_stat, p_value = stats.ks_2samp(baseline_preds, current_preds)
        
        drift_detected = p_value < 0.05
        
        return {
            "model_name": model_name,
            "drift_detected": drift_detected,
            "ks_statistic": ks_stat,
            "p_value": p_value,
            "baseline_mean": np.mean(baseline_preds),
            "current_mean": np.mean(current_preds),
            "mean_shift": np.mean(current_preds) - np.mean(baseline_preds),
            "baseline_std": np.std(baseline_preds),
            "current_std": np.std(current_preds),
            "recommendation": "Investigate model retraining" if drift_detected else "Model stable"
        }
    
    def get_model_health_dashboard(self) -> Dict:
        """Get health status for all monitored models."""
        # Get unique models
        model_names = [name[0] for name in self.db.query(PredictionLog.model_name).distinct().all()]
        
        health_status = {}
        
        for model_name in model_names:
            metrics = self.get_performance_metrics(model_name, hours=24)
            drift = self.detect_model_drift(model_name)
            
            # Determine health status
            issues = []
            
            if metrics.mae and metrics.mae > 3.0:
                issues.append("high_error")
            
            if drift["drift_detected"]:
                issues.append("prediction_drift")
            
            if metrics.drift_detected:
                issues.append("input_drift")
            
            if metrics.total_predictions == 0:
                issues.append("no_predictions")
            
            status = "healthy" if not issues else "warning" if len(issues) < 2 else "critical"
            
            health_status[model_name] = {
                "status": status,
                "issues": issues,
                "predictions_24h": metrics.total_predictions,
                "mae": metrics.mae,
                "avg_confidence": metrics.avg_confidence,
                "recommendations": metrics.recommendations[:3]  # Top 3
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "models_monitored": len(model_names),
            "healthy": sum(1 for s in health_status.values() if s["status"] == "healthy"),
            "warning": sum(1 for s in health_status.values() if s["status"] == "warning"),
            "critical": sum(1 for s in health_status.values() if s["status"] == "critical"),
            "models": health_status
        }


if __name__ == "__main__":
    print("ML Model Monitor")
    print("=" * 60)
    print("Components:")
    print("  - PredictionLogger: Logs all predictions")
    print("  - ModelMonitor: Tracks performance and drift")
    print("  - Dashboard: Real-time model health")
    print("\nReady for integration.")
