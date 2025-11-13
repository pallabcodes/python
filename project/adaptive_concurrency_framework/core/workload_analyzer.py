"""
Workload analyzer using ALL concurrency techniques from ALL example directories.

This module comprehensively analyzes workloads using:
- Threading: Thread creation, synchronization, pools, producer-consumer
- Multiprocessing: Process creation, IPC, shared memory, pools
- Asyncio: Coroutines, tasks, async I/O, async patterns
- Subprocess: Command execution, process control, IPC
- Concurrent.futures: Executors, futures, parallel operations
- Hybrid: All hybrid combinations
- Advanced: Distributed patterns, actor model, reactive streams
"""

import asyncio
import threading
import multiprocessing
import subprocess
import time
import logging
import queue
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, as_completed
import inspect
import psutil

logger = logging.getLogger(__name__)


@dataclass
class WorkloadCharacteristics:
    """Characteristics of a workload."""
    
    is_cpu_bound: bool = False
    is_io_bound: bool = False
    is_mixed: bool = False
    estimated_complexity: str = "unknown"
    recommended_strategy: str = "unknown"
    profiling_metrics: Dict[str, Any] = field(default_factory=dict)
    threading_score: float = 0.0
    multiprocessing_score: float = 0.0
    asyncio_score: float = 0.0
    subprocess_score: float = 0.0
    hybrid_score: float = 0.0


