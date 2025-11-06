"""
Model registry and versioning for MLOps.

Provides enterprise-grade model management with versioning, metadata tracking,
and deployment lifecycle management.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import mlflow
from pydantic import BaseModel

try:
    from ..core.config import PlatformConfig
except ImportError:
    # Fallback for direct imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from core.config import PlatformConfig


class ModelMetadata(BaseModel):
    """Metadata for a registered model."""

    name: str
    version: str
    description: Optional[str] = None
    model_type: str
    framework: str
    hyperparameters: Dict[str, Any] = {}
    metrics: Dict[str, float] = {}
    tags: Dict[str, str] = {}
    created_at: datetime
    updated_at: datetime
    experiment_id: Optional[str] = None
    run_id: Optional[str] = None
    artifact_path: Optional[str] = None
    status: str = "development"  # development, staging, production, archived


class ModelVersion(BaseModel):
    """Model version information."""

    version: str
    model_uri: str
    metadata: ModelMetadata
    created_at: datetime


class ModelRegistry:
    """
    Enterprise model registry with versioning and lifecycle management.

    Features:
    - Model versioning and metadata tracking
    - Stage transitions (dev → staging → production)
    - Model artifact management
    - Deployment tracking and rollback
    - Integration with MLflow registry
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize model registry.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.ModelRegistry")

        # Registry storage
        self._registry_file = self.config.data_dir / "model_registry.json"
        self._models: Dict[str, Dict[str, ModelMetadata]] = {}

        # MLflow setup
        if self.config.mlflow.registry_uri:
            mlflow.set_registry_uri(self.config.mlflow.registry_uri)

    async def initialize(self) -> None:
        """Initialize model registry."""
        self.logger.info("Initializing model registry...")

        # Load existing registry
        await self._load_registry()

        # Ensure registry file exists
        self._registry_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Model registry initialized with {len(self._models)} models")

    async def _load_registry(self) -> None:
        """Load model registry from disk."""
        if self._registry_file.exists():
            try:
                with open(self._registry_file, "r") as f:
                    data = json.load(f)

                # Convert back to ModelMetadata objects
                for model_name, versions in data.items():
                    self._models[model_name] = {}
                    for version, metadata_dict in versions.items():
                        # Convert datetime strings back
                        metadata_dict["created_at"] = datetime.fromisoformat(metadata_dict["created_at"])
                        metadata_dict["updated_at"] = datetime.fromisoformat(metadata_dict["updated_at"])
                        self._models[model_name][version] = ModelMetadata(**metadata_dict)

                self.logger.info(f"Loaded {len(self._models)} models from registry")
            except Exception as e:
                self.logger.error(f"Failed to load registry: {e}")
        else:
            self.logger.info("No existing registry found, starting fresh")

    async def _save_registry(self) -> None:
        """Save model registry to disk."""
        try:
            # Convert to serializable format
            data = {}
            for model_name, versions in self._models.items():
                data[model_name] = {}
                for version, metadata in versions.items():
                    metadata_dict = metadata.dict()
                    # Convert datetimes to ISO format
                    metadata_dict["created_at"] = metadata.created_at.isoformat()
                    metadata_dict["updated_at"] = metadata.updated_at.isoformat()
                    data[model_name][version] = metadata_dict

            with open(self._registry_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save registry: {e}")

    async def register_model(
        self,
        name: str,
        model_artifact: Any,
        metadata: ModelMetadata,
        experiment_id: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> str:
        """
        Register a new model version.

        Args:
            name: Model name
            model_artifact: Model artifact (file path or object)
            metadata: Model metadata
            experiment_id: Optional experiment ID
            run_id: Optional run ID

        Returns:
            Model version
        """
        self.logger.info(f"Registering model: {name}")

        # Generate version number
        existing_versions = list(self._models.get(name, {}).keys())
        if not existing_versions:
            version = "1.0.0"
            self._models[name] = {}
        else:
            # Simple versioning: increment patch version
            latest_version = max(existing_versions, key=lambda v: [int(x) for x in v.split('.')])
            major, minor, patch = map(int, latest_version.split('.'))
            version = f"{major}.{minor}.{patch + 1}"

        # Update metadata
        metadata.version = version
        metadata.created_at = datetime.now()
        metadata.updated_at = datetime.now()
        metadata.experiment_id = experiment_id
        metadata.run_id = run_id

        # Store artifact
        artifact_path = self.config.models_dir / name / version
        artifact_path.mkdir(parents=True, exist_ok=True)

        if isinstance(model_artifact, str):
            # Copy file
            import shutil
            shutil.copy2(model_artifact, artifact_path / "model.pkl")
        elif hasattr(model_artifact, 'save'):
            # Save method
            model_artifact.save(str(artifact_path / "model.pkl"))
        else:
            # Assume it's a PyTorch model
            import torch
            torch.save(model_artifact.state_dict(), artifact_path / "model.pt")

        metadata.artifact_path = str(artifact_path)

        # Store in registry
        self._models[name][version] = metadata
        await self._save_registry()

        # Register with MLflow if available
        if self.config.mlflow.registry_uri:
            try:
                mlflow.register_model(
                    f"models:/{name}/{version}",
                    name
                )
            except Exception as e:
                self.logger.warning(f"Failed to register with MLflow: {e}")

        self.logger.info(f"Registered model {name} version {version}")
        return version

    async def get_model(self, name: str, version: Optional[str] = None) -> Optional[ModelMetadata]:
        """
        Get model metadata.

        Args:
            name: Model name
            version: Optional version (latest if not specified)

        Returns:
            Model metadata or None if not found
        """
        if name not in self._models:
            return None

        if version is None:
            # Get latest version
            versions = list(self._models[name].keys())
            if not versions:
                return None
            version = max(versions, key=lambda v: [int(x) for x in v.split('.')])

        return self._models[name].get(version)

    async def list_models(self, name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List registered models.

        Args:
            name_filter: Optional name filter

        Returns:
            List of model summaries
        """
        models = []

        for model_name, versions in self._models.items():
            if name_filter and name_filter not in model_name:
                continue

            latest_version = max(versions.keys(), key=lambda v: [int(x) for x in v.split('.')])
            metadata = versions[latest_version]

            models.append({
                "name": model_name,
                "latest_version": latest_version,
                "versions": len(versions),
                "status": metadata.status,
                "model_type": metadata.model_type,
                "created_at": metadata.created_at,
                "updated_at": metadata.updated_at,
            })

        return sorted(models, key=lambda x: x["updated_at"], reverse=True)

    async def update_model_status(self, name: str, version: str, status: str) -> bool:
        """
        Update model status.

        Args:
            name: Model name
            version: Model version
            status: New status

        Returns:
            True if updated, False otherwise
        """
        if name not in self._models or version not in self._models[name]:
            return False

        valid_statuses = ["development", "staging", "production", "archived"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        self._models[name][version].status = status
        self._models[name][version].updated_at = datetime.now()

        await self._save_registry()

        self.logger.info(f"Updated model {name}:{version} status to {status}")
        return True

    async def delete_model(self, name: str, version: Optional[str] = None) -> bool:
        """
        Delete a model or model version.

        Args:
            name: Model name
            version: Optional version (deletes all versions if not specified)

        Returns:
            True if deleted, False otherwise
        """
        if name not in self._models:
            return False

        if version is None:
            # Delete entire model
            del self._models[name]
            self.logger.info(f"Deleted model: {name}")
        else:
            # Delete specific version
            if version not in self._models[name]:
                return False
            del self._models[name][version]
            self.logger.info(f"Deleted model {name}:{version}")

            # If no versions left, remove model entirely
            if not self._models[name]:
                del self._models[name]

        await self._save_registry()
        return True

    async def deploy_model(self, name: str, version: str, target: str = "production") -> str:
        """
        Deploy a model to a target environment.

        Args:
            name: Model name
            version: Model version
            target: Deployment target

        Returns:
            Deployment ID
        """
        metadata = await self.get_model(name, version)
        if not metadata:
            raise ValueError(f"Model {name}:{version} not found")

        self.logger.info(f"Deploying model {name}:{version} to {target}")

        # Update status to production
        await self.update_model_status(name, version, "production")

        # Here you would implement actual deployment logic
        # For now, just return a deployment ID
        deployment_id = f"deploy_{name}_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # In a real implementation, this would:
        # - Copy model to deployment directory
        # - Update serving configuration
        # - Restart serving infrastructure
        # - Update load balancer/routing

        self.logger.info(f"Model {name}:{version} deployed with ID: {deployment_id}")
        return deployment_id

    async def get_model_versions(self, name: str) -> List[ModelVersion]:
        """
        Get all versions of a model.

        Args:
            name: Model name

        Returns:
            List of model versions
        """
        if name not in self._models:
            return []

        versions = []
        for version, metadata in self._models[name].items():
            versions.append(ModelVersion(
                version=version,
                model_uri=metadata.artifact_path or "",
                metadata=metadata,
                created_at=metadata.created_at
            ))

        return sorted(versions, key=lambda x: x.created_at, reverse=True)

    async def compare_models(
        self,
        model_names: List[str],
        metric: str = "accuracy"
    ) -> Dict[str, Any]:
        """
        Compare models based on a metric.

        Args:
            model_names: List of model names to compare
            metric: Metric to compare on

        Returns:
            Comparison results
        """
        comparison = {}

        for name in model_names:
            metadata = await self.get_model(name)
            if metadata and metric in metadata.metrics:
                comparison[name] = {
                    "version": metadata.version,
                    "metric_value": metadata.metrics[metric],
                    "status": metadata.status,
                }

        return comparison

    async def shutdown(self) -> None:
        """Shutdown model registry."""
        self.logger.info("Shutting down model registry...")

        # Save final state
        await self._save_registry()

        self.logger.info("Model registry shutdown complete")
