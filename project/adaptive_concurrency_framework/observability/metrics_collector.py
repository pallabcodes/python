"""
Metrics collector for the adaptive concurrency framework.

Collects metrics from all components:
- Workload analyzer metrics
- Benchmark results
- Optimization decisions
- Performance profiler data
- Resource usage
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Single metric value."""
    
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Metrics collector for the adaptive concurrency framework.
    
    Collects and aggregates metrics from:
    - Workload analyzer
    - Benchmark runner
    - Adaptive optimizer
    - Performance profiler
    - Real-time adapter
    """
    
    def __init__(self, max_metrics: int = 10000):
        """
        Initialize metrics collector.
        
        Args:
            max_metrics: Maximum number of metrics to keep in memory
        """
        self.max_metrics = max_metrics
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._metrics: Dict[str, deque] = {}
        self._lock = asyncio.Lock()
        
    async def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags
        """
        async with self._lock:
            if name not in self._metrics:
                self._metrics[name] = deque(maxlen=self.max_metrics)
            
            metric = Metric(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags or {}
            )
            
            self._metrics[name].append(metric)
    
    async def get_metric(self, name: str) -> Optional[List[Metric]]:
        """Get all values for a metric."""
        async with self._lock:
            if name in self._metrics:
                return list(self._metrics[name])
            return None
    
    async def get_metric_summary(self, name: str) -> Optional[Dict[str, float]]:
        """Get summary statistics for a metric."""
        metrics = await self.get_metric(name)
        if not metrics:
            return None
        
        values = [m.value for m in metrics]
        
        if not values:
            return None
        
        import statistics
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        }
    
    async def get_all_metrics(self) -> Dict[str, List[Metric]]:
        """Get all collected metrics."""
        async with self._lock:
            return {name: list(metrics) for name, metrics in self._metrics.items()}
    
    async def get_all_summaries(self) -> Dict[str, Dict[str, float]]:
        """Get summaries for all metrics."""
        summaries = {}
        async with self._lock:
            for name in self._metrics.keys():
                summary = await self.get_metric_summary(name)
                if summary:
                    summaries[name] = summary
        return summaries

