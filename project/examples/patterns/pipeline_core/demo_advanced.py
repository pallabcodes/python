"""
Advanced pipeline demonstrations.

This module contains advanced demonstrations including error handling,
complex workflows, and performance comparisons.
"""

import time
import random
import logging
from typing import List, Any, Dict

from .message import create_data_message
from .stage import TransformStage, FilterStage, SinkStage
from .runner import PipelineRunner


def demo_error_handling() -> None:
    """Demonstrate error handling in pipelines."""
    print("=== Error Handling Demo ===")

    class ErrorProneStage(TransformStage):
        """Stage that occasionally fails."""

        def __init__(self, name: str = "ErrorProne"):
            super().__init__(name)
            self._processed = 0

        def transform(self, data: Any) -> Any:
            self._processed += 1
            if self._processed % 3 == 0:  # Fail every 3rd item
                raise ValueError(f"Simulated error on item {self._processed}")
            return f"processed-{data}"

    class ErrorResilientSink(SinkStage):
        """Sink that handles errors gracefully."""

        def consume(self, data: Any) -> None:
            print(f"[Resilient] Successfully processed: {data}")

    # Create pipeline with error-prone stage
    error_stage = ErrorProneStage(name="Unreliable")
    sink = ErrorResilientSink(name="ResilientSink")

    stages = [error_stage, sink]

    # Input data
    input_data = [f"item-{i}" for i in range(9)]
    input_messages = [create_data_message(data) for data in input_data]

    print(f"Input: {input_data}")
    print("Pipeline: ErrorProne -> ResilientSink")
    print("Note: ErrorProne fails every 3rd item, but pipeline continues")
    print()

    # Run pipeline
    runner = PipelineRunner(stages)
    results = runner.run_pipeline(input_messages, timeout=10.0)

    print(f"\nPipeline completed in {results['execution_time']:.2f}s")
    print(f"Success: {results['success']}")
    if results.get('errors'):
        print(f"Errors encountered: {len(results['errors'])}")


def demo_complex_workflow() -> None:
    """Demonstrate complex multi-stage workflow."""
    print("\n=== Complex Workflow Demo ===")

    class DataValidator(FilterStage):
        """Validate input data structure."""

        def should_pass(self, data: Any) -> bool:
            return isinstance(data, dict) and "type" in data and "value" in data

    class TypeRouter(TransformStage):
        """Route data based on type."""

        def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
            data_type = data["type"]
            return {
                **data,
                "route": "numeric" if data_type in ["int", "float"] else "text",
                "routed_at": time.time()
            }

    class NumericProcessor(TransformStage):
        """Process numeric data."""

        def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
            if data.get("route") == "numeric":
                value = data["value"]
                return {
                    **data,
                    "processed_value": value * 2,
                    "is_even": value % 2 == 0,
                    "processed_by": "numeric_processor"
                }
            return data

    class TextProcessor(TransformStage):
        """Process text data."""

        def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
            if data.get("route") == "text":
                text = str(data["value"])
                return {
                    **data,
                    "processed_value": text.upper(),
                    "length": len(text),
                    "processed_by": "text_processor"
                }
            return data

    class ResultAggregator(SinkStage):
        """Aggregate and display results."""

        def __init__(self, name: str = "Aggregator"):
            super().__init__(name)
            self._results = []

        def consume(self, data: Dict[str, Any]) -> None:
            self._results.append(data)
            print(f"[Result] {data.get('type', 'unknown')}: {data.get('processed_value', 'N/A')}")

    # Build complex pipeline
    validator = DataValidator(name="Validator")
    router = TypeRouter(name="Router")
    numeric_proc = NumericProcessor(name="NumericProc")
    text_proc = TextProcessor(name="TextProc")
    aggregator = ResultAggregator(name="Results")

    stages = [validator, router, numeric_proc, text_proc, aggregator]

    # Complex input data
    input_data = [
        {"type": "int", "value": 5},
        {"type": "text", "value": "hello"},
        {"type": "float", "value": 3.14},
        {"type": "text", "value": "world"},
        {"invalid": "data"},  # Should be filtered out
        {"type": "int", "value": 10},
    ]
    input_messages = [create_data_message(data) for data in input_data]

    print("Complex workflow with validation, routing, and parallel processing:")
    print(f"Input: {len(input_data)} items")
    print("Pipeline: Validate -> Route -> Process(Numeric|Text) -> Aggregate")
    print()

    # Run pipeline
    runner = PipelineRunner(stages)
    results = runner.run_pipeline(input_messages, timeout=15.0)

    print(f"\nWorkflow completed in {results['execution_time']:.2f}s")
    print(f"Success: {results['success']}")
    print(f"Items processed: {len(aggregator._results)}")


