"""
Benchmark runner for executing and managing performance benchmarks.
Provides tools for running benchmarks, collecting results, and generating reports.
"""

import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .benchmark_framework import BenchmarkSuite, BenchmarkResult, PerformanceMetrics

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Runner for executing benchmark suites and managing results."""

    def __init__(self, output_dir: str = "benchmarks/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_suite(self, suite: BenchmarkSuite, iterations: int = 1,
                 warmup_iterations: int = 0, save_results: bool = True) -> List[BenchmarkResult]:
        """Run a complete benchmark suite."""
        logger.info(f"Running benchmark suite: {suite.name}")

        results = suite.run_all(iterations=iterations, warmup_iterations=warmup_iterations)

        if save_results:
            self.save_results(results, suite.name)

        # Generate summary report
        self.generate_report(results, suite.name)

        return results

    def run_single_benchmark(self, suite: BenchmarkSuite, benchmark_name: str,
                           iterations: int = 1, warmup_iterations: int = 0,
                           save_results: bool = True) -> BenchmarkResult:
        """Run a single benchmark from a suite."""
        logger.info(f"Running benchmark: {benchmark_name}")

        result = suite.run_benchmark(benchmark_name, iterations, warmup_iterations)

        if save_results:
            self.save_results([result], suite.name)

        return result

    def save_results(self, results: List[BenchmarkResult], suite_name: str):
        """Save benchmark results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{suite_name}_{timestamp}"

        # Save as JSON
        json_file = self.output_dir / f"{base_filename}.json"
        with open(json_file, 'w') as f:
            json.dump([r.to_dict() for r in results], f, indent=2, default=str)

        # Save as CSV for easy analysis
        csv_file = self.output_dir / f"{base_filename}.csv"
        self._save_csv_results(results, csv_file)

        logger.info(f"Results saved to {json_file} and {csv_file}")

    def _save_csv_results(self, results: List[BenchmarkResult], csv_file: Path):
        """Save results in CSV format."""
        if not results:
            return

        fieldnames = [
            'name', 'timestamp', 'iterations', 'execution_time', 'cpu_percent',
            'memory_usage', 'peak_memory', 'allocations', 'deallocations',
            'memory_delta', 'error'
        ]

        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                row = {
                    'name': result.name,
                    'timestamp': result.timestamp.isoformat(),
                    'iterations': result.iterations,
                    'execution_time': result.metrics.execution_time,
                    'cpu_percent': result.metrics.cpu_percent,
                    'memory_usage': result.metrics.memory_usage,
                    'peak_memory': result.metrics.peak_memory,
                    'allocations': result.metrics.allocations,
                    'deallocations': result.metrics.deallocations,
                    'memory_delta': result.metrics.memory_delta,
                    'error': result.error or ''
                }
                writer.writerow(row)

    def generate_report(self, results: List[BenchmarkResult], suite_name: str):
        """Generate a human-readable performance report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"{suite_name}_report_{timestamp}.txt"

        successful_results = [r for r in results if not r.error]
        failed_results = [r for r in results if r.error]

        with open(report_file, 'w') as f:
            f.write(f"Performance Benchmark Report\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Suite: {suite_name}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Total Benchmarks: {len(results)}\n")
            f.write(f"Successful: {len(successful_results)}\n")
            f.write(f"Failed: {len(failed_results)}\n\n")

            if successful_results:
                f.write("Performance Summary:\n")
                f.write("-" * 30 + "\n")

                # Calculate aggregates
                exec_times = [r.metrics.execution_time for r in successful_results]
                memory_usage = [r.metrics.memory_usage for r in successful_results]

                f.write(".6f")
                f.write(".6f")
                f.write(".2f")
                f.write(".2f")

                f.write("\nDetailed Results:\n")
                f.write("-" * 30 + "\n")

                for result in successful_results:
                    f.write(f"\nBenchmark: {result.name}\n")
                    f.write(f"  Iterations: {result.iterations}\n")
                    f.write(".6f")
                    f.write(".2f")
                    f.write(",")
                    f.write(",")
                    if result.metadata:
                        f.write(f"  Metadata: {result.metadata}\n")

            if failed_results:
                f.write("\n\nFailed Benchmarks:\n")
                f.write("-" * 20 + "\n")
                for result in failed_results:
                    f.write(f"  {result.name}: {result.error}\n")

        logger.info(f"Report generated: {report_file}")

    def load_results(self, suite_name: str, timestamp: Optional[str] = None) -> List[BenchmarkResult]:
        """Load benchmark results from file."""
        if timestamp:
            json_file = self.output_dir / f"{suite_name}_{timestamp}.json"
        else:
            # Find the most recent results file
            pattern = f"{suite_name}_*.json"
            files = list(self.output_dir.glob(pattern))
            if not files:
                return []
            json_file = max(files, key=lambda f: f.stat().st_mtime)

        if not json_file.exists():
            return []

        with open(json_file, 'r') as f:
            data = json.load(f)

        return [BenchmarkResult.from_dict(item) for item in data]

    def compare_results(self, baseline_results: List[BenchmarkResult],
                       current_results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Compare two sets of benchmark results."""
        comparison = {}

        # Create lookup dictionaries
        baseline_dict = {r.name: r for r in baseline_results}
        current_dict = {r.name: r for r in current_results}

        all_benchmarks = set(baseline_dict.keys()) | set(current_dict.keys())

        for benchmark_name in all_benchmarks:
            baseline = baseline_dict.get(benchmark_name)
            current = current_dict.get(benchmark_name)

            if baseline and current:
                # Calculate differences
                time_diff = current.metrics.execution_time - baseline.metrics.execution_time
                time_change_pct = (time_diff / baseline.metrics.execution_time) * 100

                memory_diff = current.metrics.memory_usage - baseline.metrics.memory_usage
                memory_change_pct = (memory_diff / baseline.metrics.memory_usage) * 100 if baseline.metrics.memory_usage else 0

                comparison[benchmark_name] = {
                    'status': 'compared',
                    'baseline_time': baseline.metrics.execution_time,
                    'current_time': current.metrics.execution_time,
                    'time_difference': time_diff,
                    'time_change_percent': time_change_pct,
                    'baseline_memory': baseline.metrics.memory_usage,
                    'current_memory': current.metrics.memory_usage,
                    'memory_difference': memory_diff,
                    'memory_change_percent': memory_change_pct
                }
            elif baseline:
                comparison[benchmark_name] = {'status': 'removed'}
            else:
                comparison[benchmark_name] = {'status': 'added'}

        return comparison


