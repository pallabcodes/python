#!/usr/bin/env python3
"""
Script to run asyncio examples.

Usage:
    python run_examples.py                    # Run basic examples only
    python run_examples.py basic             # Run basic asyncio examples
    python run_examples.py context           # Run async context managers
    python run_examples.py generators        # Run async generators
    python run_examples.py patterns          # Run concurrency patterns
    python run_examples.py io                # Run async I/O examples
    python run_examples.py primitives        # Run async primitives
    python run_examples.py tasks             # Run task management
    python run_examples.py web               # Run web examples (requires aiohttp)
    python run_examples.py demo              # Run comprehensive demo
    python run_examples.py benchmark         # Run performance benchmark
"""

import asyncio
import sys
from typing import Optional

# Add current directory to path
sys.path.insert(0, __file__.rsplit('/', 1)[0])

from basic_asyncio import BasicAsyncioExample
from async_context_managers import AsyncContextManagerExample
from async_generators import AsyncGeneratorExample
from concurrency_patterns import ConcurrencyPatternsExample
from async_io import AsyncIOExample
from async_primitives import AsyncPrimitivesExample
from task_management import TaskManagementExample
from web_asyncio import WebAsyncioExample
from asyncio_demo import AsyncioDemo, benchmark_asyncio_performance


async def run_basic_examples() -> None:
    """Run basic asyncio examples."""
    print("Running Basic Asyncio Examples...")
    example = BasicAsyncioExample()
    await example.basic_coroutine_execution()
    await example.concurrent_execution()
    await example.task_vs_coroutine()
    await example.future_operations()
    await example.exception_handling()
    await example.event_loop_info()
    await example.nested_coroutines()
    await example.performance_comparison()


async def run_context_manager_examples() -> None:
    """Run async context manager examples."""
    print("Running Async Context Manager Examples...")
    example = AsyncContextManagerExample()
    await example.basic_async_context_manager()
    await example.resource_management()
    await example.exception_handling_in_context()
    await example.nested_context_managers()
    await example.multiple_resources()
    await example.stacking_with_timer()
    await example.database_example()
    await example.lock_example()
    await example.conditional_resources()
    await example.context_manager_stacking()


async def run_generator_examples() -> None:
    """Run async generator examples."""
    print("Running Async Generator Examples...")
    example = AsyncGeneratorExample()
    await example.basic_async_iteration()
    await example.exception_handling_example()
    await example.streaming_consumer()
    await example.aiter_example()
    await example.cleanup_example()
    await example.concurrent_async_generators()
    await example.nested_iteration_example()
    await example.timeout_example()
    await example.real_world_processing()
    await example.pipeline_example()


async def run_patterns_examples() -> None:
    """Run concurrency patterns examples."""
    print("Running Concurrency Patterns Examples...")
    example = ConcurrencyPatternsExample()
    await example.producer_consumer_queue()
    await example.data_pipeline_pattern()
    await example.pub_sub_pattern()
    await example.circuit_breaker_pattern()
    await example.retry_with_backoff_pattern()
    await example.rate_limiting_pattern()
    await example.request_batching_pattern()
    await example.fan_out_fan_in_pattern()


async def run_io_examples() -> None:
    """Run async I/O examples."""
    print("Running Async I/O Examples...")
    example = AsyncIOExample()
    await example.file_operations_example()
    await example.concurrent_file_processing()
    await example.network_operations_example()
    await example.async_http_client_example()
    await example.stream_processing_example()
    await example.concurrent_io_operations()
    await example.error_handling_in_async_io()
    await example.async_file_copy_example()
    await example.batch_io_operations()


async def run_primitives_examples() -> None:
    """Run async primitives examples."""
    print("Running Async Primitives Examples...")
    example = AsyncPrimitivesExample()
    await example.lock_basic_example()
    await example.lock_reentrance_issue()
    await example.semaphore_example()
    await example.bounded_semaphore_example()
    await example.event_coordination()
    await example.event_barrier_simulation()
    await example.condition_variables()
    await example.reader_writer_lock()
    await example.deadlock_prevention()
    await example.lock_performance_comparison()
    await example.synchronization_best_practices()


async def run_task_examples() -> None:
    """Run task management examples."""
    print("Running Task Management Examples...")
    example = TaskManagementExample()
    await example.basic_task_creation()
    await example.task_introspection()
    await example.task_cancellation()
    await example.timeout_with_cancellation()
    await example.task_groups_structured_concurrency()
    await example.exception_handling_in_tasks()
    await example.task_prioritization_simulation()
    await example.task_monitoring_and_metrics()
    await example.task_cleanup_and_resources()


async def run_web_examples() -> None:
    """Run web asyncio examples."""
    print("Running Web Asyncio Examples...")
    example = WebAsyncioExample()
    # Note: These run servers, so we only run the client examples
    await example.async_http_client_operations()
    await example.concurrent_request_simulation()


async def run_demo() -> None:
    """Run comprehensive demo."""
    print("Running Comprehensive Asyncio Demo...")
    demo = AsyncioDemo()
    await demo.run_demo()


async def run_benchmark() -> None:
    """Run performance benchmark."""
    print("Running Asyncio Performance Benchmark...")
    await benchmark_asyncio_performance()


async def run_all_examples() -> None:
    """Run all examples (basic set only, to avoid server examples)."""
    print("Running All Asyncio Examples")
    print("=" * 30)

    try:
        await run_basic_examples()
        print("\n" + "="*30 + "\n")

        await run_context_manager_examples()
        print("\n" + "="*30 + "\n")

        await run_generator_examples()
        print("\n" + "="*30 + "\n")

        await run_primitives_examples()
        print("\n" + "="*30 + "\n")

        await run_task_examples()
        print("\n" + "="*30 + "\n")

        await run_patterns_examples()
        print("\n" + "="*30 + "\n")

        await run_io_examples()
        print("\n" + "="*30 + "\n")

        # Skip web examples and demo in full run (they run servers)
        print("Note: Web server examples and full demo not run in batch mode.")
        print("Use 'python run_examples.py web' or 'python run_examples.py demo' separately.")

    except KeyboardInterrupt:
        print("\nExecution interrupted by user")
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1:
        example_type = sys.argv[1].lower()

        if example_type == 'basic':
            asyncio.run(run_basic_examples())
        elif example_type == 'context':
            asyncio.run(run_context_manager_examples())
        elif example_type == 'generators':
            asyncio.run(run_generator_examples())
        elif example_type == 'patterns':
            asyncio.run(run_patterns_examples())
        elif example_type == 'io':
            asyncio.run(run_io_examples())
        elif example_type == 'primitives':
            asyncio.run(run_primitives_examples())
        elif example_type == 'tasks':
            asyncio.run(run_task_examples())
        elif example_type == 'web':
            asyncio.run(run_web_examples())
        elif example_type == 'demo':
            asyncio.run(run_demo())
        elif example_type == 'benchmark':
            asyncio.run(run_benchmark())
        else:
            print(f"Unknown example type: {example_type}")
            print("Available types: basic, context, generators, patterns, io, primitives, tasks, web, demo, benchmark")
    else:
        asyncio.run(run_all_examples())


if __name__ == "__main__":
    main()
