"""
Monitoring and Metrics System

Provides comprehensive tracking of:
- Cost optimization metrics
- Performance monitoring
- Quality assessment
- Usage analytics
- System health monitoring
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

from .config import MonitoringConfig
from .types import GenerationResponse

@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    timestamp: float
    provider: str
    quality_requirement: str
    tokens_used: int
    cost: float
    latency: float
    quality_score: float
    batch_efficiency: Optional[float] = None
    error: Optional[str] = None

@dataclass
class CostMetrics:
    """Cost tracking metrics."""
    total_cost: float = 0.0
    total_tokens: int = 0
    requests_count: int = 0
    cost_by_provider: Dict[str, float] = field(default_factory=dict)
    cost_by_quality: Dict[str, float] = field(default_factory=dict)
    cost_savings: float = 0.0  # Compared to traditional pricing

@dataclass
class PerformanceMetrics:
    """Performance tracking metrics."""
    avg_latency: float = 0.0
    p95_latency: float = 0.0
    success_rate: float = 0.0
    throughput: float = 0.0  # requests per second
    error_rate: float = 0.0

@dataclass
class QualityMetrics:
    """Quality assessment metrics."""
    avg_quality_score: float = 0.0
    quality_distribution: Dict[str, int] = field(default_factory=dict)
    intervention_rate: float = 0.0
    user_satisfaction: Optional[float] = None

class MetricsCollector:
    """
    Collects and analyzes system metrics.

    Provides:
    - Real-time performance monitoring
    - Cost tracking and optimization insights
    - Quality assessment analytics
    - Predictive analytics for optimization
    """

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger("MetricsCollector")

        # Data storage
        self.requests: deque[RequestMetrics] = deque(maxlen=10000)
        self.cost_metrics = CostMetrics()
        self.performance_metrics = PerformanceMetrics()
        self.quality_metrics = QualityMetrics()

        # Time windows for analysis
        self.window_hours = [1, 24, 168]  # 1h, 24h, 7d

        # Start background analysis
        if config.enabled:
            self.analysis_task = asyncio.create_task(self._analyze_metrics())

    async def record_request(self, response: GenerationResponse):
        """Record metrics for a completed request."""
        if not self.config.enabled:
            return

        metrics = RequestMetrics(
            timestamp=time.time(),
            provider=response.provider_used,
            quality_requirement=getattr(response, 'quality_requirement', 'unknown'),
            tokens_used=response.tokens_used,
            cost=response.cost,
            latency=response.latency,
            quality_score=response.quality_score,
            batch_efficiency=getattr(response, 'batch_efficiency', None)
        )

        self.requests.append(metrics)
        await self._update_aggregates(metrics)

    async def _update_aggregates(self, metrics: RequestMetrics):
        """Update aggregated metrics."""
        # Cost metrics
        self.cost_metrics.total_cost += metrics.cost
        self.cost_metrics.total_tokens += metrics.tokens_used
        self.cost_metrics.requests_count += 1

        # Cost by provider
        if metrics.provider not in self.cost_metrics.cost_by_provider:
            self.cost_metrics.cost_by_provider[metrics.provider] = 0.0
        self.cost_metrics.cost_by_provider[metrics.provider] += metrics.cost

        # Cost by quality
        if metrics.quality_requirement not in self.cost_metrics.cost_by_quality:
            self.cost_metrics.cost_by_quality[metrics.quality_requirement] = 0.0
        self.cost_metrics.cost_by_quality[metrics.quality_requirement] += metrics.cost

        # Quality metrics
        quality_range = self._get_quality_range(metrics.quality_score)
        if quality_range not in self.quality_metrics.quality_distribution:
            self.quality_metrics.quality_distribution[quality_range] = 0
        self.quality_metrics.quality_distribution[quality_range] += 1

    def _get_quality_range(self, score: float) -> str:
        """Categorize quality score into ranges."""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.7:
            return "acceptable"
        else:
            return "poor"

    async def get_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        if not self.config.enabled:
            return {"monitoring": "disabled"}

        cutoff_time = time.time() - (hours * 3600)
        recent_requests = [r for r in self.requests if r.timestamp > cutoff_time]

        if not recent_requests:
            return {"message": f"No requests in the last {hours} hours"}

        # Calculate metrics
        summary = {
            "time_window_hours": hours,
            "total_requests": len(recent_requests),
            "cost_metrics": await self._get_cost_summary(recent_requests),
            "performance_metrics": await self._get_performance_summary(recent_requests),
            "quality_metrics": await self._get_quality_summary(recent_requests),
            "optimization_insights": await self._get_optimization_insights(recent_requests)
        }

        return summary

    async def _get_cost_summary(self, requests: List[RequestMetrics]) -> Dict[str, Any]:
        """Calculate cost-related metrics."""
        total_cost = sum(r.cost for r in requests)
        total_tokens = sum(r.tokens_used for r in requests)

        # Cost by provider
        cost_by_provider = defaultdict(float)
        for r in requests:
            cost_by_provider[r.provider] += r.cost

        # Cost efficiency (lower is better)
        avg_cost_per_token = total_cost / max(total_tokens, 1)
        avg_cost_per_request = total_cost / max(len(requests), 1)

        # Savings calculation (compared to GPT-4 pricing)
        gpt4_equivalent_cost = total_tokens * 0.03 / 1000  # $0.03 per 1K tokens
        actual_savings = gpt4_equivalent_cost - total_cost

        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "avg_cost_per_token": round(avg_cost_per_token, 6),
            "avg_cost_per_request": round(avg_cost_per_request, 4),
            "cost_by_provider": dict(cost_by_provider),
            "savings_vs_gpt4": round(actual_savings, 4),
            "savings_percentage": round((actual_savings / max(gpt4_equivalent_cost, 0.01)) * 100, 1)
        }

    async def _get_performance_summary(self, requests: List[RequestMetrics]) -> Dict[str, Any]:
        """Calculate performance metrics."""
        if not requests:
            return {}

        latencies = [r.latency for r in requests]
        latencies.sort()

        # Calculate percentiles
        p50_idx = int(len(latencies) * 0.5)
        p95_idx = int(len(latencies) * 0.95)
        p99_idx = int(len(latencies) * 0.99)

        # Success rate
        successful_requests = [r for r in requests if r.error is None]
        success_rate = len(successful_requests) / len(requests)

        # Throughput (requests per second over the time window)
        time_span = max(r.timestamp for r in requests) - min(r.timestamp for r in requests)
        throughput = len(requests) / max(time_span, 1)

        # Error rate
        error_rate = 1 - success_rate

        return {
            "avg_latency": round(sum(latencies) / len(latencies), 3),
            "p50_latency": round(latencies[p50_idx], 3),
            "p95_latency": round(latencies[min(p95_idx, len(latencies)-1)], 3),
            "p99_latency": round(latencies[min(p99_idx, len(latencies)-1)], 3),
            "success_rate": round(success_rate * 100, 1),
            "error_rate": round(error_rate * 100, 1),
            "throughput_rps": round(throughput, 2)
        }

    async def _get_quality_summary(self, requests: List[RequestMetrics]) -> Dict[str, Any]:
        """Calculate quality metrics."""
        if not requests:
            return {}

        quality_scores = [r.quality_score for r in requests]
        avg_quality = sum(quality_scores) / len(quality_scores)

        # Quality distribution
        distribution = defaultdict(int)
        for r in requests:
            quality_range = self._get_quality_range(r.quality_score)
            distribution[quality_range] += 1

        # Intervention rate (estimated)
        intervention_rate = len([r for r in requests if r.quality_score < 0.8]) / len(requests)

        return {
            "avg_quality_score": round(avg_quality, 3),
            "quality_distribution": dict(distribution),
            "intervention_rate": round(intervention_rate * 100, 1),
            "high_quality_rate": round((distribution.get("excellent", 0) + distribution.get("good", 0)) / len(requests) * 100, 1)
        }

    async def _get_optimization_insights(self, requests: List[RequestMetrics]) -> Dict[str, Any]:
        """Generate optimization insights."""
        insights = {}

        # Cost optimization
        cost_by_provider = defaultdict(float)
        for r in requests:
            cost_by_provider[r.provider] += r.cost

        # Find most cost-effective provider
        if cost_by_provider:
            cheapest_provider = min(cost_by_provider.items(), key=lambda x: x[1])
            insights["cheapest_provider"] = cheapest_provider[0]

        # Performance optimization
        avg_latency = sum(r.latency for r in requests) / len(requests)
        if avg_latency > 5.0:
            insights["latency_issue"] = f"High average latency: {avg_latency:.2f}s"

        # Quality optimization
        low_quality_requests = [r for r in requests if r.quality_score < 0.7]
        if low_quality_requests:
            insights["quality_improvement"] = f"{len(low_quality_requests)} requests below quality threshold"

        # Batching efficiency
        batch_requests = [r for r in requests if r.batch_efficiency is not None]
        if batch_requests:
            avg_batch_efficiency = sum(r.batch_efficiency for r in batch_requests) / len(batch_requests)
            insights["batch_efficiency"] = f"{avg_batch_efficiency:.1%} average batching efficiency"

        return insights

    async def _analyze_metrics(self):
        """Background task for continuous metrics analysis."""
        while True:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes

                # Check cost alerts
                if self.config.cost_alert_threshold > 0:
                    recent_cost = await self._get_cost_summary(self.requests)
                    if recent_cost["total_cost"] > self.config.cost_alert_threshold:
                        self.logger.warning(
                            f"Cost alert: ${recent_cost['total_cost']:.2f} exceeds threshold of ${self.config.cost_alert_threshold}"
                        )

                # Log periodic summary
                summary = await self.get_summary(hours=1)
                if summary.get("total_requests", 0) > 0:
                    self.logger.info(
                        f"Metrics: {summary['total_requests']} requests, "
                        f"${summary['cost_metrics']['total_cost']:.4f} cost, "
                        f"{summary['performance_metrics']['avg_latency']:.2f}s avg latency"
                    )

            except Exception as e:
                self.logger.error(f"Metrics analysis error: {e}")

    async def export_metrics(self, path: str, hours: int = 24) -> str:
        """Export metrics to file."""
        import json
        from pathlib import Path

        summary = await self.get_summary(hours)

        export_path = Path(path)
        export_path.parent.mkdir(parents=True, exist_ok=True)

        with open(export_path, 'w') as f:
            json.dump({
                "exported_at": datetime.now().isoformat(),
                "time_window_hours": hours,
                **summary
            }, f, indent=2)

        return str(export_path)

    async def shutdown(self):
        """Shutdown metrics collection."""
        if hasattr(self, 'analysis_task'):
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Metrics collection shutdown complete")
