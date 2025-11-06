"""
Demonstrations of the pipeline core framework.

This module provides practical examples of building and running
pipelines using the core framework components.
"""

import time
import logging
from typing import List, Any

from .message import DataMessage, create_data_message
from .stage import TransformStage, FilterStage, SinkStage
from .runner import PipelineRunner


class DataMultiplier(TransformStage):
    """Stage that multiplies numeric data by a factor."""

    def __init__(self, factor: int, name: str = "Multiplier"):
        super().__init__(name)
        self._factor = factor

    def transform(self, data: Any) -> Any:
        """Multiply numeric data."""
        if isinstance(data, (int, float)):
            return data * self._factor
        return data


class EvenFilter(FilterStage):
    """Stage that filters out odd numbers."""

    def __init__(self, name: str = "EvenFilter"):
        super().__init__(name)

    def should_pass(self, data: Any) -> bool:
        """Pass only even numbers."""
        return isinstance(data, int) and data % 2 == 0


class DataPrinter(SinkStage):
    """Stage that prints data to console."""

    def __init__(self, name: str = "Printer"):
        super().__init__(name)
        self._count = 0

    def consume(self, data: Any) -> None:
        """Print the data."""
        self._count += 1
        print(f"[{self._name}] Item {self._count}: {data}")


def demo_simple_pipeline() -> None:
    """Demonstrate a simple 3-stage pipeline."""
    print("=== Simple Pipeline Demo ===")

    # Create stages
    multiplier = DataMultiplier(factor=3, name="Triple")
    even_filter = EvenFilter(name="EvenOnly")
    printer = DataPrinter(name="Output")

    stages = [multiplier, even_filter, printer]

    # Create input messages
    input_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    input_messages = [create_data_message(data) for data in input_data]

    print(f"Input: {input_data}")
    print("Pipeline: Multiply by 3 -> Filter Even -> Print")
    print("Expected output: Even numbers multiplied by 3")
    print()

    # Run pipeline
    runner = PipelineRunner(stages)
    results = runner.run_pipeline(input_messages, timeout=10.0)

    print(f"\nPipeline completed in {results['execution_time']:.2f}s")
    print(f"Success: {results['success']}")


def demo_complex_pipeline() -> None:
    """Demonstrate a more complex pipeline with branching logic."""
    print("\n=== Complex Pipeline Demo ===")

    class StringTransformer(TransformStage):
        """Transform data to strings with formatting."""

        def transform(self, data: Any) -> str:
            return f"Value: {data}"

    class LengthFilter(FilterStage):
        """Filter strings by length."""

        def __init__(self, max_length: int, name: str = "LengthFilter"):
            super().__init__(name)
            self._max_length = max_length

        def should_pass(self, data: Any) -> bool:
            return isinstance(data, str) and len(data) <= self._max_length

    class UppercaseTransformer(TransformStage):
        """Convert strings to uppercase."""

        def transform(self, data: Any) -> str:
            if isinstance(data, str):
                return data.upper()
            return str(data).upper()

    # Create pipeline: Transform -> Filter -> Uppercase -> Print
    transformer = StringTransformer(name="ToString")
    length_filter = LengthFilter(max_length=15, name="ShortStrings")
    uppercase = UppercaseTransformer(name="Uppercase")
    printer = DataPrinter(name="Results")

    stages = [transformer, length_filter, uppercase, printer]

    # Mixed input data
    input_data = [
        42, "hello", 3.14, "a very long string that should be filtered out",
        "world", 100, "short"
    ]
    input_messages = [create_data_message(data) for data in input_data]

    print(f"Input: {input_data}")
    print("Pipeline: ToString -> Filter(short) -> Uppercase -> Print")
    print("Expected: Short strings converted to uppercase")
    print()

    # Run pipeline
    runner = PipelineRunner(stages)
    results = runner.run_pipeline(input_messages, timeout=10.0)

    print(f"\nPipeline completed in {results['execution_time']:.2f}s")
    print(f"Success: {results['success']}")


def demo_error_handling() -> None:
    """Demonstrate error handling in pipelines."""
    print("\n=== Error Handling Demo ===")

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

    for config_name, stages in configs:
        # Add sink to consume output
        pipeline_stages = stages + [DataPrinter(name="Sink")]

        runner = PipelineRunner(pipeline_stages)
        start_time = time.time()
        results = runner.run_pipeline(input_messages.copy(), timeout=30.0)
        end_time = time.time()

        print(f"{config_name}: {results['execution_time']:.2f}s "
              f"({'✓' if results['success'] else '✗'})")


def run_all_demos() -> None:
    """Run all pipeline core demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running Pipeline Core Framework Demonstrations")
    print("=" * 60)

    try:
        demo_simple_pipeline()
        demo_complex_pipeline()
        demo_error_handling()
        demo_performance_comparison()

        print("\n" + "=" * 60)
        print("All demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run demonstrations when executed directly."""
    run_all_demos()

