"""
Advanced HTTP fetcher demonstrations.

This module contains advanced demonstrations including batch processing,
error handling, and custom configurations.
"""

import logging
from typing import List, Any

from ..pipeline_core.message import create_data_message
from ..pipeline_core.runner import PipelineRunner
from .fetcher_stage import HttpFetcherStage, BatchHttpFetcherStage
from ..pipeline_core.stage_types import TransformStage


def demo_batch_fetching() -> None:
    """Demonstrate batch HTTP fetching."""
    print("=== Batch HTTP Fetch Demo ===")

    # Create batch fetcher
    batch_fetcher = BatchHttpFetcherStage(
        name="BatchFetcher",
        max_concurrent=3,
        requests_per_second=5.0,
        max_retries=1
    )

    # Create processor
    processor = TransformStage("BatchProcessor")

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

    processor = TransformStage(name="ErrorProcessor")
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

    processor = TransformStage(name="AuthProcessor")
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


def run_advanced_demos() -> None:
    """Run all advanced HTTP fetcher demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running Advanced HTTP Fetcher Demonstrations")
    print("=" * 45)

    try:
        demo_batch_fetching()
        demo_error_handling()
        demo_custom_headers_and_auth()

        print("\n" + "=" * 45)
        print("Advanced demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run advanced demonstrations when executed directly."""
    run_advanced_demos()