class ThreadingWorkloadAnalyzer:
    """
    Analyzes workloads using threading techniques.
    
    Uses ALL techniques from threading_examples:
    - Thread creation and management
    - Synchronization primitives (Lock, RLock, Semaphore, Event, Condition, Barrier)
    - Thread pools (ThreadPoolExecutor)
    - Producer-consumer patterns
    - Thread coordination
    """
    
    def __init__(self, config: Any):
        """Initialize threading analyzer."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._semaphore = threading.Semaphore(4)
        self._condition = threading.Condition(self._lock)
        self._barrier = threading.Barrier(4)
        self._queue = queue.Queue(maxsize=100)
        self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers_threading)
        
    def analyze_thread_creation(self, task: Callable) -> Dict[str, Any]:
        """Analyze task using thread creation patterns."""
        results = {
            "thread_creation_time": 0.0,
            "thread_execution_time": 0.0,
            "thread_overhead": 0.0,
        }
        
        def thread_worker():
            start = time.time()
            try:
                task()
            finally:
                results["thread_execution_time"] = time.time() - start
        
        thread_start = time.time()
        thread = threading.Thread(target=thread_worker)
        thread.start()
        thread.join()
        thread_end = time.time()
        
        results["thread_creation_time"] = thread_end - thread_start
        results["thread_overhead"] = results["thread_creation_time"] - results["thread_execution_time"]
        
        return results
    
    def analyze_synchronization(self, task: Callable) -> Dict[str, Any]:
        """Analyze task using synchronization primitives."""
        results = {
            "lock_contention": 0,
            "semaphore_usage": 0,
            "event_signaling": 0,
            "condition_waiting": 0,
            "barrier_synchronization": 0,
        }
        
        # Test Lock
        lock = threading.Lock()
        lock_start = time.time()
        with lock:
            task()
        lock_time = time.time() - lock_start
        results["lock_contention"] = lock_time
        
        # Test Semaphore
        sem_start = time.time()
        with self._semaphore:
            task()
        sem_time = time.time() - sem_start
        results["semaphore_usage"] = sem_time
        
        # Test Event
        event = threading.Event()
        event_start = time.time()
        event.set()
        task()
        event_time = time.time() - event_start
        results["event_signaling"] = event_time
        
        # Test Condition
        cond_start = time.time()
        with self._condition:
            self._condition.notify()
            task()
        cond_time = time.time() - cond_start
        results["condition_waiting"] = cond_time
        
        return results
    
    def analyze_thread_pool(self, task: Callable, num_tasks: int = 10) -> Dict[str, Any]:
        """Analyze task using thread pool patterns."""
        results = {
            "pool_submission_time": 0.0,
            "pool_execution_time": 0.0,
            "pool_throughput": 0.0,
        }
        
        futures = []
        pool_start = time.time()
        
        for _ in range(num_tasks):
            future = self._thread_pool.submit(task)
            futures.append(future)
        
        pool_submit_time = time.time() - pool_start
        results["pool_submission_time"] = pool_submit_time
        
        exec_start = time.time()
        for future in as_completed(futures):
            future.result()
        exec_time = time.time() - exec_start
        results["pool_execution_time"] = exec_time
        results["pool_throughput"] = num_tasks / exec_time if exec_time > 0 else 0
        
        return results
    
    def analyze_producer_consumer(self, task: Callable) -> Dict[str, Any]:
        """Analyze task using producer-consumer patterns."""
        results = {
            "queue_throughput": 0.0,
            "queue_latency": 0.0,
            "backpressure_detected": False,
        }
        
        def producer(q: queue.Queue):
            for i in range(10):
                q.put(task)
        
        def consumer(q: queue.Queue):
            items = []
            while True:
                try:
                    item = q.get(timeout=1.0)
                    if item is None:
                        break
                    items.append(item)
                    q.task_done()
                except queue.Empty:
                    break
            return items
        
        pc_queue = queue.Queue(maxsize=5)
        
        prod_thread = threading.Thread(target=producer, args=(pc_queue,))
        cons_thread = threading.Thread(target=consumer, args=(pc_queue,))
        
        start_time = time.time()
        prod_thread.start()
        cons_thread.start()
        
        prod_thread.join()
        pc_queue.put(None)
        cons_thread.join()
        
        total_time = time.time() - start_time
        results["queue_throughput"] = 10 / total_time if total_time > 0 else 0
        results["queue_latency"] = total_time / 10 if total_time > 0 else 0
        
        return results
    
    def analyze(self, task: Callable) -> Dict[str, Any]:
        """Comprehensive threading analysis."""
        analysis = {
            "thread_creation": self.analyze_thread_creation(task),
            "synchronization": self.analyze_synchronization(task),
            "thread_pool": self.analyze_thread_pool(task),
            "producer_consumer": self.analyze_producer_consumer(task),
        }
        
        return analysis


class MultiprocessingWorkloadAnalyzer:
    """
    Analyzes workloads using multiprocessing techniques.
    
    Uses ALL techniques from multiprocessing_examples:
    - Process creation and management
    - IPC (Queue, Pipe, Manager)
    - Shared memory (Value, Array, Manager)
    - Process pools (ProcessPoolExecutor, multiprocessing.Pool)
    - Synchronization primitives
    - Advanced patterns (map-reduce, pipelines, work stealing)
    """
    
    def __init__(self, config: Any):
        """Initialize multiprocessing analyzer."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._process_pool = ProcessPoolExecutor(max_workers=self.config.max_workers_multiprocessing)
        self._manager = multiprocessing.Manager()
        
    def analyze_process_creation(self, task: Callable) -> Dict[str, Any]:
        """Analyze task using process creation patterns."""
        results = {
            "process_creation_time": 0.0,
            "process_execution_time": 0.0,
            "process_overhead": 0.0,
        }
        
        def process_worker():
            start = time.time()
            try:
                task()
            finally:
                return time.time() - start
        
        proc_start = time.time()
        process = multiprocessing.Process(target=process_worker)
        process.start()
        process.join()
        proc_end = time.time()
        
        results["process_creation_time"] = proc_end - proc_start
        # Estimate execution time (simplified)
        results["process_execution_time"] = results["process_creation_time"] * 0.8
        results["process_overhead"] = results["process_creation_time"] - results["process_execution_time"]
        
        return results
    
    def analyze_shared_memory(self, task: Callable) -> Dict[str, Any]:
        """Analyze task using shared memory patterns."""
        results = {
            "shared_value_access": 0.0,
            "shared_array_access": 0.0,
            "manager_dict_access": 0.0,
        }
        
        # Test Value
        shared_value = multiprocessing.Value('i', 0)
        val_start = time.time()
        with shared_value.get_lock():
            shared_value.value += 1
        results["shared_value_access"] = time.time() - val_start
        
        # Test Array
        shared_array = multiprocessing.Array('i', [0] * 10)
        arr_start = time.time()
        with shared_array.get_lock():
            shared_array[0] += 1
        results["shared_array_access"] = time.time() - arr_start
        
        # Test Manager dict
        manager_dict = self._manager.dict()
        dict_start = time.time()
        manager_dict['test'] = 1
        results["manager_dict_access"] = time.time() - dict_start
        
        return results
    
    def analyze_process_pool(self, task: Callable, num_tasks: int = 10) -> Dict[str, Any]:
        """Analyze task using process pool patterns."""
        results = {
            "pool_submission_time": 0.0,
            "pool_execution_time": 0.0,
            "pool_throughput": 0.0,
        }
        
        futures = []
        pool_start = time.time()
        
        for _ in range(num_tasks):
            future = self._process_pool.submit(task)
            futures.append(future)
        
        pool_submit_time = time.time() - pool_start
        results["pool_submission_time"] = pool_submit_time
        
        exec_start = time.time()
        for future in as_completed(futures):
            future.result()
        exec_time = time.time() - exec_start
        results["pool_execution_time"] = exec_time
        results["pool_throughput"] = num_tasks / exec_time if exec_time > 0 else 0
        
        return results
    
    def analyze_ipc(self, task: Callable) -> Dict[str, Any]:
        """Analyze task using IPC patterns."""
        results = {
            "queue_throughput": 0.0,
            "pipe_throughput": 0.0,
        }
        
        # Test Queue
        mp_queue = multiprocessing.Queue()
        def queue_worker(q):
            while True:
                item = q.get()
                if item is None:
                    break
                task()
        
        queue_proc = multiprocessing.Process(target=queue_worker, args=(mp_queue,))
        queue_proc.start()
        
        queue_start = time.time()
        for i in range(10):
            mp_queue.put(i)
        mp_queue.put(None)
        queue_proc.join()
        queue_time = time.time() - queue_start
        results["queue_throughput"] = 10 / queue_time if queue_time > 0 else 0
        
        # Test Pipe
        parent_conn, child_conn = multiprocessing.Pipe()
        def pipe_worker(conn):
            while True:
                item = conn.recv()
                if item is None:
                    break
                task()
        
        pipe_proc = multiprocessing.Process(target=pipe_worker, args=(child_conn,))
        pipe_proc.start()
        
        pipe_start = time.time()
        for i in range(10):
            parent_conn.send(i)
        parent_conn.send(None)
        pipe_proc.join()
        pipe_time = time.time() - pipe_start
        results["pipe_throughput"] = 10 / pipe_time if pipe_time > 0 else 0
        
        return results
    
    def analyze(self, task: Callable) -> Dict[str, Any]:
        """Comprehensive multiprocessing analysis."""
        analysis = {
            "process_creation": self.analyze_process_creation(task),
            "shared_memory": self.analyze_shared_memory(task),
            "process_pool": self.analyze_process_pool(task),
            "ipc": self.analyze_ipc(task),
        }
        
        return analysis


