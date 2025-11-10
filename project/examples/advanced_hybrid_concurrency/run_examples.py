"""
Run Examples for Advanced Hybrid Concurrency.

This script demonstrates all the advanced hybrid concurrency patterns
including distributed systems, actor models, reactive programming,
custom primitives, performance profiling, and more.
"""

import asyncio
import sys
import logging
from typing import List, Optional


def run_advanced_sync():
    """Run advanced synchronization patterns example."""
    print("🔒 Running Advanced Synchronization Patterns")
    print("=" * 50)

    try:
        from .advanced_sync import demonstrate_distributed_lock, demonstrate_transactional_memory, demonstrate_lock_free_queue
        demonstrate_distributed_lock()
        demonstrate_transactional_memory()
        demonstrate_lock_free_queue()
    except Exception as e:
        print(f"❌ Advanced sync demo failed: {e}")


def run_distributed_concurrency():
    """Run distributed concurrency patterns example."""
    print("🌐 Running Distributed Concurrency Patterns")
    print("=" * 50)

    try:
        from .distributed_concurrency import (
            demonstrate_celery_executor,
            demonstrate_dask_executor,
            demonstrate_ray_executor,
            demonstrate_kubernetes_executor,
            demonstrate_service_mesh
        )

        asyncio.run(demonstrate_celery_executor())
        asyncio.run(demonstrate_dask_executor())
        asyncio.run(demonstrate_ray_executor())
        asyncio.run(demonstrate_kubernetes_executor())
        asyncio.run(demonstrate_service_mesh())

    except Exception as e:
        print(f"❌ Distributed concurrency demo failed: {e}")


def run_actor_model():
    """Run actor model patterns example."""
    print("🎭 Running Actor Model Patterns")
    print("=" * 35)

    try:
        from .actor_model import demonstrate_actor_system
        demonstrate_actor_system()
    except Exception as e:
        print(f"❌ Actor model demo failed: {e}")


def run_reactive_programming():
    """Run reactive programming patterns example."""
    print("⚡ Running Reactive Programming Patterns")
    print("=" * 45)

    try:
        from .reactive_programming import demonstrate_reactive_patterns
        asyncio.run(demonstrate_reactive_patterns())
    except Exception as e:
        print(f"❌ Reactive programming demo failed: {e}")


def run_custom_primitives():
    """Run custom concurrency primitives example."""
    print("🎯 Running Custom Concurrency Primitives")
    print("=" * 45)

    try:
        from .custom_primitives import (
            demonstrate_priority_queue,
            demonstrate_adaptive_rate_limiter,
            demonstrate_smart_circuit_breaker
        )

        demonstrate_priority_queue()
        demonstrate_adaptive_rate_limiter()
        demonstrate_smart_circuit_breaker()

    except Exception as e:
        print(f"❌ Custom primitives demo failed: {e}")


def run_performance_profiling():
    """Run performance profiling tools example."""
    print("📊 Running Performance Profiling Tools")
    print("=" * 42)

    try:
        from .performance_profiling import demonstrate_performance_profiling
        asyncio.run(demonstrate_performance_profiling())
    except Exception as e:
        print(f"❌ Performance profiling demo failed: {e}")


def run_config_driven():
    """Run configuration-driven concurrency example."""
    print("⚙️  Running Configuration-Driven Concurrency")
    print("=" * 47)

    try:
        from .config_driven import demonstrate_adaptive_executor, demonstrate_runtime_switcher

        asyncio.run(demonstrate_adaptive_executor())
        asyncio.run(demonstrate_runtime_switcher())

    except Exception as e:
        print(f"❌ Config-driven demo failed: {e}")


def run_container_aware():
    """Run container-aware concurrency example."""
    print("🐳 Running Container-Aware Concurrency")
    print("=" * 40)

    try:
        from .container_aware import demonstrate_container_patterns
        asyncio.run(demonstrate_container_patterns())
    except Exception as e:
        print(f"❌ Container-aware demo failed: {e}")


