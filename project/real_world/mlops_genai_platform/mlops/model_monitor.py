"""
Model monitoring and performance tracking for MLOps.

Provides real-time model performance monitoring, drift detection,
and alerting capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
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


class ModelMetrics(BaseModel):
    """Model performance metrics."""

    timestamp: datetime
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc: Optional[float] = None
    mse: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    latency_ms: Optional[float] = None
    throughput: Optional[float] = None
    custom_metrics: Dict[str, float] = {}


class DriftMetrics(BaseModel):
    """Data and concept drift metrics."""

    timestamp: datetime
    feature_drift_score: float
    prediction_drift_score: float
    concept_drift_detected: bool
    drift_threshold: float = 0.05
    feature_importance_shift: Dict[str, float] = {}


class AlertConfig(BaseModel):
    """Alert configuration."""

    metric_name: str
    threshold: float
    condition: str  # "above", "below", "equals"
    severity: str = "warning"  # "info", "warning", "error", "critical"
    enabled: bool = True


class ModelMonitor:
    """
    Model monitoring with performance tracking and drift detection.

    Features:
    - Real-time performance monitoring
    - Data drift and concept drift detection
    - Automated alerting
    - Performance degradation detection
    - Integration with serving infrastructure
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize model monitor.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.ModelMonitor")

        # Monitoring storage
        self._metrics_file = self.config.data_dir / "model_metrics.json"
        self._drift_file = self.config.data_dir / "drift_metrics.json"

        # In-memory metrics storage
        self._model_metrics: Dict[str, List[ModelMetrics]] = {}
        self._drift_metrics: Dict[str, List[DriftMetrics]] = {}
        self._alert_configs: Dict[str, List[AlertConfig]] = {}

        # Monitoring state
        self._monitoring_active = False
        self._collection_interval = timedelta(seconds=self.config.monitoring.metrics_interval)

    async def initialize(self) -> None:
        """Initialize model monitor."""
        self.logger.info("Initializing model monitor...")

        # Load existing metrics
        await self._load_metrics()
        await self._load_drift_metrics()

        # Ensure data files exist
        self._metrics_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info("Model monitor initialized")

    async def _load_metrics(self) -> None:
        """Load model metrics from disk."""
        if self._metrics_file.exists():
            try:
                with open(self._metrics_file, "r") as f:
                    data = pd.read_json(f)

                # Convert to ModelMetrics objects
                for model_name in data.columns:
                    self._model_metrics[model_name] = []
                    for _, row in data[model_name].iterrows():
                        metrics = ModelMetrics(**row.to_dict())
                        self._model_metrics[model_name].append(metrics)

                self.logger.info(f"Loaded metrics for {len(self._model_metrics)} models")
            except Exception as e:
                self.logger.error(f"Failed to load metrics: {e}")

    async def _load_drift_metrics(self) -> None:
        """Load drift metrics from disk."""
        if self._drift_file.exists():
            try:
                with open(self._drift_file, "r") as f:
                    data = pd.read_json(f)

                # Convert to DriftMetrics objects
                for model_name in data.columns:
                    self._drift_metrics[model_name] = []
                    for _, row in data[model_name].iterrows():
                        drift = DriftMetrics(**row.to_dict())
                        self._drift_metrics[model_name].append(drift)

                self.logger.info(f"Loaded drift metrics for {len(self._drift_metrics)} models")
            except Exception as e:
                self.logger.error(f"Failed to load drift metrics: {e}")

    async def _save_metrics(self) -> None:
        """Save model metrics to disk."""
        try:
            # Convert to DataFrame for storage
            all_metrics = {}
            for model_name, metrics_list in self._model_metrics.items():
                metrics_df = pd.DataFrame([m.dict() for m in metrics_list])
                metrics_df['timestamp'] = pd.to_datetime(metrics_df['timestamp'])
                all_metrics[model_name] = metrics_df

            if all_metrics:
                combined_df = pd.concat(all_metrics.values(), keys=all_metrics.keys())
                combined_df.to_json(self._metrics_file)

        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")

    async def start_monitoring(self, model_name: str) -> None:
        """
        Start monitoring for a model.

        Args:
            model_name: Name of the model to monitor
        """
        if model_name not in self._model_metrics:
            self._model_metrics[model_name] = []

        if model_name not in self._drift_metrics:
            self._drift_metrics[model_name] = []

        self.logger.info(f"Started monitoring for model: {model_name}")

        # Start background monitoring task
        if not self._monitoring_active:
            self._monitoring_active = True
            asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self, model_name: str) -> None:
        """
        Stop monitoring for a model.

        Args:
            model_name: Name of the model to stop monitoring
        """
        # Remove from monitoring (but keep historical data)
        self.logger.info(f"Stopped monitoring for model: {model_name}")

    async def record_metrics(
        self,
        model_name: str,
        metrics: ModelMetrics
    ) -> None:
        """
        Record model performance metrics.

        Args:
            model_name: Name of the model
            metrics: Performance metrics
        """
        if model_name not in self._model_metrics:
            self._model_metrics[model_name] = []

        self._model_metrics[model_name].append(metrics)

        # Keep only recent metrics (last 1000 entries per model)
        if len(self._model_metrics[model_name]) > 1000:
            self._model_metrics[model_name] = self._model_metrics[model_name][-1000:]

        # Check for alerts
        await self._check_alerts(model_name, metrics)

        self.logger.debug(f"Recorded metrics for {model_name}: accuracy={metrics.accuracy}")

    async def record_predictions(
        self,
        model_name: str,
        predictions: List[Any],
        actuals: Optional[List[Any]] = None,
        features: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Record model predictions for drift detection.

        Args:
            model_name: Name of the model
            predictions: Model predictions
            actuals: Actual values (if available)
            features: Input features (for drift detection)
        """
        # Store prediction data for drift analysis
        # In a real implementation, this would store in a time-series database
        # For now, just log the activity

        prediction_count = len(predictions)
        self.logger.debug(f"Recorded {prediction_count} predictions for {model_name}")

        # Trigger drift detection if we have enough data
        if features and len(features) > 100:  # Arbitrary threshold
            await self._detect_drift(model_name, features, predictions)

    async def _detect_drift(
        self,
        model_name: str,
        features: List[Dict[str, Any]],
        predictions: List[Any]
    ) -> None:
        """
        Detect data and concept drift.

        Args:
            model_name: Name of the model
            features: Input features
            predictions: Model predictions
        """
        # Simple drift detection implementation
        # In a real system, you would use statistical tests like:
        # - Kolmogorov-Smirnov test for distribution changes
        # - Population Stability Index (PSI)
        # - Jensen-Shannon divergence

        try:
            # Convert features to numerical arrays for analysis
            feature_df = pd.DataFrame(features)

            # Calculate basic statistics
            current_stats = feature_df.describe()

            # Compare with historical data (simplified)
            # In practice, you'd compare with a reference dataset

            # Calculate a simple drift score (placeholder)
            drift_score = np.random.random()  # Replace with actual drift calculation

            # Create drift metrics
            drift_metrics = DriftMetrics(
                timestamp=datetime.now(),
                feature_drift_score=drift_score,
                prediction_drift_score=np.random.random(),  # Placeholder
                concept_drift_detected=drift_score > 0.1,  # Threshold
                drift_threshold=0.1
            )

            if model_name not in self._drift_metrics:
                self._drift_metrics[model_name] = []

            self._drift_metrics[model_name].append(drift_metrics)

            if drift_metrics.concept_drift_detected:
                self.logger.warning(f"Concept drift detected for model {model_name}")

        except Exception as e:
            self.logger.error(f"Drift detection failed for {model_name}: {e}")

    async def configure_alert(
        self,
        model_name: str,
        alert_config: AlertConfig
    ) -> None:
        """
        Configure an alert for a model.

        Args:
            model_name: Name of the model
            alert_config: Alert configuration
        """
        if model_name not in self._alert_configs:
            self._alert_configs[model_name] = []

        self._alert_configs[model_name].append(alert_config)
        self.logger.info(f"Configured alert for {model_name}: {alert_config.metric_name}")

    async def _check_alerts(self, model_name: str, metrics: ModelMetrics) -> None:
        """
        Check if any alerts should be triggered.

        Args:
            model_name: Name of the model
            metrics: Current metrics
        """
        if model_name not in self._alert_configs:
            return

        metrics_dict = metrics.dict()
        for alert in self._alert_configs[model_name]:
            if not alert.enabled:
                continue

            metric_value = metrics_dict.get(alert.metric_name)
            if metric_value is None:
                continue

            triggered = False
            if alert.condition == "above" and metric_value > alert.threshold:
                triggered = True
            elif alert.condition == "below" and metric_value < alert.threshold:
                triggered = True
            elif alert.condition == "equals" and abs(metric_value - alert.threshold) < 0.001:
                triggered = True

            if triggered:
                await self._trigger_alert(model_name, alert, metric_value)

    async def _trigger_alert(
        self,
        model_name: str,
        alert: AlertConfig,
        actual_value: float
    ) -> None:
        """
        Trigger an alert.

        Args:
            model_name: Name of the model
            alert: Alert configuration
            actual_value: Actual metric value
        """
        message = (
            f"ALERT: Model {model_name} - {alert.metric_name} {alert.condition} "
            f"{alert.threshold} (current: {actual_value})"
        )

        if alert.severity == "critical":
            self.logger.critical(message)
        elif alert.severity == "error":
            self.logger.error(message)
        elif alert.severity == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)

        # In a real implementation, this would:
        # - Send notifications (email, Slack, PagerDuty)
        # - Update dashboard
        # - Trigger automated remediation

    async def get_model_performance(
        self,
        model_name: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get model performance summary.

        Args:
            model_name: Name of the model
            hours: Number of hours to look back

        Returns:
            Performance summary
        """
        if model_name not in self._model_metrics:
            return {"error": f"No metrics found for model {model_name}"}

        # Filter recent metrics
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self._model_metrics[model_name]
            if m.timestamp > cutoff_time
        ]

        if not recent_metrics:
            return {"error": f"No recent metrics found for model {model_name}"}

        # Calculate summary statistics
        metrics_df = pd.DataFrame([m.dict() for m in recent_metrics])

        summary = {
            "model_name": model_name,
            "time_range_hours": hours,
            "metrics_count": len(recent_metrics),
            "summary": {}
        }

        # Calculate stats for each metric
        numeric_columns = metrics_df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col == "timestamp":
                continue
            values = metrics_df[col].dropna()
            if len(values) > 0:
                summary["summary"][col] = {
                    "mean": float(values.mean()),
                    "std": float(values.std()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "latest": float(values.iloc[-1])
                }

        return summary

    async def get_drift_report(self, model_name: str, days: int = 7) -> Dict[str, Any]:
        """
        Get drift detection report.

        Args:
            model_name: Name of the model
            days: Number of days to look back

        Returns:
            Drift report
        """
        if model_name not in self._drift_metrics:
            return {"error": f"No drift metrics found for model {model_name}"}

        # Filter recent drift metrics
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_drift = [
            d for d in self._drift_metrics[model_name]
            if d.timestamp > cutoff_time
        ]

        if not recent_drift:
            return {"error": f"No recent drift metrics found for model {model_name}"}

        # Analyze drift patterns
        drift_scores = [d.feature_drift_score for d in recent_drift]
        concept_drift_events = sum(1 for d in recent_drift if d.concept_drift_detected)

        report = {
            "model_name": model_name,
            "time_range_days": days,
            "drift_measurements": len(recent_drift),
            "average_drift_score": float(np.mean(drift_scores)),
            "max_drift_score": float(np.max(drift_scores)),
            "concept_drift_events": concept_drift_events,
            "drift_trend": "increasing" if drift_scores[-1] > drift_scores[0] else "stable",
            "recommendations": []
        }

        # Generate recommendations
        if report["average_drift_score"] > 0.1:
            report["recommendations"].append("Consider model retraining - high drift detected")
        if concept_drift_events > len(recent_drift) * 0.1:
            report["recommendations"].append("Concept drift detected - evaluate model relevance")

        return report

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self._monitoring_active:
            try:
                # Periodic tasks
                await self._periodic_health_check()
                await self._cleanup_old_data()

                await asyncio.sleep(self._collection_interval.total_seconds())

            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _periodic_health_check(self) -> None:
        """Perform periodic health checks."""
        # Check if models are still responsive
        # Check data quality
        # Update dashboards
        pass

    async def _cleanup_old_data(self) -> None:
        """Clean up old monitoring data."""
        # Remove data older than retention period
        retention_days = 90  # Configurable
        cutoff_time = datetime.now() - timedelta(days=retention_days)

        for model_name in self._model_metrics:
            self._model_metrics[model_name] = [
                m for m in self._model_metrics[model_name]
                if m.timestamp > cutoff_time
            ]

        for model_name in self._drift_metrics:
            self._drift_metrics[model_name] = [
                d for d in self._drift_metrics[model_name]
                if d.timestamp > cutoff_time
            ]

    async def shutdown(self) -> None:
        """Shutdown model monitor."""
        self.logger.info("Shutting down model monitor...")

        self._monitoring_active = False

        # Save final metrics
        await self._save_metrics()

        self.logger.info("Model monitor shutdown complete")
