"""
Race condition detection test for counter implementations.

This module provides comprehensive testing to detect and demonstrate
race conditions in thread-unsafe counter implementations. It uses
statistical analysis and multiple test runs to reliably detect
concurrency bugs.
"""

import threading
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from statistics import mean, stdev

from counter import ThreadSafeCounter, UnsafeCounter, increment_counter


@dataclass
class RaceTestResult:
    """Result of a race condition test run.

    Attributes:
        expected_value: Expected counter value after test.
        actual_value: Actual counter value obtained.
        is_correct: Whether result matches expectation.
        duration: Time taken for the test run.
        thread_count: Number of threads used.
        iterations_per_thread: Increments per thread.
    """

    expected_value: int
    actual_value: int
    is_correct: bool
    duration: float
    thread_count: int
    iterations_per_thread: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "is_correct": self.is_correct,
            "duration": self.duration,
            "thread_count": self.thread_count,
            "iterations_per_thread": self.iterations_per_thread,
            "error_count": abs(self.expected_value - self.actual_value)
        }


class RaceConditionDetector:
    """Detector for race conditions in counter implementations.

    This class provides statistical testing to reliably detect
    race conditions by running multiple test iterations and
    analyzing the results for inconsistencies.

    Attributes:
        logger: Logger for test execution details.
    """

    def __init__(self) -> None:
        """Initialize the race condition detector."""
        self._logger: logging.Logger = logging.getLogger(__name__)

    def test_counter_implementation(
        self,
        counter_class: type,
        thread_count: int = 4,
        iterations_per_thread: int = 1000,
        test_runs: int = 10
    ) -> List[RaceTestResult]:
        """Test a counter implementation for race conditions.

        Runs multiple test iterations and collects results to
        statistically detect race conditions.

        Args:
            counter_class: Counter class to test (ThreadSafeCounter or UnsafeCounter).
            thread_count: Number of concurrent threads.
            iterations_per_thread: Counter increments per thread.
            test_runs: Number of test runs for statistical analysis.

        Returns:
            List of test results from each run.
        """
        results: List[RaceTestResult] = []
        expected_total = thread_count * iterations_per_thread

        self._logger.info(
            f"Starting race condition test for {counter_class.__name__}",
            extra={
                "counter_class": counter_class.__name__,
                "thread_count": thread_count,
                "iterations_per_thread": iterations_per_thread,
                "test_runs": test_runs,
                "expected_total": expected_total
            }
        )

        for run in range(test_runs):
            start_time = time.time()

            # Create counter instance
            counter = counter_class()

            # Create and start threads
            threads: List[threading.Thread] = []
            for _ in range(thread_count):
                thread = threading.Thread(
                    target=increment_counter,
                    args=(counter, iterations_per_thread)
                )
                threads.append(thread)

            for thread in threads:
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join()

            duration = time.time() - start_time
            actual_value = counter.get_value()
            is_correct = actual_value == expected_total

            result = RaceTestResult(
                expected_value=expected_total,
                actual_value=actual_value,
                is_correct=is_correct,
                duration=duration,
                thread_count=thread_count,
                iterations_per_thread=iterations_per_thread
            )

            results.append(result)

            self._logger.debug(
                f"Test run {run + 1}/{test_runs} completed",
                extra={
                    "run": run + 1,
                    "expected": expected_total,
                    "actual": actual_value,
                    "correct": is_correct,
                    "duration": duration
                }
            )

        return results

    def analyze_results(self, results: List[RaceTestResult]) -> Dict[str, Any]:
        """Analyze test results for race condition indicators.

        Performs statistical analysis on test results to determine
        if race conditions are present.

        Args:
            results: List of test results to analyze.

        Returns:
            Analysis results including race condition detection.
        """
        if not results:
            return {"error": "No results to analyze"}

        # Calculate statistics
        correct_count = sum(1 for r in results if r.is_correct)
        incorrect_count = len(results) - correct_count
        error_values = [abs(r.expected_value - r.actual_value) for r in results if not r.is_correct]
        durations = [r.duration for r in results]

        analysis = {
            "total_runs": len(results),
            "correct_runs": correct_count,
            "incorrect_runs": incorrect_count,
            "success_rate": correct_count / len(results),
            "race_condition_detected": incorrect_count > 0,
            "max_error": max(error_values) if error_values else 0,
            "avg_duration": mean(durations),
            "duration_stddev": stdev(durations) if len(durations) > 1 else 0.0,
            "results": [r.to_dict() for r in results]
        }

        # Log analysis results
        if analysis["race_condition_detected"]:
            self._logger.warning(
                f"Race condition detected: {incorrect_count}/{len(results)} runs failed",
                extra={
                    "incorrect_runs": incorrect_count,
                    "total_runs": len(results),
                    "max_error": analysis["max_error"]
                }
            )
        else:
            self._logger.info(
                f"No race conditions detected: all {len(results)} runs passed"
            )

        return analysis


def run_race_condition_tests() -> None:
    """Run comprehensive race condition tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    detector = RaceConditionDetector()

    # Test configurations
    configs = [
        {"threads": 2, "iterations": 1000, "runs": 5},
        {"threads": 4, "iterations": 1000, "runs": 5},
        {"threads": 8, "iterations": 500, "runs": 5},
    ]

    print("=== Race Condition Detection Tests ===\n")

    for config in configs:
        print(f"Configuration: {config['threads']} threads, "
              f"{config['iterations']} iterations, {config['runs']} runs")

        # Test thread-safe counter
        print("Testing ThreadSafeCounter...")
        safe_results = detector.test_counter_implementation(
            ThreadSafeCounter,
            thread_count=config["threads"],
            iterations_per_thread=config["iterations"],
            test_runs=config["runs"]
        )
        safe_analysis = detector.analyze_results(safe_results)

        # Test unsafe counter
        print("Testing UnsafeCounter...")
        unsafe_results = detector.test_counter_implementation(
            UnsafeCounter,
            thread_count=config["threads"],
            iterations_per_thread=config["iterations"],
            test_runs=config["runs"]
        )
        unsafe_analysis = detector.analyze_results(unsafe_results)

        # Print comparison
        print(f"  ThreadSafe: {safe_analysis['correct_runs']}/{safe_analysis['total_runs']} correct")
        print(f"  Unsafe:     {unsafe_analysis['correct_runs']}/{unsafe_analysis['total_runs']} correct")
        print(f"  Race condition in unsafe: {unsafe_analysis['race_condition_detected']}")
        print()


if __name__ == "__main__":
    """Run race condition tests when executed directly."""
    run_race_condition_tests()

