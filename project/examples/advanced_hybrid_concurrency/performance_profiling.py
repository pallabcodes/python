"""
Performance Profiling Tools for Hybrid Concurrency.

This module provides performance monitoring, profiling, and bottleneck
detection tools for hybrid concurrency applications.

Features:
- Real-time performance monitoring
- Concurrency profiler integration
- Bottleneck detection and analysis
- Performance dashboards
- Tracing and observability
"""

import asyncio
import threading
import time
import logging
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
import statistics
from typing import Any, Callable, List, Dict, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import tracemalloc

logger = logging.getLogger(__name__)

# Optional profiling imports
try:
    import pyspy
    PYSPY_AVAILABLE = True
except ImportError:
    pyspy = None
    PYSPY_AVAILABLE = False


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""
    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    threads_active: int = 0
    tasks_pending: int = 0
    throughput: float = 0.0
    latency_p95: float = 0.0
    error_rate: float = 0.0


class ConcurrencyProfiler:
    """Profiler for concurrency performance analysis."""

    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self._running = False
        self._metrics: List[PerformanceMetrics] = []
        self._lock = threading.Lock()
        self._start_time = 0

    def start_profiling(self):
        """Start performance profiling."""
        if self._running:
            return

        self._running = True
        self._start_time = time.time()
        self._metrics.clear()

        # Start profiling thread
        thread = threading.Thread(target=self._profile_loop, daemon=True)
        thread.start()

        logger.info("Started ConcurrencyProfiler")

    def stop_profiling(self):
        """Stop performance profiling."""
        self._running = False
        logger.info("Stopped ConcurrencyProfiler")

    def _profile_loop(self):
        """Main profiling loop."""
        while self._running:
            try:
                metrics = self._collect_metrics()
                with self._lock:
                    self._metrics.append(metrics)
                    # Keep only recent metrics
                    max_metrics = 1000
                    if len(self._metrics) > max_metrics:
                        self._metrics = self._metrics[-max_metrics:]

            except Exception as e:
                logger.error(f"Profiling error: {e}")

            time.sleep(self.sample_interval)

    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        try:
            if not PSUTIL_AVAILABLE:
                # Return basic metrics without psutil
                tasks_pending = 0
                try:
                    loop = asyncio.get_running_loop()
                    tasks_pending = len(asyncio.all_tasks(loop))
                except RuntimeError:
                    pass

                return PerformanceMetrics(
                    cpu_percent=50.0,  # Default values
                    memory_mb=512.0,
                    threads_active=threading.active_count(),
                    tasks_pending=tasks_pending
                )

            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024

            threads_active = threading.active_count()

            # Get asyncio tasks if available
            tasks_pending = 0
            try:
                loop = asyncio.get_running_loop()
                tasks_pending = len(asyncio.all_tasks(loop))
            except RuntimeError:
                pass

            return PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                threads_active=threads_active,
                tasks_pending=tasks_pending
            )

        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
            return PerformanceMetrics()

    def get_recent_metrics(self, seconds: int = 60) -> List[PerformanceMetrics]:
        """Get metrics from the last N seconds."""
        cutoff_time = time.time() - seconds
        with self._lock:
            return [m for m in self._metrics if m.timestamp > cutoff_time]

    def get_summary_stats(self, seconds: int = 60) -> Dict[str, Any]:
        """Get summary statistics."""
        metrics = self.get_recent_metrics(seconds)

        if not metrics:
            return {"message": "No metrics available"}

        cpu_percents = [m.cpu_percent for m in metrics]
        memory_mbs = [m.memory_mb for m in metrics]

        return {
            "duration_seconds": seconds,
            "samples_count": len(metrics),
            "cpu_avg": statistics.mean(cpu_percents) if cpu_percents else 0,
            "cpu_max": max(cpu_percents) if cpu_percents else 0,
            "memory_avg_mb": statistics.mean(memory_mbs) if memory_mbs else 0,
            "memory_max_mb": max(memory_mbs) if memory_mbs else 0,
            "threads_avg": statistics.mean(m.threads_active for m in metrics),
            "tasks_avg": statistics.mean(m.tasks_pending for m in metrics)
        }