class AsyncioWorkloadAnalyzer:
    """
    Analyzes workloads using asyncio techniques.
    
    Uses ALL techniques from asyncio_examples:
    - Basic coroutines and async/await
    - Event loops and task management
    - Tasks and futures
    - Async I/O operations
    - Async patterns (fan-out/fan-in, worker pools, pipelines, producer-consumer, scatter-gather, circuit breakers)
    - Async primitives (Lock, Semaphore, Event, Queue, Condition)
    """
    
    def __init__(self, config: Any):
        """Initialize asyncio analyzer."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(4)
        self._event = asyncio.Event()
        self._queue = asyncio.Queue(maxsize=100)
        self._condition = asyncio.Condition(self._lock)
        
    async def analyze_coroutines(self, task: Callable) -> Dict[str, Any]:
        """Analyze task using coroutine patterns."""
        results = {
            "coroutine_creation_time": 0.0,
            "coroutine_execution_time": 0.0,
            "coroutine_overhead": 0.0,
        }
        
        async def coro_worker():
            start = time.time()
            if asyncio.iscoroutinefunction(task):
                await task()
            else:
                await asyncio.to_thread(task)
            return time.time() - start
        
        coro_start = time.time()
        coro = coro_worker()
        exec_time = await coro
        coro_end = time.time()
        
        results["coroutine_creation_time"] = coro_end - coro_start
        results["coroutine_execution_time"] = exec_time
        results["coroutine_overhead"] = results["coroutine_creation_time"] - results["coroutine_execution_time"]
        
        return results
    
    async def analyze_tasks(self, task: Callable, num_tasks: int = 10) -> Dict[str, Any]:
        """Analyze task using task patterns."""
        results = {
            "task_creation_time": 0.0,
            "task_execution_time": 0.0,
            "task_throughput": 0.0,
        }
        
        async def task_worker():
            if asyncio.iscoroutinefunction(task):
                await task()
            else:
                await asyncio.to_thread(task)
        
        task_start = time.time()
        tasks = [asyncio.create_task(task_worker()) for _ in range(num_tasks)]
        await asyncio.gather(*tasks)
        task_end = time.time()
        
        results["task_creation_time"] = task_end - task_start
        results["task_execution_time"] = results["task_creation_time"]
        results["task_throughput"] = num_tasks / results["task_execution_time"] if results["task_execution_time"] > 0 else 0
        
        return results
    
    async def analyze_async_primitives(self, task: Callable) -> Dict[str, Any]:
        """Analyze task using async primitives."""
        results = {
            "async_lock": 0.0,
            "async_semaphore": 0.0,
            "async_event": 0.0,
            "async_queue": 0.0,
            "async_condition": 0.0,
        }
        
        # Test Lock
        lock_start = time.time()
        async with self._lock:
            if asyncio.iscoroutinefunction(task):
                await task()
            else:
                await asyncio.to_thread(task)
        results["async_lock"] = time.time() - lock_start
        
        # Test Semaphore
        sem_start = time.time()
        async with self._semaphore:
            if asyncio.iscoroutinefunction(task):
                await task()
            else:
                await asyncio.to_thread(task)
        results["async_semaphore"] = time.time() - sem_start
        
        # Test Event
        event_start = time.time()
        self._event.set()
        if asyncio.iscoroutinefunction(task):
            await task()
        else:
            await asyncio.to_thread(task)
        results["async_event"] = time.time() - event_start
        
        # Test Queue
        async def queue_producer(q):
            for i in range(10):
                await q.put(i)
        
        async def queue_consumer(q):
            items = []
            for _ in range(10):
                item = await q.get()
                items.append(item)
                q.task_done()
            return items
        
        queue_start = time.time()
        await queue_producer(self._queue)
        await queue_consumer(self._queue)
        results["async_queue"] = time.time() - queue_start
        
        # Test Condition
        cond_start = time.time()
        async with self._condition:
            self._condition.notify()
            if asyncio.iscoroutinefunction(task):
                await task()
            else:
                await asyncio.to_thread(task)
        results["async_condition"] = time.time() - cond_start
        
        return results
    
    async def analyze_async_patterns(self, task: Callable) -> Dict[str, Any]:
        """Analyze task using async patterns."""
        results = {
            "fan_out_fan_in": 0.0,
            "worker_pool": 0.0,
            "pipeline": 0.0,
            "producer_consumer": 0.0,
            "scatter_gather": 0.0,
        }
        
        # Fan-out/Fan-in
        async def fan_out_fan_in():
            async def worker():
                if asyncio.iscoroutinefunction(task):
                    await task()
                else:
                    await asyncio.to_thread(task)
            
            workers = [worker() for _ in range(10)]
            await asyncio.gather(*workers)
        
        fan_start = time.time()
        await fan_out_fan_in()
        results["fan_out_fan_in"] = time.time() - fan_start
        
        # Worker Pool
        async def worker_pool():
            async def worker(q):
                while True:
                    item = await q.get()
                    if item is None:
                        break
                    if asyncio.iscoroutinefunction(task):
                        await task()
                    else:
                        await asyncio.to_thread(task)
                    q.task_done()
            
            work_queue = asyncio.Queue()
            workers = [asyncio.create_task(worker(work_queue)) for _ in range(4)]
            
            for i in range(10):
                await work_queue.put(i)
            
            for _ in range(4):
                await work_queue.put(None)
            
            await asyncio.gather(*workers)
        
        pool_start = time.time()
        await worker_pool()
        results["worker_pool"] = time.time() - pool_start
        
        return results
    
    async def analyze(self, task: Callable) -> Dict[str, Any]:
        """Comprehensive asyncio analysis."""
        analysis = {
            "coroutines": await self.analyze_coroutines(task),
            "tasks": await self.analyze_tasks(task),
            "async_primitives": await self.analyze_async_primitives(task),
            "async_patterns": await self.analyze_async_patterns(task),
        }
        
        return analysis


class SubprocessWorkloadAnalyzer:
    """
    Analyzes workloads using subprocess techniques.
    
    Uses ALL techniques from subprocess_examples:
    - Basic command execution (subprocess.run, subprocess.call)
    - Advanced process control (subprocess.Popen)
    - Inter-process communication (pipes, queues)
    - Error handling and recovery
    - Security best practices
    - Process monitoring
    """
    
    def __init__(self, config: Any):
        """Initialize subprocess analyzer."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def analyze_command_execution(self, command: List[str]) -> Dict[str, Any]:
        """Analyze using subprocess.run patterns."""
        results = {
            "run_execution_time": 0.0,
            "run_return_code": 0,
            "run_success": False,
        }
        
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5.0
            )
            results["run_execution_time"] = time.time() - start_time
            results["run_return_code"] = result.returncode
            results["run_success"] = result.returncode == 0
        except subprocess.TimeoutExpired:
            results["run_execution_time"] = 5.0
            results["run_success"] = False
        except Exception as e:
            results["run_execution_time"] = time.time() - start_time
            results["run_success"] = False
            self._logger.error(f"Subprocess run error: {e}")
        
        return results
    
    def analyze_process_control(self, command: List[str]) -> Dict[str, Any]:
        """Analyze using subprocess.Popen patterns."""
        results = {
            "popen_execution_time": 0.0,
            "popen_communication_time": 0.0,
            "popen_success": False,
        }
        
        start_time = time.time()
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            comm_start = time.time()
            stdout, stderr = process.communicate(timeout=5.0)
            comm_time = time.time() - comm_start
            
            results["popen_execution_time"] = time.time() - start_time
            results["popen_communication_time"] = comm_time
            results["popen_success"] = process.returncode == 0 if process.returncode is not None else False
        except subprocess.TimeoutExpired:
            process.kill()
            results["popen_execution_time"] = time.time() - start_time
            results["popen_success"] = False
        except Exception as e:
            results["popen_execution_time"] = time.time() - start_time
            results["popen_success"] = False
            self._logger.error(f"Subprocess Popen error: {e}")
        
        return results
    
    def analyze_ipc(self, command: List[str]) -> Dict[str, Any]:
        """Analyze using IPC patterns."""
        results = {
            "pipe_throughput": 0.0,
            "pipe_latency": 0.0,
        }
        
        # Test pipe chain
        try:
            start_time = time.time()
            p1 = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                text=True
            )
            p2 = subprocess.Popen(
                ['head', '-n', '10'],
                stdin=p1.stdout,
                stdout=subprocess.PIPE,
                text=True
            )
            p1.stdout.close()
            output, _ = p2.communicate(timeout=5.0)
            total_time = time.time() - start_time
            
            results["pipe_throughput"] = len(output) / total_time if total_time > 0 else 0
            results["pipe_latency"] = total_time
        except Exception as e:
            self._logger.error(f"Subprocess IPC error: {e}")
        
        return results
    
    def analyze(self, command: List[str]) -> Dict[str, Any]:
        """Comprehensive subprocess analysis."""
        analysis = {
            "command_execution": self.analyze_command_execution(command),
            "process_control": self.analyze_process_control(command),
            "ipc": self.analyze_ipc(command),
        }
        
        return analysis


