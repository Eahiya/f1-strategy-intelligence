"""
F1 Strategy Platform v6.0 - Shadow Deployment
Runs new models silently alongside production models for comparison.
"""
import logging
from typing import Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ShadowComparison:
    """Comparison between production and shadow model."""
    input_features: Dict[str, Any]
    production_prediction: float
    shadow_prediction: float
    difference: float
    percent_difference: float
    timestamp: str


class ShadowDeploymentManager:
    """
    Manages shadow deployment of new model versions.
    
    Shadow deployment:
    1. Production model serves real traffic
    2. Shadow model runs silently on same inputs
    3. Compare predictions without affecting users
    4. Promote shadow to production if performance is better
    """
    
    def __init__(self, traffic_percentage: float = 10.0):
        """
        Initialize shadow deployment.
        
        Args:
            traffic_percentage: % of traffic to route to shadow model
        """
        self.traffic_percentage = traffic_percentage
        self.shadow_models: Dict[str, Dict] = {}  # model_name -> model info
        self.comparisons: Dict[str, List[ShadowComparison]] = {}
    
    def register_shadow_model(
        self,
        model_name: str,
        shadow_version: str,
        model_instance: Any,
        production_version: str = None
    ):
        """
        Register a model for shadow deployment.
        
        Args:
            model_name: Model identifier
            shadow_version: Version string for shadow model
            model_instance: The shadow model object
            production_version: Current production version (for tracking)
        """
        self.shadow_models[model_name] = {
            "version": shadow_version,
            "model": model_instance,
            "production_version": production_version,
            "enabled": True,
            "start_time": datetime.now().isoformat(),
            "comparison_count": 0
        }
        
        self.comparisons[model_name] = []
        
        logger.info(f"Registered shadow model {model_name} v{shadow_version}")
    
    def should_use_shadow(self, model_name: str) -> bool:
        """Determine if this request should use shadow model."""
        if model_name not in self.shadow_models:
            return False
        
        if not self.shadow_models[model_name]["enabled"]:
            return False
        
        # Simple percentage-based routing
        import random
        return random.random() < (self.traffic_percentage / 100)
    
    def predict_with_shadow(
        self,
        model_name: str,
        production_predict_fn: Callable,
        shadow_predict_fn: Callable,
        features: Dict[str, Any],
        use_shadow: bool = None
    ) -> Dict[str, Any]:
        """
        Make prediction with optional shadow comparison.
        
        Args:
            model_name: Model name
            production_predict_fn: Production model prediction function
            shadow_predict_fn: Shadow model prediction function
            features: Input features
            use_shadow: Force shadow (None = auto-decide)
        
        Returns:
            Result dict with prediction and comparison if shadow was used
        """
        # Always get production prediction
        production_result = production_predict_fn(features)
        
        result = {
            "prediction": production_result,
            "model": model_name,
            "version": self.shadow_models.get(model_name, {}).get("production_version", "unknown"),
            "shadow_used": False
        }
        
        # Decide if we should use shadow
        if use_shadow is None:
            use_shadow = self.should_use_shadow(model_name)
        
        if use_shadow and model_name in self.shadow_models:
            try:
                # Get shadow prediction
                shadow_result = shadow_predict_fn(features)
                
                # Record comparison
                comparison = ShadowComparison(
                    input_features=features,
                    production_prediction=production_result if isinstance(production_result, (int, float)) else production_result[0],
                    shadow_prediction=shadow_result if isinstance(shadow_result, (int, float)) else shadow_result[0],
                    difference=abs(shadow_result - production_result) if isinstance(production_result, (int, float)) and isinstance(shadow_result, (int, float)) else 0,
                    percent_difference=abs(shadow_result - production_result) / production_result * 100 if isinstance(production_result, (int, float)) and production_result != 0 else 0,
                    timestamp=datetime.now().isoformat()
                )
                
                self.comparisons[model_name].append(comparison)
                self.shadow_models[model_name]["comparison_count"] += 1
                
                result["shadow_used"] = True
                result["shadow_prediction"] = shadow_result
                result["shadow_version"] = self.shadow_models[model_name]["version"]
                result["difference"] = comparison.difference
                result["percent_difference"] = comparison.percent_difference
                
            except Exception as e:
                logger.error(f"Shadow prediction failed for {model_name}: {e}")
                # Fall back to production only
        
        return result
    
    def get_shadow_analysis(self, model_name: str) -> Dict:
        """
        Analyze shadow model performance vs production.
        
        Args:
            model_name: Model to analyze
        
        Returns:
            Analysis results with recommendation
        """
        if model_name not in self.comparisons or not self.comparisons[model_name]:
            return {
                "model_name": model_name,
                "comparisons": 0,
                "status": "insufficient_data",
                "recommendation": "Need more comparisons for analysis"
            }
        
        comparisons = self.comparisons[model_name]
        
        # Calculate statistics
        diffs = [c.difference for c in comparisons]
        pct_diffs = [c.percent_difference for c in comparisons]
        
        avg_diff = np.mean(diffs)
        avg_pct_diff = np.mean(pct_diffs)
        max_diff = np.max(diffs)
        
        # Determine if shadow is better
        # For lap time predictions, lower is generally better
        # shadow_predictions = [c.shadow_prediction for c in comparisons]  # unused variable removed
        # production_predictions = [c.production_prediction for c in comparisons]  # unused variable removed
        
        shadow_better_count = sum(1 for c in comparisons if c.shadow_prediction < c.production_prediction)
        better_ratio = shadow_better_count / len(comparisons)
        
        # Generate recommendation
        if len(comparisons) < 100:
            status = "collecting_data"
            recommendation = f"Continue shadow deployment ({len(comparisons)}/100 comparisons)"
        elif better_ratio > 0.6 and avg_pct_diff > 1.0:
            status = "promote_recommended"
            recommendation = f"Shadow model shows {better_ratio:.1%} improvement - ready to promote"
        elif better_ratio < 0.4:
            status = "underperforming"
            recommendation = "Shadow model performing worse - investigate before promoting"
        else:
            status = "similar_performance"
            recommendation = "Shadow model similar to production - marginal improvement"
        
        return {
            "model_name": model_name,
            "shadow_version": self.shadow_models[model_name]["version"],
            "comparisons": len(comparisons),
            "production_version": self.shadow_models[model_name]["production_version"],
            "avg_difference": avg_diff,
            "avg_percent_difference": avg_pct_diff,
            "max_difference": max_diff,
            "shadow_better_ratio": better_ratio,
            "status": status,
            "recommendation": recommendation,
            "start_time": self.shadow_models[model_name]["start_time"]
        }
    
    def disable_shadow(self, model_name: str):
        """Disable shadow deployment for a model."""
        if model_name in self.shadow_models:
            self.shadow_models[model_name]["enabled"] = False
            logger.info(f"Disabled shadow deployment for {model_name}")
    
    def enable_shadow(self, model_name: str):
        """Enable shadow deployment for a model."""
        if model_name in self.shadow_models:
            self.shadow_models[model_name]["enabled"] = True
            logger.info(f"Enabled shadow deployment for {model_name}")
    
    def get_all_shadow_status(self) -> Dict:
        """Get status of all shadow deployments."""
        status = {}
        
        for model_name in self.shadow_models:
            status[model_name] = self.get_shadow_analysis(model_name)
        
        return {
            "shadow_deployments": len(self.shadow_models),
            "models": status,
            "traffic_percentage": self.traffic_percentage
        }


if __name__ == "__main__":
    print("Shadow Deployment Manager")
    print("=" * 60)
    print("Features:")
    print("  - Silent model testing")
    print("  - Production vs shadow comparison")
    print("  - Automatic promotion recommendations")
    print("  - Risk-free model updates")
    print("\nReady for integration.")
