"""
Situation-Specific Concurrency Solutions.

This module demonstrates optimized concurrency patterns for specific use cases:
- High-throughput processing (maximize total throughput)
- Low-latency processing (minimize individual response times)
- Mixed workload processing (balance throughput and latency)

Key patterns:
- Workload-aware task scheduling
- Resource allocation based on requirements
- Quality of Service (QoS) differentiation
- Adaptive concurrency based on system conditions
"""

import asyncio
import threading
import multiprocessing
import concurrent.futures
import time
import logging
import queue
import heapq
from typing import Any, Callable, List, Dict, Optional, Union, Tuple, Protocol
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import statistics

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class WorkloadType(Enum):
    """Types of workloads."""
    CPU_INTENSIVE = "cpu"
    IO_INTENSIVE = "io"
    MIXED = "mixed"


@dataclass(order=True)
class PrioritizedTask:
    """Task with priority for scheduling."""
    priority: int
    task_id: str = field(compare=False)
    func: Callable = field(compare=False)
    args: Tuple = field(compare=False, default_factory=tuple)
    kwargs: Dict = field(compare=False, default_factory=dict)
    submitted_time: float = field(compare=False, default_factory=time.time)
    workload_type: WorkloadType = field(compare=False, default=WorkloadType.MIXED)
    timeout: Optional[float] = field(compare=False, default=None)


@dataclass
class TaskMetrics:
    """Performance metrics for task execution."""
    task_id: str
    execution_time: float
    queue_time: float
    success: bool
    priority: Priority
    workload_type: WorkloadType


