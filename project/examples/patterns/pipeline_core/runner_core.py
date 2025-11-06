"""
Core PipelineRunner implementation.

This module provides the main PipelineRunner class for
orchestrating pipeline execution.
"""

import time
import logging
from typing import List, Optional, Dict, Any

from .message import Message, PIPELINE_START, PIPELINE_SHUTDOWN
from .queue import MessageQueue, create_message_queue
from .stage_base import PipelineStage


class PipelineRunner:
    """Runner for executing pipeline stages.

    Orchestrates the execution of pipeline stages by managing
    message queues between stages and coordinating stage execution.

    Attributes:
        _stages: List of pipeline stages in execution order.
        _queues: Queues between stages for message passing.
        _executor: Thread pool for running stages.
        _running: Whether pipeline is currently running.
        _logger: Logger for pipeline execution.
    """

    def __init__(
        self,
        stages: List[PipelineStage],
        queue_factory: Optional[callable] = None,
        max_workers: Optional[int] = None
    ):
        """Initialize the pipeline runner.

        Args:
            stages: List of stages in execution order.
            queue_factory: Factory for creating queues between stages.
            max_workers: Maximum worker threads for stage execution.
        """
        if not stages:
            raise ValueError("Pipeline must have at least one stage")

        self._stages = stages
        self._queue_factory = queue_factory or create_message_queue
        self._max_workers = max_workers
        self._running = False
        self._logger = logging.getLogger(__name__)

        # Create queues between stages
        self._queues: List[MessageQueue] = []
        for i in range(len(stages) - 1):
            queue = self._queue_factory(
                name=f"Stage{i}-{i+1}",
                maxsize=0  # Unbounded for now
            )
            self._queues.append(queue)

        # Import execution methods
        from .runner_execution import (
            run_stage,
            submit_input_messages,
            send_control_message
        )

        # Monkey patch execution methods
        self._run_stage = run_stage.__get__(self, PipelineRunner)
        self._submit_input_messages = submit_input_messages.__get__(self, PipelineRunner)
        self._send_control_message = send_control_message.__get__(self, PipelineRunner)

        self._logger.info(
            f"Pipeline runner initialized with {len(stages)} stages",
            extra={"stage_count": len(stages), "queue_count": len(self._queues)}
        )

    def run_pipeline(self, input_messages: List[Message], timeout: Optional[float] = None) -> Dict[str, Any]:
        """Run the pipeline with input messages.

        Args:
            input_messages: Messages to feed into the pipeline.
            timeout: Maximum execution time.

        Returns:
            Execution results and statistics.
        """
        start_time = time.time()

        try:
            self._running = True

            # Initialize all stages
            for stage in self._stages:
                stage.initialize()

            # Send start signal
            self._send_control_message(PIPELINE_START)

            # Submit input messages
            self._submit_input_messages(input_messages)

            # Start stage execution
            futures = []
            for i, stage in enumerate(self._stages):
                # Import here to avoid circular imports
                from concurrent.futures import ThreadPoolExecutor
                executor = ThreadPoolExecutor(max_workers=self._max_workers, thread_name_prefix="Pipeline")
                future = executor.submit(self._run_stage, i)
                futures.append((future, executor))

            # Wait for completion
            for future, executor in futures:
                future.result(timeout=timeout)
                executor.shutdown(wait=True)

            # Send shutdown signal
            self._send_control_message(PIPELINE_SHUTDOWN)

            execution_time = time.time() - start_time

            results = {
                "success": True,
                "execution_time": execution_time,
                "stages_processed": len(self._stages),
                "messages_processed": len(input_messages),
                "errors": []
            }

            self._logger.info(
                f"Pipeline execution completed in {execution_time:.2f}s",
                extra={
                    "execution_time": execution_time,
                    "stages_processed": len(self._stages),
                    "messages_processed": len(input_messages)
                }
            )

            return results

        except Exception as e:
            execution_time = time.time() - start_time
            error_result = {
                "success": False,
                "execution_time": execution_time,
                "error": str(e),
                "error_type": type(e).__name__,
                "stages_processed": 0,
                "messages_processed": 0,
                "errors": [str(e)]
            }

            self._logger.error(
                f"Pipeline execution failed after {execution_time:.2f}s: {e}",
                extra={
                    "execution_time": execution_time,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )

            return error_result

        finally:
            self._running = False
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up pipeline resources."""
        # Clean up stages
        for stage in self._stages:
            try:
                stage.cleanup()
            except Exception as e:
                self._logger.error(
                    f"Error cleaning up stage '{stage.name}': {e}",
                    extra={"stage_name": stage.name, "error": str(e)}
                )

        # Clean up queues
        for queue in self._queues:
            try:
                queue.close()
            except Exception as e:
                self._logger.error(
                    f"Error closing queue: {e}",
                    extra={"error": str(e)}
                )

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics.

        Returns:
            Current pipeline statistics.
        """
        return {
            "running": self._running,
            "stage_count": len(self._stages),
            "queue_count": len(self._queues),
            "stages": [stage.name for stage in self._stages],
        }


def run_pipeline(
    stages: List[PipelineStage],
    input_messages: List[Message],
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """Convenience function to run a pipeline.

    Args:
        stages: Pipeline stages to execute.
        input_messages: Input messages for the pipeline.
        timeout: Execution timeout.

    Returns:
        Pipeline execution results.
    """
    runner = PipelineRunner(stages)
    return runner.run_pipeline(input_messages, timeout)

