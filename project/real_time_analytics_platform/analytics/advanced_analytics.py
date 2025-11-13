"""
Advanced Analytics with Predictive Models and Forecasting.

Demonstrates:
- Time series forecasting
- Anomaly detection algorithms
- Statistical analysis and trend detection
- Predictive modeling
- Integration with ML pipeline
"""

import asyncio
import time
import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta

# Scientific computing imports (with fallbacks)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    stats = None

logger = logging.getLogger(__name__)


@dataclass
class TimeSeriesPoint:
    """Time series data point."""
    timestamp: float
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForecastResult:
    """Forecasting result."""
    forecast_id: str
    metric_name: str
    current_value: float
    forecast_values: List[float]
    forecast_timestamps: List[float]
    confidence_intervals: Optional[List[Tuple[float, float]]] = None
    model_type: str = "linear"
    accuracy_score: Optional[float] = None


@dataclass
class AnomalyResult:
    """Anomaly detection result."""
    anomaly_id: str
    metric_name: str
    timestamp: float
    value: float
    anomaly_score: float
    anomaly_type: str  # "spike", "drop", "trend_change"
    severity: str  # "low", "medium", "high"
    expected_value: Optional[float] = None


@dataclass
class TrendAnalysis:
    """Trend analysis result."""
    metric_name: str
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0.0 to 1.0
    slope: float
    r_squared: float
    change_percentage: float


