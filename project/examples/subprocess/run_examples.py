#!/usr/bin/env python3
"""
Run script for subprocess examples.

Usage:
    python run_examples.py [example_type]

Available example types:
    basic      - Basic subprocess usage
    advanced   - Advanced Popen and process control
    comm       - Communication patterns
    error      - Error handling
    security   - Security best practices
    real       - Real-world applications
    all        - Run all examples
"""

import sys
import time
from typing import List


def run_basic_examples() -> None:
    """Run basic subprocess examples."""
    print("Running Basic Subprocess Examples...")
    try:
        from .basic_subprocess import main as basic_main
        basic_main()
    except ImportError:
        print("Basic subprocess module not found")


def run_advanced_examples() -> None:
    """Run advanced subprocess examples."""
    print("Running Advanced Subprocess Examples...")
    try:
        from .advanced_subprocess import main as advanced_main
        advanced_main()
    except ImportError:
        print("Advanced subprocess module not found")


def run_communication_examples() -> None:
    """Run communication examples."""
    print("Running Communication Examples...")
    try:
        from .communication import main as comm_main
        comm_main()
    except ImportError:
        print("Communication module not found")


def run_error_handling_examples() -> None:
    """Run error handling examples."""
    print("Running Error Handling Examples...")
    try:
        from .error_handling import main as error_main
        error_main()
    except ImportError:
        print("Error handling module not found")


def run_security_examples() -> None:
    """Run security examples."""
    print("Running Security Examples...")
    try:
        from .security import main as security_main
        security_main()
    except ImportError:
        print("Security module not found")


def run_real_world_examples() -> None:
    """Run real-world examples."""
    print("Running Real-World Examples...")
    try:
        from .real_world_examples import main as real_main
        real_main()
    except ImportError:
        print("Real-world examples module not found")


def run_all_examples() -> None:
    """Run all examples in sequence."""
    print("Running ALL Subprocess Examples")
    print("=" * 40)

    examples = [
        ("Basic", run_basic_examples),
        ("Advanced", run_advanced_examples),
        ("Communication", run_communication_examples),
        ("Error Handling", run_error_handling_examples),
        ("Security", run_security_examples),
        ("Real-World", run_real_world_examples),
    ]

    total_start = time.time()

    for name, func in examples:
        print(f"\\n{'='*20} {name} Examples {'='*20}")
        try:
            start_time = time.time()
            func()
            elapsed = time.time() - start_time
            print(".2f")
        except Exception as e:
            print(f"❌ {name} examples failed: {e}")
            # Continue with other examples

    total_elapsed = time.time() - total_start
    print(f"\\n{'='*40}")
    print(".2f")


def show_help() -> None:
    """Show help information."""
    print(__doc__)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        show_help()
        return

    example_type = sys.argv[1].lower()

    example_map = {
        'basic': run_basic_examples,
        'advanced': run_advanced_examples,
        'comm': run_communication_examples,
        'error': run_error_handling_examples,
        'security': run_security_examples,
        'real': run_real_world_examples,
        'all': run_all_examples,
    }

    if example_type in ['help', '-h', '--help']:
        show_help()
    elif example_type in example_map:
        example_map[example_type]()
    else:
        print(f"Unknown example type: {example_type}")
        print("Available types:", ', '.join(example_map.keys()))
        print("Use 'help' for more information")


if __name__ == "__main__":
    main()
