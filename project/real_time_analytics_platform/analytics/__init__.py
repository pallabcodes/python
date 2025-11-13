"""
Analytics layer with multiprocessing capabilities.

Provides:
- Multiprocessing analytics engine
- Statistical analysis and anomaly detection
- ML pipeline with GPU acceleration
- Advanced analytics with forecasting and predictive models
"""

from .analytics_engine import AnalyticsEngine
from .ml_processor import MLProcessor, MLModelConfig
from .advanced_analytics import AdvancedAnalyticsEngine, ForecastResult, AnomalyResult, TrendAnalysis

__all__ = [
    "AnalyticsEngine",
    "MLProcessor",
    "MLModelConfig",
    "AdvancedAnalyticsEngine",
    "ForecastResult",
    "AnomalyResult",
    "TrendAnalysis"
]