class RealTimeMonitor:
    """Real-time performance monitoring with alerts."""

    def __init__(self, profiler: ConcurrencyProfiler):
        self.profiler = profiler
        self._alerts: List[Dict[str, Any]] = []
        self._thresholds = {
            "cpu_percent": 80.0,
            "memory_mb": 1000.0,  # 1GB
            "threads_active": 50
        }
        self._alert_callbacks: List[Callable] = []

    def set_threshold(self, metric: str, value: float):
        """Set alert threshold for metric."""
        self._thresholds[metric] = value

    def add_alert_callback(self, callback: Callable):
        """Add callback for alerts."""
        self._alert_callbacks.append(callback)

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for performance alerts."""
        alerts = []

        # Get recent metrics
        metrics = self.profiler.get_recent_metrics(10)  # Last 10 seconds

        if not metrics:
            return alerts

        latest = metrics[-1]

        # Check thresholds
        for metric, threshold in self._thresholds.items():
            value = getattr(latest, metric, 0)
            if value > threshold:
                alert = {
                    "timestamp": time.time(),
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "severity": "high" if value > threshold * 1.5 else "medium"
                }
                alerts.append(alert)

                # Trigger callbacks
                for callback in self._alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Alert callback error: {e}")

        self._alerts.extend(alerts)
        return alerts

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        # Simple implementation - return recent alerts
        return self._alerts[-10:] if self._alerts else []


class BottleneckDetector:
    """Automatic bottleneck detection and analysis."""

    def __init__(self, profiler: ConcurrencyProfiler):
        self.profiler = profiler
        self._analysis_window = 60  # seconds

    def analyze_bottlenecks(self) -> Dict[str, Any]:
        """Analyze performance data for bottlenecks."""
        metrics = self.profiler.get_recent_metrics(self._analysis_window)

        if len(metrics) < 10:
            return {"message": "Insufficient data for bottleneck analysis"}

        # Analyze CPU usage patterns
        cpu_values = [m.cpu_percent for m in metrics]
        cpu_avg = statistics.mean(cpu_values)
        cpu_std = statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0

        # Analyze memory usage
        memory_values = [m.memory_mb for m in metrics]
        memory_trend = self._calculate_trend(memory_values)

        # Analyze thread usage
        thread_values = [m.threads_active for m in metrics]
        thread_avg = statistics.mean(thread_values)

        bottlenecks = []

        # CPU bottleneck detection
        if cpu_avg > 70:
            bottlenecks.append({
                "type": "cpu",
                "severity": "high" if cpu_avg > 90 else "medium",
                "description": f"High CPU usage: {cpu_avg:.1f}% average",
                "recommendation": "Consider using multiprocessing for CPU-intensive tasks"
            })

        # Memory bottleneck detection
        if memory_trend > 10:  # MB per minute
            bottlenecks.append({
                "type": "memory",
                "severity": "high",
                "description": f"Memory leak detected: {memory_trend:.1f} MB/min growth",
                "recommendation": "Check for memory leaks in long-running tasks"
            })

        # Thread bottleneck detection
        if thread_avg > 20:
            bottlenecks.append({
                "type": "threads",
                "severity": "medium",
                "description": f"High thread count: {thread_avg:.1f} average",
                "recommendation": "Consider using asyncio for I/O-bound tasks"
            })

        return {
            "analysis_period_seconds": self._analysis_window,
            "bottlenecks_found": len(bottlenecks),
            "bottlenecks": bottlenecks,
            "performance_summary": {
                "cpu_avg": cpu_avg,
                "cpu_variability": cpu_std,
                "memory_trend_mb_per_min": memory_trend,
                "threads_avg": thread_avg
            }
        }

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend (units per time)."""
        if len(values) < 2:
            return 0

        # Simple linear regression slope
        n = len(values)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)

        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
        denominator = sum((xi - x_mean) ** 2 for xi in x)

        if denominator == 0:
            return 0

        slope = numerator / denominator

        # Convert to per-minute rate (assuming 1 sample per minute)
        return slope * 60


class PerformanceDashboard:
    """Performance dashboard for visualization."""

    def __init__(self, profiler: ConcurrencyProfiler):
        self.profiler = profiler
        self.monitor = RealTimeMonitor(profiler)
        self.detector = BottleneckDetector(profiler)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        summary = self.profiler.get_summary_stats(300)  # Last 5 minutes
        alerts = self.monitor.get_active_alerts()
        bottlenecks = self.detector.analyze_bottlenecks()

        # Generate recommendations
        recommendations = self._generate_recommendations(summary, bottlenecks)

        return {
            "timestamp": time.time(),
            "summary": summary,
            "alerts": alerts,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "health_score": self._calculate_health_score(summary, alerts, bottlenecks)
        }

    def _generate_recommendations(self, summary: Dict, bottlenecks: Dict) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []

        if summary.get("cpu_avg", 0) > 75:
            recommendations.append("High CPU usage detected. Consider using multiprocessing for CPU-intensive tasks.")

        if summary.get("memory_max_mb", 0) > 800:
            recommendations.append("High memory usage. Monitor for memory leaks and consider optimizing data structures.")

        if summary.get("threads_avg", 0) > 15:
            recommendations.append("High thread count. Consider using asyncio for I/O-bound operations.")

        for bottleneck in bottlenecks.get("bottlenecks", []):
            recommendations.append(bottleneck["recommendation"])

        if not recommendations:
            recommendations.append("Performance looks good. Continue monitoring.")

        return recommendations

    def _calculate_health_score(self, summary: Dict, alerts: List, bottlenecks: Dict) -> float:
        """Calculate overall system health score (0-100)."""
        score = 100.0

        # CPU impact
        cpu_avg = summary.get("cpu_avg", 0)
        if cpu_avg > 90:
            score -= 30
        elif cpu_avg > 75:
            score -= 15

        # Memory impact
        memory_max = summary.get("memory_max_mb", 0)
        if memory_max > 2000:  # 2GB
            score -= 25
        elif memory_max > 1000:  # 1GB
            score -= 10

        # Alert impact
        alert_penalty = len(alerts) * 5
        score -= min(alert_penalty, 20)

        # Bottleneck impact
        bottleneck_count = bottlenecks.get("bottlenecks_found", 0)
        score -= bottleneck_count * 10

        return max(0.0, min(100.0, score))


