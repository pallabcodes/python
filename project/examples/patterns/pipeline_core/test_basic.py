"""
Basic unit tests for the pipeline core framework.

This module contains fundamental tests for messages, queues,
stages, and basic pipeline functionality.
"""

import pytest
from typing import Any

from .message import Message, DataMessage, ControlMessage, create_data_message, create_control_message
from .queue import InMemoryMessageQueue
from .stage_base import BasePipelineStage
from .stage_types import TransformStage, FilterStage, SinkStage, PassThroughStage


class TestMessage:
    """Tests for message classes."""

    def test_data_message_creation(self):
        """Test data message creation."""
        msg = DataMessage(payload="test data")
        assert msg.payload == "test data"
        assert msg.id is not None
        assert msg.timestamp is not None
        assert isinstance(msg.metadata, dict)

    def test_data_message_without_payload_fails(self):
        """Test that data message requires payload."""
        with pytest.raises(ValueError):
            DataMessage()

    def test_control_message_creation(self):
        """Test control message creation."""
        msg = ControlMessage(control_type="test", payload={"action": "start"})
        assert msg.control_type == "test"
        assert msg.payload == {"action": "start"}

    def test_control_message_without_type_fails(self):
        """Test that control message requires type."""
        with pytest.raises(ValueError):
            ControlMessage()

    def test_message_with_metadata(self):
        """Test message with additional metadata."""
        msg = create_data_message("data", source="test", priority=1)
        assert msg.payload == "data"
        assert msg.metadata["source"] == "test"
        assert msg.metadata["priority"] == 1

    def test_message_to_dict(self):
        """Test message serialization to dict."""
        msg = create_data_message("test")
        data = msg.to_dict()

        assert data["payload"] == "test"
        assert "id" in data
        assert "timestamp" in data
        assert "message_type" in data


class TestMessageQueue:
    """Tests for message queue implementations."""

    def test_queue_creation(self):
        """Test queue creation and basic properties."""
        queue = InMemoryMessageQueue(maxsize=10, name="TestQueue")
        assert queue.qsize() == 0
        assert queue.empty()
        assert not queue._closed

    def test_queue_put_get(self):
        """Test basic put and get operations."""
        queue = InMemoryMessageQueue()
        msg = create_data_message("test")

        queue.put(msg)
        assert queue.qsize() == 1
        assert not queue.empty()

        retrieved = queue.get()
        assert retrieved is not None
        assert retrieved.payload == "test"

        assert queue.empty()

    def test_queue_timeout(self):
        """Test queue timeout behavior."""
        queue = InMemoryMessageQueue()

        # Test get timeout
        result = queue.get(timeout=0.1)
        assert result is None


class TestPipelineStages:
    """Tests for pipeline stage implementations."""

    def test_base_stage_properties(self):
        """Test base stage properties."""
        stage = BasePipelineStage("TestStage")
        assert stage.name == "TestStage"

    def test_base_stage_initialization(self):
        """Test stage initialization and cleanup."""
        stage = BasePipelineStage("TestStage")
        assert not stage._initialized

        stage.initialize()
        assert stage._initialized

        stage.cleanup()
        assert not stage._initialized

    def test_transform_stage(self):
        """Test transform stage implementation."""
        class DoubleTransform(TransformStage):
            def transform(self, data: Any) -> Any:
                return data * 2

        stage = DoubleTransform("Doubler")
        input_msg = create_data_message(5)

        result = stage.process_message(input_msg)
        assert result is not None
        assert result.payload == 10

    def test_filter_stage(self):
        """Test filter stage implementation."""
        class EvenFilter(FilterStage):
            def should_pass(self, data: Any) -> bool:
                return data % 2 == 0

        stage = EvenFilter("EvenFilter")

        # Even number should pass
        even_msg = create_data_message(4)
        result = stage.process_message(even_msg)
        assert result is not None
        assert result.payload == 4

        # Odd number should be filtered
        odd_msg = create_data_message(5)
        result = stage.process_message(odd_msg)
        assert result is None

    def test_sink_stage(self):
        """Test sink stage implementation."""
        consumed_data = []

        class DataCollector(SinkStage):
            def consume(self, data: Any) -> None:
                consumed_data.append(data)

        stage = DataCollector("Collector")
        input_msg = create_data_message("test data")

        result = stage.process_message(input_msg)
        assert result is None  # Sink stages don't produce output
        assert consumed_data == ["test data"]

    def test_pass_through_stage(self):
        """Test pass-through stage."""
        stage = PassThroughStage("PassThrough")
        input_msg = create_data_message("test")

        result = stage.process_message(input_msg)
        assert result is not None
        assert result.payload == "test"
        assert result.id == input_msg.id

    def test_control_message_handling(self):
        """Test control message handling."""
        stage = BasePipelineStage("TestStage")
        control_msg = create_control_message("test_control", payload={"action": "test"})

        result = stage.process_message(control_msg)
        assert result is not None
        assert result.control_type == "test_control"


class TestPipelineRunnerBasic:
    """Basic tests for pipeline runner."""

    def test_runner_creation(self):
        """Test pipeline runner creation."""
        stage = BasePipelineStage("TestStage")

        # Need to implement process_data_message for BasePipelineStage
        class TestStage(BasePipelineStage):
            def process_data_message(self, message):
                return message

        stage = TestStage("TestStage")
        runner = PipelineRunner([stage])

        stats = runner.get_stats()
        assert stats["stage_count"] == 1
        assert stats["queue_count"] == 0  # Single stage, no queues

    def test_runner_empty_stages_fails(self):
        """Test that empty stage list fails."""
        with pytest.raises(ValueError):
            PipelineRunner([])

    def test_single_stage_pipeline(self):
        """Test single stage pipeline execution."""
        processed = []

        class ProcessingStage(SinkStage):
            def consume(self, data: Any) -> None:
                processed.append(data)

        stage = ProcessingStage("Processor")
        runner = PipelineRunner([stage])

        input_messages = [create_data_message(f"item-{i}") for i in range(3)]
        results = runner.run_pipeline(input_messages)

        assert results["success"] is True
        assert len(processed) == 3
        assert processed == ["item-0", "item-1", "item-2"]