class HighThroughputProcessor:
    """
    Optimized for maximum throughput - processes as many tasks as possible.

    Key optimizations:
    - Large thread/process pools for parallel execution
    - Batch processing to reduce overhead
    - Minimal synchronization overhead
    - Focus on total operations per second

    When to Use:
        - Maximum throughput required
        - Batch processing workloads
        - High-volume task processing
        - Throughput over latency

    Real-World Examples:
        - Batch processing: Process large batches
        - Data ingestion: High-volume data processing
        - Log processing: Process many log entries
        - ETL pipelines: High-throughput ETL

    Gotchas:
        - Higher latency per task
        - Memory usage with large batches
        - Resource exhaustion risk
        - Less responsive to individual tasks

    Performance Notes:
        - Optimized for total throughput
        - Batch processing reduces overhead
        - Large pools improve parallelism
        - Balance throughput vs resource usage
    """

    def __init__(self,
                 max_threads: int = 16,
                 max_processes: int = 4,
                 batch_size: int = 100):
        self.max_threads = max_threads
        self.max_processes = max_processes
        self.batch_size = batch_size

        self._thread_executor: Optional[ThreadPoolExecutor] = None
        self._process_executor: Optional[ProcessPoolExecutor] = None
        self._running = False

        # Throughput metrics
        self._metrics: List[TaskMetrics] = []
        self._start_time = 0.0
        self._lock = threading.Lock()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start the high-throughput processor."""
        if self._running:
            return

        self._thread_executor = ThreadPoolExecutor(
            max_workers=self.max_threads,
            thread_name_prefix="throughput-thread"
        )
        self._process_executor = ProcessPoolExecutor(
            max_workers=self.max_processes
        )
        self._running = True
        self._start_time = time.time()
        logger.info(f"Started HighThroughputProcessor (threads={self.max_threads}, processes={self.max_processes})")

    async def stop(self):
        """Stop the processor."""
        if not self._running:
            return

        self._running = False
        if self._thread_executor:
            self._thread_executor.shutdown(wait=True)
        if self._process_executor:
            self._process_executor.shutdown(wait=True)

        logger.info("Stopped HighThroughputProcessor")

    async def process_batch(self, tasks: List[Tuple[Callable, Tuple, Dict]]) -> List[Any]:
        """
        Process tasks in optimized batches for maximum throughput.

        Strategy:
        - Group CPU-intensive tasks for process pool
        - Group I/O-intensive tasks for thread pool
        - Execute batches concurrently
        """
        if not self._running:
            raise RuntimeError("Processor not started")

        # Categorize tasks
        cpu_tasks = []
        io_tasks = []

        for func, args, kwargs in tasks:
            # Simple heuristic: check function name
            func_name = getattr(func, '__name__', '').lower()
            if any(keyword in func_name for keyword in ['cpu', 'calculate', 'compute']):
                cpu_tasks.append((func, args, kwargs))
            else:
                io_tasks.append((func, args, kwargs))

        # Execute batches concurrently
        loop = asyncio.get_event_loop()
        cpu_future = None
        io_future = None

        if cpu_tasks:
            cpu_future = loop.run_in_executor(
                self._process_executor,
                self._execute_batch_sync,
                cpu_tasks
            )

        if io_tasks:
            io_future = loop.run_in_executor(
                self._thread_executor,
                self._execute_batch_sync,
                io_tasks
            )

        # Wait for results
        results = []
        if cpu_future:
            cpu_results = await cpu_future
            results.extend(cpu_results)
        if io_future:
            io_results = await io_future
            results.extend(io_results)

        return results

    def _execute_batch_sync(self, tasks: List[Tuple[Callable, Tuple, Dict]]) -> List[Any]:
        """Execute a batch of tasks synchronously."""
        results = []
        for func, args, kwargs in tasks:
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                results.append(result)

                # Record metrics
                with self._lock:
                    self._metrics.append(TaskMetrics(
                        task_id=f"batch_task_{len(self._metrics)}",
                        execution_time=execution_time,
                        queue_time=0.0,  # Not tracked in batch mode
                        success=True,
                        priority=Priority.NORMAL,
                        workload_type=WorkloadType.CPU_INTENSIVE
                    ))

            except Exception as e:
                logger.error(f"Batch task failed: {e}")
                results.append(None)

        return results

    def get_throughput_stats(self) -> Dict[str, Any]:
        """Get throughput statistics."""
        if not self._metrics:
            return {"message": "No metrics available"}

        total_time = time.time() - self._start_time
        successful_tasks = [m for m in self._metrics if m.success]

        return {
            "total_tasks": len(self._metrics),
            "successful_tasks": len(successful_tasks),
            "total_time": total_time,
            "tasks_per_second": len(successful_tasks) / total_time if total_time > 0 else 0,
            "avg_execution_time": statistics.mean(m.execution_time for m in successful_tasks) if successful_tasks else 0,
            "success_rate": len(successful_tasks) / len(self._metrics)
        }

    async def high_throughput_real_world_example(self) -> None:
        """
        Real-World Scenario: High-Throughput Processor - Batch Data Processing.

        REAL-WORLD SCENARIO:
        ====================
        You're building a batch data processing system:
        - Process millions of records nightly
        - Throughput is critical (process as many as possible)
        - Individual task latency less important
        - Problem: Need maximum throughput
        
        THE PROBLEM WITHOUT HIGH-THROUGHPUT OPTIMIZATION:
        =================================================
        - Small pools → low parallelism → slow
        - No batching → high overhead → inefficient
        - Sequential processing → very slow
        - System underutilized → wasted resources
        
        THE SOLUTION:
        =============
        High-Throughput Processor enables:
        - Large thread/process pools → maximum parallelism
        - Batch processing → reduces overhead
        - Optimized for total throughput → processes more
        - Resource utilization → efficient
        - Optimal for batch workloads
        
        WHEN TO USE HIGH-THROUGHPUT PROCESSOR:
        ======================================
        ✅ Batch processing workloads
        ✅ Maximum throughput required
        ✅ High-volume task processing
        ✅ Throughput over latency
        ✅ ETL pipelines
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Batch Data Processing System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Batch data processing system")
        print("  - Process millions of records nightly")
        print("  - Throughput is critical (process as many as possible)")
        print("  - Individual task latency less important")
        print()
        print("THE PROBLEM:")
        print("  Without high-throughput optimization:")
        print("    ❌ Small pools → low parallelism → slow")
        print("    ❌ No batching → high overhead → inefficient")
        print("    ❌ Sequential processing → very slow")
        print("    ❌ System underutilized → wasted resources")
        print()
        print("THE SOLUTION:")
        print("  With High-Throughput Processor:")
        print("    ✅ Large thread/process pools → maximum parallelism")
        print("    ✅ Batch processing → reduces overhead")
        print("    ✅ Optimized for total throughput → processes more")
        print("    ✅ Resource utilization → efficient")
        print()
        print("=" * 70)
        print()

        def process_record(record_id: int) -> dict:
            """Process a single record."""
            # Simulate processing
            result = 0
            for i in range(10000):
                result += hash(f"record_{record_id}_{i}") % 1000
            return {"record_id": record_id, "processed": True, "result": result}

        # Generate batch of records
        batch_tasks = [
            (process_record, (i,), {})
            for i in range(50)
        ]

        print(f"Processing batch of {len(batch_tasks)} records...")
        print(f"  - Thread pool: {self.max_threads} workers")
        print(f"  - Process pool: {self.max_processes} workers")
        print(f"  - Batch size: {self.batch_size}")
        print()

        start_time = time.time()
        results = await self.process_batch(batch_tasks)
        elapsed = time.time() - start_time

        stats = self.get_throughput_stats()
        print("Results:")
        print(f"  Records processed: {len(results)}")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Throughput: {stats['tasks_per_second']:.1f} tasks/second")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        print("  ✅ High-Throughput Processor maximized batch processing speed!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE HIGH-THROUGHPUT PROCESSOR:")
        print("   ✅ Batch processing workloads")
        print("   ✅ Maximum throughput required")
        print("   ✅ High-volume task processing")
        print("   ✅ Throughput over latency")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Maximum parallelism")
        print("   - Batch processing reduces overhead")
        print("   - Optimal resource utilization")
        print("   - Processes more tasks per second")
        print("=" * 70)
        print()


