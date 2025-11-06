"""
Unit tests for the pipeline core framework.

This module provides comprehensive tests for the pipeline
framework components including messages, queues, stages, and runner.
"""

import time
import pytest
from typing import Any, List

from .message import Message, DataMessage, ControlMessage, create_data_message, create_control_message
from .queue import InMemoryMessageQueue
from .stage import BasePipelineStage, TransformStage, FilterStage, SinkStage
from .runner import PipelineRunner


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

        # Test put timeout on full queue
        full_queue = InMemoryMessageQueue(maxsize=1)
        full_queue.put(create_data_message("item1"))

        # Should work without timeout
        with pytest.raises(RuntimeError):
            full_queue.put(create_data_message("item2"), timeout=0.1)

    def test_queue_close(self):
        """Test queue closing behavior."""
        queue = InMemoryMessageQueue()
        queue.put(create_data_message("test"))

        queue.close()
        assert queue._closed

        # Should not be able to put after close
        with pytest.raises(RuntimeError):
            queue.put(create_data_message("after_close"))


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

    def test_control_message_handling(self):
        """Test control message handling."""
        stage = BasePipelineStage("TestStage")
        control_msg = create_control_message("test_control", payload={"action": "test"})

        result = stage.process_message(control_msg)
        assert result is not None
        assert result.control_type == "test_control"


class TestPipelineRunner:
    """Tests for pipeline runner."""

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

    def test_multi_stage_pipeline(self):
        """Test multi-stage pipeline execution."""
        class UppercaseTransform(TransformStage):
            def transform(self, data: Any) -> str:
                return str(data).upper()

        class LengthFilter(FilterStage):
            def should_pass(self, data: Any) -> bool:
                return len(str(data)) <= 5

        results = []

        class ResultCollector(SinkStage):
            def consume(self, data: Any) -> None:
                results.append(data)

        stages = [
            UppercaseTransform("Upper"),
            LengthFilter("ShortOnly"),
            ResultCollector("Collector")
        ]

        runner = PipelineRunner(stages)

        input_messages = [
            create_data_message("hi"),      # -> "HI" (passes)
            create_data_message("hello"),   # -> "HELLO" (fails length)
            create_data_message("a"),       # -> "A" (passes)
        ]

        pipeline_result = runner.run_pipeline(input_messages)

        assert pipeline_result["success"] is True
        assert len(results) == 2
        assert set(results) == {"HI", "A"}

    def test_pipeline_error_handling(self):
        """Test pipeline error handling."""
        class FailingStage(TransformStage):
            def transform(self, data: Any) -> Any:
                raise ValueError("Stage failure")

        stage = FailingStage("Failing")
        runner = PipelineRunner([stage])

        input_messages = [create_data_message("test")]
        results = runner.run_pipeline(input_messages, timeout=5.0)

        assert results["success"] is False
        assert "error" in results
        assert len(results["errors"]) > 0

    def test_pipeline_timeout(self):
        """Test pipeline timeout behavior."""
        class SlowStage(TransformStage):
            def transform(self, data: Any) -> Any:
                time.sleep(2)  # Slow operation
                return data

        stage = SlowStage("Slow")
        runner = PipelineRunner([stage])

        input_messages = [create_data_message("test")]
        results = runner.run_pipeline(input_messages, timeout=1.0)

        assert results["success"] is False
        # Timeout behavior may vary by implementation


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v"])

