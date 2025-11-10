"""
Custom Hybrid Executor.

This module demonstrates intelligent concurrency execution that automatically
chooses the best concurrency model based on task characteristics and system
load, combining asyncio, threading, and multiprocessing dynamically.

Key patterns:
- Intelligent task routing based on workload characteristics
- Dynamic resource allocation and load balancing
- Performance monitoring and adaptive scaling
- Unified API for different concurrency models
"""

import asyncio
import threading
import multiprocessing
import concurrent.futures
import time
import logging
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
import os
from typing import Any, Callable, List, Dict, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import statistics

logger = logging.getLogger(__name__)


class ConcurrencyModel(Enum):
    """Available concurrency models."""
    ASYNCIO = "asyncio"
    THREADING = "threading"
    MULTIPROCESSING = "multiprocessing"


@dataclass
class TaskProfile:
    """Profile information for a task type."""
    name: str
    model: ConcurrencyModel
    avg_execution_time: float = 0.0
    execution_count: int = 0
    success_rate: float = 1.0
    cpu_intensity: float = 0.0  # 0.0 = I/O bound, 1.0 = CPU bound
    memory_usage: float = 0.0
    last_used: float = 0.0


@dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    result: Any
    execution_time: float
    model_used: ConcurrencyModel
    worker_id: Union[int, str]
    success: bool
    error: Optional[str] = None


@dataclass
class SystemMetrics:
    """Current system performance metrics."""
    cpu_percent: float
    memory_percent: float
    active_threads: int
    active_processes: int
    load_average: Optional[float]

    @classmethod
    def collect(cls) -> 'SystemMetrics':
        """Collect current system metrics."""
        if not PSUTIL_AVAILABLE:
            # Return basic metrics without psutil
            return cls(
                cpu_percent=0.0,
                memory_percent=0.0,
                active_threads=threading.active_count(),
                active_processes=0,
                load_average=None
            )

        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Get thread and process counts
            active_threads = threading.active_count()
            active_processes = len(psutil.Process().children(recursive=True))

            # Load average (Unix-like systems only)
            try:
                load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else None
            except (OSError, AttributeError):
                load_avg = None

            return cls(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                active_threads=active_threads,
                active_processes=active_processes,
                load_average=load_avg
            )
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            return cls(0.0, 0.0, threading.active_count(), 0, None)


