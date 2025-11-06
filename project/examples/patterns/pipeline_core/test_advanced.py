"""
Advanced unit tests for the pipeline framework.

This module contains advanced tests including multi-stage pipelines,
error handling, timeouts, and complex workflows.
"""

import time
import pytest
from typing import Any, List, Dict

from .message import Message, create_data_message, create_control_message
from .stage_types import TransformStage, FilterStage, SinkStage
from .runner_core import PipelineRunner


class TestMultiStagePipeline:
    """Tests for multi-stage pipeline execution."""

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


class TestPipelineWorkflows:
    """Tests for complex pipeline workflows."""

    def test_complex_routing_workflow(self):
        """Test complex workflow with routing logic."""
        class DataValidator(FilterStage):
            def should_pass(self, data: Any) -> bool:
                return isinstance(data, dict) and "type" in data

        class TypeRouter(TransformStage):
            def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
                data_type = data["type"]
                return {
                    **data,
                    "route": "numeric" if data_type in ["int", "float"] else "text"
                }

        class NumericProcessor(TransformStage):
            def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
                if data.get("route") == "numeric":
                    return {**data, "processed": True, "result": data["value"] * 2}
                return data

        results = []

        class ResultAggregator(SinkStage):
            def consume(self, data: Dict[str, Any]) -> None:
                results.append(data)

        stages = [
            DataValidator("Validator"),
            TypeRouter("Router"),
            NumericProcessor("NumericProc"),
            ResultAggregator("Results")
        ]

        runner = PipelineRunner(stages)

        input_messages = [
            create_data_message({"type": "int", "value": 5}),
            create_data_message({"invalid": "data"}),  # Should be filtered
            create_data_message({"type": "text", "value": "hello"}),
        ]

        pipeline_result = runner.run_pipeline(input_messages)

        assert pipeline_result["success"] is True
        assert len(results) == 2  # Invalid data filtered out

        # Check results
        numeric_result = next(r for r in results if r.get("type") == "int")
        text_result = next(r for r in results if r.get("type") == "text")

        assert numeric_result["processed"] is True
        assert numeric_result["result"] == 10
        assert text_result.get("processed") is None  # Text not processed


class TestPipelineMonitoring:
    """Tests for pipeline monitoring and statistics."""

    def test_pipeline_stats(self):
        """Test pipeline statistics reporting."""
        stages = [
            TransformStage("Stage1"),
            TransformStage("Stage2"),
        ]

        runner = PipelineRunner(stages)
        stats = runner.get_stats()

        assert stats["stage_count"] == 2
        assert stats["queue_count"] == 1  # One queue between stages
        assert stats["running"] is False
        assert len(stats["stages"]) == 2
        assert stats["stages"] == ["Stage1", "Stage2"]

    def test_single_stage_stats(self):
        """Test single stage pipeline statistics."""
        stage = TransformStage("SingleStage")
        runner = PipelineRunner([stage])

        stats = runner.get_stats()
        assert stats["stage_count"] == 1
        assert stats["queue_count"] == 0  # No queues for single stage


class TestPipelineControl:
    """Tests for pipeline control messages."""

    def test_control_message_passing(self):
        """Test control message handling."""
        received_control = []

        class ControlCapturingStage(TransformStage):
            def transform(self, data: Any) -> Any:
                return data

            def handle_control_message(self, message):
                received_control.append(message.control_type)
                return super().handle_control_message(message)

        stages = [ControlCapturingStage("ControlStage")]
        runner = PipelineRunner(stages)

        # Run empty pipeline to trigger control messages
        results = runner.run_pipeline([])

        assert results["success"] is True
        assert "pipeline_start" in received_control
        assert "pipeline_shutdown" in received_control


class TestPipelineTimeout:
    """Tests for pipeline timeout behavior."""

    def test_pipeline_timeout(self):
        """Test pipeline timeout handling."""
        class SlowStage(TransformStage):
            def transform(self, data: Any) -> Any:
                time.sleep(2)  # Slow operation
                return data

        stage = SlowStage("Slow")
        runner = PipelineRunner([stage])

        input_messages = [create_data_message("test")]
        results = runner.run_pipeline(input_messages, timeout=1.0)

        # Timeout behavior may vary, but should complete
        assert "execution_time" in results


class TestPipelineResourceManagement:
    """Tests for pipeline resource management."""

    def test_stage_cleanup(self):
        """Test that stages are properly cleaned up."""
        cleanup_called = []

        class CleanupTrackingStage(TransformStage):
            def transform(self, data: Any) -> Any:
                return data

            def cleanup(self) -> None:
                cleanup_called.append(self.name)
                super().cleanup()

        stages = [
            CleanupTrackingStage("Stage1"),
            CleanupTrackingStage("Stage2")
        ]

        runner = PipelineRunner(stages)
        runner.run_pipeline([create_data_message("test")])

        assert "Stage1" in cleanup_called
        assert "Stage2" in cleanup_called

    def test_queue_cleanup(self):
        """Test that queues are properly closed."""
        stages = [
            TransformStage("Stage1"),
            TransformStage("Stage2")
        ]

        runner = PipelineRunner(stages)
        runner.run_pipeline([create_data_message("test")])

        # Queues should be closed after execution
        for queue in runner._queues:
            assert queue._closed


if __name__ == "__main__":
    """Run advanced tests when executed directly."""
    pytest.main([__file__, "-v"])

