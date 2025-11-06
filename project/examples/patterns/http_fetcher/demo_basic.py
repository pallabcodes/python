"""
Basic HTTP fetcher demonstrations.

This module contains fundamental demonstrations of HTTP fetching
with rate limiting and basic error handling.
"""

import logging
from typing import List, Any

from ..pipeline_core.message import create_data_message
from ..pipeline_core.runner import PipelineRunner
from .fetcher_stage import HttpFetcherStage
from ..pipeline_core.stage_types import TransformStage


class ResponseProcessor(TransformStage):
    """Process HTTP fetcher responses."""

    def __init__(self, name: str = "ResponseProcessor"):
        super().__init__(name)
        self._processed = 0

    def transform(self, data: Any) -> Any:
        """Process HTTP response data."""
        self._processed += 1

        if isinstance(data, dict) and data.get("error"):
            # Handle error responses
            return {
                "processed": False,
                "error": data["error_message"],
                "original": data.get("original_request")
            }

        # Process successful responses
        if isinstance(data, dict) and "status_code" in data:
            return {
                "processed": True,
                "url": data.get("url"),
                "status": data.get("status_code"),
                "content_type": data.get("content_type"),
                "data_length": len(str(data.get("data", ""))),
                "elapsed": data.get("elapsed", 0)
            }

        return data


def demo_basic_http_fetch() -> None:
    """Demonstrate basic HTTP fetching."""
    print("=== Basic HTTP Fetch Demo ===")

    # Create fetcher stage
    fetcher = HttpFetcherStage(
        name="BasicFetcher",
        requests_per_second=2.0,  # Conservative rate limiting
        max_retries=2
    )

    # Create processor stage
    processor = ResponseProcessor(name="ResponseProcessor")

    # Create pipeline
    pipeline = PipelineRunner([fetcher, processor])

    # Test URLs (using httpbin.org for testing)
    test_requests = [
        {"url": "https://httpbin.org/get", "method": "GET"},
        {"url": "https://httpbin.org/status/200", "method": "GET"},
        {"url": "https://httpbin.org/delay/1", "method": "GET"},  # 1 second delay
    ]

    input_messages = [create_data_message(req) for req in test_requests]

    print("Fetching data from test endpoints...")
    print("Pipeline: HTTP Fetch -> Response Processing")
    print()

    try:
        results = pipeline.run_pipeline(input_messages, timeout=30.0)

        print(f"Pipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

        if results.get("errors"):
            print(f"Errors: {len(results['errors'])}")

    except Exception as e:
        print(f"Demo failed: {e}")


def demo_rate_limiting() -> None:
    """Demonstrate rate limiting behavior."""
    print("\n=== Rate Limiting Demo ===")

    # Create fetcher with strict rate limiting
    fetcher = HttpFetcherStage(
        name="RateLimitedFetcher",
        requests_per_second=1.0,  # 1 request per second
        max_retries=0  # No retries for timing demo
    )

    processor = ResponseProcessor(name="RateProcessor")
    pipeline = PipelineRunner([fetcher, processor])

    # Multiple requests to test rate limiting
    test_requests = [
        {"url": "https://httpbin.org/get", "params": {"req": i}}
        for i in range(5)
    ]

    input_messages = [create_data_message(req) for req in test_requests]

    print("Testing rate limiting: 1 request/second...")
    print("Making 5 requests, should take ~5 seconds due to rate limiting")
    print()

    import time
    start_time = time.time()
    try:
        results = pipeline.run_pipeline(input_messages, timeout=30.0)
        end_time = time.time()

        print(".2f"        print(".2f"        print(f"Success: {results['success']}")

        if results['success']:
            expected_time = 5.0  # 5 requests at 1 req/sec
            print(".2f"
    except Exception as e:
        print(f"Demo failed: {e}")


def run_basic_demos() -> None:
    """Run all basic HTTP fetcher demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running Basic HTTP Fetcher Demonstrations")
    print("=" * 40)

    try:
        demo_basic_http_fetch()
        demo_rate_limiting()

        print("\n" + "=" * 40)
        print("Basic demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run basic demonstrations when executed directly."""
    run_basic_demos()

