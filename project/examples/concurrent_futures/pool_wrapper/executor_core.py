"""
Core TypedThreadPoolExecutor implementation.

This module provides the core executor class with initialization,
basic configuration, and fundamental operations.
"""

import logging
from typing import Optional

from concurrent.futures import ThreadPoolExecutor


class TypedThreadPoolExecutor:
    """Enhanced ThreadPoolExecutor with type safety and monitoring.

    This wrapper provides production-grade features around ThreadPoolExecutor:
    - Type-safe task submission and result handling
    - Comprehensive error handling and aggregation
    - Task cancellation and timeout management
    - Detailed performance monitoring and statistics
    - Structured logging with correlation IDs

    The class is split across multiple modules for maintainability:
    - executor_core.py: Initialization and basic operations
    - executor_tasks.py: Task submission and management
    - executor_results.py: Result handling and retrieval
    - executor_lifecycle.py: Shutdown and lifecycle management
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
        self._name = name
        self._logger = logging.getLogger(__name__)

        self._logger.info(
            f"TypedThreadPoolExecutor '{name}' initialized",
            extra={
                "executor_name": name,
                "max_workers": max_workers,
                "thread_name_prefix": thread_name_prefix
            }
        )

    @property
    def name(self) -> str:
        """Get executor name."""
        return self._name

    @property
    def executor(self) -> ThreadPoolExecutor:
        """Get underlying ThreadPoolExecutor (for internal use)."""
        return self._executor

    @property
    def logger(self) -> logging.Logger:
        """Get logger instance."""
        return self._logger

    def get_basic_stats(self) -> dict[str, any]:
        """Get basic executor statistics.

        Returns:
            Dictionary with basic executor information.
        """
        return {
            "executor_name": self._name,
            "max_workers": self._executor._max_workers,
            "threads_alive": self._executor._threads and len(self._executor._threads) or 0,
        }

    # Placeholder methods - implemented in other modules
    def submit_task(self, func, *args, **kwargs):
        """Submit a task (implemented in executor_tasks.py)."""
        raise NotImplementedError("Implemented in executor_tasks.py")

    def get_task_result(self, task_id, timeout=None):
        """Get task result (implemented in executor_results.py)."""
        raise NotImplementedError("Implemented in executor_results.py")

    def cancel_task(self, task_id):
        """Cancel task (implemented in executor_tasks.py)."""
        raise NotImplementedError("Implemented in executor_tasks.py")

    def submit_batch(self, tasks):
        """Submit batch (implemented in executor_tasks.py)."""
        raise NotImplementedError("Implemented in executor_tasks.py")

    def get_batch_results(self, task_ids, timeout=None):
        """Get batch results (implemented in executor_results.py)."""
        raise NotImplementedError("Implemented in executor_results.py")

    def shutdown(self, wait=True, timeout=None):
        """Shutdown executor (implemented in executor_lifecycle.py)."""
        raise NotImplementedError("Implemented in executor_lifecycle.py")

    def get_stats(self):
        """Get statistics (implemented in executor_lifecycle.py)."""
        raise NotImplementedError("Implemented in executor_lifecycle.py")

    # Context manager support
    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.shutdown(wait=True, timeout=30.0)

