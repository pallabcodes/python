"""
Run examples for Hybrid Concurrency Patterns.

This script demonstrates various hybrid concurrency approaches that combine
multiple concurrency models for complex, real-world applications.
"""

import asyncio
import sys
import logging
from typing import List, Optional


def run_asyncio_threading():
    """Run AsyncIO + Threading hybrid example."""
    print("🔄 Running AsyncIO + Threading Hybrid Example")
    print("=" * 50)

    from .asyncio_threading import demonstrate_asyncio_threading_hybrid
    asyncio.run(demonstrate_asyncio_threading_hybrid())


def run_asyncio_multiprocessing():
    """Run AsyncIO + Multiprocessing hybrid example."""
    print("🔄 Running AsyncIO + Multiprocessing Hybrid Example")
    print("=" * 55)

    from .asyncio_multiprocessing import demonstrate_asyncio_multiprocessing_hybrid
    asyncio.run(demonstrate_asyncio_multiprocessing_hybrid())


def run_threading_multiprocessing():
    """Run Threading + Multiprocessing hybrid example."""
    print("🔄 Running Threading + Multiprocessing Hybrid Example")
    print("=" * 58)

    from .threading_multiprocessing import demonstrate_threading_multiprocessing_hybrid
    demonstrate_threading_multiprocessing_hybrid()


def run_custom_executor():
    """Run Custom Hybrid Executor example."""
    print("🎯 Running Custom Hybrid Executor Example")
    print("=" * 45)

    from .custom_executor import demonstrate_custom_hybrid_executor
    asyncio.run(demonstrate_custom_hybrid_executor())


def run_situation_specific():
    """Run Situation-Specific Processors example."""
    print("🎯 Running Situation-Specific Processors Example")
    print("=" * 50)

    from .situation_specific import demonstrate_situation_specific_processors
    asyncio.run(demonstrate_situation_specific_processors())


def run_real_world_hybrids():
    """Run Real-World Hybrid Applications example."""
    print("🌐 Running Real-World Hybrid Applications Example")
    print("=" * 55)

    from .real_world_hybrids import demonstrate_real_world_hybrids
    asyncio.run(demonstrate_real_world_hybrids())


def run_all_examples():
    """Run all hybrid concurrency examples."""
    print("🚀 Running ALL Hybrid Concurrency Examples")
    print("=" * 50)

    examples = [
        ("AsyncIO + Threading", run_asyncio_threading),
        ("AsyncIO + Multiprocessing", run_asyncio_multiprocessing),
        ("Threading + Multiprocessing", run_threading_multiprocessing),
        ("Custom Executor", run_custom_executor),
        ("Situation-Specific", run_situation_specific),
        ("Real-World Applications", run_real_world_hybrids),
    ]

    for name, func in examples:
        try:
            print(f"\n{'='*20} {name} {'='*20}")
            func()
            print(f"✅ {name} completed successfully")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            continue

    print(f"\n🎉 All hybrid concurrency examples completed!")


def show_menu():
    """Show the examples menu."""
    print("🔄 Hybrid Concurrency Patterns Examples")
    print("=" * 45)
    print("1. AsyncIO + Threading Hybrid")
    print("2. AsyncIO + Multiprocessing Hybrid")
    print("3. Threading + Multiprocessing Hybrid")
    print("4. Custom Hybrid Executor")
    print("5. Situation-Specific Processors")
    print("6. Real-World Hybrid Applications")
    print("7. Run All Examples")
    print("8. Exit")
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
            "asyncio_threading": run_asyncio_threading,
            "asyncio_multiprocessing": run_asyncio_multiprocessing,
            "threading_multiprocessing": run_threading_multiprocessing,
            "custom_executor": run_custom_executor,
            "situation_specific": run_situation_specific,
            "real_world": run_real_world_hybrids,
            "all": run_all_examples,
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
                choice = input("Select an example (1-8): ").strip()

                if choice == "1":
                    run_asyncio_threading()
                elif choice == "2":
                    run_asyncio_multiprocessing()
                elif choice == "3":
                    run_threading_multiprocessing()
                elif choice == "4":
                    run_custom_executor()
                elif choice == "5":
                    run_situation_specific()
                elif choice == "6":
                    run_real_world_hybrids()
                elif choice == "7":
                    run_all_examples()
                elif choice == "8":
                    print("Goodbye! 👋")
                    break
                else:
                    print("Invalid choice. Please select 1-8.")

                input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"Error: {e}")
                input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