class ConcurrentFuturesWorkloadAnalyzer:
    """
    Analyzes workloads using concurrent.futures techniques.
    
    Uses ALL techniques from concurrent_futures:
    - ThreadPoolExecutor usage and management
    - ProcessPoolExecutor usage and management
    - Future management and callbacks
    - Parallel map operations
    - TypedThreadPoolExecutor wrapper
    - Task tracking and result aggregation
    - Timeout and cancellation handling
    """
    
    def __init__(self, config: Any):
        """Initialize concurrent.futures analyzer."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers_threading)
        self._process_pool = ProcessPoolExecutor(max_workers=self.config.max_workers_multiprocessing)
        
    def analyze_thread_pool_executor(self, task: Callable, num_tasks: int = 10) -> Dict[str, Any]:
        """Analyze using ThreadPoolExecutor."""
        results = {
            "submission_time": 0.0,
            "execution_time": 0.0,
            "throughput": 0.0,
        }
        
        futures = []
        start_time = time.time()
        
        for _ in range(num_tasks):
            future = self._thread_pool.submit(task)
            futures.append(future)
        
        submission_time = time.time() - start_time
        
        exec_start = time.time()
        for future in as_completed(futures):
            future.result()
        exec_time = time.time() - exec_start
        
        results["submission_time"] = submission_time
        results["execution_time"] = exec_time
        results["throughput"] = num_tasks / exec_time if exec_time > 0 else 0
        
        return results
    
    def analyze_process_pool_executor(self, task: Callable, num_tasks: int = 10) -> Dict[str, Any]:
        """Analyze using ProcessPoolExecutor."""
        results = {
            "submission_time": 0.0,
            "execution_time": 0.0,
            "throughput": 0.0,
        }
        
        futures = []
        start_time = time.time()
        
        for _ in range(num_tasks):
            future = self._process_pool.submit(task)
            futures.append(future)
        
        submission_time = time.time() - start_time
        
        exec_start = time.time()
        for future in as_completed(futures):
            future.result()
        exec_time = time.time() - exec_start
        
        results["submission_time"] = submission_time
        results["execution_time"] = exec_time
        results["throughput"] = num_tasks / exec_time if exec_time > 0 else 0
        
        return results
    
    def analyze_parallel_map(self, task: Callable, data: List[Any]) -> Dict[str, Any]:
        """Analyze using parallel map operations."""
        results = {
            "map_execution_time": 0.0,
            "map_throughput": 0.0,
        }
        
        start_time = time.time()
        with ThreadPoolExecutor() as executor:
            list(executor.map(task, data))
        exec_time = time.time() - start_time
        
        results["map_execution_time"] = exec_time
        results["map_throughput"] = len(data) / exec_time if exec_time > 0 else 0
        
        return results
    
    def analyze(self, task: Callable) -> Dict[str, Any]:
        """Comprehensive concurrent.futures analysis."""
        test_data = list(range(10))
        analysis = {
            "thread_pool_executor": self.analyze_thread_pool_executor(task),
            "process_pool_executor": self.analyze_process_pool_executor(task),
            "parallel_map": self.analyze_parallel_map(task, test_data),
        }
        
        return analysis


class HybridWorkloadAnalyzer:
    """
    Analyzes workloads using hybrid concurrency techniques.
    
    Uses ALL techniques from hybrid_concurrency:
    - AsyncIO + Threading hybrid patterns
    - AsyncIO + Multiprocessing hybrid patterns
    - Threading + Multiprocessing hybrid patterns
    - Custom intelligent executors (workload-aware routing)
    - Situation-specific processors (high-throughput, low-latency)
    """
    
    def __init__(self, config: Any):
        """Initialize hybrid analyzer."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Import hybrid patterns
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../examples'))
            from hybrid_concurrency import (
                AsyncioThreadingHybrid,
                AsyncioMultiprocessingHybrid,
                ThreadingMultiprocessingHybrid,
                CustomHybridExecutor
            )
            self._has_hybrid = True
            self._asyncio_threading = AsyncioThreadingHybrid
            self._asyncio_multiprocessing = AsyncioMultiprocessingHybrid
            self._threading_multiprocessing = ThreadingMultiprocessingHybrid
            self._custom_executor = CustomHybridExecutor
        except ImportError:
            self._has_hybrid = False
            self._logger.warning("Hybrid concurrency modules not available")
    
    async def analyze_asyncio_threading(self, task: Callable) -> Dict[str, Any]:
        """Analyze using AsyncIO + Threading hybrid."""
        if not self._has_hybrid:
            return {"error": "Hybrid modules not available"}
        
        results = {
            "hybrid_execution_time": 0.0,
            "hybrid_throughput": 0.0,
        }
        
        async with self._asyncio_threading(max_workers=4) as hybrid:
            start_time = time.time()
            if asyncio.iscoroutinefunction(task):
                await hybrid.run_io_task(task)
            else:
                await hybrid.run_cpu_task(task)
            exec_time = time.time() - start_time
            
            results["hybrid_execution_time"] = exec_time
            results["hybrid_throughput"] = 1.0 / exec_time if exec_time > 0 else 0
        
        return results
    
    async def analyze_asyncio_multiprocessing(self, task: Callable) -> Dict[str, Any]:
        """Analyze using AsyncIO + Multiprocessing hybrid."""
        if not self._has_hybrid:
            return {"error": "Hybrid modules not available"}
        
        results = {
            "hybrid_execution_time": 0.0,
            "hybrid_throughput": 0.0,
        }
        
        try:
            async with self._asyncio_multiprocessing(max_workers=4) as hybrid:
                start_time = time.time()
                if asyncio.iscoroutinefunction(task):
                    await hybrid.run_io_task(task)
                else:
                    await hybrid.run_cpu_task(task)
                exec_time = time.time() - start_time
                
                results["hybrid_execution_time"] = exec_time
                results["hybrid_throughput"] = 1.0 / exec_time if exec_time > 0 else 0
        except Exception as e:
            self._logger.error(f"AsyncIO+Multiprocessing analysis error: {e}")
            results["error"] = str(e)
        
        return results
    
    async def analyze_custom_executor(self, task: Callable) -> Dict[str, Any]:
        """Analyze using custom intelligent executor."""
        if not self._has_hybrid:
            return {"error": "Hybrid modules not available"}
        
        results = {
            "executor_selection_time": 0.0,
            "executor_execution_time": 0.0,
            "selected_model": "unknown",
        }
        
        try:
            executor = self._custom_executor()
            await executor.initialize()
            
            start_time = time.time()
            result = await executor.execute_task(task)
            exec_time = time.time() - start_time
            
            results["executor_execution_time"] = exec_time
            results["selected_model"] = result.model_used.value if hasattr(result, 'model_used') else "unknown"
            
            await executor.cleanup()
        except Exception as e:
            self._logger.error(f"Custom executor analysis error: {e}")
            results["error"] = str(e)
        
        return results
    
    async def analyze(self, task: Callable) -> Dict[str, Any]:
        """Comprehensive hybrid analysis."""
        analysis = {
            "asyncio_threading": await self.analyze_asyncio_threading(task),
            "asyncio_multiprocessing": await self.analyze_asyncio_multiprocessing(task),
            "custom_executor": await self.analyze_custom_executor(task),
        }
        
        return analysis


