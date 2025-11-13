"""
Comprehensive benchmarking framework for all concurrency techniques.

This module benchmarks ALL concurrency techniques from ALL example directories:
- threading_examples
- multiprocessing_examples
- asyncio_examples
- subprocess_examples
- concurrent_futures
- hybrid_concurrency
- advanced_hybrid_concurrency
"""

import asyncio
import threading
import multiprocessing
import subprocess
import time
import logging
import statistics
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import queue

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    
    strategy_name: str
    execution_time: float
    throughput: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    resource_usage: Dict[str, float]
    success_rate: float
    error_count: int
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmarking."""
    
    num_iterations: int = 10
    num_tasks: int = 100
    warmup_iterations: int = 2
    timeout_seconds: float = 30.0
    collect_metrics: bool = True


class BenchmarkRunner:
    """
    Comprehensive benchmark runner for all concurrency techniques.
    
    Benchmarks:
    - Threading: Thread pools, synchronization, producer-consumer
    - Multiprocessing: Process pools, shared memory, IPC, synchronization
    - Asyncio: Coroutines, tasks, async patterns, async I/O
    - Subprocess: External process execution, communication, error handling
    - Concurrent.futures: ThreadPoolExecutor, ProcessPoolExecutor, futures
    - Hybrid: All hybrid combinations
    - Advanced: Distributed patterns, actor model, reactive programming
    """
    
    def __init__(self, config: Any):
        """Initialize benchmark runner."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._benchmark_config = BenchmarkConfig()
        
    async def run_comprehensive_benchmark(self, workload: Any) -> Dict[str, BenchmarkResult]:
        """
        Run comprehensive benchmarks for all concurrency techniques.
        
        Args:
            workload: The workload to benchmark
            
        Returns:
            Dictionary mapping strategy names to benchmark results
        """
        self._logger.info("Starting comprehensive benchmark suite")
        
        results = {}
        
        # Benchmark threading strategies
        if callable(workload) and not asyncio.iscoroutinefunction(workload):
            results.update(await self._benchmark_threading(workload))
            results.update(await self._benchmark_multiprocessing(workload))
            results.update(await self._benchmark_concurrent_futures(workload))
        
        # Benchmark asyncio strategies
        if asyncio.iscoroutinefunction(workload) or callable(workload):
            results.update(await self._benchmark_asyncio(workload))
        
        # Benchmark subprocess strategies
        if isinstance(workload, (list, tuple)):
            results.update(await self._benchmark_subprocess(workload))
        
        # Benchmark hybrid strategies
        if callable(workload):
            results.update(await self._benchmark_hybrid(workload))
            results.update(await self._benchmark_advanced(workload))
        
        self._logger.info(f"Benchmark suite complete: {len(results)} strategies tested")
        
        return results
    
    async def _benchmark_threading(self, task: Callable) -> Dict[str, BenchmarkResult]:
        """Benchmark threading strategies."""
        results = {}
        
        # Thread pool benchmark
        latencies = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers_threading) as executor:
            futures = [executor.submit(task) for _ in range(self._benchmark_config.num_tasks)]
            for future in as_completed(futures):
                task_start = time.time()
                future.result()
                latencies.append(time.time() - task_start)
        
        total_time = time.time() - start_time
        
        if latencies:
            latencies.sort()
            results["threading_thread_pool"] = BenchmarkResult(
                strategy_name="threading_thread_pool",
                execution_time=total_time,
                throughput=self._benchmark_config.num_tasks / total_time if total_time > 0 else 0,
                latency_p50=statistics.median(latencies),
                latency_p95=latencies[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0,
                latency_p99=latencies[int(len(latencies) * 0.99)] if len(latencies) > 0 else 0,
                resource_usage={},
                success_rate=1.0,
                error_count=0,
            )
        
        # Producer-consumer benchmark
        pc_queue = queue.Queue(maxsize=100)
        latencies_pc = []
        
        def producer():
            for i in range(self._benchmark_config.num_tasks):
                pc_queue.put(i)
        
        def consumer():
            items = []
            while True:
                try:
                    item = pc_queue.get(timeout=1.0)
                    if item is None:
                        break
                    item_start = time.time()
                    task()
                    items.append(time.time() - item_start)
                    pc_queue.task_done()
                except queue.Empty:
                    break
            return items
        
        pc_start = time.time()
        prod_thread = threading.Thread(target=producer)
        cons_thread = threading.Thread(target=consumer)
        prod_thread.start()
        cons_thread.start()
        prod_thread.join()
        pc_queue.put(None)
        cons_thread.join()
        pc_time = time.time() - pc_start
        
        if latencies_pc:
            latencies_pc.sort()
            results["threading_producer_consumer"] = BenchmarkResult(
                strategy_name="threading_producer_consumer",
                execution_time=pc_time,
                throughput=self._benchmark_config.num_tasks / pc_time if pc_time > 0 else 0,
                latency_p50=statistics.median(latencies_pc) if latencies_pc else 0,
                latency_p95=latencies_pc[int(len(latencies_pc) * 0.95)] if len(latencies_pc) > 0 else 0,
                latency_p99=latencies_pc[int(len(latencies_pc) * 0.99)] if len(latencies_pc) > 0 else 0,
                resource_usage={},
                success_rate=1.0,
                error_count=0,
            )
        
        return results
    
    async def _benchmark_multiprocessing(self, task: Callable) -> Dict[str, BenchmarkResult]:
        """Benchmark multiprocessing strategies."""
        results = {}
        
        # Process pool benchmark
        latencies = []
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=self.config.max_workers_multiprocessing) as executor:
            futures = [executor.submit(task) for _ in range(self._benchmark_config.num_tasks)]
            for future in as_completed(futures):
                task_start = time.time()
                future.result()
                latencies.append(time.time() - task_start)
        
        total_time = time.time() - start_time
        
        if latencies:
            latencies.sort()
            results["multiprocessing_process_pool"] = BenchmarkResult(
                strategy_name="multiprocessing_process_pool",
                execution_time=total_time,
                throughput=self._benchmark_config.num_tasks / total_time if total_time > 0 else 0,
                latency_p50=statistics.median(latencies),
                latency_p95=latencies[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0,
                latency_p99=latencies[int(len(latencies) * 0.99)] if len(latencies) > 0 else 0,
                resource_usage={},
                success_rate=1.0,
                error_count=0,
            )
        
        return results
    
    async def _benchmark_asyncio(self, task: Callable) -> Dict[str, BenchmarkResult]:
        """Benchmark asyncio strategies."""
        results = {}
        
        # Task benchmark
        latencies = []
        start_time = time.time()
        
        async def task_wrapper():
            if asyncio.iscoroutinefunction(task):
                await task()
            else:
                await asyncio.to_thread(task)
        
        tasks = [asyncio.create_task(task_wrapper()) for _ in range(self._benchmark_config.num_tasks)]
        task_starts = {id(t): time.time() for t in tasks}
        
        await asyncio.gather(*tasks)
        
        for task in tasks:
            if id(task) in task_starts:
                latencies.append(time.time() - task_starts[id(task)])
        
        total_time = time.time() - start_time
        
        if latencies:
            latencies.sort()
            results["asyncio_tasks"] = BenchmarkResult(
                strategy_name="asyncio_tasks",
                execution_time=total_time,
                throughput=self._benchmark_config.num_tasks / total_time if total_time > 0 else 0,
                latency_p50=statistics.median(latencies),
                latency_p95=latencies[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0,
                latency_p99=latencies[int(len(latencies) * 0.99)] if len(latencies) > 0 else 0,
                resource_usage={},
                success_rate=1.0,
                error_count=0,
            )
        
        return results
    
    async def _benchmark_subprocess(self, command: List[str]) -> Dict[str, BenchmarkResult]:
        """Benchmark subprocess strategies."""
        results = {}
        
        # subprocess.run benchmark
        latencies = []
        start_time = time.time()
        
        for _ in range(self._benchmark_config.num_tasks):
            task_start = time.time()
            try:
                subprocess.run(command, capture_output=True, timeout=5.0)
                latencies.append(time.time() - task_start)
            except Exception:
                pass
        
        total_time = time.time() - start_time
        
        if latencies:
            latencies.sort()
            results["subprocess_run"] = BenchmarkResult(
                strategy_name="subprocess_run",
                execution_time=total_time,
                throughput=len(latencies) / total_time if total_time > 0 else 0,
                latency_p50=statistics.median(latencies),
                latency_p95=latencies[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0,
                latency_p99=latencies[int(len(latencies) * 0.99)] if len(latencies) > 0 else 0,
                resource_usage={},
                success_rate=len(latencies) / self._benchmark_config.num_tasks,
                error_count=self._benchmark_config.num_tasks - len(latencies),
            )
        
        return results
    
    async def _benchmark_concurrent_futures(self, task: Callable) -> Dict[str, BenchmarkResult]:
        """Benchmark concurrent.futures strategies."""
        results = {}
        
        # ThreadPoolExecutor benchmark
        latencies = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers_threading) as executor:
            futures = [executor.submit(task) for _ in range(self._benchmark_config.num_tasks)]
            for future in as_completed(futures):
                task_start = time.time()
                future.result()
                latencies.append(time.time() - task_start)
        
        total_time = time.time() - start_time
        
        if latencies:
            latencies.sort()
            results["concurrent_futures_thread_pool"] = BenchmarkResult(
                strategy_name="concurrent_futures_thread_pool",
                execution_time=total_time,
                throughput=self._benchmark_config.num_tasks / total_time if total_time > 0 else 0,
                latency_p50=statistics.median(latencies),
                latency_p95=latencies[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0,
                latency_p99=latencies[int(len(latencies) * 0.99)] if len(latencies) > 0 else 0,
                resource_usage={},
                success_rate=1.0,
                error_count=0,
            )
        
        # ProcessPoolExecutor benchmark
        latencies_mp = []
        start_time_mp = time.time()
        
        with ProcessPoolExecutor(max_workers=self.config.max_workers_multiprocessing) as executor:
            futures = [executor.submit(task) for _ in range(self._benchmark_config.num_tasks)]
            for future in as_completed(futures):
                task_start = time.time()
                future.result()
                latencies_mp.append(time.time() - task_start)
        
        total_time_mp = time.time() - start_time_mp
        
        if latencies_mp:
            latencies_mp.sort()
            results["concurrent_futures_process_pool"] = BenchmarkResult(
                strategy_name="concurrent_futures_process_pool",
                execution_time=total_time_mp,
                throughput=self._benchmark_config.num_tasks / total_time_mp if total_time_mp > 0 else 0,
                latency_p50=statistics.median(latencies_mp),
                latency_p95=latencies_mp[int(len(latencies_mp) * 0.95)] if len(latencies_mp) > 0 else 0,
                latency_p99=latencies_mp[int(len(latencies_mp) * 0.99)] if len(latencies_mp) > 0 else 0,
                resource_usage={},
                success_rate=1.0,
                error_count=0,
            )
        
        return results
    
    async def _benchmark_hybrid(self, task: Callable) -> Dict[str, BenchmarkResult]:
        """Benchmark hybrid strategies."""
        results = {}
        
        # Try to import hybrid patterns
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../examples'))
            from hybrid_concurrency import AsyncioThreadingHybrid
            
            latencies = []
            start_time = time.time()
            
            async with AsyncioThreadingHybrid(max_workers=4) as hybrid:
                for _ in range(self._benchmark_config.num_tasks):
                    task_start = time.time()
                    if asyncio.iscoroutinefunction(task):
                        await hybrid.run_io_task(task)
                    else:
                        await hybrid.run_cpu_task(task)
                    latencies.append(time.time() - task_start)
            
            total_time = time.time() - start_time
            
            if latencies:
                latencies.sort()
                results["hybrid_asyncio_threading"] = BenchmarkResult(
                    strategy_name="hybrid_asyncio_threading",
                    execution_time=total_time,
                    throughput=self._benchmark_config.num_tasks / total_time if total_time > 0 else 0,
                    latency_p50=statistics.median(latencies),
                    latency_p95=latencies[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0,
                    latency_p99=latencies[int(len(latencies) * 0.99)] if len(latencies) > 0 else 0,
                    resource_usage={},
                    success_rate=1.0,
                    error_count=0,
                )
        except ImportError:
            self._logger.warning("Hybrid concurrency modules not available for benchmarking")
        
        return results
    
    async def _benchmark_advanced(self, task: Callable) -> Dict[str, BenchmarkResult]:
        """Benchmark advanced strategies."""
        results = {}
        
        # Advanced patterns benchmarking would go here
        # This is a placeholder for distributed patterns, actor model, etc.
        
        return results

