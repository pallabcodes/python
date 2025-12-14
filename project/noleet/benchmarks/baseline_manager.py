"""
Baseline management for performance benchmarks.
Manages baseline performance expectations and tracks changes over time.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import statistics
import logging

from .benchmark_framework import BenchmarkResult, PerformanceMetrics

logger = logging.getLogger(__name__)


class BaselineManager:
    """Manages performance baselines for benchmark comparison."""

    def __init__(self, baseline_dir: str = "benchmarks/baselines"):
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.baselines: Dict[str, Dict[str, Any]] = {}

        # Load existing baselines
        self._load_baselines()

    def set_baseline(self, suite_name: str, results: List[BenchmarkResult],
                    description: str = ""):
        """Set a new baseline for a benchmark suite."""
        baseline_data = {
            'suite_name': suite_name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'results': [r.to_dict() for r in results]
        }

        # Calculate summary statistics
        successful_results = [r for r in results if not r.error]
        if successful_results:
            baseline_data['summary'] = self._calculate_summary_stats(successful_results)

        # Save to file
        baseline_file = self.baseline_dir / f"{suite_name}_baseline.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2, default=str)

        # Update in-memory cache
        self.baselines[suite_name] = baseline_data

        logger.info(f"Baseline set for suite '{suite_name}' with {len(results)} benchmarks")

    def get_baseline(self, suite_name: str) -> Optional[Dict[str, Any]]:
        """Get baseline for a benchmark suite."""
        return self.baselines.get(suite_name)

    def compare_to_baseline(self, suite_name: str,
                           current_results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Compare current results to baseline."""
        baseline = self.get_baseline(suite_name)
        if not baseline:
            return {
                'status': 'no_baseline',
                'message': f'No baseline found for suite {suite_name}'
            }

        baseline_results = [BenchmarkResult.from_dict(r) for r in baseline['results']]

        # Create lookup dictionaries
        baseline_dict = {r.name: r for r in baseline_results}
        current_dict = {r.name: r for r in current_results}

        comparison = {
            'status': 'compared',
            'suite_name': suite_name,
            'baseline_created': baseline['created_at'],
            'current_timestamp': datetime.now().isoformat(),
            'benchmarks': {}
        }

        all_benchmarks = set(baseline_dict.keys()) | set(current_dict.keys())

        for benchmark_name in all_benchmarks:
            baseline_result = baseline_dict.get(benchmark_name)
            current_result = current_dict.get(benchmark_name)

            if baseline_result and current_result and not current_result.error:
                # Compare metrics
                comparison['benchmarks'][benchmark_name] = self._compare_benchmark_results(
                    baseline_result, current_result
                )
            elif baseline_result and not current_result:
                comparison['benchmarks'][benchmark_name] = {'status': 'removed_from_current'}
            elif current_result and not baseline_result:
                comparison['benchmarks'][benchmark_name] = {'status': 'added_to_current'}
            else:
                comparison['benchmarks'][benchmark_name] = {'status': 'error_in_current'}

        # Calculate overall comparison summary
        comparison['summary'] = self._calculate_comparison_summary(comparison)

        return comparison

    def update_baseline(self, suite_name: str, new_results: List[BenchmarkResult],
                       update_threshold: float = 5.0):
        """Update baseline if performance improvement exceeds threshold."""
        current_comparison = self.compare_to_baseline(suite_name, new_results)

        if current_comparison['status'] != 'compared':
            return False

        # Check if there are significant improvements
        significant_improvements = 0
        total_benchmarks = 0

        for benchmark_data in current_comparison['benchmarks'].values():
            if benchmark_data.get('status') == 'compared':
                total_benchmarks += 1
                time_change = benchmark_data.get('time_change_percent', 0)
                memory_change = benchmark_data.get('memory_change_percent', 0)

                # Consider it a significant improvement if either metric improved by threshold
                if time_change < -update_threshold or memory_change < -update_threshold:
                    significant_improvements += 1

        # Update baseline if majority of benchmarks show improvement
        if significant_improvements > total_benchmarks * 0.5:  # More than 50% improved
            self.set_baseline(suite_name, new_results,
                            f"Auto-updated baseline - {significant_improvements}/{total_benchmarks} benchmarks improved")
            logger.info(f"Baseline updated for suite '{suite_name}' due to performance improvements")
            return True

        return False

    def list_baselines(self) -> List[Dict[str, Any]]:
        """List all available baselines."""
        return [
            {
                'suite_name': name,
                'description': data.get('description', ''),
                'created_at': data['created_at'],
                'benchmark_count': len(data.get('results', [])),
                'summary': data.get('summary', {})
            }
            for name, data in self.baselines.items()
        ]

    def delete_baseline(self, suite_name: str) -> bool:
        """Delete a baseline."""
        if suite_name not in self.baselines:
            return False

        baseline_file = self.baseline_dir / f"{suite_name}_baseline.json"
        if baseline_file.exists():
            baseline_file.unlink()

        del self.baselines[suite_name]
        logger.info(f"Baseline deleted for suite '{suite_name}'")
        return True

    def export_baseline(self, suite_name: str, export_path: str):
        """Export baseline to a file."""
        baseline = self.get_baseline(suite_name)
        if not baseline:
            raise ValueError(f"No baseline found for suite '{suite_name}'")

        export_file = Path(export_path)
        export_file.parent.mkdir(parents=True, exist_ok=True)

        with open(export_file, 'w') as f:
            json.dump(baseline, f, indent=2, default=str)

        logger.info(f"Baseline exported to {export_file}")

    def import_baseline(self, import_path: str) -> str:
        """Import baseline from a file."""
        import_file = Path(import_path)
        if not import_file.exists():
            raise FileNotFoundError(f"Baseline file not found: {import_path}")

        with open(import_file, 'r') as f:
            baseline_data = json.load(f)

        suite_name = baseline_data['suite_name']
        self.baselines[suite_name] = baseline_data

        # Save to baseline directory
        baseline_file = self.baseline_dir / f"{suite_name}_baseline.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2, default=str)

        logger.info(f"Baseline imported for suite '{suite_name}'")
        return suite_name

    def _load_baselines(self):
        """Load all baselines from disk."""
        if not self.baseline_dir.exists():
            return

        for baseline_file in self.baseline_dir.glob("*_baseline.json"):
            try:
                with open(baseline_file, 'r') as f:
                    baseline_data = json.load(f)
                    suite_name = baseline_data['suite_name']
                    self.baselines[suite_name] = baseline_data
            except Exception as e:
                logger.error(f"Failed to load baseline from {baseline_file}: {e}")

    def _calculate_summary_stats(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Calculate summary statistics for a set of results."""
        if not results:
            return {}

        execution_times = [r.metrics.execution_time for r in results]
        memory_usage = [r.metrics.memory_usage for r in results]
        cpu_usage = [r.metrics.cpu_percent for r in results]

        return {
            'benchmark_count': len(results),
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

    def _compare_benchmark_results(self, baseline: BenchmarkResult,
                                 current: BenchmarkResult) -> Dict[str, Any]:
        """Compare two benchmark results."""
        comparison = {'status': 'compared'}

        # Compare execution time
        baseline_time = baseline.metrics.execution_time
        current_time = current.metrics.execution_time

        if baseline_time > 0:
            time_diff = current_time - baseline_time
            time_change_pct = (time_diff / baseline_time) * 100
            comparison.update({
                'baseline_time': baseline_time,
                'current_time': current_time,
                'time_difference': time_diff,
                'time_change_percent': time_change_pct
            })

        # Compare memory usage
        baseline_memory = baseline.metrics.memory_usage
        current_memory = current.metrics.memory_usage

        if baseline_memory > 0:
            memory_diff = current_memory - baseline_memory
            memory_change_pct = (memory_diff / baseline_memory) * 100
            comparison.update({
                'baseline_memory': baseline_memory,
                'current_memory': current_memory,
                'memory_difference': memory_diff,
                'memory_change_percent': memory_change_pct
            })

        # Compare CPU usage
        baseline_cpu = baseline.metrics.cpu_percent
        current_cpu = current.metrics.cpu_percent

        if baseline_cpu > 0:
            cpu_diff = current_cpu - baseline_cpu
            cpu_change_pct = (cpu_diff / baseline_cpu) * 100
            comparison.update({
                'baseline_cpu': baseline_cpu,
                'current_cpu': current_cpu,
                'cpu_difference': cpu_diff,
                'cpu_change_percent': cpu_change_pct
            })

        return comparison

    def _calculate_comparison_summary(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall comparison summary."""
        benchmarks = comparison.get('benchmarks', {})
        compared_benchmarks = [
            data for data in benchmarks.values()
            if data.get('status') == 'compared'
        ]

        if not compared_benchmarks:
            return {'status': 'no_comparable_benchmarks'}

        # Calculate averages
        time_changes = [b.get('time_change_percent', 0) for b in compared_benchmarks if 'time_change_percent' in b]
        memory_changes = [b.get('memory_change_percent', 0) for b in compared_benchmarks if 'memory_change_percent' in b]
        cpu_changes = [b.get('cpu_change_percent', 0) for b in compared_benchmarks if 'cpu_change_percent' in b]

        summary = {
            'total_benchmarks': len(benchmarks),
            'compared_benchmarks': len(compared_benchmarks),
            'added_benchmarks': len([b for b in benchmarks.values() if b.get('status') == 'added_to_current']),
            'removed_benchmarks': len([b for b in benchmarks.values() if b.get('status') == 'removed_from_current'])
        }

        if time_changes:
            summary['average_time_change_percent'] = statistics.mean(time_changes)
            summary['time_improvements'] = len([c for c in time_changes if c < 0])
            summary['time_regressions'] = len([c for c in time_changes if c > 0])

        if memory_changes:
            summary['average_memory_change_percent'] = statistics.mean(memory_changes)
            summary['memory_improvements'] = len([c for c in memory_changes if c < 0])
            summary['memory_regressions'] = len([c for c in memory_changes if c > 0])

        if cpu_changes:
            summary['average_cpu_change_percent'] = statistics.mean(cpu_changes)
            summary['cpu_improvements'] = len([c for c in cpu_changes if c < 0])
            summary['cpu_regressions'] = len([c for c in cpu_changes if c > 0])

        return summary