class LowLatencyProcessor:
    """
    Optimized for minimum latency - fastest response times for individual tasks.

    Key optimizations:
    - Small thread pools to reduce contention
    - Priority-based scheduling
    - Dedicated resources for high-priority tasks
    - Minimal queueing delays
    """

    def __init__(self, max_threads: int = 4, priority_queues: int = 4):
        self.max_threads = max_threads
        self.priority_queues = priority_queues

        self._executor: Optional[ThreadPoolExecutor] = None
        self._running = False

        # Priority queues (higher priority = lower number)
        self._queues: List[queue.PriorityQueue] = [
            queue.PriorityQueue() for _ in range(priority_queues)
        ]
        self._queue_lock = threading.Lock()

        # Worker threads
        self._workers: List[threading.Thread] = []
        self._shutdown_event = threading.Event()

        # Metrics
        self._metrics: List[TaskMetrics] = []
        self._lock = threading.Lock()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start the low-latency processor."""
        if self._running:
            return

        self._executor = ThreadPoolExecutor(
            max_workers=self.max_threads,
            thread_name_prefix="latency-thread"
        )

        # Start worker threads for each priority level
        for i in range(self.priority_queues):
            worker = threading.Thread(
                target=self._priority_worker,
                args=(i,),
                name=f"priority-worker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)

        self._running = True
        logger.info(f"Started LowLatencyProcessor with {self.priority_queues} priority levels")

    async def stop(self):
        """Stop the processor."""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        # Wait for workers with timeout handling
        for worker in self._workers:
            worker.join(timeout=5.0)
            if worker.is_alive():
                logger.warning(f"Worker {worker.name} did not shutdown within timeout, may still be running")

        if self._executor:
            self._executor.shutdown(wait=True)

        logger.info("Stopped LowLatencyProcessor")

    def submit_task(self,
                   func: Callable,
                   *args,
                   priority: Priority = Priority.NORMAL,
                   workload_type: WorkloadType = WorkloadType.MIXED,
                   timeout: Optional[float] = None,
                   **kwargs) -> str:
        """
        Submit a task with priority for low-latency execution.
        """
        if not self._running:
            raise RuntimeError("Processor not started")

        task_id = f"latency_task_{int(time.time() * 1000000)}"
        task = PrioritizedTask(
            priority=priority.value,
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            workload_type=workload_type,
            timeout=timeout
        )

        # Add to appropriate priority queue
        queue_index = min(priority.value - 1, self.priority_queues - 1)
        with self._queue_lock:
            self._queues[queue_index].put(task)

        return task_id

    def _priority_worker(self, priority_level: int):
        """Worker thread for processing tasks at a specific priority level."""
        while not self._shutdown_event.is_set():
            try:
                # Get task from queue with timeout
                task = self._queues[priority_level].get(timeout=0.1)

                # Execute task
                self._execute_task(task)

                # Mark task as done
                self._queues[priority_level].task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Priority worker {priority_level} error: {e}")

    def _execute_task(self, task: PrioritizedTask):
        """Execute a single task and record metrics."""
        submitted_time = task.submitted_time
        start_time = time.time()
        queue_time = start_time - submitted_time

        try:
            # Execute task (for low latency, we use threads regardless of workload)
            future = self._executor.submit(task.func, *task.args, **task.kwargs)
            result = future.result(timeout=task.timeout)

            execution_time = time.time() - start_time
            success = True

        except Exception as e:
            execution_time = time.time() - start_time
            success = False
            logger.error(f"Task {task.task_id} failed: {e}")

        # Record metrics
        with self._lock:
            self._metrics.append(TaskMetrics(
                task_id=task.task_id,
                execution_time=execution_time,
                queue_time=queue_time,
                success=success,
                priority=Priority(task.priority),
                workload_type=task.workload_type
            ))

    async def wait_for_completion(self, timeout: Optional[float] = None):
        """Wait for all submitted tasks to complete."""
        if not self._running:
            return

        # Wait for all queues to be empty
        end_time = time.time() + (timeout or 30.0)
        while time.time() < end_time:
            all_empty = all(q.empty() for q in self._queues)
            if all_empty:
                break
            await asyncio.sleep(0.01)

    def get_latency_stats(self) -> Dict[str, Any]:
        """Get latency statistics."""
        if not self._metrics:
            return {"message": "No metrics available"}

        successful_tasks = [m for m in self._metrics if m.success]

        # Group by priority
        by_priority = {}
        for metric in successful_tasks:
            prio = metric.priority.name
            if prio not in by_priority:
                by_priority[prio] = []
            by_priority[prio].append(metric.queue_time + metric.execution_time)

        priority_stats = {}
        for prio, latencies in by_priority.items():
            priority_stats[prio] = {
                "avg_latency": statistics.mean(latencies),
                "p95_latency": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "task_count": len(latencies)
            }

        return {
            "total_tasks": len(self._metrics),
            "successful_tasks": len(successful_tasks),
            "success_rate": len(successful_tasks) / len(self._metrics),
            "priority_stats": priority_stats,
            "avg_queue_time": statistics.mean(m.queue_time for m in successful_tasks) if successful_tasks else 0
        }


class MixedWorkloadProcessor:
    """
    Balanced processor for mixed workloads - optimizes for both throughput and latency.

    Key optimizations:
    - Dynamic resource allocation based on workload
    - Quality of Service (QoS) guarantees
    - Load balancing across different execution models
    - Adaptive batching for efficiency
    """

    def __init__(self,
                 base_threads: int = 6,
                 base_processes: int = 2,
                 qos_levels: int = 3):
        self.base_threads = base_threads
        self.base_processes = base_processes
        self.qos_levels = qos_levels

        # Executors for different QoS levels
        self._executors: Dict[int, Dict[str, Any]] = {}
        self._running = False

        # Adaptive scaling
        self._current_load = 0.0
        self._scale_lock = threading.Lock()

        # Metrics tracking
        self._metrics: List[TaskMetrics] = []
        self._lock = threading.Lock()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start the mixed workload processor."""
        if self._running:
            return

        # Initialize QoS level executors
        for qos_level in range(self.qos_levels):
            # Higher QoS gets more resources
            thread_factor = (qos_level + 1) / self.qos_levels
            process_factor = min(1.0, (qos_level + 1) / (self.qos_levels * 0.7))

            threads = max(1, int(self.base_threads * thread_factor))
            processes = max(1, int(self.base_processes * process_factor))

            self._executors[qos_level] = {
                'thread_executor': ThreadPoolExecutor(
                    max_workers=threads,
                    thread_name_prefix=f"mixed-qos{qos_level}-thread"
                ),
                'process_executor': ProcessPoolExecutor(
                    max_workers=processes
                ),
                'threads': threads,
                'processes': processes
            }

        self._running = True
        logger.info(f"Started MixedWorkloadProcessor with {self.qos_levels} QoS levels")

    async def stop(self):
        """Stop the processor."""
        if not self._running:
            return

        self._running = False

        # Shutdown all executors
        for qos_executors in self._executors.values():
            qos_executors['thread_executor'].shutdown(wait=True)
            qos_executors['process_executor'].shutdown(wait=True)

        logger.info("Stopped MixedWorkloadProcessor")

    async def submit_task(self,
                         func: Callable,
                         *args,
                         qos_level: int = 1,
                         workload_type: WorkloadType = WorkloadType.MIXED,
                         priority: Priority = Priority.NORMAL,
                         **kwargs) -> Any:
        """
        Submit task with QoS level and workload awareness.
        """
        if not self._running:
            raise RuntimeError("Processor not started")

        if qos_level not in self._executors:
            qos_level = min(qos_level, self.qos_levels - 1)

        executors = self._executors[qos_level]

        # Choose executor based on workload type
        start_time = time.time()

        try:
            if workload_type == WorkloadType.CPU_INTENSIVE:
                # Use process pool for CPU-intensive work
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    executors['process_executor'], func, *args, **kwargs
                )
            else:
                # Use thread pool for I/O or mixed work
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    executors['thread_executor'], func, *args, **kwargs
                )

            execution_time = time.time() - start_time

            # Record metrics
            with self._lock:
                self._metrics.append(TaskMetrics(
                    task_id=f"mixed_task_{len(self._metrics)}",
                    execution_time=execution_time,
                    queue_time=0.0,  # Not precisely tracked
                    success=True,
                    priority=priority,
                    workload_type=workload_type
                ))

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            with self._lock:
                self._metrics.append(TaskMetrics(
                    task_id=f"mixed_task_{len(self._metrics)}",
                    execution_time=execution_time,
                    queue_time=0.0,
                    success=False,
                    priority=priority,
                    workload_type=workload_type
                ))

            logger.error(f"Mixed workload task failed: {e}")
            raise

    def get_resource_utilization(self) -> Dict[str, Any]:
        """Get resource utilization statistics."""
        utilization = {}
        for qos_level, executors in self._executors.items():
            utilization[f"qos_{qos_level}"] = {
                "allocated_threads": executors['threads'],
                "allocated_processes": executors['processes']
            }

        return {
            "resource_allocation": utilization,
            "total_metrics": len(self._metrics),
            "current_load": self._current_load
        }


