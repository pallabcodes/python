"""
Performance benchmark for TypedThreadPoolExecutor.

This module provides comprehensive benchmarking to compare the
performance characteristics of different executor configurations
and workloads.
"""

import time
import statistics
import logging
from typing import List, Dict, Any, Callable
from dataclasses import dataclass

from .typed_executor import TypedThreadPoolExecutor


@dataclass
class BenchmarkResult:
    """Result of an executor benchmark run.

    Attributes:
        executor_name: Name of the executor configuration.
        max_workers: Number of worker threads.
        task_count: Number of tasks executed.
        total_time: Total time for all tasks.
        throughput: Tasks completed per second.
        avg_latency: Average time per task.
        min_latency: Minimum task latency.
        max_latency: Maximum task latency.
        success_rate: Percentage of successful tasks.
        error_count: Number of failed tasks.
    """

    executor_name: str
    max_workers: int
    task_count: int
    total_time: float
    throughput: float
    avg_latency: float
    min_latency: float
    max_latency: float
    success_rate: float
    error_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analysis."""
        return {
            "executor_name": self.executor_name,
            "max_workers": self.max_workers,
            "task_count": self.task_count,
            "total_time": self.total_time,
            "throughput": self.throughput,
            "avg_latency": self.avg_latency,
            "min_latency": self.min_latency,
            "max_latency": self.max_latency,
            "success_rate": self.success_rate,
            "error_count": self.error_count
        }


class ExecutorBenchmark:
    """Benchmark suite for TypedThreadPoolExecutor.

    Provides comprehensive performance testing of different executor
    configurations under various workload patterns.

    Attributes:
        logger: Logger for benchmark execution details.
    """

    def __init__(self) -> None:
        """Initialize the benchmark suite."""
        self._logger = logging.getLogger(__name__)

    def benchmark_executor(
        self,
        executor: TypedThreadPoolExecutor,
        task_func: Callable[[int], Any],
        task_args: List[int],
        name: str = "Benchmark"
    ) -> BenchmarkResult:
        """Benchmark a specific executor configuration.

        Args:
            executor: Executor to benchmark.
            task_func: Function to execute for each task.
            task_args: Arguments for each task.
            name: Benchmark name for identification.

        Returns:
            Detailed benchmark results.
        """
        task_count = len(task_args)
        self._logger.info(
            f"Starting benchmark '{name}' with {task_count} tasks",
            extra={"benchmark_name": name, "task_count": task_count}
        )

        # Submit all tasks
        task_ids = []
        submit_start = time.time()

        for arg in task_args:
            task_id = executor.submit_task(task_func, arg)
            task_ids.append(task_id)

        submit_time = time.time() - submit_start

        # Collect all results
        results = []
        execution_start = time.time()

        for task_id in task_ids:
            result = executor.get_task_result(task_id, timeout=60.0)
            results.append(result)

        execution_time = time.time() - execution_start
        total_time = submit_time + execution_time

        # Calculate metrics
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        if successful_results:
            latencies = [r.duration for r in successful_results]
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
        else:
            avg_latency = min_latency = max_latency = 0.0

        throughput = task_count / total_time if total_time > 0 else 0
        success_rate = (len(successful_results) / task_count) * 100

        benchmark_result = BenchmarkResult(
            executor_name=name,
            max_workers=executor.get_stats()["max_workers"],
            task_count=task_count,
            total_time=total_time,
            throughput=throughput,
            avg_latency=avg_latency,
            min_latency=min_latency,
            max_latency=max_latency,
            success_rate=success_rate,
            error_count=len(failed_results)
        )

        self._logger.info(
            f"Benchmark '{name}' completed: {throughput:.1f} tasks/sec, "
            f"{success_rate:.1f}% success",
            extra={
                "benchmark_name": name,
                "throughput": throughput,
                "success_rate": success_rate,
                "avg_latency": avg_latency,
                "error_count": len(failed_results)
            }
        )

        return benchmark_result

    def compare_configurations(
        self,
        configurations: List[Dict[str, Any]],
        task_func: Callable[[int], Any],
        task_args: List[int]
    ) -> List[BenchmarkResult]:
        """Compare multiple executor configurations.

        Args:
            configurations: List of executor configurations to test.
            task_func: Task function to execute.
            task_args: Task arguments.

        Returns:
            List of benchmark results for each configuration.
        """
        results = []

        for config in configurations:
            try:
                with TypedThreadPoolExecutor(**config) as executor:
                    result = self.benchmark_executor(
                        executor, task_func, task_args,
                        name=config.get("name", f"Config-{len(results)}")
                    )
                    results.append(result)
            except Exception as e:
                self._logger.error(
                    f"Benchmark failed for config {config}: {e}",
                    extra={"config": config, "error": str(e)},
                    exc_info=True
                )

        return results


def run_performance_benchmark() -> None:
    """Run comprehensive performance benchmark."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    benchmark = ExecutorBenchmark()

    # Define benchmark tasks
    def cpu_task(complexity: int) -> int:
        """CPU-bound task with adjustable complexity."""
        result = 0
        for i in range(complexity * 100):
            result += i * i
        return result

    def io_task(delay: int) -> str:
        """I/O-bound task with simulated delay."""
        time.sleep(delay * 0.01)  # Convert to seconds
        return f"Completed after {delay * 0.01}s"

    # Test configurations
    configs = [
        {"max_workers": 1, "name": "SingleThread"},
        {"max_workers": 2, "name": "DualThread"},
        {"max_workers": 4, "name": "QuadThread"},
        {"max_workers": 8, "name": "OctoThread"},
    ]

    print("=== TypedThreadPoolExecutor Performance Benchmark ===\n")

    # CPU-bound benchmark
    print("Running CPU-bound benchmark...")
    cpu_task_args = [500] * 20  # 20 tasks of medium complexity
    cpu_results = benchmark.compare_configurations(configs, cpu_task, cpu_task_args)

    print("CPU-bound Results:")
    for result in cpu_results:
        print(f"  {result.executor_name}: {result.throughput:.1f} tasks/sec, "
              f"{result.avg_latency:.3f}s avg latency")

    # I/O-bound benchmark
    print("\nRunning I/O-bound benchmark...")
    io_task_args = [5] * 20  # 20 tasks with 50ms delay each
    io_results = benchmark.compare_configurations(configs, io_task, io_task_args)

    print("I/O-bound Results:")
    for result in io_results:
        print(f"  {result.executor_name}: {result.throughput:.1f} tasks/sec, "
              f"{result.avg_latency:.3f}s avg latency")

    # Analysis
    print("\n=== Analysis ===")

    if cpu_results and len(cpu_results) > 1:
        single_cpu = next((r for r in cpu_results if r.max_workers == 1), None)
        multi_cpu = max(cpu_results, key=lambda r: r.throughput)

        if single_cpu and multi_cpu:
            speedup = multi_cpu.throughput / single_cpu.throughput
            print(".2f")

    if io_results and len(io_results) > 1:
        single_io = next((r for r in io_results if r.max_workers == 1), None)
        multi_io = max(io_results, key=lambda r: r.throughput)

        if single_io and multi_io:
            speedup = multi_io.throughput / single_io.throughput
            print(".2f")

    print("\nBenchmark completed!")


if __name__ == "__main__":
    """Run benchmark when executed directly."""
    run_performance_benchmark()

