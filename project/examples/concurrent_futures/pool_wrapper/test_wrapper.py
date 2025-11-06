"""
Unit tests for TypedThreadPoolExecutor wrapper.

This module provides comprehensive testing for the enhanced
executor wrapper including success/failure cases, edge conditions,
and concurrent operation validation.
"""

import time
import pytest
from concurrent.futures import TimeoutError

from .typed_executor import TypedThreadPoolExecutor
from .task_result import TaskResult, TaskBatchResult


class TestTypedThreadPoolExecutor:
    """Unit tests for TypedThreadPoolExecutor."""

    def test_initialization(self):
        """Test executor initialization."""
        executor = TypedThreadPoolExecutor(max_workers=4)
        assert executor.get_stats()["max_workers"] == 4

        # Test default initialization
        executor = TypedThreadPoolExecutor()
        stats = executor.get_stats()
        assert stats["shutdown"] is False

        executor.shutdown()

    def test_task_submission_success(self):
        """Test successful task submission and completion."""
        def simple_task(x: int) -> int:
            return x * 2

        with TypedThreadPoolExecutor(max_workers=2) as executor:
            task_id = executor.submit_task(simple_task, 5)

            result = executor.get_task_result(task_id)

            assert result.success is True
            assert result.result == 10
            assert result.task_id == task_id
            assert result.duration > 0
            assert result.error is None

    def test_task_submission_failure(self):
        """Test task submission that raises an exception."""
        def failing_task() -> None:
            raise ValueError("Task failed")

        with TypedThreadPoolExecutor(max_workers=2) as executor:
            task_id = executor.submit_task(failing_task)

            result = executor.get_task_result(task_id)

            assert result.success is False
            assert result.result is None
            assert result.task_id == task_id
            assert isinstance(result.error, ValueError)
            assert "Task failed" in str(result.error)

    def test_task_cancellation(self):
        """Test task cancellation."""
        def slow_task() -> str:
            time.sleep(2.0)
            return "completed"

        with TypedThreadPoolExecutor(max_workers=2) as executor:
            task_id = executor.submit_task(slow_task)

            # Cancel immediately
            cancelled = executor.cancel_task(task_id)
            assert cancelled is True

            # Get result for cancelled task
            result = executor.get_task_result(task_id, timeout=1.0)

            assert result.cancelled is True
            assert result.success is False

    def test_task_timeout(self):
        """Test task timeout handling."""
        def slow_task() -> str:
            time.sleep(2.0)
            return "completed"

        with TypedThreadPoolExecutor(max_workers=2) as executor:
            task_id = executor.submit_task(slow_task)

            # Try to get result with short timeout
            result = executor.get_task_result(task_id, timeout=0.1)

            assert result.timeout is True
            assert result.success is False

    def test_batch_submission(self):
        """Test batch task submission."""
        def multiply_task(x: int, multiplier: int = 2) -> int:
            return x * multiplier

        tasks = [
            (multiply_task, (5,), {}),
            (multiply_task, (3, 4), {}),
            (multiply_task, (10,), {"multiplier": 3}),
        ]

        with TypedThreadPoolExecutor(max_workers=2) as executor:
            task_ids = executor.submit_batch(tasks)
            assert len(task_ids) == 3

            batch_result = executor.get_batch_results(task_ids)

            assert batch_result.total_tasks == 3
            assert batch_result.successful_tasks == 3
            assert batch_result.success_rate == 100.0

            # Check individual results
            results = batch_result.task_results
            assert results[0].result == 10  # 5 * 2
            assert results[1].result == 12  # 3 * 4
            assert results[2].result == 30  # 10 * 3

    def test_batch_with_failures(self):
        """Test batch processing with some failures."""
        def task_that_fails(x: int) -> int:
            if x == 5:
                raise ValueError("Failing on 5")
            return x * 2

        tasks = [
            (task_that_fails, (2,), {}),
            (task_that_fails, (5,), {}),  # This will fail
            (task_that_fails, (3,), {}),
        ]

        with TypedThreadPoolExecutor(max_workers=2) as executor:
            task_ids = executor.submit_batch(tasks)
            batch_result = executor.get_batch_results(task_ids)

            assert batch_result.total_tasks == 3
            assert batch_result.successful_tasks == 2
            assert batch_result.failed_tasks == 1
            assert batch_result.success_rate == pytest.approx(66.67, abs=0.01)

    def test_shutdown_behavior(self):
        """Test executor shutdown behavior."""
        executor = TypedThreadPoolExecutor(max_workers=2)

        # Should be able to submit tasks
        task_id = executor.submit_task(lambda: 42)
        assert task_id is not None

        # Shutdown
        executor.shutdown()

        # Should not be able to submit after shutdown
        with pytest.raises(RuntimeError):
            executor.submit_task(lambda: 24)

        # Should still be able to get results
        result = executor.get_task_result(task_id)
        assert result.success is True
        assert result.result == 42

    def test_context_manager(self):
        """Test context manager behavior."""
        with TypedThreadPoolExecutor(max_workers=2) as executor:
            task_id = executor.submit_task(lambda: "test")

            # Executor should be active
            assert executor.get_stats()["shutdown"] is False

        # After context exit, executor should be shut down
        assert executor.get_stats()["shutdown"] is True

    def test_invalid_task_id(self):
        """Test handling of invalid task IDs."""
        with TypedThreadPoolExecutor(max_workers=2) as executor:
            with pytest.raises(KeyError):
                executor.get_task_result("nonexistent-task-id")

            with pytest.raises(KeyError):
                executor.cancel_task("nonexistent-task-id")

    def test_statistics_reporting(self):
        """Test statistics reporting."""
        with TypedThreadPoolExecutor(max_workers=3, name="TestExecutor") as executor:
            stats = executor.get_stats()

            assert stats["executor_name"] == "TestExecutor"
            assert stats["max_workers"] == 3
            assert stats["active_tasks"] == 0
            assert stats["shutdown"] is False
            assert isinstance(stats["task_ids"], list)

    def test_error_during_submission(self):
        """Test error handling during task submission."""
        def invalid_func():
            pass

        # This should not raise an exception during submission
        # (errors are handled during execution)
        with TypedThreadPoolExecutor(max_workers=2) as executor:
            task_id = executor.submit_task(invalid_func)
            assert task_id is not None

            result = executor.get_task_result(task_id)
            assert result.success is True  # Function executed successfully