class TracingManager:
    """Distributed tracing for hybrid concurrency."""

    def __init__(self):
        self._traces: Dict[str, List[Dict]] = defaultdict(list)
        self._active_spans: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def start_trace(self, trace_id: str, operation: str) -> str:
        """Start a new trace span."""
        span_id = f"{trace_id}_{len(self._traces[trace_id])}"

        span = {
            "span_id": span_id,
            "operation": operation,
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
            "metadata": {}
        }

        with self._lock:
            self._traces[trace_id].append(span)
            self._active_spans[span_id] = span

        return span_id

    def end_trace(self, span_id: str):
        """End a trace span."""
        with self._lock:
            if span_id in self._active_spans:
                span = self._active_spans[span_id]
                span["end_time"] = time.time()
                span["duration"] = span["end_time"] - span["start_time"]
                del self._active_spans[span_id]

    def add_metadata(self, span_id: str, key: str, value: Any):
        """Add metadata to a span."""
        with self._lock:
            if span_id in self._active_spans:
                self._active_spans[span_id]["metadata"][key] = value

    def get_trace(self, trace_id: str) -> List[Dict]:
        """Get complete trace."""
        with self._lock:
            return self._traces[trace_id].copy()

    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get trace summary statistics."""
        trace = self.get_trace(trace_id)

        if not trace:
            return {"message": "Trace not found"}

        completed_spans = [span for span in trace if span["duration"] is not None]
        total_duration = sum(span["duration"] for span in completed_spans) if completed_spans else 0

        return {
            "trace_id": trace_id,
            "total_spans": len(trace),
            "completed_spans": len(completed_spans),
            "total_duration": total_duration,
            "avg_span_duration": total_duration / len(completed_spans) if completed_spans else 0
        }


async def demonstrate_performance_profiling():
    """Demonstrate performance profiling tools."""
    print("📊 Performance Profiling Demonstration")
    print("=" * 42)

    # Create profiler
    profiler = ConcurrencyProfiler(sample_interval=0.5)
    profiler.start_profiling()

    # Create monitoring components
    monitor = RealTimeMonitor(profiler)
    dashboard = PerformanceDashboard(profiler)

    # Simulate some work
    print("\n1. Simulating concurrent workload...")

    async def cpu_task():
        import math
        for _ in range(10000):
            math.sin(time.time())
        await asyncio.sleep(0.1)

    async def io_task():
        await asyncio.sleep(0.2)

    # Run concurrent tasks
    tasks = []
    for i in range(10):
        if i % 2 == 0:
            tasks.append(asyncio.create_task(cpu_task()))
        else:
            tasks.append(asyncio.create_task(io_task()))

    await asyncio.gather(*tasks)

    # Wait for profiling data
    await asyncio.sleep(2.0)

    print("\n2. Performance Summary:")
    summary = profiler.get_summary_stats(10)
    print(f"   CPU Average: {summary['cpu_avg']:.1f}%")
    print(f"   Memory Max: {summary['memory_max_mb']:.1f} MB")
    print(f"   Threads Average: {summary['threads_avg']:.1f}")

    print("\n3. Bottleneck Analysis:")
    bottlenecks = dashboard.detector.analyze_bottlenecks()
    if bottlenecks['bottlenecks_found'] > 0:
        for bottleneck in bottlenecks['bottlenecks']:
            print(f"   {bottleneck['type'].upper()}: {bottleneck['description']}")
    else:
        print("   No significant bottlenecks detected")

    print("\n4. Dashboard Health Score:")
    dashboard_data = dashboard.get_dashboard_data()
    health_score = dashboard_data['health_score']
    print(f"   Health Score: {health_score:.1f}/100")

    print("\n5. Recommendations:")
    for rec in dashboard_data['recommendations']:
        print(f"   • {rec}")

    profiler.stop_profiling()
    print("\n✅ Performance profiling demonstration complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demonstrate_performance_profiling())
