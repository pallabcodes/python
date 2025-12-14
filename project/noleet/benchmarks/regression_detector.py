"""
Performance regression detection and alerting.
Analyzes benchmark results to identify performance degradation.
"""

import statistics
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from .benchmark_framework import BenchmarkResult

logger = logging.getLogger(__name__)


@dataclass
class RegressionAlert:
    """Alert for detected performance regression."""
    benchmark_name: str
    metric: str
    baseline_value: float
    current_value: float
    change_percent: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    threshold_breached: float
    description: str


class RegressionDetector:
    """Detects performance regressions in benchmark results."""

    def __init__(self, time_threshold_percent: float = 10.0,
                 memory_threshold_percent: float = 20.0,
                 cpu_threshold_percent: float = 15.0):
        self.time_threshold = time_threshold_percent
        self.memory_threshold = memory_threshold_percent
        self.cpu_threshold = cpu_threshold_percent

    def detect_regressions(self, baseline_results: List[BenchmarkResult],
                          current_results: List[BenchmarkResult]) -> List[RegressionAlert]:
        """Detect regressions by comparing current results against baseline."""
        alerts = []

        # Create lookup dictionaries
        baseline_dict = {r.name: r for r in baseline_results}
        current_dict = {r.name: r for r in current_results}

        for benchmark_name, current_result in current_dict.items():
            baseline_result = baseline_dict.get(benchmark_name)

            if baseline_result and not current_result.error:
                # Check for regressions in different metrics
                alerts.extend(self._check_time_regression(benchmark_name, baseline_result, current_result))
                alerts.extend(self._check_memory_regression(benchmark_name, baseline_result, current_result))
                alerts.extend(self._check_cpu_regression(benchmark_name, baseline_result, current_result))

        return alerts

    def detect_trends(self, historical_results: List[List[BenchmarkResult]],
                     window_size: int = 5) -> List[RegressionAlert]:
        """Detect performance trends over multiple benchmark runs."""
        alerts = []

        if len(historical_results) < window_size:
            return alerts

        # Group results by benchmark name
        benchmark_history = {}
        for result_set in historical_results:
            for result in result_set:
                if result.name not in benchmark_history:
                    benchmark_history[result.name] = []
                benchmark_history[result.name].append(result)

        # Analyze trends for each benchmark
        for benchmark_name, results in benchmark_history.items():
            if len(results) < window_size:
                continue

            # Sort by timestamp
            results.sort(key=lambda r: r.timestamp)

            # Check recent trend (last window_size results)
            recent_results = results[-window_size:]

            alerts.extend(self._analyze_trend(benchmark_name, recent_results))

        return alerts

    def _check_time_regression(self, benchmark_name: str, baseline: BenchmarkResult,
                             current: BenchmarkResult) -> List[RegressionAlert]:
        """Check for execution time regression."""
        alerts = []

        baseline_time = baseline.metrics.execution_time
        current_time = current.metrics.execution_time

        if baseline_time == 0:
            return alerts

        change_percent = ((current_time - baseline_time) / baseline_time) * 100

        # Determine severity based on change magnitude
        severity, threshold = self._calculate_severity(change_percent, self.time_threshold)

        if severity != 'none':
            alerts.append(RegressionAlert(
                benchmark_name=benchmark_name,
                metric='execution_time',
                baseline_value=baseline_time,
                current_value=current_time,
                change_percent=change_percent,
                severity=severity,
                threshold_breached=threshold,
                description=".2f"
            ))

        return alerts

    def _check_memory_regression(self, benchmark_name: str, baseline: BenchmarkResult,
                               current: BenchmarkResult) -> List[RegressionAlert]:
        """Check for memory usage regression."""
        alerts = []

        baseline_memory = baseline.metrics.memory_usage
        current_memory = current.metrics.memory_usage

        if baseline_memory == 0:
            return alerts

        change_percent = ((current_memory - baseline_memory) / baseline_memory) * 100

        severity, threshold = self._calculate_severity(change_percent, self.memory_threshold)

        if severity != 'none':
            alerts.append(RegressionAlert(
                benchmark_name=benchmark_name,
                metric='memory_usage',
                baseline_value=baseline_memory,
                current_value=current_memory,
                change_percent=change_percent,
                severity=severity,
                threshold_breached=threshold,
                description=".2f"
            ))

        return alerts

    def _check_cpu_regression(self, benchmark_name: str, baseline: BenchmarkResult,
                            current: BenchmarkResult) -> List[RegressionAlert]:
        """Check for CPU usage regression."""
        alerts = []

        baseline_cpu = baseline.metrics.cpu_percent
        current_cpu = current.metrics.cpu_percent

        if baseline_cpu == 0:
            return alerts

        change_percent = ((current_cpu - baseline_cpu) / baseline_cpu) * 100

        severity, threshold = self._calculate_severity(change_percent, self.cpu_threshold)

        if severity != 'none':
            alerts.append(RegressionAlert(
                benchmark_name=benchmark_name,
                metric='cpu_percent',
                baseline_value=baseline_cpu,
                current_value=current_cpu,
                change_percent=change_percent,
                severity=severity,
                threshold_breached=threshold,
                description=".2f"
            ))

        return alerts

    def _calculate_severity(self, change_percent: float, threshold: float) -> Tuple[str, float]:
        """Calculate severity level based on change percentage."""
        abs_change = abs(change_percent)

        if abs_change >= threshold * 3:  # 3x threshold
            return 'critical', threshold * 3
        elif abs_change >= threshold * 2:  # 2x threshold
            return 'high', threshold * 2
        elif abs_change >= threshold:  # 1x threshold
            return 'medium', threshold
        elif abs_change >= threshold * 0.5:  # 0.5x threshold
            return 'low', threshold * 0.5
        else:
            return 'none', 0

    def _analyze_trend(self, benchmark_name: str, results: List[BenchmarkResult]) -> List[RegressionAlert]:
        """Analyze performance trend over multiple runs."""
        alerts = []

        if len(results) < 3:
            return alerts

        # Extract metric values
        execution_times = [r.metrics.execution_time for r in results if r.metrics.execution_time > 0]
        memory_usage = [r.metrics.memory_usage for r in results if r.metrics.memory_usage > 0]

        if len(execution_times) >= 3:
            alerts.extend(self._detect_trend_regression(
                benchmark_name, 'execution_time_trend', execution_times, self.time_threshold
            ))

        if len(memory_usage) >= 3:
            alerts.extend(self._detect_trend_regression(
                benchmark_name, 'memory_usage_trend', memory_usage, self.memory_threshold
            ))

        return alerts

    def _detect_trend_regression(self, benchmark_name: str, metric: str,
                               values: List[float], threshold: float) -> List[RegressionAlert]:
        """Detect regression trends in a series of values."""
        alerts = []

        if len(values) < 3:
            return alerts

        # Calculate linear trend (simple slope)
        n = len(values)
        x_values = list(range(n))

        # Calculate slope using linear regression
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return alerts

        slope = numerator / denominator

        # Calculate average change per step
        avg_change_percent = (slope / y_mean) * 100 if y_mean != 0 else 0

        # Check if trend indicates significant degradation
        if avg_change_percent > threshold:
            severity, _ = self._calculate_severity(avg_change_percent, threshold)

            alerts.append(RegressionAlert(
                benchmark_name=benchmark_name,
                metric=metric,
                baseline_value=values[0],
                current_value=values[-1],
                change_percent=avg_change_percent,
                severity=severity,
                threshold_breached=threshold,
                description=".2f"
            ))

        return alerts