class TestTaskResult:
    """Tests for TaskResult class."""

    def test_success_result(self):
        """Test successful task result creation."""
        result = TaskResult.from_success("task-1", 42, 1.0, 2.0)

        assert result.task_id == "task-1"
        assert result.success is True
        assert result.result == 42
        assert result.error is None
        assert result.duration == 1.0
        assert result.cancelled is False
        assert result.timeout is False

    def test_error_result(self):
        """Test error task result creation."""
        error = ValueError("Test error")
        result = TaskResult.from_error("task-1", error, 1.0, 2.0)

        assert result.task_id == "task-1"
        assert result.success is False
        assert result.result is None
        assert result.error == error
        assert result.duration == 1.0
        assert result.cancelled is False
        assert result.timeout is False

    def test_cancelled_result(self):
        """Test cancelled task result."""
        error = Exception("Cancelled")
        result = TaskResult.from_error("task-1", error, 1.0, 2.0, cancelled=True)

        assert result.cancelled is True
        assert result.success is False

    def test_timeout_result(self):
        """Test timeout task result."""
        error = TimeoutError("Timeout")
        result = TaskResult.from_error("task-1", error, 1.0, 2.0, timeout=True)

        assert result.timeout is True
        assert result.success is False

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        result = TaskResult.from_success("task-1", 42, 1.0, 2.0)
        data = result.to_dict()

        assert data["task_id"] == "task-1"
        assert data["success"] is True
        assert data["result"] == 42
        assert data["cancelled"] is False
        assert data["timeout"] is False


class TestTaskBatchResult:
    """Tests for TaskBatchResult class."""

    def test_batch_result_creation(self):
        """Test batch result creation and statistics."""
        results = [
            TaskResult.from_success("task-1", 10, 1.0, 1.5),
            TaskResult.from_success("task-2", 20, 1.0, 2.0),
            TaskResult.from_error("task-3", ValueError("fail"), 1.0, 1.2),
        ]

        batch = TaskBatchResult(results)

        assert batch.total_tasks == 3
        assert batch.successful_tasks == 2
        assert batch.failed_tasks == 1
        assert batch.success_rate == pytest.approx(66.67, abs=0.01)
        assert batch.total_duration > 0

    def test_empty_batch(self):
        """Test batch result with no tasks."""
        batch = TaskBatchResult([])

        assert batch.total_tasks == 0
        assert batch.successful_tasks == 0
        assert batch.success_rate == 0.0

    def test_error_details(self):
        """Test error details extraction."""
        results = [
            TaskResult.from_success("task-1", 10, 1.0, 1.5),
            TaskResult.from_error("task-2", ValueError("fail"), 1.0, 1.2),
            TaskResult.from_error("task-3", RuntimeError("crash"), 1.0, 1.3, cancelled=True),
        ]

        batch = TaskBatchResult(results)
        errors = batch.error_details

        assert len(errors) == 2
        assert errors[0]["task_id"] == "task-2"
        assert errors[1]["task_id"] == "task-3"
        assert errors[1]["cancelled"] is True


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v"])

