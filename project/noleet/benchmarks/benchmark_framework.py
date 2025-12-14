"""
Core benchmarking framework for performance measurement and analysis.
Provides tools for running benchmarks, collecting metrics, and analyzing results.
"""

import time
import psutil
import tracemalloc
import statistics
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance measurement data."""
    execution_time: float = 0.0
    cpu_percent: float = 0.0
    memory_usage: int = 0  # bytes
    peak_memory: int = 0   # bytes
    allocations: int = 0
    deallocations: int = 0
    memory_delta: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'execution_time': self.execution_time,
            'cpu_percent': self.cpu_percent,
            'memory_usage': self.memory_usage,
            'peak_memory': self.peak_memory,
            'allocations': self.allocations,
            'deallocations': self.deallocations,
            'memory_delta': self.memory_delta
        }


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    timestamp: datetime
    iterations: int
    metrics: PerformanceMetrics
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'name': self.name,
            'timestamp': self.timestamp.isoformat(),
            'iterations': self.iterations,
            'metrics': self.metrics.to_dict(),
            'metadata': self.metadata,
            'error': self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkResult':
        """Create result from dictionary."""
        return cls(
            name=data['name'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            iterations=data['iterations'],
            metrics=PerformanceMetrics(**data['metrics']),
            metadata=data.get('metadata', {}),
            error=data.get('error')
        )


class BenchmarkSuite:
    """Base class for benchmark suites."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.benchmarks: Dict[str, Callable] = {}

    def add_benchmark(self, name: str, func: Callable, **metadata):
        """Add a benchmark function."""
        self.benchmarks[name] = func
        # Store metadata for the function
        if not hasattr(func, '_benchmark_metadata'):
            func._benchmark_metadata = {}
        func._benchmark_metadata.update(metadata)

    def run_benchmark(self, benchmark_name: str, iterations: int = 1,
                     warmup_iterations: int = 0) -> BenchmarkResult:
        """Run a specific benchmark."""
        if benchmark_name not in self.benchmarks:
            raise ValueError(f"Benchmark '{benchmark_name}' not found")

        func = self.benchmarks[benchmark_name]
        metadata = getattr(func, '_benchmark_metadata', {})

        # Warmup runs
        for _ in range(warmup_iterations):
            try:
                func()
            except Exception:
                pass  # Ignore warmup errors

        # Actual benchmark run
        return self._run_single_benchmark(benchmark_name, func, iterations, metadata)

    def run_all(self, iterations: int = 1, warmup_iterations: int = 0) -> List[BenchmarkResult]:
        """Run all benchmarks in the suite."""
        results = []
        for name in self.benchmarks.keys():
            try:
                result = self.run_benchmark(name, iterations, warmup_iterations)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to run benchmark '{name}': {e}")
                # Create error result
                results.append(BenchmarkResult(
                    name=name,
                    timestamp=datetime.now(),
                    iterations=iterations,
                    metrics=PerformanceMetrics(),
                    error=str(e)
                ))
        return results

    def _run_single_benchmark(self, name: str, func: Callable, iterations: int,
                             metadata: Dict[str, Any]) -> BenchmarkResult:
        """Run a single benchmark with performance monitoring."""
        # Start memory tracing
        tracemalloc.start()
        tracemalloc.clear_traces()

        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        initial_cpu = psutil.cpu_percent(interval=None)

        start_time = time.perf_counter()
        start_cpu_time = time.process_time()

        try:
            # Run the benchmark function
            for _ in range(iterations):
                result = func()

            end_time = time.perf_counter()
            end_cpu_time = time.process_time()

            # Collect final metrics
            final_memory = process.memory_info().rss
            final_cpu = psutil.cpu_percent(interval=None)

            # Memory tracing stats
            current, peak = tracemalloc.get_traced_memory()
            stats = tracemalloc.get_tracemalloc_memory()
            tracemalloc.stop()

            # Calculate metrics
            execution_time = (end_time - start_time) / iterations
            cpu_time = (end_cpu_time - start_cpu_time) / iterations
            cpu_percent = max(0, final_cpu - initial_cpu)
            memory_usage = final_memory - initial_memory
            memory_delta = current - initial_memory if initial_memory else current

            # Extract allocation stats
            allocations = sum(stat.size for stat in stats)
            deallocations = sum(stat.count for stat in stats)

            metrics = PerformanceMetrics(
                execution_time=execution_time,
                cpu_percent=cpu_percent,
                memory_usage=memory_usage,
                peak_memory=peak,
                allocations=allocations,
                deallocations=deallocations,
                memory_delta=memory_delta
            )

            return BenchmarkResult(
                name=name,
                timestamp=datetime.now(),
                iterations=iterations,
                metrics=metrics,
                metadata=metadata
            )

        except Exception as e:
            tracemalloc.stop()
            raise e


