"""
Lifecycle management for TypedThreadPoolExecutor.

This module handles executor shutdown, statistics reporting,
and lifecycle monitoring.
"""

import logging
from typing import Any, Optional

from .executor_core import TypedThreadPoolExecutor


def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
    """Shutdown the executor.

    Args:
        wait: Whether to wait for running tasks to complete.
        timeout: Maximum time to wait for shutdown.
    """
    if self._shutdown:
        return

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
    self._executor.shutdown(wait=wait, timeout=timeout)

    self._logger.info(
        f"TypedThreadPoolExecutor '{self._name}' shutdown complete",
        extra={"executor_name": self._name}
    )

# Add method to class
TypedThreadPoolExecutor.shutdown = shutdown


def get_stats(self) -> dict[str, Any]:
    """Get executor statistics.

    Returns:
        Dictionary with current executor statistics.
    """
    basic_stats = self.get_basic_stats()

    return {
        **basic_stats,
        "active_tasks": len(self._active_tasks),
        "shutdown": self._shutdown,
        "task_ids": list(self._active_tasks.keys())
    }

# Add method to class
TypedThreadPoolExecutor.get_stats = get_stats


# Import all modules to ensure methods are added to the class
from . import executor_tasks
from . import executor_results

# Ensure all methods are properly attached
assert hasattr(TypedThreadPoolExecutor, 'submit_task')
assert hasattr(TypedThreadPoolExecutor, 'get_task_result')
assert hasattr(TypedThreadPoolExecutor, 'cancel_task')
assert hasattr(TypedThreadPoolExecutor, 'submit_batch')
assert hasattr(TypedThreadPoolExecutor, 'get_batch_results')
assert hasattr(TypedThreadPoolExecutor, 'shutdown')
assert hasattr(TypedThreadPoolExecutor, 'get_stats')

