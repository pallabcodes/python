"""
Concrete pipeline stage implementations.

This module provides ready-to-use stage implementations for
common pipeline processing patterns.
"""

from typing import Any, Optional

from .message import Message, create_data_message
from .stage_base import BasePipelineStage


class TransformStage(BasePipelineStage):
    """Stage that transforms input data to output data.

    A common pattern for stages that take input data, transform it,
    and produce output data of potentially different structure.
    """

    def process_data_message(self, message) -> Optional[Message]:
        """Transform the input data.

        Args:
            message: Input data message.

        Returns:
            Transformed data message.
        """
        transformed_data = self.transform(message.payload)

        if transformed_data is not None:
            return create_data_message(
                payload=transformed_data,
                correlation_id=message.correlation_id,
                stage_name=self._name,
                input_type=type(message.payload).__name__,
                output_type=type(transformed_data).__name__
            )
        return None

    def transform(self, data: Any) -> Any:
        """Transform input data to output data.

        Args:
            data: Input data to transform.

        Returns:
            Transformed data or None to drop the message.
        """
        raise NotImplementedError("Subclasses must implement transform()")


class FilterStage(BasePipelineStage):
    """Stage that filters messages based on criteria.

    Only passes through messages that meet the filtering criteria.
    Messages that don't pass are dropped (return None).
    """

    def process_data_message(self, message) -> Optional[Message]:
        """Filter the message.

        Args:
            message: Input data message.

        Returns:
            Message if it passes filter, None otherwise.
        """
        if self.should_pass(message.payload):
            return message
        else:
            self._logger.debug(
                f"Message {message.id} filtered out by stage '{self._name}'",
                extra={"stage_name": self._name, "message_id": message.id}
            )
            return None

    def should_pass(self, data: Any) -> bool:
        """Determine if data should pass through the filter.

        Args:
            data: Data to evaluate.

        Returns:
            True if data should pass, False to filter out.
        """
        raise NotImplementedError("Subclasses must implement should_pass()")


class SinkStage(BasePipelineStage):
    """Stage that consumes messages without producing output.

    Used for final processing stages that store data, send notifications,
    or perform other terminal operations.
    """

    def process_data_message(self, message) -> Optional[Message]:
        """Consume the message.

        Args:
            message: Data message to consume.

        Returns:
            Always returns None (no output).
        """
        self.consume(message.payload)

        self._logger.debug(
            f"Message {message.id} consumed by stage '{self._name}'",
            extra={"stage_name": self._name, "message_id": message.id}
        )

        return None

    def consume(self, data: Any) -> None:
        """Consume the data (no return value).

        Args:
            data: Data to consume.
        """
        raise NotImplementedError("Subclasses must implement consume()")


class PassThroughStage(BasePipelineStage):
    """Stage that passes messages through unchanged.

    Useful for debugging, monitoring, or conditional processing.
    """

    def process_data_message(self, message) -> Optional[Message]:
        """Pass the message through unchanged.

        Args:
            message: Input data message.

        Returns:
            Same message unchanged.
        """
        self._logger.debug(
            f"Passing through message {message.id} in stage '{self._name}'",
            extra={"stage_name": self._name, "message_id": message.id}
        )
        return message


class LoggingStage(BasePipelineStage):
    """Stage that logs message information without modifying them.

    Useful for debugging and monitoring pipeline flow.
    """

    def __init__(self, name: str = "Logger", log_level: int = 20):
        """Initialize logging stage.

        Args:
            name: Stage name.
            log_level: Logging level to use.
        """
        super().__init__(name)
        self._log_level = log_level

    def process_data_message(self, message) -> Optional[Message]:
        """Log message information and pass through.

        Args:
            message: Input data message.

        Returns:
            Same message unchanged.
        """
        self._logger.log(
            self._log_level,
            f"Message {message.id}: {message.payload}",
            extra={
                "stage_name": self._name,
                "message_id": message.id,
                "payload_type": type(message.payload).__name__,
                "correlation_id": message.correlation_id
            }
        )
        return message

