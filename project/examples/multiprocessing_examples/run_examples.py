#!/usr/bin/env python3
"""
Script to run multiprocessing examples.

Usage:
    python run_examples.py                    # Run all examples
    python run_examples.py basic             # Run basic process examples
    python run_examples.py pool              # Run process pool examples
    python run_examples.py shared            # Run shared memory examples
    python run_examples.py queues            # Run queues and pipes examples
    python run_examples.py sync              # Run synchronization examples
    python run_examples.py advanced          # Run advanced patterns examples
    python run_examples.py demo              # Run comprehensive demo
"""

import sys
import os
import multiprocessing

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from basic_processes import BasicProcessExample
from process_pool import ProcessPoolExample
from shared_memory import SharedMemoryExample
from queues_pipes import QueuePipeExample
from synchronization import SynchronizationExample
from advanced_patterns import AdvancedPatternsExample
from multiprocessing_demo import MultiprocessingDemo


def run_basic_examples() -> None:
    """Run basic process examples."""
    print("Running Basic Process Examples...")
    example = BasicProcessExample()
    example.basic_process_creation()
    example.process_properties()
    example.daemon_processes()
    example.process_termination()
    example.parallel_computation()


def run_pool_examples() -> None:
    """Run process pool examples."""
    print("Running Process Pool Examples...")
    example = ProcessPoolExample()
    example.process_pool_executor_basic()
    example.process_pool_executor_map()
    example.process_pool_executor_async()
    example.multiprocessing_pool_basic()
    example.multiprocessing_pool_advanced()
    example.pool_resource_management()
    example.error_handling_in_pools()


def run_shared_memory_examples() -> None:
    """Run shared memory examples."""
    print("Running Shared Memory Examples...")
    example = SharedMemoryExample()
    example.shared_value_example()
    example.shared_array_example()
    example.synchronization_primitives()
    example.event_example()
    example.condition_example()
    example.manager_example()
    example.atomic_operations()


def run_queues_examples() -> None:
    """Run queues and pipes examples."""
    print("Running Queues and Pipes Examples...")
    example = QueuePipeExample()
    example.basic_queue_example()
    example.multiple_producers_consumers()
    example.joinable_queue_example()
    example.priority_queue_example()
    example.pipe_example()
    example.duplex_pipe_example()
    example.queue_timeout_example()
    example.message_passing_patterns()


def run_synchronization_examples() -> None:
    """Run synchronization examples."""
    print("Running Synchronization Examples...")
    example = SynchronizationExample()
    example.lock_vs_rlock()
    example.semaphore_patterns()
    example.event_coordination()
    example.condition_example()
    example.barrier_synchronization()
    example.reader_writer_problem()
    example.deadlock_prevention()
    example.synchronization_best_practices()


def run_advanced_examples() -> None:
    """Run advanced patterns examples."""
    print("Running Advanced Patterns Examples...")
    example = AdvancedPatternsExample()
    example.custom_worker_initialization()
    example.map_reduce_pattern()
    example.pipeline_processing()
    example.work_stealing_pool()
    example.process_monitoring_health_checks()
    example.graceful_shutdown_patterns()
    example.resource_management_cleanup()


def run_demo() -> None:
    """Run comprehensive demo."""
    print("Running Comprehensive Multiprocessing Demo...")
    demo = MultiprocessingDemo(num_workers=4)
    demo.benchmark_approaches()
    results = demo.run_complete_pipeline(dataset_size=2000)
    print(f"Demo completed! Processed {results.get('total_processed', 0)} items")


def run_all_examples() -> None:
    """Run all examples."""
    print("Running All Multiprocessing Examples")
    print("=" * 50)

    try:
        run_basic_examples()
        print("\n" + "="*50 + "\n")

        run_pool_examples()
        print("\n" + "="*50 + "\n")

        run_shared_memory_examples()
        print("\n" + "="*50 + "\n")

        run_queues_examples()
        print("\n" + "="*50 + "\n")

        run_synchronization_examples()
        print("\n" + "="*50 + "\n")

        run_advanced_examples()
        print("\n" + "="*50 + "\n")

        run_demo()

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

        # Set start method for cross-platform compatibility
        if os.name == 'posix':
            multiprocessing.set_start_method('fork', force=True)
        else:
            multiprocessing.set_start_method('spawn', force=True)

        if example_type == 'basic':
            run_basic_examples()
        elif example_type == 'pool':
            run_pool_examples()
        elif example_type == 'shared':
            run_shared_memory_examples()
        elif example_type == 'queues':
            run_queues_examples()
        elif example_type == 'sync':
            run_synchronization_examples()
        elif example_type == 'advanced':
            run_advanced_examples()
        elif example_type == 'demo':
            run_demo()
        else:
            print(f"Unknown example type: {example_type}")
            print("Available types: basic, pool, shared, queues, sync, advanced, demo")
    else:
        run_all_examples()


if __name__ == "__main__":
    main()
