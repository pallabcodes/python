"""
Basic pipeline demonstrations.

This module contains fundamental demonstrations of pipeline
functionality including simple stage chains and basic message flow.
"""

import logging
from typing import List, Any

from .message import create_data_message
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


def demo_linear_processing() -> None:
    """Demonstrate linear data processing pipeline."""
    print("\n=== Linear Processing Demo ===")

    class StringAppender(TransformStage):
        """Append text to string data."""

        def __init__(self, suffix: str, name: str = "Appender"):
            super().__init__(name)
            self._suffix = suffix

        def transform(self, data: Any) -> str:
            return f"{data}{self._suffix}"

    class LengthChecker(FilterStage):
        """Filter strings by minimum length."""

        def __init__(self, min_length: int, name: str = "LengthChecker"):
            super().__init__(name)
            self._min_length = min_length

        def should_pass(self, data: Any) -> bool:
            return isinstance(data, str) and len(data) >= self._min_length

    # Create processing pipeline
    appender = StringAppender("-processed", name="AddSuffix")
    length_filter = LengthChecker(min_length=10, name="LongEnough")
    output = DataPrinter(name="Results")

    stages = [appender, length_filter, output]

    # Test data
    input_data = ["short", "medium length", "this is a long string", "tiny"]
    input_messages = [create_data_message(data) for data in input_data]

    print(f"Input: {input_data}")
    print("Pipeline: Add '-processed' -> Filter length >= 10 -> Print")
    print()

    # Run pipeline
    runner = PipelineRunner(stages)
    results = runner.run_pipeline(input_messages, timeout=10.0)

    print(f"\nPipeline completed in {results['execution_time']:.2f}s")
    print(f"Success: {results['success']}")


def run_basic_demos() -> None:
    """Run all basic pipeline demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running Basic Pipeline Demonstrations")
    print("=" * 40)

    try:
        demo_simple_pipeline()
        demo_linear_processing()

        print("\n" + "=" * 40)
        print("Basic demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run basic demonstrations when executed directly."""
    run_basic_demos()