class TimeSeriesForecaster:
    """
    Time series forecasting using various models.
    
    Features:
    - Linear regression forecasting
    - Moving average forecasting
    - Exponential smoothing
    - Seasonal decomposition
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.time_series: Dict[str, deque] = {}
    
    def add_data_point(self, metric_name: str, timestamp: float, value: float):
        """Add a data point to time series."""
        if metric_name not in self.time_series:
            self.time_series[metric_name] = deque(maxlen=self.window_size)
        
        self.time_series[metric_name].append(TimeSeriesPoint(
            timestamp=timestamp,
            value=value
        ))
    
    def forecast(
        self,
        metric_name: str,
        steps: int = 10,
        model_type: str = "linear"
    ) -> Optional[ForecastResult]:
        """Generate forecast for a metric."""
        if metric_name not in self.time_series:
            logger.warning(f"No data for metric: {metric_name}")
            return None
        
        series = list(self.time_series[metric_name])
        if len(series) < 2:
            return None
        
        current_value = series[-1].value
        timestamps = [p.timestamp for p in series]
        values = [p.value for p in series]
        
        # Generate forecast timestamps
        last_timestamp = timestamps[-1]
        forecast_timestamps = [
            last_timestamp + (i + 1) * (timestamps[-1] - timestamps[-2])
            for i in range(steps)
        ]
        
        if model_type == "linear":
            forecast_values, confidence = self._linear_forecast(
                timestamps, values, steps
            )
        elif model_type == "moving_average":
            forecast_values, confidence = self._moving_average_forecast(
                values, steps
            )
        elif model_type == "exponential_smoothing":
            forecast_values, confidence = self._exponential_smoothing_forecast(
                values, steps
            )
        else:
            forecast_values, confidence = self._linear_forecast(
                timestamps, values, steps
            )
        
        return ForecastResult(
            forecast_id=f"forecast_{int(time.time()*1000)}",
            metric_name=metric_name,
            current_value=current_value,
            forecast_values=forecast_values,
            forecast_timestamps=forecast_timestamps,
            confidence_intervals=confidence,
            model_type=model_type
        )
    
    def _linear_forecast(
        self,
        timestamps: List[float],
        values: List[float],
        steps: int
    ) -> Tuple[List[float], Optional[List[Tuple[float, float]]]]:
        """Linear regression forecast."""
        if HAS_NUMPY and HAS_SCIPY:
            x = np.array(timestamps)
            y = np.array(values)
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Forecast
            last_timestamp = timestamps[-1]
            time_step = timestamps[-1] - timestamps[-2] if len(timestamps) > 1 else 1.0
            
            forecast_x = np.array([
                last_timestamp + (i + 1) * time_step
                for i in range(steps)
            ])
            
            forecast_y = slope * forecast_x + intercept
            
            # Confidence intervals (simplified)
            confidence = [
                (y - std_err * 2, y + std_err * 2)
                for y in forecast_y
            ]
            
            return forecast_y.tolist(), confidence
        else:
            # Simple linear extrapolation
            if len(values) < 2:
                return [values[-1]] * steps, None
            
            slope = (values[-1] - values[0]) / (timestamps[-1] - timestamps[0])
            last_value = values[-1]
            last_time = timestamps[-1]
            time_step = timestamps[-1] - timestamps[-2] if len(timestamps) > 1 else 1.0
            
            forecast = []
            for i in range(steps):
                forecast.append(last_value + slope * (i + 1) * time_step)
            
            return forecast, None
    
    def _moving_average_forecast(
        self,
        values: List[float],
        steps: int,
        window: int = 5
    ) -> Tuple[List[float], Optional[List[Tuple[float, float]]]]:
        """Moving average forecast."""
        if len(values) < window:
            return [values[-1]] * steps, None
        
        # Calculate moving average
        recent_values = values[-window:]
        avg = sum(recent_values) / len(recent_values)
        
        # Forecast as constant average
        forecast = [avg] * steps
        
        # Simple confidence interval
        std_dev = math.sqrt(sum((v - avg) ** 2 for v in recent_values) / len(recent_values))
        confidence = [
            (avg - std_dev * 2, avg + std_dev * 2)
            for _ in range(steps)
        ]
        
        return forecast, confidence
    
    def _exponential_smoothing_forecast(
        self,
        values: List[float],
        steps: int,
        alpha: float = 0.3
    ) -> Tuple[List[float], Optional[List[Tuple[float, float]]]]:
        """Exponential smoothing forecast."""
        if not values:
            return [], None
        
        # Calculate smoothed values
        smoothed = [values[0]]
        for i in range(1, len(values)):
            smoothed.append(alpha * values[i] + (1 - alpha) * smoothed[-1])
        
        # Forecast
        last_smoothed = smoothed[-1]
        forecast = [last_smoothed] * steps
        
        return forecast, None


class AnomalyDetector:
    """
    Advanced anomaly detection using statistical methods.
    
    Features:
    - Z-score based detection
    - Moving average deviation
    - Percentile-based detection
    - Trend change detection
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metric_history: Dict[str, deque] = {}
    
    def add_data_point(self, metric_name: str, timestamp: float, value: float):
        """Add a data point for anomaly detection."""
        if metric_name not in self.metric_history:
            self.metric_history[metric_name] = deque(maxlen=self.window_size)
        
        self.metric_history[metric_name].append((timestamp, value))
    
    def detect_anomaly(
        self,
        metric_name: str,
        timestamp: float,
        value: float,
        method: str = "z_score",
        threshold: float = 3.0
    ) -> Optional[AnomalyResult]:
        """Detect anomaly in a data point."""
        if metric_name not in self.metric_history:
            self.add_data_point(metric_name, timestamp, value)
            return None
        
        history = list(self.metric_history[metric_name])
        if len(history) < 10:
            self.add_data_point(metric_name, timestamp, value)
            return None
        
        values = [v for _, v in history]
        
        if method == "z_score":
            return self._z_score_detection(
                metric_name, timestamp, value, values, threshold
            )
        elif method == "percentile":
            return self._percentile_detection(
                metric_name, timestamp, value, values, threshold
            )
        elif method == "moving_average":
            return self._moving_average_detection(
                metric_name, timestamp, value, values, threshold
            )
        else:
            return self._z_score_detection(
                metric_name, timestamp, value, values, threshold
            )
    
    def _z_score_detection(
        self,
        metric_name: str,
        timestamp: float,
        value: float,
        history_values: List[float],
        threshold: float
    ) -> Optional[AnomalyResult]:
        """Z-score based anomaly detection."""
        if HAS_NUMPY:
            mean = np.mean(history_values)
            std = np.std(history_values)
        else:
            mean = sum(history_values) / len(history_values)
            variance = sum((x - mean) ** 2 for x in history_values) / len(history_values)
            std = math.sqrt(variance)
        
        if std == 0:
            return None
        
        z_score = abs((value - mean) / std)
        
        if z_score > threshold:
            anomaly_type = "spike" if value > mean else "drop"
            severity = (
                "high" if z_score > threshold * 2
                else "medium" if z_score > threshold * 1.5
                else "low"
            )
            
            return AnomalyResult(
                anomaly_id=f"anomaly_{int(time.time()*1000)}",
                metric_name=metric_name,
                timestamp=timestamp,
                value=value,
                anomaly_score=z_score,
                anomaly_type=anomaly_type,
                severity=severity,
                expected_value=mean
            )
        
        return None
    
    def _percentile_detection(
        self,
        metric_name: str,
        timestamp: float,
        value: float,
        history_values: List[float],
        threshold: float
    ) -> Optional[AnomalyResult]:
        """Percentile-based anomaly detection."""
        sorted_values = sorted(history_values)
        n = len(sorted_values)
        
        lower_percentile = sorted_values[int(n * 0.05)]
        upper_percentile = sorted_values[int(n * 0.95)]
        
        if value < lower_percentile or value > upper_percentile:
            anomaly_type = "spike" if value > upper_percentile else "drop"
            severity = "high" if abs(value - (lower_percentile + upper_percentile) / 2) > threshold else "medium"
            
            return AnomalyResult(
                anomaly_id=f"anomaly_{int(time.time()*1000)}",
                metric_name=metric_name,
                timestamp=timestamp,
                value=value,
                anomaly_score=abs(value - (lower_percentile + upper_percentile) / 2),
                anomaly_type=anomaly_type,
                severity=severity,
                expected_value=(lower_percentile + upper_percentile) / 2
            )
        
        return None
    
    def _moving_average_detection(
        self,
        metric_name: str,
        timestamp: float,
        value: float,
        history_values: List[float],
        threshold: float
    ) -> Optional[AnomalyResult]:
        """Moving average deviation detection."""
        window = min(10, len(history_values))
        recent_avg = sum(history_values[-window:]) / window
        
        deviation = abs(value - recent_avg) / recent_avg if recent_avg != 0 else 0
        
        if deviation > threshold:
            anomaly_type = "spike" if value > recent_avg else "drop"
            severity = "high" if deviation > threshold * 2 else "medium"
            
            return AnomalyResult(
                anomaly_id=f"anomaly_{int(time.time()*1000)}",
                metric_name=metric_name,
                timestamp=timestamp,
                value=value,
                anomaly_score=deviation,
                anomaly_type=anomaly_type,
                severity=severity,
                expected_value=recent_avg
            )
        
        return None


