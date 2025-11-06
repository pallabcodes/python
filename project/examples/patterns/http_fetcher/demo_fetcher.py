"""
Demonstrations of HTTP Fetcher functionality.

This module provides practical examples of using the HTTP fetcher
stage in pipelines with various scenarios and configurations.
"""

import time
import logging
from typing import List, Any

from ..pipeline_core.message import create_data_message
from ..pipeline_core.runner import PipelineRunner
from .fetcher_stage import HttpFetcherStage, BatchHttpFetcherStage
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
    from ..pipeline_core.runner import PipelineRunner
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


def demo_batch_fetching() -> None:
    """Demonstrate batch HTTP fetching."""
    print("\n=== Batch HTTP Fetch Demo ===")

    # Create batch fetcher
    batch_fetcher = BatchHttpFetcherStage(
        name="BatchFetcher",
        max_concurrent=3,
        requests_per_second=5.0,
        max_retries=1
    )

    # Create processor
    processor = ResponseProcessor(name="BatchProcessor")

    # Create pipeline
    pipeline = PipelineRunner([batch_fetcher, processor])

    # Create batch of requests
    batch_requests = [
        {"url": "https://httpbin.org/get", "params": {"id": i}}
        for i in range(5)
    ]

    input_messages = [create_data_message(batch_requests)]

    print("Fetching batch of 5 requests concurrently...")
    print("Max concurrent: 3, Rate limit: 5 req/sec")
    print()

    try:
        results = pipeline.run_pipeline(input_messages, timeout=30.0)

        print(f"Batch pipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

    except Exception as e:
        print(f"Demo failed: {e}")


def demo_error_handling() -> None:
    """Demonstrate error handling and retries."""
    print("\n=== Error Handling Demo ===")

    # Create fetcher with retry configuration
    fetcher = HttpFetcherStage(
        name="ResilientFetcher",
        requests_per_second=1.0,  # Slow for demo
        max_retries=3
    )

    processor = ResponseProcessor(name="ErrorProcessor")
    pipeline = PipelineRunner([fetcher, processor])

    # Mix of good and bad requests
    test_requests = [
        {"url": "https://httpbin.org/get", "method": "GET"},  # Should work
        {"url": "https://httpbin.org/status/500", "method": "GET"},  # Server error
        {"url": "https://httpbin.org/status/429", "method": "GET"},  # Rate limited
        {"url": "https://invalid-domain-that-does-not-exist.com", "method": "GET"},  # DNS error
    ]

    input_messages = [create_data_message(req) for req in test_requests]

    print("Testing error handling with various failure scenarios...")
    print("Requests include: success, 500 error, 429 rate limit, DNS failure")
    print("Retry policy: 3 attempts with exponential backoff")
    print()

    try:
        results = pipeline.run_pipeline(input_messages, timeout=60.0)

        print(f"Error handling demo completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

        # Show fetcher stats
        fetcher_stats = fetcher.get_stats()
        print("
Fetcher Statistics:")
        print(f"  Requests made: {fetcher_stats['requests_made']}")
        print(f"  Successful: {fetcher_stats['requests_successful']}")
        print(f"  Failed: {fetcher_stats['requests_failed']}")
        print(".1f"
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


def demo_custom_headers_and_auth() -> None:
    """Demonstrate custom headers and authentication."""
    print("\n=== Custom Headers & Auth Demo ===")

    # Create fetcher with custom headers
    fetcher = HttpFetcherStage(
        name="AuthFetcher",
        headers={
            "Authorization": "Bearer demo-token",
            "X-API-Key": "demo-key",
            "Accept": "application/json"
        },
        requests_per_second=2.0
    )

    processor = ResponseProcessor(name="AuthProcessor")
    pipeline = PipelineRunner([fetcher, processor])

    # Request with additional headers
    request = {
        "url": "https://httpbin.org/get",
        "headers": {
            "X-Custom-Header": "custom-value",
            "User-Agent": "PipelineFetcher/1.0"
        }
    }

    input_messages = [create_data_message(request)]

    print("Testing custom headers and authentication...")
    print("Headers include: Authorization, API-Key, Custom headers")
    print()

    try:
        results = pipeline.run_pipeline(input_messages, timeout=15.0)

        print(f"Auth demo completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

    except Exception as e:
        print(f"Demo failed: {e}")


def run_all_fetcher_demos() -> None:
    """Run all HTTP fetcher demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running HTTP Fetcher Demonstrations")
    print("=" * 50)

    try:
        demo_basic_http_fetch()
        demo_batch_fetching()
        demo_error_handling()
        demo_rate_limiting()
        demo_custom_headers_and_auth()

        print("\n" + "=" * 50)
        print("All HTTP fetcher demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run demonstrations when executed directly."""
    run_all_fetcher_demos()