class PerformanceProfiler:
    """Advanced performance profiling utilities."""

    @staticmethod
    def profile_function(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Profile a function execution with detailed metrics."""
        import cProfile
        import pstats
        import io

        pr = cProfile.Profile()
        pr.enable()

        start_time = time.perf_counter()
        tracemalloc.start()

        try:
            result = func(*args, **kwargs)
        finally:
            pr.disable()
            tracemalloc.stop()

        end_time = time.perf_counter()

        # Get profile stats
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()

        # Memory stats
        current, peak = tracemalloc.get_traced_memory()

        return {
            'result': result,
            'execution_time': end_time - start_time,
            'peak_memory': peak,
            'current_memory': current,
            'profile_stats': s.getvalue()
        }

    @staticmethod
    def measure_throughput(func: Callable, duration_seconds: int = 10,
                          *args, **kwargs) -> Dict[str, Any]:
        """Measure function throughput over a time period."""
        start_time = time.time()
        operations = 0
        latencies = []

        while time.time() - start_time < duration_seconds:
            op_start = time.perf_counter()
            func(*args, **kwargs)
            op_end = time.perf_counter()

            operations += 1
            latencies.append(op_end - op_start)

        total_time = time.time() - start_time

        return {
            'total_operations': operations,
            'total_time': total_time,
            'operations_per_second': operations / total_time,
            'average_latency': statistics.mean(latencies) if latencies else 0,
            'p50_latency': statistics.median(latencies) if latencies else 0,
            'p95_latency': statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies) if latencies else 0,
            'min_latency': min(latencies) if latencies else 0,
            'max_latency': max(latencies) if latencies else 0
        }


class MemoryProfiler:
    """Memory usage profiling and leak detection."""

    @staticmethod
    def profile_memory_usage(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Profile memory usage of a function."""
        tracemalloc.start()
        tracemalloc.clear_traces()

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        current, peak = tracemalloc.get_traced_memory()
        final_memory = process.memory_info().rss

        # Get allocation stats
        stats = tracemalloc.get_tracemalloc_memory()
        tracemalloc.stop()

        return {
            'result': result,
            'execution_time': end_time - start_time,
            'initial_memory': initial_memory,
            'final_memory': final_memory,
            'memory_delta': final_memory - initial_memory,
            'peak_memory': peak,
            'current_memory': current,
            'allocation_stats': [
                {
                    'file': stat.filename,
                    'line': stat.lineno,
                    'size': stat.size,
                    'count': stat.count
                }
                for stat in stats[:10]  # Top 10 allocations
            ]
        }

    @staticmethod
    def detect_memory_leaks(func: Callable, iterations: int = 100,
                           *args, **kwargs) -> Dict[str, Any]:
        """Detect potential memory leaks by running function multiple times."""
        tracemalloc.start()
        tracemalloc.clear_traces()

        memory_readings = []

        for i in range(iterations):
            tracemalloc.clear_traces()
            func(*args, **kwargs)
            current, _ = tracemalloc.get_traced_memory()
            memory_readings.append(current)

        tracemalloc.stop()

        # Analyze memory growth
        initial_memory = memory_readings[0]
        final_memory = memory_readings[-1]
        growth_rate = (final_memory - initial_memory) / iterations

        # Check for linear growth (potential leak)
        leak_detected = growth_rate > 1024  # More than 1KB per iteration

        return {
            'iterations': iterations,
            'initial_memory': initial_memory,
            'final_memory': final_memory,
            'memory_growth': final_memory - initial_memory,
            'growth_rate_per_iteration': growth_rate,
            'leak_detected': leak_detected,
            'memory_readings': memory_readings
        }