class TrendAnalyzer:
    """Trend analysis for time series data."""
    
    def analyze_trend(
        self,
        timestamps: List[float],
        values: List[float]
    ) -> TrendAnalysis:
        """Analyze trend in time series data."""
        if len(values) < 2:
            return TrendAnalysis(
                metric_name="unknown",
                trend_direction="stable",
                trend_strength=0.0,
                slope=0.0,
                r_squared=0.0,
                change_percentage=0.0
            )
        
        if HAS_NUMPY and HAS_SCIPY:
            x = np.array(timestamps)
            y = np.array(values)
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            trend_direction = (
                "increasing" if slope > 0
                else "decreasing" if slope < 0
                else "stable"
            )
            
            trend_strength = abs(r_value)
            change_percentage = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0.0
            
            return TrendAnalysis(
                metric_name="unknown",
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                slope=slope,
                r_squared=r_value ** 2,
                change_percentage=change_percentage
            )
        else:
            # Simple trend calculation
            slope = (values[-1] - values[0]) / (timestamps[-1] - timestamps[0]) if timestamps[-1] != timestamps[0] else 0
            trend_direction = (
                "increasing" if slope > 0
                else "decreasing" if slope < 0
                else "stable"
            )
            change_percentage = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0.0
            
            return TrendAnalysis(
                metric_name="unknown",
                trend_direction=trend_direction,
                trend_strength=abs(slope) / max(abs(values[-1]), 1.0),
                slope=slope,
                r_squared=0.0,
                change_percentage=change_percentage
            )


class AdvancedAnalyticsEngine:
    """
    Advanced analytics engine combining forecasting, anomaly detection, and trend analysis.
    
    Features:
    - Real-time forecasting
    - Anomaly detection
    - Trend analysis
    - Predictive insights
    """
    
    def __init__(self):
        self.forecaster = TimeSeriesForecaster(window_size=1000)
        self.anomaly_detector = AnomalyDetector(window_size=1000)
        self.trend_analyzer = TrendAnalyzer()
    
    def add_metric_point(self, metric_name: str, timestamp: float, value: float):
        """Add a metric data point for analysis."""
        self.forecaster.add_data_point(metric_name, timestamp, value)
        self.anomaly_detector.add_data_point(metric_name, timestamp, value)
    
    def generate_forecast(
        self,
        metric_name: str,
        steps: int = 10,
        model_type: str = "linear"
    ) -> Optional[ForecastResult]:
        """Generate forecast for a metric."""
        return self.forecaster.forecast(metric_name, steps, model_type)
    
    def detect_anomalies(
        self,
        metric_name: str,
        timestamp: float,
        value: float,
        method: str = "z_score"
    ) -> Optional[AnomalyResult]:
        """Detect anomalies in metric data."""
        return self.anomaly_detector.detect_anomaly(
            metric_name, timestamp, value, method
        )
    
    def analyze_trends(
        self,
        metric_name: str,
        timestamps: List[float],
        values: List[float]
    ) -> TrendAnalysis:
        """Analyze trends in metric data."""
        result = self.trend_analyzer.analyze_trend(timestamps, values)
        result.metric_name = metric_name
        return result


# Export engine
if not HAS_NUMPY:
    logger.warning("NumPy not available. Install numpy for advanced analytics.")
if not HAS_SCIPY:
    logger.warning("SciPy not available. Install scipy for statistical analysis.")

