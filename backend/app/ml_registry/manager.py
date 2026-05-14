"""
F1 Strategy Platform v5.0 - Model Lifecycle Manager
Manages the complete lifecycle of ML models from training to retirement.
"""
import logging
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .registry import ModelRegistry, ModelMetadata

logger = logging.getLogger(__name__)


class ModelStage(Enum):
    """Model lifecycle stages."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass
class ModelPerformanceThresholds:
    """Performance thresholds for model promotion."""
    min_accuracy: float = 0.85
    max_latency_ms: float = 100.0
    max_error_rate: float = 0.05


class ModelLifecycleManager:
    """
    Manages the complete lifecycle of ML models.
    
    Stages:
    1. Development → Training and validation
    2. Staging → Testing with real data
    3. Production → Live serving
    4. Deprecated → Still serving but being replaced
    5. Retired → No longer used
    """
    
    def __init__(self, registry: ModelRegistry = None):
        self.registry = registry or ModelRegistry()
        self.thresholds = ModelPerformanceThresholds()
        self._stage_callbacks: Dict[ModelStage, List[Callable]] = {
            stage: [] for stage in ModelStage
        }
    
    def on_stage_change(self, stage: ModelStage, callback: Callable):
        """Register callback for stage transitions."""
        self._stage_callbacks[stage].append(callback)
    
    def _trigger_callbacks(self, stage: ModelStage, model_name: str, version: str):
        """Trigger callbacks for a stage."""
        for callback in self._stage_callbacks[stage]:
            try:
                callback(model_name, version)
            except Exception as e:
                logger.error(f"Stage callback failed: {e}")
    
    def validate_for_staging(
        self,
        model_name: str,
        version: str,
        test_data: Any,
        validation_func: Callable
    ) -> bool:
        """
        Validate a model for staging deployment.
        
        Args:
            model_name: Model name
            version: Version string
            test_data: Test dataset
            validation_func: Function to validate model
        
        Returns:
            True if model passes validation
        """
        try:
            model = self.registry.load_model(model_name, version)
            results = validation_func(model, test_data)
            
            # Check thresholds
            passed = (
                results.get("accuracy", 0) >= self.thresholds.min_accuracy and
                results.get("latency_ms", float("inf")) <= self.thresholds.max_latency_ms and
                results.get("error_rate", 1) <= self.thresholds.max_error_rate
            )
            
            # Update metadata
            metadata = self.registry.get_model_metadata(model_name, version)
            metadata.is_validated = passed
            metadata.validation_results = results
            
            if passed:
                logger.info(f"Model {model_name} v{version} passed staging validation")
                self._trigger_callbacks(ModelStage.STAGING, model_name, version)
            else:
                logger.warning(f"Model {model_name} v{version} failed staging validation")
            
            return passed
            
        except Exception as e:
            logger.error(f"Staging validation failed: {e}")
            return False
    
    def promote_to_production(
        self,
        model_name: str,
        version: str,
        canary_percentage: float = 0.0
    ) -> bool:
        """
        Promote model to production.
        
        Args:
            model_name: Model name
            version: Version to promote
            canary_percentage: Percentage of traffic for canary (0-100)
        
        Returns:
            True if promotion successful
        """
        try:
            # Get previous production for rollback
            # previous_version = self.registry.get_production_version(model_name)  # retained for potential rollback reference
            
            # Set new production
            self.registry.set_production(model_name, version)
            
            # metadata = self.registry.get_model_metadata(model_name, version)  # metadata usage removed
            logger.info(
                f"Promoted {model_name} v{version} to production "
                f"(canary: {canary_percentage}%)"
            )
            
            # Trigger callbacks
            self._trigger_callbacks(ModelStage.PRODUCTION, model_name, version)
            
            return True
            
        except Exception as e:
            logger.error(f"Production promotion failed: {e}")
            return False
    
    def deploy_canary(
        self,
        model_name: str,
        version: str,
        traffic_percentage: float = 10.0,
        duration_hours: float = 24.0
    ) -> Dict:
        """
        Deploy model with canary rollout.
        
        Args:
            model_name: Model name
            version: Version to deploy
            traffic_percentage: Initial traffic percentage
            duration_hours: Canary duration
        
        Returns:
            Deployment info dict
        """
        deployment_info = {
            "model_name": model_name,
            "version": version,
            "traffic_percentage": traffic_percentage,
            "start_time": datetime.now().isoformat(),
            "estimated_end": None,
            "status": "canary",
            "metrics": {}
        }
        
        if duration_hours > 0:
            from datetime import timedelta
            end_time = datetime.now() + timedelta(hours=duration_hours)
            deployment_info["estimated_end"] = end_time.isoformat()
        
        logger.info(
            f"Canary deployment: {model_name} v{version} "
            f"at {traffic_percentage}% traffic"
        )
        
        return deployment_info
    
    def rollback_production(self, model_name: str, reason: str = "") -> Optional[str]:
        """
        Rollback production to previous version.
        
        Args:
            model_name: Model name
            reason: Rollback reason for logging
        
        Returns:
            New production version or None if failed
        """
        try:
            current = self.registry.get_production_version(model_name)
            if not current:
                logger.warning(f"No production version for {model_name}")
                return None
            
            # Perform rollback
            new_version = self.registry.rollback(model_name, steps=1)
            
            logger.warning(
                f"Rolled back {model_name} to v{new_version}. "
                f"Reason: {reason or 'Not specified'}"
            )
            
            # Move old version to deprecated
            self._deprecate_version(model_name, current)
            
            return new_version
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return None
    
    def _deprecate_version(self, model_name: str, version: str):
        """Mark a version as deprecated."""
        try:
            metadata = self.registry.get_model_metadata(model_name, version)
            metadata.tags.append("deprecated")
            
            self._trigger_callbacks(ModelStage.DEPRECATED, model_name, version)
            
            logger.info(f"Deprecated {model_name} v{version}")
        except Exception as e:
            logger.error(f"Deprecation failed: {e}")
    
    def retire_version(self, model_name: str, version: str):
        """
        Retire a model version (permanently remove from serving).
        
        Args:
            model_name: Model name
            version: Version to retire
        """
        try:
            # Cannot retire production version
            if self.registry.get_production_version(model_name) == version:
                raise ValueError("Cannot retire production version. Promote another first.")
            
            metadata = self.registry.get_model_metadata(model_name, version)
            metadata.tags.append("retired")
            
            self._trigger_callbacks(ModelStage.RETIRED, model_name, version)
            
            logger.info(f"Retired {model_name} v{version}")
            
        except Exception as e:
            logger.error(f"Retirement failed: {e}")
    
    def get_model_health(self, model_name: str) -> Dict:
        """
        Get health status of a model.
        
        Returns:
            Health metrics dict
        """
        try:
            production_version = self.registry.get_production_version(model_name)
            
            if not production_version:
                return {
                    "status": "no_production",
                    "model_name": model_name,
                    "recommendation": "Set a production version"
                }
            
            metadata = self.registry.get_model_metadata(model_name, production_version)
            
            # Calculate health score
            health_score = 100.0
            issues = []
            
            if not metadata.is_validated:
                health_score -= 30
                issues.append("Not validated")
            
            accuracy = metadata.metrics.get("accuracy", 0)
            if accuracy < self.thresholds.min_accuracy:
                health_score -= (self.thresholds.min_accuracy - accuracy) * 100
                issues.append(f"Low accuracy: {accuracy:.2%}")
            
            # Check age
            from datetime import datetime
            created = datetime.fromisoformat(metadata.created_at)
            age_days = (datetime.now() - created).days
            if age_days > 30:
                health_score -= min(20, age_days - 30)
                issues.append(f"Old model: {age_days} days")
            
            status = "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical"
            
            return {
                "status": status,
                "model_name": model_name,
                "version": production_version,
                "health_score": max(0, health_score),
                "issues": issues,
                "metrics": metadata.metrics,
                "age_days": age_days,
                "recommendation": "Consider retraining" if health_score < 80 else "Model healthy"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def auto_rollback_on_degradation(
        self,
        model_name: str,
        current_metrics: Dict[str, float]
    ) -> bool:
        """
        Automatically rollback if model performance degrades.
        
        Args:
            model_name: Model name
            current_metrics: Current performance metrics
        
        Returns:
            True if rollback was triggered
        """
        production_version = self.registry.get_production_version(model_name)
        if not production_version:
            return False
        
        metadata = self.registry.get_model_metadata(model_name, production_version)
        baseline_metrics = metadata.metrics
        
        # Check for degradation
        degraded = False
        reasons = []
        
        for metric, current_value in current_metrics.items():
            baseline = baseline_metrics.get(metric)
            if baseline is not None:
                # For accuracy, higher is better
                if metric in ["accuracy", "f1", "precision", "recall"]:
                    if current_value < baseline * 0.95:  # 5% degradation
                        degraded = True
                        reasons.append(f"{metric} degraded: {baseline:.3f} -> {current_value:.3f}")
                # For latency/error, lower is better
                elif metric in ["latency_ms", "error_rate"]:
                    if current_value > baseline * 1.2:  # 20% increase
                        degraded = True
                        reasons.append(f"{metric} increased: {baseline:.3f} -> {current_value:.3f}")
        
        if degraded:
            reason = "Auto-rollback: " + "; ".join(reasons)
            self.rollback_production(model_name, reason)
            return True
        
        return False


if __name__ == "__main__":
    # Test model lifecycle manager
    print("Testing Model Lifecycle Manager")
    print("=" * 60)
    
    registry = ModelRegistry("./test_registry_lifecycle")
    manager = ModelLifecycleManager(registry)
    
    # Register a model
    dummy_model = {"type": "test", "version": "1.0.0"}
    
    metadata = ModelMetadata(
        name="lifecycle_test",
        version="1.0.0",
        created_at=datetime.now().isoformat(),
        metrics={"accuracy": 0.92, "f1": 0.90}
    )
    
    version = registry.register_model(dummy_model, "lifecycle_test", metadata=metadata)
    
    # Test promotion
    manager.promote_to_production("lifecycle_test", "1.0.0")
    
    # Test health check
    health = manager.get_model_health("lifecycle_test")
    print(f"✓ Model health: {health['status']} (score: {health['health_score']:.1f})")
    
    # Register second version
    metadata2 = ModelMetadata(
        name="lifecycle_test",
        version="2.0.0",
        created_at=datetime.now().isoformat(),
        metrics={"accuracy": 0.95, "f1": 0.94}
    )
    
    registry.register_model(dummy_model, "lifecycle_test", metadata=metadata2)
    
    # Test rollback
    manager.promote_to_production("lifecycle_test", "2.0.0")
    print("✓ Promoted to v2.0.0")
    
    new_version = manager.rollback_production("lifecycle_test", "Test rollback")
    print(f"✓ Rolled back to v{new_version}")
    
    print("\n✓ Model lifecycle manager working correctly!")
