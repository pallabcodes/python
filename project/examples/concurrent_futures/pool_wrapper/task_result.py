"""
Task result representation with enhanced metadata.

This module provides comprehensive task result handling with
success/failure states, timing information, and error details.
"""

import time
from typing import Any, Optional, Union
from dataclasses import dataclass
from concurrent.futures import Future

"""

WHAT IT DEFINES:
- TaskResult: Individual task execution result with metadata
- TaskBatchResult: Aggregated results from multiple tasks
- Factory methods for creating results
- Serialization methods for logging/monitoring

KEY FEATURES:
- @dataclass: Automatic constructor, repr, equality methods
- Rich metadata: task_id, success/failure, timing, error details
- Factory pattern: TaskResult.from_success() vs from_error()
- Serialization: to_dict() for JSON logging
- Aggregation: Batch results with statistics and error details

WHY RICH DATA STRUCTURES:
Standard ThreadPoolExecutor only returns raw results or raises exceptions
This project provides observability into:
- Which tasks succeeded/failed
- How long tasks took
- What errors occurred and where
- Correlation IDs for tracing
- Batch-level success rates and timing

PRODUCTION BENEFITS:
- Monitoring: Track task success rates, latency, error patterns
- Debugging: Rich context for troubleshooting failures
- Alerting: Detect performance degradation or error spikes
- Analytics: Understand system behavior and bottlenecks

"""


@dataclass
class TaskResult:
    """Enhanced task result with comprehensive metadata.

    Provides detailed information about task execution including
    timing, success/failure state, and error information.

    Attributes:
        task_id: Unique identifier for the task.
        success: Whether the task completed successfully.
        result: The result value if successful.
        error: The exception if failed.
        start_time: When the task started execution.
        end_time: When the task completed.
        duration: Total execution time in seconds.
        cancelled: Whether the task was cancelled.
        timeout: Whether the task timed out.
    """

    task_id: str
    success: bool
    result: Any
    error: Optional[Exception]
    start_time: float
    end_time: float
    cancelled: bool = False
    timeout: bool = False

    @property
    def duration(self) -> float:
        """Get task execution duration."""
        return self.end_time - self.start_time

    @classmethod
    def from_success(
        cls,
        task_id: str,
        result: Any,
        start_time: float,
        end_time: float
    ) -> "TaskResult":
        """Create a successful task result.

        Args:
            task_id: Unique task identifier.
            result: The successful result value.
            start_time: Task start timestamp.
            end_time: Task completion timestamp.

        Returns:
            TaskResult instance for successful execution.
        """
        return cls(
            task_id=task_id,
            success=True,
            result=result,
            error=None,
            start_time=start_time,
            end_time=end_time,
            cancelled=False,
            timeout=False
        )

    @classmethod
    def from_error(
        cls,
        task_id: str,
        error: Exception,
        start_time: float,
        end_time: float,
        cancelled: bool = False,
        timeout: bool = False
    ) -> "TaskResult":
        """Create an error task result.

        Args:
            task_id: Unique task identifier.
            error: The exception that occurred.
            start_time: Task start timestamp.
            end_time: Task completion timestamp.
            cancelled: Whether the task was cancelled.
            timeout: Whether the task timed out.

        Returns:
            TaskResult instance for failed execution.
        """
        return cls(
            task_id=task_id,
            success=False,
            result=None,
            error=error,
            start_time=start_time,
            end_time=end_time,
            cancelled=cancelled,
            timeout=timeout
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for serialization.

        Returns:
            Dictionary representation suitable for logging/JSON.
        """
        return {
            "task_id": self.task_id,
            "success": self.success,
            "result": self.result,
            "error_type": type(self.error).__name__ if self.error else None,
            "error_message": str(self.error) if self.error else None,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "cancelled": self.cancelled,
            "timeout": self.timeout
        }


class TaskBatchResult:
    """Results from a batch of tasks.

    Aggregates results from multiple tasks with summary statistics
    and error analysis.

    Attributes:
        task_results: List of individual task results.
        total_tasks: Total number of tasks submitted.
        successful_tasks: Number of successfully completed tasks.
        failed_tasks: Number of failed tasks.
        cancelled_tasks: Number of cancelled tasks.
        timed_out_tasks: Number of timed out tasks.
        total_duration: Total time for all tasks.
        start_time: When the batch started.
        end_time: When the batch completed.
    """

    def __init__(self, task_results: list[TaskResult]):
        """Initialize batch result.

        Args:
            task_results: List of task results to aggregate.
        """
        self.task_results = task_results
        self.total_tasks = len(task_results)
        self.successful_tasks = sum(1 for r in task_results if r.success)
        self.failed_tasks = sum(1 for r in task_results if not r.success and not r.cancelled)
        self.cancelled_tasks = sum(1 for r in task_results if r.cancelled)
        self.timed_out_tasks = sum(1 for r in task_results if r.timeout)

        # Calculate timing
        if task_results:
            self.start_time = min(r.start_time for r in task_results)
            self.end_time = max(r.end_time for r in task_results)
            self.total_duration = self.end_time - self.start_time
        else:
            self.start_time = self.end_time = self.total_duration = 0.0

    @property
    def success_rate(self) -> float:
        """Get success rate as a percentage."""
        return (self.successful_tasks / self.total_tasks) * 100 if self.total_tasks > 0 else 0.0

    @property
    def error_details(self) -> list[dict[str, Any]]:
        """Get details of all errors in the batch.

        Returns:
            List of error details for failed tasks.
        """
        return [
            {
                "task_id": result.task_id,
                "error_type": type(result.error).__name__ if result.error else None,
                "error_message": str(result.error) if result.error else None,
                "cancelled": result.cancelled,
                "timeout": result.timeout
            }
            for result in self.task_results
            if not result.success
        ]

    def to_summary_dict(self) -> dict[str, Any]:
        """Get summary statistics for the batch.

        Returns:
            Dictionary with batch summary statistics.
        """
        return {
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "cancelled_tasks": self.cancelled_tasks,
            "timed_out_tasks": self.timed_out_tasks,
            "success_rate": self.success_rate,
            "total_duration": self.total_duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error_count": len(self.error_details)
        }

