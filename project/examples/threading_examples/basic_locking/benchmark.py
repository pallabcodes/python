"""
Performance benchmark for counter implementations.

This module provides comprehensive benchmarking to compare the
performance characteristics of thread-safe vs unsafe counter
implementations. It measures throughput, latency, and scalability
under different concurrency levels.
"""

import time
import threading
import logging
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from statistics import mean, median, stdev

from counter import ThreadSafeCounter, UnsafeCounter, increment_counter


@dataclass
class BenchmarkResult:
    """Result of a benchmark run.

    Attributes:
        implementation: Name of the implementation tested.
        thread_count: Number of threads used.
        total_operations: Total operations performed.
        total_time: Time taken for all operations.
        throughput: Operations per second.
        avg_latency: Average time per operation.
        thread_results: Individual thread timing results.
    """

    implementation: str
    thread_count: int
    total_operations: int
    total_time: float
    throughput: float
    avg_latency: float
    thread_results: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for analysis."""
        return {
            "implementation": self.implementation,
            "thread_count": self.thread_count,
            "total_operations": self.total_operations,
            "total_time": self.total_time,
            "throughput": self.throughput,
            "avg_latency": self.avg_latency,
            "thread_results": self.thread_results
        }


class CounterBenchmark:
    """
    Benchmark suite for counter implementations.

    Provides comprehensive performance testing of different counter
    implementations under various concurrency scenarios.

    When to Use:
        - Performance testing
        - Comparing implementations
        - Optimizing synchronization
        - Understanding lock overhead
        - Capacity planning

    Real-World Examples:
        - Performance testing: Test counter performance
        - Optimization: Optimize synchronization
        - Comparison: Compare implementations
        - Capacity planning: Plan for load
        - Benchmarking: Benchmark counter operations

    Gotchas:
        - Benchmark results vary by system
        - Warmup runs affect results
        - System load affects measurements
        - Multiple runs needed for accuracy
        - Results are relative, not absolute

    Performance Notes:
        - Benchmark overhead affects results
        - Warmup reduces JIT effects
        - Multiple runs improve accuracy
        - System load affects measurements

    Attributes:
        logger: Logger for benchmark execution details.
    """

    def __init__(self) -> None:
        """Initialize the benchmark suite."""
        self._logger: logging.Logger = logging.getLogger(__name__)

    def benchmark_implementation(
        self,
        counter_class: type,
        thread_count: int,
        operations_per_thread: int,
        warmup_runs: int = 2
    ) -> BenchmarkResult:
        """Benchmark a specific counter implementation.

        Args:
            counter_class: Counter class to benchmark.
            thread_count: Number of concurrent threads.
            operations_per_thread: Operations per thread.
            warmup_runs: Number of warmup runs before measurement.

        Returns:
            Detailed benchmark results.
        """
        implementation_name = counter_class.__name__
        total_operations = thread_count * operations_per_thread

        self._logger.info(
            f"Benchmarking {implementation_name}",
            extra={
                "implementation": implementation_name,
                "thread_count": thread_count,
                "operations_per_thread": operations_per_thread,
                "total_operations": total_operations
            }
        )

        # Warmup runs
        for _ in range(warmup_runs):
            self._run_single_benchmark(counter_class, thread_count, operations_per_thread)

        # Actual benchmark run
        start_time = time.time()
        thread_times = self._run_single_benchmark(
            counter_class, thread_count, operations_per_thread
        )
        total_time = time.time() - start_time

        # Calculate metrics
        throughput = total_operations / total_time
        avg_latency = total_time / total_operations

        result = BenchmarkResult(
            implementation=implementation_name,
            thread_count=thread_count,
            total_operations=total_operations,
            total_time=total_time,
            throughput=throughput,
            avg_latency=avg_latency,
            thread_results=thread_times
        )

        self._logger.info(
            f"Benchmark completed: {throughput:.0f} ops/sec, "
            f"{avg_latency*1000:.2f} ms/op",
            extra={
                "implementation": implementation_name,
                "throughput": throughput,
                "avg_latency": avg_latency,
                "total_time": total_time
            }
        )

        return result

    def _run_single_benchmark(
        self,
        counter_class: type,
        thread_count: int,
        operations_per_thread: int
    ) -> List[Dict[str, Any]]:
        """Run a single benchmark iteration.

        Args:
            counter_class: Counter class to test.
            thread_count: Number of threads.
            operations_per_thread: Operations per thread.

        Returns:
            List of thread execution results.
        """
        counter = counter_class()
        threads: List[threading.Thread] = []
        thread_results: List[Dict[str, Any]] = []

        # Create threads with timing
        def timed_increment(thread_id: int) -> None:
            """Increment counter with timing measurement."""
            thread_start = time.time()
            increment_counter(counter, operations_per_thread)
            thread_end = time.time()

            thread_results.append({
                "thread_id": thread_id,
                "duration": thread_end - thread_start,
                "operations": operations_per_thread
            })

        # Start all threads
        for i in range(thread_count):
            thread = threading.Thread(target=lambda tid=i: timed_increment(tid))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        return thread_results

    def run_comprehensive_benchmark(
        self,
        implementations: List[type],
        thread_counts: List[int],
        operations_per_thread: int = 10000
    ) -> List[BenchmarkResult]:
        """Run comprehensive benchmark across multiple configurations.

        Args:
            implementations: List of counter classes to test.
            thread_counts: List of thread counts to test.
            operations_per_thread: Operations per thread.

        Returns:
            List of all benchmark results.
        """
        results: List[BenchmarkResult] = []

        for impl in implementations:
            for thread_count in thread_counts:
                try:
                    result = self.benchmark_implementation(
                        impl, thread_count, operations_per_thread
                    )
                    results.append(result)
                except Exception as e:
                    self._logger.error(
                        f"Benchmark failed for {impl.__name__} "
                        f"with {thread_count} threads: {e}",
                        exc_info=True
                    )

        return results


def analyze_benchmark_results(results: List[BenchmarkResult]) -> Dict[str, Any]:
    """Analyze benchmark results and generate insights.

    Args:
        results: List of benchmark results to analyze.

    Returns:
        Analysis summary with key insights.
    """
    if not results:
        return {"error": "No results to analyze"}

    # Group by implementation
    by_implementation: Dict[str, List[BenchmarkResult]] = {}
    for result in results:
        if result.implementation not in by_implementation:
            by_implementation[result.implementation] = []
        by_implementation[result.implementation].append(result)

    analysis = {
        "implementations": {},
        "recommendations": []
    }

    for impl, impl_results in by_implementation.items():
        # Calculate throughput scaling
        throughput_by_threads = {}
        for result in impl_results:
            throughput_by_threads[result.thread_count] = result.throughput

        # Sort by thread count for scaling analysis
        sorted_threads = sorted(throughput_by_threads.keys())
        scaling_factors = []

        for i in range(1, len(sorted_threads)):
            prev_threads = sorted_threads[i-1]
            curr_threads = sorted_threads[i]
            scaling = throughput_by_threads[curr_threads] / throughput_by_threads[prev_threads]
            scaling_factors.append(scaling / (curr_threads / prev_threads))

        avg_scaling = mean(scaling_factors) if scaling_factors else 1.0

        analysis["implementations"][impl] = {
            "results": [r.to_dict() for r in impl_results],
            "avg_scaling_efficiency": avg_scaling,
            "max_throughput": max(r.throughput for r in impl_results),
            "min_latency": min(r.avg_latency for r in impl_results)
        }

    # Generate recommendations
    safe_results = by_implementation.get("ThreadSafeCounter", [])
    unsafe_results = by_implementation.get("UnsafeCounter", [])

    if safe_results and unsafe_results:
        safe_throughput = mean(r.throughput for r in safe_results)
        unsafe_throughput = mean(r.throughput for r in unsafe_results)
        overhead = ((safe_throughput - unsafe_throughput) / unsafe_throughput) * 100

        if overhead > 50:
            analysis["recommendations"].append(
                f"ThreadSafeCounter has {overhead:.1f}% throughput overhead. "
                "Consider lock-free alternatives for high-contention scenarios."
            )
        elif overhead < 10:
            analysis["recommendations"].append(
                "ThreadSafeCounter overhead is minimal. "
                "Use for all concurrent scenarios."
            )

    return analysis


def run_performance_benchmark() -> None:
    """Run comprehensive performance benchmark."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    benchmark = CounterBenchmark()

    # Test configurations
    implementations = [ThreadSafeCounter, UnsafeCounter]
    thread_counts = [1, 2, 4, 8]
    operations_per_thread = 5000

    print("=== Counter Performance Benchmark ===\n")

    # Run benchmarks
    results = benchmark.run_comprehensive_benchmark(
        implementations, thread_counts, operations_per_thread
    )

    # Print results
    for result in results:
        print(f"{result.implementation} ({result.thread_count} threads):")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")
        print(f"  Avg Latency: {result.avg_latency*1000:.2f} ms/op")
        print()

    # Analyze results
    analysis = analyze_benchmark_results(results)

    print("=== Analysis ===")
    for impl, data in analysis.get("implementations", {}).items():
        print(f"{impl}:")
        print(f"  Scaling Efficiency: {data['avg_scaling_efficiency']:.1f}")
        print(f"  Max Throughput: {data['max_throughput']:.0f} ops/sec")
        print(f"  Min Latency: {data['min_latency']*1000:.1f} ms/op")
        print()

    for rec in analysis.get("recommendations", []):
        print(f"💡 {rec}")


if __name__ == "__main__":
    """Run benchmark when executed directly."""
    run_performance_benchmark()

