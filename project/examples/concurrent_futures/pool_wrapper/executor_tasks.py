"""
Task management for TypedThreadPoolExecutor.

This module handles task submission, cancellation, and batch operations.
"""

import uuid
import logging
from typing import Any, Callable, List, Dict, Optional

from .executor_core import TypedThreadPoolExecutor


# Add task management to TypedThreadPoolExecutor
def _init_task_management(self):
    """Initialize task management attributes."""
    self._active_tasks: Dict[str, Any] = {}
    self._shutdown = False

# Add to class
TypedThreadPoolExecutor._init_task_management = _init_task_management


def submit_task(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
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

# Add method to class
TypedThreadPoolExecutor.submit_task = submit_task


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

# Add method to class
TypedThreadPoolExecutor.cancel_task = cancel_task


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

# Add method to class
TypedThreadPoolExecutor.submit_batch = submit_batch


# Initialize task management when executor is created
original_init = TypedThreadPoolExecutor.__init__

def new_init(self, *args, **kwargs):
    """Modified init that also initializes task management."""
    original_init(self, *args, **kwargs)
    self._init_task_management()

TypedThreadPoolExecutor.__init__ = new_init

