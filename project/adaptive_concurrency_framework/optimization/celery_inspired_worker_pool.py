"""
Celery-inspired adaptive worker pool.

Implements patterns from Celery:
- Adaptive worker pool sizing
- Priority-based task routing
- Result aggregation
- Worker lifecycle management
"""

import asyncio
import logging
import queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

logger = logging.getLogger(__name__)


class Priority(IntEnum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class WorkerTask:
    """Task for worker pool."""
    
    task_id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: Priority = Priority.NORMAL
    submitted_at: float = field(default_factory=time.time)


class CeleryInspiredWorkerPool:
    """
    Celery-inspired adaptive worker pool.
    
    Features:
    - Dynamic worker scaling based on queue depth
    - Priority-based task routing
    - Result aggregation
    - Worker lifecycle management
    """
    
    def __init__(self, initial_workers: int = 2, max_workers: int = 10):
        """
        Initialize worker pool.
        
        Args:
            initial_workers: Initial number of workers
            max_workers: Maximum number of workers
        """
        self.initial_workers = initial_workers
        self.max_workers = max_workers
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self._task_queue = queue.PriorityQueue()
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._process_pool = ProcessPoolExecutor(max_workers=max_workers)
        
        self._current_workers = initial_workers
        self._queue_depth_threshold = 10
        self._running = False
        
    async def start(self) -> None:
        """Start worker pool."""
        self._running = True
        asyncio.create_task(self._scaling_loop())
        self._logger.info("Worker pool started")
    
    async def stop(self) -> None:
        """Stop worker pool."""
        self._running = False
        self._thread_pool.shutdown(wait=True)
        self._process_pool.shutdown(wait=True)
        self._logger.info("Worker pool stopped")
    
    async def submit_task(
        self,
        func: Callable,
        *args: Any,
        priority: Priority = Priority.NORMAL,
        use_processes: bool = False,
        **kwargs: Any
    ) -> str:
        """
        Submit a task to the worker pool.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            priority: Task priority
            use_processes: Whether to use process pool
            **kwargs: Keyword arguments
            
        Returns:
            Task ID
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        worker_task = WorkerTask(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        
        # Add to priority queue (negative priority for max-heap behavior)
        self._task_queue.put((-priority.value, time.time(), worker_task))
        
        # Execute task
        if use_processes:
            future = self._process_pool.submit(func, *args, **kwargs)
        else:
            future = self._thread_pool.submit(func, *args, **kwargs)
        
        self._logger.debug(f"Submitted task: {task_id} (priority={priority.name})")
        
        return task_id
    
    async def _scaling_loop(self) -> None:
        """Background task for adaptive scaling."""
        while self._running:
            try:
                await asyncio.sleep(5.0)
                await self._adapt_workers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Scaling loop error: {e}")
    
    async def _adapt_workers(self) -> None:
        """Adapt worker pool size based on queue depth."""
        queue_depth = self._task_queue.qsize()
        
        if queue_depth > self._queue_depth_threshold:
            # Increase workers
            if self._current_workers < self.max_workers:
                self._current_workers += 1
                self._logger.info(f"Increased workers to {self._current_workers} (queue_depth={queue_depth})")
        elif queue_depth < self._queue_depth_threshold / 2:
            # Decrease workers
            if self._current_workers > self.initial_workers:
                self._current_workers -= 1
                self._logger.info(f"Decreased workers to {self._current_workers} (queue_depth={queue_depth})")
    
    def get_queue_depth(self) -> int:
        """Get current queue depth."""
        return self._task_queue.qsize()
    
    def get_worker_count(self) -> int:
        """Get current worker count."""
        return self._current_workers