class BenchmarkScheduler:
    """Scheduler for running benchmarks at regular intervals."""

    def __init__(self, runner: BenchmarkRunner):
        self.runner = runner
        self.scheduled_suites: Dict[str, Dict[str, Any]] = {}

    def schedule_suite(self, suite_name: str, suite: BenchmarkSuite,
                      interval_hours: int = 24, iterations: int = 1):
        """Schedule a benchmark suite to run periodically."""
        self.scheduled_suites[suite_name] = {
            'suite': suite,
            'interval_hours': interval_hours,
            'iterations': iterations,
            'last_run': None
        }
        logger.info(f"Scheduled benchmark suite '{suite_name}' to run every {interval_hours} hours")

    def run_scheduled(self) -> List[BenchmarkResult]:
        """Run all scheduled benchmarks that are due."""
        results = []
        current_time = datetime.now()

        for suite_name, config in self.scheduled_suites.items():
            last_run = config['last_run']
            interval_hours = config['interval_hours']

            if last_run is None or (current_time - last_run).total_seconds() >= (interval_hours * 3600):
                logger.info(f"Running scheduled benchmark: {suite_name}")

                try:
                    suite_results = self.runner.run_suite(
                        config['suite'],
                        iterations=config['iterations']
                    )
                    results.extend(suite_results)

                    # Update last run time
                    config['last_run'] = current_time

                except Exception as e:
                    logger.error(f"Failed to run scheduled benchmark '{suite_name}': {e}")

        return results

    def get_schedule_status(self) -> Dict[str, Any]:
        """Get status of all scheduled benchmarks."""
        status = {}
        current_time = datetime.now()

        for suite_name, config in self.scheduled_suites.items():
            last_run = config['last_run']
            interval_hours = config['interval_hours']

            if last_run is None:
                next_run = "ASAP"
                overdue = True
            else:
                next_run_time = last_run + timedelta(hours=interval_hours)
                if current_time >= next_run_time:
                    next_run = "OVERDUE"
                    overdue = True
                else:
                    next_run = next_run_time.isoformat()
                    overdue = False

            status[suite_name] = {
                'last_run': last_run.isoformat() if last_run else None,
                'next_run': next_run,
                'interval_hours': interval_hours,
                'overdue': overdue
            }

        return status