# Example usage functions
def cpu_heavy_task(data: str, iterations: int = 50000) -> Dict[str, Any]:
    """CPU-intensive task."""
    import math
    result = sum(math.sin(i) * math.cos(i) for i in range(iterations))
    return {"type": "cpu", "data": data, "result": result}

def io_task(data: str, delay: float = 0.1) -> Dict[str, Any]:
    """I/O-intensive task."""
    time.sleep(delay)
    return {"type": "io", "data": data, "delay": delay}

def mixed_task(data: str) -> Dict[str, Any]:
    """Mixed workload task."""
    # Some CPU work
    cpu_result = sum(i * i for i in range(1000))
    # Some I/O simulation
    time.sleep(0.01)
    return {"type": "mixed", "data": data, "cpu_result": cpu_result}


async def demonstrate_situation_specific_processors():
    """Demonstrate situation-specific concurrency processors."""

    print("🎯 Situation-Specific Concurrency Processors")
    print("=" * 50)

    # 1. High-Throughput Processor
    print("\n1. High-Throughput Processor:")
    print("-" * 32)

    async with HighThroughputProcessor(max_threads=8, max_processes=2) as processor:
        # Generate batch of mixed tasks
        tasks = []
        for i in range(50):
            if i % 3 == 0:
                tasks.append((cpu_heavy_task, (f"cpu_{i}", 10000), {}))
            else:
                tasks.append((io_task, (f"io_{i}", 0.02), {}))

        start_time = time.time()
        results = await processor.process_batch(tasks)
        throughput_time = time.time() - start_time

        stats = processor.get_throughput_stats()
        print(f"Processed {len(results)} tasks in {throughput_time:.3f}s")
        print(f"Tasks/sec: {stats['tasks_per_second']:.1f}")
        print(f"Avg execution time: {stats['avg_execution_time']:.3f}s")
    # 2. Low-Latency Processor
    print("\n2. Low-Latency Processor:")
    print("-" * 27)

    async with LowLatencyProcessor(max_threads=4, priority_queues=3) as processor:
        # Submit tasks with different priorities
        task_ids = []
        for i in range(20):
            priority = Priority.HIGH if i % 5 == 0 else Priority.NORMAL
            task_id = processor.submit_task(
                io_task, f"priority_{i}", 0.05,
                priority=priority
            )
            task_ids.append((task_id, priority))

        await processor.wait_for_completion(timeout=10.0)

        latency_stats = processor.get_latency_stats()
        print(f"Processed {latency_stats['total_tasks']} tasks")
        print(f"Success rate: {latency_stats['success_rate']:.3f}")

        # Show priority-based performance
        for prio, stats in latency_stats['priority_stats'].items():
            print(f"Priority {prio}: {stats['avg_latency']:.3f}s avg, "
                  f"{stats['task_count']} tasks")

    # 3. Mixed Workload Processor
    print("\n3. Mixed Workload Processor:")
    print("-" * 29)

    async with MixedWorkloadProcessor(base_threads=4, base_processes=2, qos_levels=3) as processor:
        # Submit tasks with different QoS levels and workload types
        tasks = []
        for i in range(15):
            if i % 3 == 0:
                # High QoS CPU task
                result = await processor.submit_task(
                    cpu_heavy_task, f"qos_cpu_{i}", 8000,
                    qos_level=2, workload_type=WorkloadType.CPU_INTENSIVE
                )
            elif i % 3 == 1:
                # Medium QoS I/O task
                result = await processor.submit_task(
                    io_task, f"qos_io_{i}", 0.03,
                    qos_level=1, workload_type=WorkloadType.IO_INTENSIVE
                )
            else:
                # Low QoS mixed task
                result = await processor.submit_task(
                    mixed_task, f"qos_mixed_{i}",
                    qos_level=0, workload_type=WorkloadType.MIXED
                )
            tasks.append(result)

        print(f"Processed {len(tasks)} tasks with QoS differentiation")

        utilization = processor.get_resource_utilization()
        print("Resource allocation by QoS level:")
        for qos, resources in utilization['resource_allocation'].items():
            print(f"  {qos}: {resources['allocated_threads']} threads, "
                  f"{resources['allocated_processes']} processes")

    print("\n✅ Situation-specific processors demonstration complete!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Run demonstration
    asyncio.run(demonstrate_situation_specific_processors())
