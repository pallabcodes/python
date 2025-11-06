"""
Message classes for pipeline communication.

This module defines the message types used for communication
between pipeline stages, including data messages and control messages.
"""

import time
import uuid
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Message:
    """Base message class for pipeline communication.

    All messages in the pipeline inherit from this base class.
    Messages carry data between stages and include metadata for
    tracking and debugging.

    Attributes:
        id: Unique message identifier.
        timestamp: Creation timestamp.
        correlation_id: ID linking related messages.
        metadata: Additional message metadata.
        payload: The actual message data.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    payload: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata.copy(),
            "payload": self.payload,
            "message_type": self.__class__.__name__
        }

    def with_metadata(self, **kwargs) -> "Message":
        """Create a copy of this message with additional metadata."""
        new_metadata = self.metadata.copy()
        new_metadata.update(kwargs)
        return Message(
            id=self.id,
            timestamp=self.timestamp,
            correlation_id=self.correlation_id,
            metadata=new_metadata,
            payload=self.payload
        )


@dataclass
class DataMessage(Message):
    """Message containing data for processing.

    Used to pass data items through the pipeline for transformation
    and processing by different stages.

    Attributes:
        payload: The data to be processed (required).
    """

    def __post_init__(self):
        """Validate that payload is provided."""
        if self.payload is None:
            raise ValueError("DataMessage must have a payload")


@dataclass
class ControlMessage(Message):
    """Control message for pipeline management.

    Used to signal control operations like pipeline start,
    shutdown, or stage-specific commands.

    Attributes:
        control_type: Type of control operation.
        target_stage: Optional stage name to target.
    """

    control_type: str = ""
    target_stage: Optional[str] = None

    def __post_init__(self):
        """Validate control message."""
        if not self.control_type:
            raise ValueError("ControlMessage must have a control_type")


# Predefined control messages
PIPELINE_START = ControlMessage(
    control_type="pipeline_start",
    payload={"action": "start"}
)

PIPELINE_SHUTDOWN = ControlMessage(
    control_type="pipeline_shutdown",
    payload={"action": "shutdown"}
)

STAGE_READY = ControlMessage(
    control_type="stage_ready",
    payload={"status": "ready"}
)

STAGE_ERROR = ControlMessage(
    control_type="stage_error",
    payload={"status": "error"}
)


def create_data_message(
    payload: Any,
    correlation_id: Optional[str] = None,
    **metadata
) -> DataMessage:
    """Create a data message with optional metadata.

    Args:
        payload: The data payload for the message.
        correlation_id: Optional correlation ID.
        **metadata: Additional metadata key-value pairs.

    Returns:
        A new DataMessage instance.
    """
    return DataMessage(
        payload=payload,
        correlation_id=correlation_id,
        metadata=metadata
    )


def create_control_message(
    control_type: str,
    target_stage: Optional[str] = None,
    payload: Any = None,
    **metadata
) -> ControlMessage:
    """Create a control message.

    Args:
        control_type: Type of control operation.
        target_stage: Optional target stage name.
        payload: Control payload data.
        **metadata: Additional metadata.

    Returns:
        A new ControlMessage instance.
    """
    return ControlMessage(
        control_type=control_type,
        target_stage=target_stage,
        payload=payload,
        metadata=metadata
    )

