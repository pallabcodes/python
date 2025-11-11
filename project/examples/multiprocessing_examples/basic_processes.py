"""
Basic multiprocessing examples demonstrating process creation and management.

This module covers:
- Creating and starting processes
- Process termination and joining
- Process identification
- Daemon processes
- Process naming and identification
"""

import multiprocessing
import os
import time
from typing import Any, Optional


class BasicProcessExample:
    """
    Basic multiprocessing examples for process creation and management.
    """

    @staticmethod
    def worker_function(name: str, delay: float = 1.0) -> None:
        """
        A simple worker function that simulates some work.

        Args:
            name: Worker identifier
            delay: Work duration in seconds
        """
        print(f"Worker {name} (PID: {os.getpid()}) starting work...")
        time.sleep(delay)
        print(f"Worker {name} (PID: {os.getpid()}) finished work!")

    @staticmethod
    def cpu_intensive_task(n: int) -> int:
        """
        CPU-intensive task for demonstrating parallel computation.

        Args:
            n: Input number for computation

        Returns:
            Result of computation
        """
        result = 0
        for i in range(n):
            result += i ** 2
        return result

    def basic_process_creation(self) -> None:
        """Demonstrate basic process creation and management."""
        print("=== Basic Process Creation ===")

        # Create multiple processes
        processes = []
        for i in range(3):
            # Create process with target function and arguments
            process = multiprocessing.Process(
                target=self.worker_function,
                args=(f"Process-{i+1}", i + 1),
                name=f"Worker-{i+1}"  # Optional process name
            )
            processes.append(process)

        print(f"Created {len(processes)} processes")

        # Start all processes
        for process in processes:
            print(f"Starting {process.name}...")
            process.start()

        # Wait for all processes to complete
        for process in processes:
            process.join()
            print(f"{process.name} finished with exit code: {process.exitcode}")

        print("All processes completed!\n")

    def process_properties(self) -> None:
        """Demonstrate process properties and identification."""
        print("=== Process Properties ===")

        def process_info_worker(info: str) -> None:
            """Worker that displays process information."""
            print(f"{info}:")
            print(f"  PID: {os.getpid()}")
            print(f"  Parent PID: {os.getppid()}")
            print(f"  Process Name: {multiprocessing.current_process().name}")
            print(f"  Is alive: {multiprocessing.current_process().is_alive()}")
            time.sleep(0.5)

        # Create process
        process = multiprocessing.Process(
            target=process_info_worker,
            args=("Child Process",),
            name="InfoProcess"
        )

        print("Main Process:")
        print(f"  PID: {os.getpid()}")
        print(f"  Process Name: {multiprocessing.current_process().name}")
        print(f"  CPU Count: {multiprocessing.cpu_count()}")

        process.start()
        process.join()
        print()

    def daemon_processes(self) -> None:
        """Demonstrate daemon processes."""
        print("=== Daemon Processes ===")

        def daemon_worker() -> None:
            """A daemon worker that runs in the background."""
            while True:
                print(f"Daemon worker (PID: {os.getpid()}) is running...")
                time.sleep(1)

        def regular_worker() -> None:
            """A regular worker that exits after some time."""
            for i in range(3):
                print(f"Regular worker (PID: {os.getpid()}): iteration {i+1}")
                time.sleep(1)
            print("Regular worker exiting...")

        # Create daemon process
        daemon_process = multiprocessing.Process(
            target=daemon_worker,
            name="DaemonWorker",
            daemon=True  # This makes it a daemon process
        )

        # Create regular process
        regular_process = multiprocessing.Process(
            target=regular_worker,
            name="RegularWorker"
        )

        print("Starting daemon and regular processes...")
        daemon_process.start()
        regular_process.start()

        # Wait for regular process to complete
        regular_process.join()
        print("Regular process completed. Daemon will be terminated automatically.")

        # Note: Daemon process will be terminated when main process exits
        print()

    def process_termination(self) -> None:
        """Demonstrate process termination."""
        print("=== Process Termination ===")

        def long_running_worker() -> None:
            """A worker that runs for a long time."""
            for i in range(10):
                print(f"Worker (PID: {os.getpid()}): {i+1}/10")
                time.sleep(1)

        process = multiprocessing.Process(
            target=long_running_worker,
            name="LongRunningWorker"
        )

        process.start()

        # Let it run for a few seconds
        time.sleep(3)

        # Terminate the process
        print("Terminating process...")
        process.terminate()

        # Wait for termination
        process.join(timeout=5)

        if process.is_alive():
            print("Process did not terminate gracefully, killing...")
            process.kill()
            process.join()

        print(f"Process terminated with exit code: {process.exitcode}\n")

    def parallel_computation(self) -> None:
        """Demonstrate parallel computation using multiple processes."""
        print("=== Parallel Computation ===")

        # Create tasks
        tasks = [1000000, 2000000, 1500000, 3000000]  # Different workloads

        # Sequential execution
        print("Sequential execution:")
        start_time = time.time()
        results = []
        for task in tasks:
            result = self.cpu_intensive_task(task)
            results.append(result)
        sequential_time = time.time() - start_time
        print(".2f")

        # Parallel execution
        print("Parallel execution:")
        start_time = time.time()

        # Create processes
        processes = []
        result_queue = multiprocessing.Queue()

        def worker_with_queue(task: int, queue: multiprocessing.Queue) -> None:
            """Worker that puts result in queue."""
            result = self.cpu_intensive_task(task)
            queue.put((task, result))

        # Start processes
        for task in tasks:
            process = multiprocessing.Process(
                target=worker_with_queue,
                args=(task, result_queue)
            )
            processes.append(process)
            process.start()

        # Collect results
        parallel_results = []
        for _ in processes:
            task, result = result_queue.get()
            parallel_results.append(result)

        # Wait for all processes
        for process in processes:
            process.join()

        parallel_time = time.time() - start_time
        print(".2f")
        print(".1f")
        print()


def main() -> None:
    """Run all basic process examples."""
    print("Multiprocessing Basic Examples")
    print("=" * 40)

    example = BasicProcessExample()

    example.basic_process_creation()
    example.process_properties()
    example.daemon_processes()
    example.process_termination()
    example.parallel_computation()

    print("All basic examples completed!")


if __name__ == "__main__":
    # Set start method for macOS/Windows compatibility
    if os.name == 'posix':
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)

    main()

"""
🎯 Key Multiprocessing Concepts Demonstrated:
Process Creation - multiprocessing.Process() with target functions
Process Lifecycle - start(), join(), exit codes
Process Identification - PIDs, parent PIDs, process names
Daemon Processes - Background processes that auto-terminate
Process Termination - terminate() and kill() methods
Parallel Computation - Speedup from running CPU tasks in parallel
Inter-Process Communication - Using queues to share results
Cross-Platform Compatibility - Different start methods for different OSes
🔑 Why Multiprocessing Matters:
True Parallelism - Bypasses GIL limitation for CPU-bound tasks
Multiple Cores - Utilizes all available CPU cores
Isolation - Each process has its own memory space
Fault Tolerance - Process crashes don't affect others
Scalability - Can run on multiple machines (distributed computing)
⚠️ Important Notes:
Resource Intensive - Each process has overhead (memory, startup time)
IPC Complexity - Communication between processes is more complex than threads
Pickle Requirements - Functions must be picklable to run in subprocesses
Platform Differences - Different OSes have different process models
This file provides the foundation for understanding multiprocessing in Python!
"""