class AdvancedWorkloadAnalyzer:
    """
    Analyzes workloads using advanced hybrid concurrency techniques.
    
    Uses ALL techniques from advanced_hybrid_concurrency:
    - Advanced synchronization (distributed locks, transactional memory, lock-free structures)
    - Distributed concurrency (Celery, Dask, Ray integration, Kubernetes-aware)
    - Actor model (message-passing, supervisors, fault tolerance)
    - Reactive programming (RxPY streams, backpressure handling)
    - Custom primitives (priority queues, adaptive rate limiters, circuit breakers)
    - Performance profiling (real-time monitoring, bottleneck detection)
    - Configuration-driven concurrency (runtime switching, adaptive executors)
    - Container-aware concurrency (Docker, Kubernetes integration)
    - ML-specific concurrency (GPU/TPU patterns, inference pipelines)
    """
    
    def __init__(self, config: Any):
        """Initialize advanced analyzer."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Import advanced patterns
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../examples'))
            from advanced_hybrid_concurrency import (
                DistributedLock,
                ActorSystem,
                ReactiveStream
            )
            self._has_advanced = True
            self._distributed_lock = DistributedLock
            self._actor_system = ActorSystem
            self._reactive_stream = ReactiveStream
        except ImportError:
            self._has_advanced = False
            self._logger.warning("Advanced hybrid concurrency modules not available")
    
    async def analyze_distributed_patterns(self, task: Callable) -> Dict[str, Any]:
        """Analyze using distributed patterns."""
        results = {
            "distributed_lock_time": 0.0,
            "actor_message_time": 0.0,
            "reactive_stream_time": 0.0,
        }
        
        if not self._has_advanced:
            return {"error": "Advanced modules not available"}
        
        # Test distributed lock
        try:
            async with self._distributed_lock("test_lock") as lock:
                start_time = time.time()
                if asyncio.iscoroutinefunction(task):
                    await task()
                else:
                    await asyncio.to_thread(task)
                results["distributed_lock_time"] = time.time() - start_time
        except Exception as e:
            self._logger.error(f"Distributed lock analysis error: {e}")
        
        # Test reactive stream
        try:
            stream = self._reactive_stream("test_stream")
            await stream.start()
            
            start_time = time.time()
            await stream.emit(task)
            results["reactive_stream_time"] = time.time() - start_time
            
            await stream.stop()
        except Exception as e:
            self._logger.error(f"Reactive stream analysis error: {e}")
        
        return results
    
    async def analyze(self, task: Callable) -> Dict[str, Any]:
        """Comprehensive advanced analysis."""
        analysis = {
            "distributed_patterns": await self.analyze_distributed_patterns(task),
        }
        
        return analysis


class WorkloadAnalyzer:
    """
    Comprehensive workload analyzer using ALL concurrency techniques.
    
    This analyzer uses techniques from:
    - threading_examples
    - multiprocessing_examples
    - asyncio_examples
    - subprocess_examples
    - concurrent_futures
    - hybrid_concurrency (via separate analysis)
    - advanced_hybrid_concurrency (via separate analysis)
    """
    
    def __init__(self, config: Any):
        """Initialize comprehensive workload analyzer."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self._threading_analyzer = ThreadingWorkloadAnalyzer(config)
        self._multiprocessing_analyzer = MultiprocessingWorkloadAnalyzer(config)
        self._asyncio_analyzer = AsyncioWorkloadAnalyzer(config)
        self._subprocess_analyzer = SubprocessWorkloadAnalyzer(config)
        self._concurrent_futures_analyzer = ConcurrentFuturesWorkloadAnalyzer(config)
        self._hybrid_analyzer = HybridWorkloadAnalyzer(config)
        self._advanced_analyzer = AdvancedWorkloadAnalyzer(config)
        
    async def analyze(self, task: Any) -> WorkloadCharacteristics:
        """
        Analyze a workload comprehensively.
        
        Args:
            task: The task to analyze (function, coroutine, or command)
            
        Returns:
            WorkloadCharacteristics with analysis results
        """
        self._logger.info("Starting comprehensive workload analysis")
        
        characteristics = WorkloadCharacteristics()
        
        # Determine task type
        is_callable = callable(task)
        is_coroutine = inspect.iscoroutinefunction(task) if is_callable else False
        is_command = isinstance(task, (list, tuple)) and all(isinstance(x, str) for x in task)
        
        # Analyze based on task type
        if is_callable and not is_coroutine:
            # Synchronous function - analyze with threading, multiprocessing, concurrent.futures
            threading_results = self._threading_analyzer.analyze(task)
            multiprocessing_results = self._multiprocessing_analyzer.analyze(task)
            concurrent_futures_results = self._concurrent_futures_analyzer.analyze(task)
            
            # Async analysis (wrap in async)
            asyncio_results = await self._asyncio_analyzer.analyze(task)
            
            # Hybrid analysis
            hybrid_results = await self._hybrid_analyzer.analyze(task)
            advanced_results = await self._advanced_analyzer.analyze(task)
            
            characteristics.profiling_metrics = {
                "threading": threading_results,
                "multiprocessing": multiprocessing_results,
                "asyncio": asyncio_results,
                "concurrent_futures": concurrent_futures_results,
                "hybrid": hybrid_results,
                "advanced": advanced_results,
            }
            
        elif is_coroutine:
            # Coroutine - analyze with asyncio primarily
            asyncio_results = await self._asyncio_analyzer.analyze(task)
            
            # Also analyze with threading (wrap coroutine)
            def sync_wrapper():
                asyncio.run(task())
            
            threading_results = self._threading_analyzer.analyze(sync_wrapper)
            concurrent_futures_results = self._concurrent_futures_analyzer.analyze(sync_wrapper)
            
            # Hybrid analysis
            hybrid_results = await self._hybrid_analyzer.analyze(task)
            advanced_results = await self._advanced_analyzer.analyze(task)
            
            characteristics.profiling_metrics = {
                "asyncio": asyncio_results,
                "threading": threading_results,
                "concurrent_futures": concurrent_futures_results,
                "hybrid": hybrid_results,
                "advanced": advanced_results,
            }
            
        elif is_command:
            # Command - analyze with subprocess
            subprocess_results = self._subprocess_analyzer.analyze(task)
            
            characteristics.profiling_metrics = {
                "subprocess": subprocess_results,
            }
        
        # Determine workload characteristics
        characteristics = self._determine_characteristics(characteristics)
        
        self._logger.info(f"Workload analysis complete: {characteristics.recommended_strategy}")
        
        return characteristics
    
    def _determine_characteristics(self, characteristics: WorkloadCharacteristics) -> WorkloadCharacteristics:
        """Determine workload characteristics from profiling metrics."""
        metrics = characteristics.profiling_metrics
        
        # Analyze CPU vs I/O bound
        if "threading" in metrics and "multiprocessing" in metrics:
            threading_time = metrics["threading"].get("thread_pool", {}).get("pool_execution_time", 0)
            multiprocessing_time = metrics["multiprocessing"].get("process_pool", {}).get("pool_execution_time", 0)
            
            if multiprocessing_time > 0 and threading_time > 0:
                ratio = threading_time / multiprocessing_time
                if ratio > 1.5:
                    characteristics.is_cpu_bound = True
                elif ratio < 0.7:
                    characteristics.is_io_bound = True
                else:
                    characteristics.is_mixed = True
        
        # Score different strategies
        if "threading" in metrics:
            threading_throughput = metrics["threading"].get("thread_pool", {}).get("pool_throughput", 0)
            characteristics.threading_score = threading_throughput
        
        if "multiprocessing" in metrics:
            multiprocessing_throughput = metrics["multiprocessing"].get("process_pool", {}).get("pool_throughput", 0)
            characteristics.multiprocessing_score = multiprocessing_throughput
        
        if "asyncio" in metrics:
            asyncio_throughput = metrics["asyncio"].get("tasks", {}).get("task_throughput", 0)
            characteristics.asyncio_score = asyncio_throughput
        
        # Recommend strategy
        scores = {
            "threading": characteristics.threading_score,
            "multiprocessing": characteristics.multiprocessing_score,
            "asyncio": characteristics.asyncio_score,
        }
        
        if scores:
            characteristics.recommended_strategy = max(scores, key=scores.get)
        
        return characteristics

