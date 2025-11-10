"""
Typed ThreadPoolExecutor wrapper with enhanced features.

This module provides a production-grade wrapper around ThreadPoolExecutor
with type safety, enhanced error handling, and comprehensive monitoring.
"""

import time
import uuid
import logging
from typing import Any, Callable, Optional, Union, List
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError, CancelledError

from .task_result import TaskResult, TaskBatchResult


class TypedThreadPoolExecutor:
    """Enhanced ThreadPoolExecutor with type safety and monitoring.

    This wrapper provides production-grade features around ThreadPoolExecutor:
    - Type-safe task submission and result handling
    - Comprehensive error handling and aggregation
    - Task cancellation and timeout management
    - Detailed performance monitoring and statistics
    - Structured logging with correlation IDs

    Attributes:
        _executor: The underlying ThreadPoolExecutor.
        _logger: Structured logger for monitoring.
        _active_tasks: Dictionary of active task futures.
        _shutdown: Whether the executor has been shut down.
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        thread_name_prefix: str = "TypedPool",
        name: str = "TypedThreadPoolExecutor"
    ) -> None:
        """Initialize the typed executor.

        Args:
            max_workers: Maximum number of worker threads.
            thread_name_prefix: Prefix for thread names.
            name: Executor name for logging.

        Raises:
            ValueError: If max_workers is invalid.
        """
        if max_workers is not None and max_workers <= 0:
            raise ValueError("max_workers must be positive")

        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix
        )
        self._logger = logging.getLogger(__name__)
        self._active_tasks: dict[str, Future[Any]] = {}
        self._shutdown = False
        self._name = name

        self._logger.info(
            f"TypedThreadPoolExecutor '{name}' initialized",
            extra={
                "executor_name": name,
                "max_workers": max_workers,
                "thread_name_prefix": thread_name_prefix
            }
        )

    def submit_task(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> str:
        """Submit a task for execution.

        Args:
            func: Function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Task ID for tracking the submitted task.

        Raises:
            RuntimeError: If executor is shut down.
        """
        if self._shutdown:
            raise RuntimeError("Cannot submit tasks to shut down executor")

        task_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Submit the task
            future = self._executor.submit(func, *args, **kwargs)
            self._active_tasks[task_id] = future

            self._logger.debug(
                f"Task {task_id} submitted to executor '{self._name}'",
                extra={
                    "task_id": task_id,
                    "executor_name": self._name,
                    "function_name": func.__name__,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs)
                }
            )

            return task_id

        except Exception as e:
            # Log submission errors
            self._logger.error(
                f"Failed to submit task {task_id}: {e}",
                extra={
                    "task_id": task_id,
                    "executor_name": self._name,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise

    def get_task_result(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> TaskResult:
        """Get the result of a completed task.

        Args:
            task_id: Task ID to retrieve result for.
            timeout: Maximum time to wait for completion.

        Returns:
            TaskResult with execution details.

        Raises:
            KeyError: If task_id is not found.
            RuntimeError: If executor is shut down.
        """
        if self._shutdown:
            raise RuntimeError("Cannot get results from shut down executor")

        if task_id not in self._active_tasks:
            raise KeyError(f"Task {task_id} not found")

        future = self._active_tasks[task_id]
        start_time = time.time()

        try:
            # Wait for completion
            result = future.result(timeout=timeout)
            end_time = time.time()

            # Create success result
            task_result = TaskResult.from_success(
                task_id=task_id,
                result=result,
                start_time=start_time,
                end_time=end_time
            )

            self._logger.debug(
                f"Task {task_id} completed successfully",
                extra={
                    "task_id": task_id,
                    "duration": task_result.duration,
                    "executor_name": self._name
                }
            )

        except CancelledError as e:
            end_time = time.time()
            task_result = TaskResult.from_error(
                task_id=task_id,
                error=e,
                start_time=start_time,
                end_time=end_time,
                cancelled=True
            )

            self._logger.warning(
                f"Task {task_id} was cancelled",
                extra={"task_id": task_id, "executor_name": self._name}
            )

        except TimeoutError as e:
            end_time = time.time()
            task_result = TaskResult.from_error(
                task_id=task_id,
                error=e,
                start_time=start_time,
                end_time=end_time,
                timeout=True
            )

            self._logger.warning(
                f"Task {task_id} timed out after {timeout}s",
                extra={
                    "task_id": task_id,
                    "timeout": timeout,
                    "executor_name": self._name
                }
            )

        except Exception as e:
            end_time = time.time()
            task_result = TaskResult.from_error(
                task_id=task_id,
                error=e,
                start_time=start_time,
                end_time=end_time
            )

            self._logger.error(
                f"Task {task_id} failed: {e}",
                extra={
                    "task_id": task_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "executor_name": self._name
                },
                exc_info=True
            )

        finally:
            # Clean up completed task
            del self._active_tasks[task_id]

        return task_result

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task.

        Args:
            task_id: Task ID to cancel.

        Returns:
            True if task was cancelled, False otherwise.

        Raises:
            KeyError: If task_id is not found.
        """
        if task_id not in self._active_tasks:
            raise KeyError(f"Task {task_id} not found")

        future = self._active_tasks[task_id]
        cancelled = future.cancel()

        if cancelled:
            self._logger.info(
                f"Task {task_id} cancelled successfully",
                extra={"task_id": task_id, "executor_name": self._name}
            )
            del self._active_tasks[task_id]
        else:
            self._logger.debug(
                f"Task {task_id} could not be cancelled",
                extra={"task_id": task_id, "executor_name": self._name}
            )

        return cancelled

    def submit_batch(
        self,
        tasks: List[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]]
    ) -> List[str]:
        """Submit a batch of tasks for execution.

        Args:
            tasks: List of (func, args, kwargs) tuples.

        Returns:
            List of task IDs for the submitted tasks.
        """
        task_ids = []

        for func, args, kwargs in tasks:
            try:
                task_id = self.submit_task(func, *args, **kwargs)
                task_ids.append(task_id)
            except Exception as e:
                self._logger.error(
                    f"Failed to submit task in batch: {e}",
                    extra={
                        "function_name": func.__name__,
                        "error_type": type(e).__name__,
                        "executor_name": self._name
                    },
                    exc_info=True
                )
                # Continue with other tasks in batch

        return task_ids

    def get_batch_results(
        self,
        task_ids: List[str],
        timeout: Optional[float] = None
    ) -> TaskBatchResult:
        """Get results for a batch of tasks.

        Args:
            task_ids: List of task IDs to get results for.
            timeout: Maximum time to wait for all results.

        Returns:
            TaskBatchResult with aggregated results.
        """
        task_results = []

        for task_id in task_ids:
            try:
                result = self.get_task_result(task_id, timeout=timeout)
                task_results.append(result)
            except Exception as e:
                # Create error result for failed retrieval
                task_results.append(TaskResult.from_error(
                    task_id=task_id,
                    error=e,
                    start_time=time.time(),
                    end_time=time.time()
                ))

        return TaskBatchResult(task_results)

    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """Shutdown the executor.

        Args:
            wait: Whether to wait for running tasks to complete.
            timeout: Maximum time to wait for shutdown (not supported by ThreadPoolExecutor).
        """
        if self._shutdown:
            return

        if timeout is not None:
            self._logger.warning(
                f"Timeout parameter ({timeout}s) ignored for ThreadPoolExecutor shutdown",
                extra={"executor_name": self._name, "timeout": timeout}
            )

        self._shutdown = True
        active_count = len(self._active_tasks)

        self._logger.info(
            f"Shutting down TypedThreadPoolExecutor '{self._name}'",
            extra={
                "executor_name": self._name,
                "active_tasks": active_count,
                "wait": wait,
                "timeout": timeout
            }
        )

        # Cancel all active tasks
        for task_id in list(self._active_tasks.keys()):
            try:
                self.cancel_task(task_id)
            except Exception:
                pass  # Ignore errors during shutdown

        # Shutdown the underlying executor
        self._executor.shutdown(wait=wait)

        self._logger.info(
            f"TypedThreadPoolExecutor '{self._name}' shutdown complete",
            extra={"executor_name": self._name}
        )

    def get_stats(self) -> dict[str, Any]:
        """Get executor statistics.

        Returns:
            Dictionary with current executor statistics.
        """
        return {
            "executor_name": self._name,
            "active_tasks": len(self._active_tasks),
            "shutdown": self._shutdown,
            "max_workers": self._executor._max_workers,
            "threads_alive": self._executor._threads and len(self._executor._threads) or 0,
            "task_ids": list(self._active_tasks.keys())
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.shutdown(wait=True)