def run_ml_specific():
    """Run ML-specific concurrency patterns example."""
    print("🤖 Running ML-Specific Concurrency Patterns")
    print("=" * 46)

    try:
        from .ml_specific import demonstrate_ml_patterns
        asyncio.run(demonstrate_ml_patterns())
    except Exception as e:
        print(f"❌ ML-specific demo failed: {e}")


def run_all_advanced():
    """Run all advanced hybrid concurrency examples."""
    print("🚀 Running ALL Advanced Hybrid Concurrency Examples")
    print("=" * 60)

    examples = [
        ("Advanced Synchronization", run_advanced_sync),
        ("Distributed Concurrency", run_distributed_concurrency),
        ("Actor Model", run_actor_model),
        ("Reactive Programming", run_reactive_programming),
        ("Custom Primitives", run_custom_primitives),
        ("Performance Profiling", run_performance_profiling),
        ("Config-Driven", run_config_driven),
        ("Container-Aware", run_container_aware),
        ("ML-Specific", run_ml_specific),
    ]

    for name, func in examples:
        try:
            print(f"\n{'='*20} {name} {'='*20}")
            func()
            print(f"✅ {name} completed successfully")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            continue

    print(f"\n🎉 ALL ADVANCED HYBRID CONCURRENCY EXAMPLES COMPLETED!")
    print("=" * 60)
    print("Advanced patterns now available:")
    print("• Distributed locks, transactional memory, lock-free structures")
    print("• Celery, Dask, Ray distributed execution")
    print("• Actor model with message passing")
    print("• Reactive streams with backpressure")
    print("• Custom queues, rate limiters, circuit breakers")
    print("• Performance profiling and monitoring")
    print("• Runtime configuration switching")
    print("• Container-aware and Kubernetes integration")
    print("• ML-specific GPU/TPU concurrency patterns")
    print()
    print("These patterns extend your hybrid concurrency capabilities")
    print("beyond basic AsyncIO + Threading + Multiprocessing combinations! 🎯")


def show_menu():
    """Show the advanced examples menu."""
    print("🔬 Advanced Hybrid Concurrency Patterns")
    print("=" * 45)
    print("1. Advanced Synchronization Patterns")
    print("2. Distributed Concurrency (Celery/Dask/Ray)")
    print("3. Actor Model Patterns")
    print("4. Reactive Programming Patterns")
    print("5. Custom Concurrency Primitives")
    print("6. Performance Profiling Tools")
    print("7. Configuration-Driven Concurrency")
    print("8. Container-Aware Concurrency")
    print("9. ML-Specific Concurrency Patterns")
    print("10. Run All Advanced Examples")
    print("11. Exit")
    print()


def main():
    """Main entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) > 1:
        # Command line mode
        example_name = sys.argv[1].lower()

        examples = {
            "sync": run_advanced_sync,
            "distributed": run_distributed_concurrency,
            "actor": run_actor_model,
            "reactive": run_reactive_programming,
            "primitives": run_custom_primitives,
            "profiling": run_performance_profiling,
            "config": run_config_driven,
            "container": run_container_aware,
            "ml": run_ml_specific,
            "all": run_all_advanced,
        }

        if example_name in examples:
            examples[example_name]()
        else:
            print(f"Unknown example: {example_name}")
            print("Available examples:", list(examples.keys()))
            sys.exit(1)
    else:
        # Interactive mode
        while True:
            show_menu()
            try:
                choice = input("Select an advanced example (1-11): ").strip()

                examples = {
                    "1": run_advanced_sync,
                    "2": run_distributed_concurrency,
                    "3": run_actor_model,
                    "4": run_reactive_programming,
                    "5": run_custom_primitives,
                    "6": run_performance_profiling,
                    "7": run_config_driven,
                    "8": run_container_aware,
                    "9": run_ml_specific,
                    "10": run_all_advanced,
                }

                if choice in examples:
                    examples[choice]()
                elif choice == "11":
                    print("Goodbye! 👋")
                    break
                else:
                    print("Invalid choice. Please select 1-11.")

                input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"Error: {e}")
                input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
