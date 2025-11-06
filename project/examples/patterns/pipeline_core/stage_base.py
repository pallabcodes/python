"""
Base pipeline stage implementation.

This module provides the core stage infrastructure including
base classes, error handling, and lifecycle management.
"""

import logging
from typing import Any, Optional, Protocol
from abc import ABC, abstractmethod

from .message import Message, DataMessage, ControlMessage


class PipelineStage(Protocol):
    """Protocol for pipeline stage operations.

    All pipeline stages must implement this protocol to be
    used in pipeline execution.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get stage name."""
        ...

    @abstractmethod
    def process_message(self, message: Message) -> Optional[Message]:
        """Process a message and return result."""
        ...

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the stage."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up stage resources."""
        ...


class BasePipelineStage(ABC):
    """Base class for pipeline stages.

    Provides common functionality for all pipeline stages including
    logging, error handling, and basic message processing patterns.

    Attributes:
        _name: Stage name for identification.
        _logger: Logger for stage operations.
        _initialized: Whether stage has been initialized.
    """

    def __init__(self, name: str):
        """Initialize the base stage.

        Args:
            name: Stage name for identification.
        """
        self._name = name
        self._logger = logging.getLogger(f"{__name__}.{name}")
        self._initialized = False

    @property
    def name(self) -> str:
        """Get stage name."""
        return self._name

    def initialize(self) -> None:
        """Initialize the stage."""
        if not self._initialized:
            self._logger.info(f"Initializing stage '{self._name}'")
            self._initialized = True
            self.on_initialize()

    def cleanup(self) -> None:
        """Clean up stage resources."""
        if self._initialized:
            self._logger.info(f"Cleaning up stage '{self._name}'")
            self.on_cleanup()
            self._initialized = False

    def process_message(self, message: Message) -> Optional[Message]:
        """Process a message with error handling.

        Args:
            message: Input message to process.

        Returns:
            Processed message or None if message should be dropped.
        """
        try:
            self._logger.debug(
                f"Processing message {message.id} in stage '{self._name}'",
                extra={
                    "stage_name": self._name,
                    "message_id": message.id,
                    "message_type": message.__class__.__name__
                }
            )

            # Handle control messages
            if isinstance(message, ControlMessage):
                return self.handle_control_message(message)

            # Handle data messages
            elif isinstance(message, DataMessage):
                result = self.process_data_message(message)
                if result is not None:
                    # Preserve correlation ID
                    if hasattr(result, 'correlation_id') and result.correlation_id is None:
                        result.correlation_id = message.correlation_id
                return result

            else:
                self._logger.warning(
                    f"Unknown message type {message.__class__.__name__} in stage '{self._name}'",
                    extra={"stage_name": self._name, "message_type": message.__class__.__name__}
                )
                return None

        except Exception as e:
            self._logger.error(
                f"Error processing message {message.id} in stage '{self._name}': {e}",
                extra={
                    "stage_name": self._name,
                    "message_id": message.id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            return None

    @abstractmethod
    def process_data_message(self, message: DataMessage) -> Optional[Message]:
        """Process a data message.

        Args:
            message: Data message to process.

        Returns:
            Processed message or None.
        """
        pass

    def handle_control_message(self, message: ControlMessage) -> Optional[Message]:
        """Handle a control message.

        Args:
            message: Control message to handle.

        Returns:
            Response message or None.
        """
        self._logger.debug(
            f"Handling control message {message.control_type} in stage '{self._name}'",
            extra={
                "stage_name": self._name,
                "control_type": message.control_type
            }
        )
        return message  # Pass through by default

    def on_initialize(self) -> None:
        """Hook for custom initialization logic."""
        pass

    def on_cleanup(self) -> None:
        """Hook for custom cleanup logic."""
        pass

