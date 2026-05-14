"""
F1 Strategy Platform v5.0 - Model Registry
Central registry for managing ML model versions and metadata.
"""
import json
import pickle
import shutil
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a model version."""
    name: str
    version: str
    created_at: str
    description: str = ""
    author: str = "unknown"
    
    # Training info
    training_data_hash: str = ""
    training_samples: int = 0
    training_duration_seconds: float = 0.0
    
    # Performance metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Model config
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    model_type: str = "unknown"
    framework: str = "unknown"
    
    # Validation
    validation_results: Dict[str, Any] = field(default_factory=dict)
    is_validated: bool = False
    
    # Deployment
    is_production: bool = False
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ModelMetadata':
        return cls(**data)


@dataclass
class ModelVersion:
    """Represents a specific model version."""
    metadata: ModelMetadata
    model_path: str
    artifacts_path: str
    
    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata.to_dict(),
            "model_path": self.model_path,
            "artifacts_path": self.artifacts_path
        }


class ModelRegistry:
    """
    Central registry for ML model versioning and lifecycle.
    
    Features:
    - Version tracking with semantic versioning
    - Metadata storage
    - Model artifact management
    - Rollback capabilities
    - A/B testing support
    """
    
    def __init__(self, registry_path: str = None):
        self.registry_path = Path(registry_path or "./ml_registry")
        self.models_path = self.registry_path / "models"
        self.metadata_path = self.registry_path / "metadata"
        self.artifacts_path = self.registry_path / "artifacts"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # In-memory cache of registered models
        self._models: Dict[str, Dict[str, ModelVersion]] = {}
        self._production_versions: Dict[str, str] = {}
        
        # Load existing models
        self._load_registry()
    
    def _ensure_directories(self):
        """Create registry directories if they don't exist."""
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)
        self.artifacts_path.mkdir(parents=True, exist_ok=True)
    
    def _load_registry(self):
        """Load existing model registry from disk."""
        if not (self.metadata_path / "registry.json").exists():
            return
        
        try:
            with open(self.metadata_path / "registry.json", "r") as f:
                registry_data = json.load(f)
            
            for model_name, versions in registry_data.get("models", {}).items():
                self._models[model_name] = {}
                for version_str, version_data in versions.items():
                    metadata = ModelMetadata.from_dict(version_data["metadata"])
                    self._models[model_name][version_str] = ModelVersion(
                        metadata=metadata,
                        model_path=version_data["model_path"],
                        artifacts_path=version_data["artifacts_path"]
                    )
            
            self._production_versions = registry_data.get("production", {})
            
            logger.info(f"Loaded {len(self._models)} models from registry")
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
    
    def _save_registry(self):
        """Save registry state to disk."""
        registry_data = {
            "models": {},
            "production": self._production_versions,
            "last_updated": datetime.now().isoformat()
        }
        
        for model_name, versions in self._models.items():
            registry_data["models"][model_name] = {
                v: self._models[model_name][v].to_dict()
                for v in versions
            }
        
        with open(self.metadata_path / "registry.json", "w") as f:
            json.dump(registry_data, f, indent=2)
    
    def register_model(
        self,
        model: Any,
        name: str,
        version: str = None,
        metadata: ModelMetadata = None,
        artifacts: Dict[str, Any] = None,
        serializer: str = "pickle"
    ) -> ModelVersion:
        """
        Register a new model version.
        
        Args:
            model: The model object to register
            name: Model name (e.g., "tire_degradation")
            version: Version string (auto-generated if None)
            metadata: Model metadata
            artifacts: Additional artifacts (plots, reports, etc.)
            serializer: Serialization method ("pickle", "joblib", "torch")
        
        Returns:
            ModelVersion object
        """
        # Generate version if not provided
        if version is None:
            version = self._generate_version(name)
        
        # Check version doesn't exist
        if name in self._models and version in self._models[name]:
            raise ValueError(f"Version {version} already exists for model {name}")
        
        # Create directories for this version
        version_path = self.models_path / name / version
        version_path.mkdir(parents=True, exist_ok=True)
        
        artifacts_path = self.artifacts_path / name / version
        artifacts_path.mkdir(parents=True, exist_ok=True)
        
        # Serialize model
        model_file = version_path / f"model.{serializer}"
        self._serialize_model(model, model_file, serializer)
        
        # Save artifacts
        if artifacts:
            for artifact_name, artifact_data in artifacts.items():
                artifact_file = artifacts_path / f"{artifact_name}.pkl"
                with open(artifact_file, "wb") as f:
                    pickle.dump(artifact_data, f)
        
        # Create default metadata if not provided
        if metadata is None:
            metadata = ModelMetadata(
                name=name,
                version=version,
                created_at=datetime.now().isoformat()
            )
        else:
            # Update with actual version info
            metadata.version = version
            metadata.name = name
            if not metadata.created_at:
                metadata.created_at = datetime.now().isoformat()
        
        # Create model version
        model_version = ModelVersion(
            metadata=metadata,
            model_path=str(model_file),
            artifacts_path=str(artifacts_path)
        )
        
        # Register in memory
        if name not in self._models:
            self._models[name] = {}
        self._models[name][version] = model_version
        
        # Save to disk
        self._save_registry()
        
        logger.info(f"Registered model {name} version {version}")
        return model_version
    
    def load_model(self, name: str, version: str = None, 
                   deserializer: str = "pickle") -> Any:
        """
        Load a model by name and version.
        
        Args:
            name: Model name
            version: Version string (loads production if None)
            deserializer: Deserialization method
        
        Returns:
            Loaded model object
        """
        # Get version to load
        if version is None:
            version = self.get_production_version(name)
            if version is None:
                raise ValueError(f"No production version for {name}")
        
        # Check version exists
        if name not in self._models or version not in self._models[name]:
            raise ValueError(f"Model {name} version {version} not found")
        
        model_version = self._models[name][version]
        model_path = Path(model_version.model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Deserialize
        return self._deserialize_model(model_path, deserializer)
    
    def get_model_metadata(self, name: str, version: str = None) -> ModelMetadata:
        """Get metadata for a model version."""
        if version is None:
            version = self.get_production_version(name)
        
        if name not in self._models or version not in self._models[name]:
            raise ValueError(f"Model {name} version {version} not found")
        
        return self._models[name][version].metadata
    
    def list_models(self) -> List[str]:
        """List all registered model names."""
        return list(self._models.keys())
    
    def list_versions(self, name: str) -> List[str]:
        """List all versions for a model."""
        if name not in self._models:
            return []
        return list(self._models[name].keys())
    
    def set_production(self, name: str, version: str):
        """Set a version as the production version."""
        if name not in self._models or version not in self._models[name]:
            raise ValueError(f"Model {name} version {version} not found")
        
        # Unset previous production
        if name in self._production_versions:
            old_version = self._production_versions[name]
            if old_version in self._models[name]:
                self._models[name][old_version].metadata.is_production = False
        
        # Set new production
        self._production_versions[name] = version
        self._models[name][version].metadata.is_production = True
        
        self._save_registry()
        logger.info(f"Set {name} version {version} as production")
    
    def get_production_version(self, name: str) -> Optional[str]:
        """Get the production version for a model."""
        return self._production_versions.get(name)
    
    def rollback(self, name: str, steps: int = 1) -> str:
        """
        Rollback to a previous version.
        
        Args:
            name: Model name
            steps: Number of versions to go back
        
        Returns:
            New production version string
        """
        if name not in self._models:
            raise ValueError(f"Model {name} not found")
        
        versions = sorted(self._models[name].keys())
        if len(versions) <= steps:
            raise ValueError(f"Cannot rollback {steps} steps, only {len(versions)} versions available")
        
        current_idx = -1
        current_version = self._production_versions.get(name)
        if current_version:
            try:
                current_idx = versions.index(current_version)
            except ValueError:
                pass
        
        target_idx = max(0, current_idx - steps)
        target_version = versions[target_idx]
        
        self.set_production(name, target_version)
        
        logger.info(f"Rolled back {name} from {current_version} to {target_version}")
        return target_version
    
    def compare_versions(self, name: str, version1: str, version2: str) -> Dict:
        """Compare two model versions."""
        if name not in self._models:
            raise ValueError(f"Model {name} not found")
        
        meta1 = self._models[name][version1].metadata
        meta2 = self._models[name][version2].metadata
        
        return {
            "version1": version1,
            "version2": version2,
            "created_at_diff": (
                datetime.fromisoformat(meta2.created_at) - 
                datetime.fromisoformat(meta1.created_at)
            ).total_seconds(),
            "metrics_comparison": {
                metric: {
                    "v1": meta1.metrics.get(metric, None),
                    "v2": meta2.metrics.get(metric, None),
                    "diff": meta2.metrics.get(metric, 0) - meta1.metrics.get(metric, 0)
                }
                for metric in set(meta1.metrics.keys()) | set(meta2.metrics.keys())
            },
            "samples_diff": meta2.training_samples - meta1.training_samples,
            "v1_is_production": meta1.is_production,
            "v2_is_production": meta2.is_production
        }
    
    def delete_version(self, name: str, version: str, force: bool = False):
        """Delete a model version."""
        if name not in self._models or version not in self._models[name]:
            raise ValueError(f"Model {name} version {version} not found")
        
        # Check if production
        if self._production_versions.get(name) == version and not force:
            raise ValueError("Cannot delete production version. Set another version first or use force=True")
        
        # Remove from memory
        del self._models[name][version]
        
        # Remove from disk
        version_path = self.models_path / name / version
        if version_path.exists():
            shutil.rmtree(version_path)
        
        artifacts_path = self.artifacts_path / name / version
        if artifacts_path.exists():
            shutil.rmtree(artifacts_path)
        
        # Remove from production if it was set
        if self._production_versions.get(name) == version:
            del self._production_versions[name]
        
        self._save_registry()
        logger.info(f"Deleted {name} version {version}")
    
    def _generate_version(self, name: str) -> str:
        """Generate next version string (semantic versioning)."""
        if name not in self._models or not self._models[name]:
            return "1.0.0"
        
        versions = sorted(self._models[name].keys())
        last_version = versions[-1]
        
        # Parse semver
        parts = last_version.split(".")
        if len(parts) == 3:
            major, minor, patch = map(int, parts)
            # Increment patch by default
            return f"{major}.{minor}.{patch + 1}"
        
        return f"{last_version}.1"
    
    def _serialize_model(self, model: Any, path: Path, method: str):
        """Serialize model to disk."""
        if method == "pickle":
            with open(path, "wb") as f:
                pickle.dump(model, f)
        elif method == "joblib":
            import joblib
            joblib.dump(model, path)
        elif method == "torch":
            import torch
            torch.save(model, path)
        else:
            raise ValueError(f"Unknown serializer: {method}")
    
    def _deserialize_model(self, path: Path, method: str) -> Any:
        """Deserialize model from disk."""
        if method == "pickle":
            with open(path, "rb") as f:
                return pickle.load(f)
        elif method == "joblib":
            import joblib
            return joblib.load(path)
        elif method == "torch":
            import torch
            return torch.load(path, map_location="cpu")
        else:
            raise ValueError(f"Unknown deserializer: {method}")
    
    def get_registry_status(self) -> Dict:
        """Get overall registry status."""
        return {
            "total_models": len(self._models),
            "total_versions": sum(len(v) for v in self._models.values()),
            "production_models": len(self._production_versions),
            "models": {
                name: {
                    "versions": len(self._models[name]),
                    "production": self._production_versions.get(name)
                }
                for name in self._models
            }
        }


if __name__ == "__main__":
    # Test model registry
    print("Testing Model Registry")
    print("=" * 60)
    
    registry = ModelRegistry("./test_registry")
    
    # Test registering a model
    dummy_model = {"weights": [1, 2, 3], "bias": 0.5}
    
    metadata = ModelMetadata(
        name="test_model",
        version="1.0.0",
        created_at=datetime.now().isoformat(),
        description="Test model for demonstration",
        author="system",
        metrics={"accuracy": 0.95, "f1": 0.93}
    )
    
    version = registry.register_model(
        model=dummy_model,
        name="test_model",
        metadata=metadata
    )
    
    print(f"✓ Registered model: {version.metadata.name} v{version.metadata.version}")
    
    # Test loading
    loaded = registry.load_model("test_model", "1.0.0")
    print(f"✓ Loaded model: {loaded}")
    
    # Test production
    registry.set_production("test_model", "1.0.0")
    prod_version = registry.get_production_version("test_model")
    print(f"✓ Production version: {prod_version}")
    
    # Test status
    status = registry.get_registry_status()
    print(f"✓ Registry status: {status['total_models']} models, {status['total_versions']} versions")
    
    print("\n✓ Model registry working correctly!")