def demo_performance_comparison() -> None:
    """Compare pipeline performance with different configurations."""
    print("\n=== Performance Comparison Demo ===")

    # Simple processing stage
    class SimpleProcessor(TransformStage):
        def transform(self, data: Any) -> Any:
            # Simulate some processing
            time.sleep(0.001)
            return data

    # Create different pipeline configurations
    configs = [
        ("Single Stage", [SimpleProcessor(name="Single")]),
        ("Two Stages", [SimpleProcessor(name="First"), SimpleProcessor(name="Second")]),
        ("Three Stages", [SimpleProcessor(name="A"), SimpleProcessor(name="B"), SimpleProcessor(name="C")])
    ]

    # Test data
    input_data = [f"data-{i}" for i in range(50)]
    input_messages = [create_data_message(data) for data in input_data]

    print("Comparing pipeline performance with different stage counts:")
    print(f"Input size: {len(input_messages)} messages")
    print()

    for config_name, stage_list in configs:
        # Add sink to consume output
        stages = stage_list + [DataPrinter(name="Sink")]

        runner = PipelineRunner(stages)
        start_time = time.time()
        results = runner.run_pipeline(input_messages.copy(), timeout=30.0)
        end_time = time.time()

        duration = end_time - start_time
        print(f"{config_name}: {duration:.2f}s "
              f"({'✓' if results['success'] else '✗'})")


def demo_message_metadata() -> None:
    """Demonstrate message metadata and correlation tracking."""
    print("\n=== Message Metadata Demo ===")

    class MetadataEnricher(TransformStage):
        """Add processing metadata to messages."""

        def transform(self, data: Any) -> Dict[str, Any]:
            return {
                "original_data": data,
                "processed_at": time.time(),
                "processor_id": "enricher-001",
                "processing_steps": ["validation", "enrichment"]
            }

    class MetadataLogger(SinkStage):
        """Log message metadata."""

        def consume(self, data: Dict[str, Any]) -> None:
            metadata = getattr(self, '_current_message', {}).get('metadata', {})
            correlation_id = metadata.get('correlation_id', 'unknown')

            print(f"[Logger] Correlation: {correlation_id}")
            print(f"        Processing time: {data.get('processed_at', 0):.6f}")
            print(f"        Steps: {data.get('processing_steps', [])}")

    # Create pipeline with metadata tracking
    enricher = MetadataEnricher(name="Enricher")
    logger = MetadataLogger(name="Logger")

    stages = [enricher, logger]

    # Input with correlation IDs
    input_messages = []
    for i in range(3):
        msg = create_data_message(
            payload=f"item-{i}",
            correlation_id=f"request-{i:03d}",
            source="demo",
            priority="normal"
        )
        input_messages.append(msg)

    print("Demonstrating message metadata and correlation tracking:")
    print("Each message has correlation ID and metadata")
    print()

    # Run pipeline
    runner = PipelineRunner(stages)
    results = runner.run_pipeline(input_messages, timeout=10.0)

    print(f"\nMetadata demo completed in {results['execution_time']:.2f}s")
    print(f"Success: {results['success']}")


def run_advanced_demos() -> None:
    """Run all advanced pipeline demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running Advanced Pipeline Demonstrations")
    print("=" * 45)

    try:
        demo_error_handling()
        demo_complex_workflow()
        demo_performance_comparison()
        demo_message_metadata()

        print("\n" + "=" * 45)
        print("Advanced demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run advanced demonstrations when executed directly."""
    run_advanced_demos()