class PerformanceAnalyzer:
    """Advanced performance analysis and insights."""

    @staticmethod
    def analyze_bottlenecks(results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze benchmark results to identify performance bottlenecks."""
        analysis = {
            'slowest_benchmarks': [],
            'memory_hungry_benchmarks': [],
            'cpu_intensive_benchmarks': [],
            'summary_stats': {}
        }

        if not results:
            return analysis

        # Filter successful results
        successful_results = [r for r in results if not r.error]

        if not successful_results:
            return analysis

        # Find slowest benchmarks
        sorted_by_time = sorted(successful_results, key=lambda r: r.metrics.execution_time, reverse=True)
        analysis['slowest_benchmarks'] = [
            {
                'name': r.name,
                'execution_time': r.metrics.execution_time,
                'percentile': (i + 1) / len(sorted_by_time) * 100
            }
            for i, r in enumerate(sorted_by_time[:5])  # Top 5 slowest
        ]

        # Find memory-hungry benchmarks
        sorted_by_memory = sorted(successful_results, key=lambda r: r.metrics.memory_usage, reverse=True)
        analysis['memory_hungry_benchmarks'] = [
            {
                'name': r.name,
                'memory_usage': r.metrics.memory_usage,
                'peak_memory': r.metrics.peak_memory
            }
            for r in sorted_by_memory[:5]  # Top 5 memory users
        ]

        # Find CPU-intensive benchmarks
        sorted_by_cpu = sorted(successful_results, key=lambda r: r.metrics.cpu_percent, reverse=True)
        analysis['cpu_intensive_benchmarks'] = [
            {
                'name': r.name,
                'cpu_percent': r.metrics.cpu_percent
            }
            for r in sorted_by_cpu[:5]  # Top 5 CPU users
        ]

        # Calculate summary statistics
        execution_times = [r.metrics.execution_time for r in successful_results]
        memory_usage = [r.metrics.memory_usage for r in successful_results]
        cpu_usage = [r.metrics.cpu_percent for r in successful_results]

        analysis['summary_stats'] = {
            'total_benchmarks': len(successful_results),
            'execution_time': {
                'mean': statistics.mean(execution_times),
                'median': statistics.median(execution_times),
                'std_dev': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                'min': min(execution_times),
                'max': max(execution_times)
            },
            'memory_usage': {
                'mean': statistics.mean(memory_usage),
                'median': statistics.median(memory_usage),
                'std_dev': statistics.stdev(memory_usage) if len(memory_usage) > 1 else 0,
                'min': min(memory_usage),
                'max': max(memory_usage)
            },
            'cpu_usage': {
                'mean': statistics.mean(cpu_usage),
                'median': statistics.median(cpu_usage),
                'std_dev': statistics.stdev(cpu_usage) if len(cpu_usage) > 1 else 0,
                'min': min(cpu_usage),
                'max': max(cpu_usage)
            }
        }

        return analysis

    @staticmethod
    def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Analyze slowest benchmarks
        slowest = analysis.get('slowest_benchmarks', [])
        if slowest:
            top_slow = slowest[0]
            recommendations.append(
                ".4f"
            )

        # Analyze memory usage
        memory_stats = analysis.get('summary_stats', {}).get('memory_usage', {})
        if memory_stats.get('mean', 0) > 100 * 1024 * 1024:  # > 100MB average
            recommendations.append(
                "High memory usage detected. Consider implementing memory-efficient data structures and caching."
            )

        # Analyze CPU usage
        cpu_stats = analysis.get('summary_stats', {}).get('cpu_usage', {})
        if cpu_stats.get('mean', 0) > 80:  # > 80% average CPU
            recommendations.append(
                "High CPU usage detected. Consider optimizing algorithms and implementing parallel processing where appropriate."
            )

        # General recommendations
        recommendations.extend([
            "Implement caching for frequently accessed data to reduce computation overhead.",
            "Consider using async/await patterns for I/O bound operations.",
            "Profile code with cProfile to identify specific bottlenecks.",
            "Implement connection pooling for database and external API calls.",
            "Consider using memory-efficient data structures (e.g., generators, iterators).",
            "Implement proper error handling to avoid expensive exception paths."
        ])

        return recommendations


class AlertManager:
    """Manages performance alerts and notifications."""

    def __init__(self):
        self.alerts: List[RegressionAlert] = []
        self.alert_handlers = []

    def add_alert_handler(self, handler: callable):
        """Add an alert handler function."""
        self.alert_handlers.append(handler)

    def process_alerts(self, alerts: List[RegressionAlert]):
        """Process and distribute alerts."""
        self.alerts.extend(alerts)

        for alert in alerts:
            logger.warning(
                f"Performance regression detected: {alert.benchmark_name} - "
                ".2f"
            )

            # Call all alert handlers
            for handler in self.alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")

    def get_alerts_by_severity(self, severity: str) -> List[RegressionAlert]:
        """Get alerts filtered by severity."""
        return [alert for alert in self.alerts if alert.severity == severity]

    def get_critical_alerts(self) -> List[RegressionAlert]:
        """Get all critical alerts."""
        return self.get_alerts_by_severity('critical')

    def clear_alerts(self):
        """Clear all stored alerts."""
        self.alerts.clear()

    def generate_alert_report(self) -> str:
        """Generate a formatted alert report."""
        if not self.alerts:
            return "No performance alerts detected."

        report = "Performance Regression Alert Report\n"
        report += "=" * 50 + "\n\n"

        # Group alerts by severity
        severity_groups = {}
        for alert in self.alerts:
            if alert.severity not in severity_groups:
                severity_groups[alert.severity] = []
            severity_groups[alert.severity].append(alert)

        for severity in ['critical', 'high', 'medium', 'low']:
            alerts = severity_groups.get(severity, [])
            if alerts:
                report += f"{severity.upper()} SEVERITY ALERTS ({len(alerts)}):\n"
                report += "-" * 30 + "\n"

                for alert in alerts:
                    report += f"• {alert.benchmark_name}: {alert.metric}\n"
                    report += ".2f"
                    report += f"  {alert.description}\n\n"

        return report
