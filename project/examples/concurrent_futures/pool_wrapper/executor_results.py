"""
Result handling for TypedThreadPoolExecutor.

This module handles task result retrieval, timeout management,
and batch result aggregation.
"""

import time
import logging
from typing import List, Optional
from concurrent.futures import TimeoutError, CancelledError

from .executor_core import TypedThreadPoolExecutor
from .task_result import TaskResult, TaskBatchResult


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

# Add method to class
TypedThreadPoolExecutor.get_task_result = get_task_result


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

# Add method to class
TypedThreadPoolExecutor.get_batch_results = get_batch_results