class CustomHybridExecutor:
    """
    Intelligent hybrid executor that automatically selects the best concurrency
    model based on task characteristics and system conditions.

    Features:
    - Automatic model selection based on workload analysis
    - Adaptive scaling based on system load
    - Performance profiling and optimization
    - Unified API for all concurrency models
    """

    def __init__(self,
                 max_threads: int = 8,
                 max_processes: Optional[int] = None,
                 enable_asyncio: bool = True):
        self.max_threads = max_threads
        self.max_processes = max_processes or multiprocessing.cpu_count()
        self.enable_asyncio = enable_asyncio

        # Executors
        self._thread_executor: Optional[ThreadPoolExecutor] = None
        self._process_executor: Optional[ProcessPoolExecutor] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        # State management
        self._running = False
        self._task_counter = 0
        self._lock = threading.Lock()

        # Performance profiling
        self._task_profiles: Dict[str, TaskProfile] = {}
        self._execution_history: List[TaskResult] = []
        self._max_history_size = 1000

        # Adaptive scaling
        self._current_thread_workers = max_threads
        self._current_process_workers = self.max_processes

        # Thresholds for model selection
        self._cpu_intensity_threshold = 0.7  # Above this = CPU bound
        self._high_load_threshold = 80.0     # CPU % for high load
        self._memory_threshold = 85.0        # Memory % for high load

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Start the custom hybrid executor."""
        if self._running:
            return

        # Start thread and process executors
        self._thread_executor = ThreadPoolExecutor(
            max_workers=self.max_threads,
            thread_name_prefix="custom-thread"
        )
        self._process_executor = ProcessPoolExecutor(
            max_workers=self.max_processes
        )

        # Get or create event loop for asyncio
        try:
            self._event_loop = asyncio.get_event_loop()
        except RuntimeError:
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)

        self._running = True
        logger.info("Started CustomHybridExecutor")

    async def stop(self):
        """Stop the custom hybrid executor."""
        if not self._running:
            return

        self._running = False

        # Shutdown executors
        if self._thread_executor:
            self._thread_executor.shutdown(wait=True)
        if self._process_executor:
            self._process_executor.shutdown(wait=True)

        logger.info("Stopped CustomHybridExecutor")

    def _get_next_task_id(self) -> str:
        """Get next unique task ID."""
        with self._lock:
            self._task_counter += 1
            return f"custom_task_{self._task_counter}"

    def _analyze_task_characteristics(self, func: Callable, *args, **kwargs) -> Dict[str, float]:
        """
        Analyze task characteristics to determine optimal execution model.

        Returns:
            Dict with cpu_intensity, memory_estimate, etc.
        """
        # Simple heuristic analysis (in real implementation, this could be more sophisticated)
        func_name = getattr(func, '__name__', str(func))

        # Check function name for clues
        name_lower = func_name.lower()
        if any(keyword in name_lower for keyword in ['cpu', 'calculate', 'compute', 'process']):
            cpu_intensity = 0.8
        elif any(keyword in name_lower for keyword in ['io', 'fetch', 'load', 'save']):
            cpu_intensity = 0.2
        else:
            cpu_intensity = 0.5  # Default assumption

        # Estimate memory usage (very rough)
        memory_estimate = 0.1  # Base memory usage

        return {
            'cpu_intensity': cpu_intensity,
            'memory_estimate': memory_estimate,
            'estimated_complexity': len(args) + len(kwargs)
        }

    def _select_optimal_model(self,
                            task_analysis: Dict[str, float],
                            system_metrics: SystemMetrics) -> ConcurrencyModel:
        """
        Select the optimal concurrency model based on task and system analysis.

        Decision tree:
        1. If CPU intensive + high system load -> multiprocessing
        2. If I/O intensive + asyncio enabled -> asyncio
        3. If moderate load -> threading
        4. Fallback to threading
        """
        cpu_intensity = task_analysis['cpu_intensity']

        # High CPU intensity + high system load -> use multiprocessing
        if (cpu_intensity > self._cpu_intensity_threshold and
            system_metrics.cpu_percent > self._high_load_threshold):
            return ConcurrencyModel.MULTIPROCESSING

        # I/O intensive + asyncio available -> use asyncio
        if (cpu_intensity < 0.3 and self.enable_asyncio and
            system_metrics.memory_percent < self._memory_threshold):
            return ConcurrencyModel.ASYNCIO

        # Default to threading for moderate workloads
        return ConcurrencyModel.THREADING

    def _update_task_profile(self, task_type: str, result: TaskResult):
        """Update performance profile for a task type."""
        if task_type not in self._task_profiles:
            self._task_profiles[task_type] = TaskProfile(
                name=task_type,
                model=result.model_used
            )

        profile = self._task_profiles[task_type]

        # Update metrics
        profile.execution_count += 1
        profile.last_used = time.time()

        if result.success:
            # Update running average execution time
            alpha = 0.1  # Smoothing factor
            profile.avg_execution_time = (
                alpha * result.execution_time +
                (1 - alpha) * profile.avg_execution_time
            )

            # Update success rate
            profile.success_rate = (
                (profile.success_rate * (profile.execution_count - 1) + 1) /
                profile.execution_count
            )
        else:
            # Update success rate with failure
            profile.success_rate = (
                (profile.success_rate * (profile.execution_count - 1)) /
                profile.execution_count
            )

    def _add_to_history(self, result: TaskResult):
        """Add result to execution history."""
        self._execution_history.append(result)
        if len(self._execution_history) > self._max_history_size:
            self._execution_history.pop(0)

    async def execute_task(self,
                          func: Callable,
                          *args,
                          task_type: Optional[str] = None,
                          force_model: Optional[ConcurrencyModel] = None,
                          **kwargs) -> TaskResult:
        """
        Execute a task using the optimal concurrency model.

        Args:
            func: Function to execute
            task_type: Optional task type for profiling
            force_model: Force specific concurrency model
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            TaskResult with execution details
        """
        if not self._running:
            raise RuntimeError("Custom executor not started")

        task_id = self._get_next_task_id()
        task_type = task_type or getattr(func, '__name__', 'unknown_task')

        start_time = time.time()

        try:
            # Analyze task and system
            task_analysis = self._analyze_task_characteristics(func, *args, **kwargs)
            system_metrics = SystemMetrics.collect()

            # Select execution model
            if force_model:
                model = force_model
            else:
                model = self._select_optimal_model(task_analysis, system_metrics)

            logger.debug(f"Task {task_id}: selected model {model.value}")

            # Execute using selected model
            if model == ConcurrencyModel.ASYNCIO:
                # For asyncio, assume the function is already async
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    # Wrap sync function in thread for async context
                    result = await self._event_loop.run_in_executor(
                        self._thread_executor, func, *args, **kwargs
                    )
                worker_id = "asyncio"

            elif model == ConcurrencyModel.THREADING:
                result = await self._event_loop.run_in_executor(
                    self._thread_executor, func, *args, **kwargs
                )
                worker_id = threading.get_ident()

            elif model == ConcurrencyModel.MULTIPROCESSING:
                result = await self._event_loop.run_in_executor(
                    self._process_executor, func, *args, **kwargs
                )
                worker_id = os.getpid()

            execution_time = time.time() - start_time

            task_result = TaskResult(
                task_id=task_id,
                result=result,
                execution_time=execution_time,
                model_used=model,
                worker_id=worker_id,
                success=True
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Task {task_id} failed: {e}")

            task_result = TaskResult(
                task_id=task_id,
                result=None,
                execution_time=execution_time,
                model_used=ConcurrencyModel.THREADING,  # Default
                worker_id=threading.get_ident(),
                success=False,
                error=str(e)
            )

        # Update profiling and history
        self._update_task_profile(task_type, task_result)
        self._add_to_history(task_result)

        return task_result

    async def execute_batch(self,
                           tasks: List[Tuple[Callable, Tuple, Dict]],
                           task_types: Optional[List[str]] = None) -> List[TaskResult]:
        """
        Execute multiple tasks as a batch.

        Args:
            tasks: List of (func, args, kwargs) tuples
            task_types: Optional list of task type names

        Returns:
            List of TaskResult objects
        """
        if task_types is None:
            task_types = [None] * len(tasks)

        # Execute all tasks concurrently
        coroutines = [
            self.execute_task(func, *args, task_type=task_type, **kwargs)
            for (func, args, kwargs), task_type in zip(tasks, task_types)
        ]

        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Filter out exceptions (they're already logged in execute_task)
        successful_results = [
            result for result in results
            if isinstance(result, TaskResult)
        ]

        return successful_results

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics and recommendations."""
        if not self._execution_history:
            return {"message": "No execution history available"}

        # Calculate overall stats
        execution_times = [r.execution_time for r in self._execution_history if r.success]
        success_rate = sum(1 for r in self._execution_history if r.success) / len(self._execution_history)

        model_usage = {}
        for result in self._execution_history:
            model = result.model_used.value
            model_usage[model] = model_usage.get(model, 0) + 1

        return {
            "total_tasks": len(self._execution_history),
            "success_rate": success_rate,
            "avg_execution_time": statistics.mean(execution_times) if execution_times else 0,
            "model_usage": model_usage,
            "task_profiles": {
                name: {
                    "model": profile.model.value,
                    "avg_time": profile.avg_execution_time,
                    "execution_count": profile.execution_count,
                    "success_rate": profile.success_rate
                }
                for name, profile in self._task_profiles.items()
            }
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        metrics = SystemMetrics.collect()

        return {
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "active_threads": metrics.active_threads,
            "active_processes": metrics.active_processes,
            "load_average": metrics.load_average,
            "executor_status": "running" if self._running else "stopped"
        }


# Example task functions
def cpu_intensive_task(data: str, iterations: int = 10000) -> Dict[str, Any]:
    """CPU-intensive task."""
    import math
    result = sum(math.sin(i) * math.cos(i) for i in range(iterations))
    return {"task": "cpu", "input": data, "result": result}

def io_intensive_task(data: str, delay: float = 0.1) -> Dict[str, Any]:
    """I/O-intensive task."""
    time.sleep(delay)
    return {"task": "io", "input": data, "delay": delay}

async def async_task(data: str) -> Dict[str, Any]:
    """Async task."""
    await asyncio.sleep(0.05)
    return {"task": "async", "input": data}

def mixed_task(data: str) -> Dict[str, Any]:
    """Mixed workload task."""
    # Some CPU work
    result = sum(i * i for i in range(1000))
    # Some I/O simulation
    time.sleep(0.01)
    return {"task": "mixed", "input": data, "cpu_result": result}


async def demonstrate_custom_hybrid_executor():
    """Demonstrate the custom hybrid executor."""

    print("🎯 Custom Hybrid Executor Demonstration")
    print("=" * 45)

    async with CustomHybridExecutor(max_threads=4, max_processes=2) as executor:

        print("\n1. Automatic model selection:")
        print("-" * 30)

        # Execute different types of tasks
        tasks = [
            (cpu_intensive_task, ("cpu_data", 5000), {"task_type": "cpu_task"}),
            (io_intensive_task, ("io_data", 0.1), {"task_type": "io_task"}),
            (async_task, ("async_data",), {"task_type": "async_task"}),
            (mixed_task, ("mixed_data",), {"task_type": "mixed_task"}),
        ]

        print("Executing tasks with automatic model selection...")
        for func, args, kwargs in tasks:
            result = await executor.execute_task(func, *args, **kwargs)
            print(".3f"
                  f"model={result.model_used.value}")

        print("\n2. Batch execution:")
        print("-" * 19)

        # Batch execution
        batch_tasks = [
            (cpu_intensive_task, ("batch_cpu_1", 3000), {}),
            (cpu_intensive_task, ("batch_cpu_2", 3000), {}),
            (io_intensive_task, ("batch_io_1", 0.05), {}),
            (io_intensive_task, ("batch_io_2", 0.05), {}),
        ]

        start_time = time.time()
        batch_results = await executor.execute_batch(batch_tasks)
        batch_time = time.time() - start_time

        print(f"Executed {len(batch_results)} tasks in {batch_time:.3f}s")
        model_counts = {}
        for result in batch_results:
            model_counts[result.model_used.value] = model_counts.get(result.model_used.value, 0) + 1
        print(f"Model usage: {model_counts}")

        print("\n3. Performance statistics:")
        print("-" * 27)

        stats = executor.get_performance_stats()
        print(f"Total tasks executed: {stats['total_tasks']}")
        print(f"Success rate: {stats['success_rate']:.3f}")
        print(f"Avg execution time: {stats['avg_execution_time']:.3f}s")
        print(f"Model usage: {stats['model_usage']}")

        print("\n4. System status:")
        print("-" * 17)

        status = executor.get_system_status()
        print(".1f"
              ".1f"
              f"threads={status['active_threads']}, "
              f"processes={status['active_processes']}")

    print("\n✅ Custom hybrid executor demonstration complete!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Run demonstration
    asyncio.run(demonstrate_custom_hybrid_executor())
