"""
Pipeline execution logic for PipelineRunner.

This module contains the core execution methods for running
pipeline stages and managing message flow.
"""

import time
import threading
import logging
from typing import List, Optional

from .message import Message
from .runner import PipelineRunner


def run_stage(self: PipelineRunner, stage_index: int) -> None:
    """Run a single stage in the pipeline.

    Args:
        stage_index: Index of stage to run.
    """
    stage = self._stages[stage_index]
    input_queue = self._queues[stage_index - 1] if stage_index > 0 else None
    output_queue = self._queues[stage_index] if stage_index < len(self._queues) else None

    self._logger.debug(
        f"Starting stage '{stage.name}' (index {stage_index})",
        extra={"stage_name": stage.name, "stage_index": stage_index}
    )

    try:
        while self._running:
            # Get input message
            if input_queue:
                message = input_queue.get(timeout=1.0)
                if message is None:
                    break
            else:
                # First stage - no input queue, stage handles its own input
                break

            # Process message
            output_message = stage.process_message(message)

            # Send to output queue if there's a next stage
            if output_message and output_queue:
                output_queue.put(output_message, timeout=1.0)

    except Exception as e:
        self._logger.error(
            f"Stage '{stage.name}' failed: {e}",
            extra={
                "stage_name": stage.name,
                "stage_index": stage_index,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise

    self._logger.debug(
        f"Stage '{stage.name}' completed",
        extra={"stage_name": stage.name, "stage_index": stage_index}
    )


def submit_input_messages(self: PipelineRunner, messages: List[Message]) -> None:
    """Submit input messages to the first stage.

    Args:
        messages: Messages to submit.
    """
    if not self._queues:
        # Single stage pipeline
        return

    first_queue = self._queues[0]
    for message in messages:
        first_queue.put(message)


def send_control_message(self: PipelineRunner, message: Message) -> None:
    """Send control message to all stages.

    Args:
        message: Control message to send.
    """
    for queue in self._queues:
        try:
            queue.put(message, timeout=0.1)
        except Exception:
            # Ignore errors in control message sending
            pass


# Monkey patch methods onto PipelineRunner
PipelineRunner._run_stage = run_stage
PipelineRunner._submit_input_messages = submit_input_messages
PipelineRunner._send_control_message = send_control_message

