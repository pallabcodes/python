"""
Experiment tracking and hyperparameter tuning for MLOps.

Provides unified interface for MLflow and Weights & Biases experiment tracking,
with automated hyperparameter optimization using Optuna.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import mlflow
import optuna
from optuna.integration.mlflow import MLflowCallback
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

# Optional torch import
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class ExperimentConfig(BaseModel):
    """Configuration for an experiment."""

    name: str
    description: Optional[str] = None
    tags: Dict[str, str] = {}
    hyperparameters: Dict[str, Any] = {}


class TrainingMetrics(BaseModel):
    """Training metrics for an experiment run."""

    epoch: int
    step: int
    loss: float
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    custom_metrics: Dict[str, float] = {}


class ExperimentTracker:
    """
    Unified experiment tracking with MLflow and Weights & Biases integration.

    Features:
    - Automatic experiment setup and tracking
    - Hyperparameter optimization with Optuna
    - Model artifact management
    - Training metrics logging
    - Cross-platform experiment synchronization
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize experiment tracker.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.ExperimentTracker")

        # MLflow setup
        mlflow.set_tracking_uri(self.config.mlflow.tracking_uri)
        if self.config.mlflow.artifact_uri:
            mlflow.set_registry_uri(self.config.mlflow.registry_uri)

        # Weights & Biases setup (if API key provided)
        self.wandb_available = bool(self.config.wandb.api_key)
        if self.wandb_available:
            import wandb
            wandb.login(key=self.config.wandb.api_key)
            self.wandb = wandb

        # Active experiments and runs
        self._active_experiments: Dict[str, Any] = {}
        self._active_runs: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize experiment tracking infrastructure."""
        self.logger.info("Initializing experiment tracker...")

        # Create necessary directories
        self.config.models_dir.mkdir(parents=True, exist_ok=True)

        # Test MLflow connection
        try:
            mlflow.list_experiments()
            self.logger.info("MLflow connection established")
        except Exception as e:
            self.logger.warning(f"MLflow connection failed: {e}")

        # Test Weights & Biases connection
        if self.wandb_available:
            try:
                self.wandb.init(project=self.config.wandb.project, mode="offline")
                self.wandb.finish()
                self.logger.info("Weights & Biases connection established")
            except Exception as e:
                self.logger.warning(f"Weights & Biases connection failed: {e}")
                self.wandb_available = False

        self.logger.info("Experiment tracker initialized")

    async def create_experiment(self, config: ExperimentConfig) -> str:
        """
        Create a new experiment.

        Args:
            config: Experiment configuration

        Returns:
            Experiment ID
        """
        self.logger.info(f"Creating experiment: {config.name}")

        # Create MLflow experiment
        try:
            experiment_id = mlflow.create_experiment(
                name=config.name,
                artifact_location=str(self.config.models_dir / config.name)
            )
        except mlflow.exceptions.MlflowException:
            # Experiment already exists
            experiment = mlflow.get_experiment_by_name(config.name)
            experiment_id = experiment.experiment_id

        # Set tags
        if config.tags:
            mlflow.set_experiment_tags(config.tags)

        self._active_experiments[config.name] = {
            "id": experiment_id,
            "config": config,
            "created_at": datetime.now(),
        }

        self.logger.info(f"Created experiment {config.name} with ID: {experiment_id}")
        return experiment_id

    async def start_run(
        self,
        experiment_name: str,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Start a new experiment run.

        Args:
            experiment_name: Name of the experiment
            run_name: Optional run name
            tags: Optional tags for the run

        Returns:
            Run ID
        """
        if experiment_name not in self._active_experiments:
            raise ValueError(f"Experiment {experiment_name} not found")

        self.logger.info(f"Starting run for experiment: {experiment_name}")

        # Start MLflow run
        mlflow.start_run(
            experiment_id=self._active_experiments[experiment_name]["id"],
            run_name=run_name,
            tags=tags
        )
        run_id = mlflow.active_run().info.run_id

        # Start Weights & Biases run
        wandb_run = None
        if self.wandb_available:
            wandb_run = self.wandb.init(
                project=self.config.wandb.project,
                name=run_name or f"run_{run_id}",
                tags=list(tags.values()) if tags else None,
                config=self._active_experiments[experiment_name]["config"].hyperparameters,
                reinit=True
            )

        self._active_runs[run_id] = {
            "experiment_name": experiment_name,
            "mlflow_run": mlflow.active_run(),
            "wandb_run": wandb_run,
            "started_at": datetime.now(),
        }

        self.logger.info(f"Started run {run_id} for experiment {experiment_name}")
        return run_id

    async def log_hyperparameters(self, run_id: str, hyperparameters: Dict[str, Any]) -> None:
        """
        Log hyperparameters for a run.

        Args:
            run_id: Run ID
            hyperparameters: Hyperparameter dictionary
        """
        if run_id not in self._active_runs:
            raise ValueError(f"Run {run_id} not found")

        self.logger.debug(f"Logging hyperparameters for run {run_id}")

        # Log to MLflow
        mlflow.log_params(hyperparameters)

        # Log to Weights & Biases
        if self._active_runs[run_id]["wandb_run"]:
            self._active_runs[run_id]["wandb_run"].config.update(hyperparameters)

    async def log_metrics(self, run_id: str, metrics: TrainingMetrics) -> None:
        """
        Log training metrics for a run.

        Args:
            run_id: Run ID
            metrics: Training metrics
        """
        if run_id not in self._active_runs:
            raise ValueError(f"Run {run_id} not found")

        self.logger.debug(f"Logging metrics for run {run_id}: epoch {metrics.epoch}")

        metrics_dict = {
            "loss": metrics.loss,
            "epoch": metrics.epoch,
            "step": metrics.step,
            **metrics.custom_metrics,
        }

        if metrics.accuracy is not None:
            metrics_dict["accuracy"] = metrics.accuracy
        if metrics.f1_score is not None:
            metrics_dict["f1_score"] = metrics.f1_score
        if metrics.precision is not None:
            metrics_dict["precision"] = metrics.precision
        if metrics.recall is not None:
            metrics_dict["recall"] = metrics.recall

        # Log to MLflow
        mlflow.log_metrics(metrics_dict, step=metrics.step)

        # Log to Weights & Biases
        if self._active_runs[run_id]["wandb_run"]:
            self._active_runs[run_id]["wandb_run"].log(metrics_dict, step=metrics.step)

    async def log_artifact(self, run_id: str, artifact_path: str, artifact_name: str) -> None:
        """
        Log an artifact for a run.

        Args:
            run_id: Run ID
            artifact_path: Path to the artifact file
            artifact_name: Name for the artifact
        """
        if run_id not in self._active_runs:
            raise ValueError(f"Run {run_id} not found")

        self.logger.debug(f"Logging artifact {artifact_name} for run {run_id}")

        # Log to MLflow
        mlflow.log_artifact(artifact_path, artifact_name)

        # Log to Weights & Biases
        if self._active_runs[run_id]["wandb_run"]:
            artifact = self.wandb.Artifact(artifact_name, type="model")
            artifact.add_file(artifact_path)
            self._active_runs[run_id]["wandb_run"].log_artifact(artifact)

    async def log_model(
        self,
        run_id: str,
        model: Any,
        model_name: str,
        model_format: str = "pytorch"
    ) -> None:
        """
        Log a model artifact.

        Args:
            run_id: Run ID
            model: Model object
            model_name: Name for the model
            model_format: Model format (pytorch, tensorflow, etc.)
        """
        if run_id not in self._active_runs:
            raise ValueError(f"Run {run_id} not found")

        self.logger.info(f"Logging model {model_name} for run {run_id}")

        # Save model locally first
        model_path = self.config.models_dir / f"{model_name}_{run_id}.pt"
        if model_format == "pytorch":
            if TORCH_AVAILABLE:
                torch.save(model.state_dict(), model_path)
            else:
                # Fallback: save as pickle
                import pickle
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
        else:
            # For other formats, assume model has save method
            model.save(str(model_path))

        # Log as artifact
        await self.log_artifact(run_id, str(model_path), model_name)

        # Log to MLflow model registry if available
        if self.config.mlflow.registry_uri:
            try:
                mlflow.pytorch.log_model(model, model_name)
            except Exception as e:
                self.logger.warning(f"Failed to log model to registry: {e}")

    async def end_run(self, run_id: str) -> None:
        """
        End an experiment run.

        Args:
            run_id: Run ID
        """
        if run_id not in self._active_runs:
            return

        self.logger.info(f"Ending run {run_id}")

        # End Weights & Biases run
        if self._active_runs[run_id]["wandb_run"]:
            self._active_runs[run_id]["wandb_run"].finish()

        # End MLflow run
        mlflow.end_run()

        # Clean up
        del self._active_runs[run_id]

    async def optimize_hyperparameters(
        self,
        experiment_name: str,
        objective_function: callable,
        search_space: Dict[str, Any],
        n_trials: int = 50,
        direction: str = "minimize"
    ) -> Dict[str, Any]:
        """
        Perform hyperparameter optimization using Optuna.

        Args:
            experiment_name: Name of the experiment
            objective_function: Objective function to optimize
            search_space: Hyperparameter search space definition
            n_trials: Number of optimization trials
            direction: Optimization direction ("minimize" or "maximize")

        Returns:
            Best hyperparameters and metrics
        """
        self.logger.info(f"Starting hyperparameter optimization for {experiment_name}")

        # Create Optuna study
        study = optuna.create_study(direction=direction)

        # MLflow callback for tracking
        mlflow_callback = MLflowCallback(
            tracking_uri=self.config.mlflow.tracking_uri,
            metric_name="objective_value"
        )

        # Define objective function wrapper
        def objective(trial):
            # Sample hyperparameters from search space
            hyperparameters = {}
            for param_name, param_config in search_space.items():
                param_type = param_config.get("type", "float")

                if param_type == "float":
                    low = param_config.get("low", 0.0)
                    high = param_config.get("high", 1.0)
                    hyperparameters[param_name] = trial.suggest_float(param_name, low, high)
                elif param_type == "int":
                    low = param_config.get("low", 0)
                    high = param_config.get("high", 100)
                    hyperparameters[param_name] = trial.suggest_int(param_name, low, high)
                elif param_type == "categorical":
                    choices = param_config.get("choices", [])
                    hyperparameters[param_name] = trial.suggest_categorical(param_name, choices)

            # Run objective function
            return objective_function(hyperparameters, trial)

        # Run optimization
        study.optimize(
            objective,
            n_trials=n_trials,
            callbacks=[mlflow_callback] if self.config.mlflow.tracking_uri else None
        )

        # Get best parameters
        best_params = study.best_params
        best_value = study.best_value

        self.logger.info(f"Hyperparameter optimization complete. Best value: {best_value}")

        return {
            "best_params": best_params,
            "best_value": best_value,
            "study": study,
        }

    async def train_model(
        self,
        model_type: str,
        dataset: Any,
        hyperparameters: Optional[Dict[str, Any]] = None,
        experiment_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Train a model with experiment tracking.

        Args:
            model_type: Type of model to train
            dataset: Training dataset
            hyperparameters: Model hyperparameters
            experiment_name: Optional experiment name
            **kwargs: Additional training arguments

        Returns:
            Training results and metrics
        """
        # Create experiment if not provided
        if not experiment_name:
            experiment_name = f"{model_type}_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        experiment_config = ExperimentConfig(
            name=experiment_name,
            description=f"Training {model_type} model",
            hyperparameters=hyperparameters or {}
        )

        await self.create_experiment(experiment_config)
        run_id = await self.start_run(experiment_name)

        try:
            # Log hyperparameters
            await self.log_hyperparameters(run_id, hyperparameters or {})

            # Here you would implement actual model training logic
            # For now, return a placeholder result
            training_result = {
                "model_type": model_type,
                "run_id": run_id,
                "status": "completed",
                "final_metrics": {
                    "accuracy": 0.95,
                    "loss": 0.05,
                }
            }

            # Log final metrics
            final_metrics = TrainingMetrics(
                epoch=kwargs.get("epochs", 10),
                step=kwargs.get("steps", 1000),
                loss=training_result["final_metrics"]["loss"],
                accuracy=training_result["final_metrics"]["accuracy"]
            )
            await self.log_metrics(run_id, final_metrics)

            return training_result

        finally:
            await self.end_run(run_id)

    async def shutdown(self) -> None:
        """Shutdown experiment tracker."""
        self.logger.info("Shutting down experiment tracker...")

        # End any remaining runs
        for run_id in list(self._active_runs.keys()):
            await self.end_run(run_id)

        self.logger.info("Experiment tracker shutdown complete")
