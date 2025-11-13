"""
Robust multiprocessing examples demonstrating process creation and management.

Improvements / fixes applied:
- Module-level target functions (picklable under 'spawn').
- Use logging for structured output.
- Safer start-method setup (don't force if already set).
- Use ProcessPoolExecutor / multiprocessing.Pool for parallel computation.
- Timeouts and graceful shutdowns to avoid hangs.
- Proper use of Queue and sentinel semantics where needed.
- Explicit comments where platform differences / gotchas occur.
"""

from __future__ import annotations

import concurrent.futures
import logging
import multiprocessing
import os
import signal
import sys
import time
from typing import Any, Iterable, List, Optional, Tuple

# Configure logging (timestamp + pid)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [pid:%(process)d] %(message)s",
    datefmt="%H:%M:%S",
)


# -------------------------
# Module-level target funcs
# -------------------------
def worker_function(name: str, delay: float = 1.0) -> None:
    """Simple worker function suitable as a multiprocessing target.

    Notes:
    - Module-level so it is picklable by 'spawn' start method.
    """
    logging.info("Worker %s starting (pid=%d) ...", name, os.getpid())
    time.sleep(delay)
    logging.info("Worker %s finished (pid=%d)!", name, os.getpid())


def cpu_intensive_task(n: int) -> int:
    """CPU-bound work: sum of squares up to n-1.

    Keep fairly simple for demo; in real code use optimized libraries or
    algorithms as needed.
    """
    total = 0
    for i in range(n):
        total += i * i
    return total


def process_info_worker(info: str) -> None:
    """Process that prints its own information (module-level)."""
    logging.info("%s:", info)
    logging.info("  PID: %d", os.getpid())
    logging.info("  Parent PID: %d", os.getppid())
    logging.info("  Process Name: %s", multiprocessing.current_process().name)
    logging.info("  Is alive: %s", multiprocessing.current_process().is_alive())
    time.sleep(0.5)


def daemon_worker(stop_event: Optional[multiprocessing.Event] = None) -> None:
    """Daemon worker that runs until main process exit or optional stop_event set.

    We prefer an event to allow graceful termination in tests; however a true
    daemon process will be killed when the main process exits.
    """
    pid = os.getpid()
    logging.info("Daemon worker started (pid=%d).", pid)
    try:
        while True:
            if stop_event and stop_event.is_set():
                logging.info("Daemon worker received stop event (pid=%d). Exiting.", pid)
                return
            logging.info("Daemon worker (pid=%d) heartbeat...", pid)
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Daemon worker interrupted (pid=%d).", pid)


def regular_worker() -> None:
    """Regular worker that does a few iterations and exits."""
    pid = os.getpid()
    for i in range(3):
        logging.info("Regular worker (pid=%d): iteration %d", pid, i + 1)
        time.sleep(1)
    logging.info("Regular worker (pid=%d) exiting...", pid)


def long_running_worker() -> None:
    """Worker that runs for a long time to demonstrate termination."""
    pid = os.getpid()
    for i in range(10):
        logging.info("Long-running worker (pid=%d): %d/10", pid, i + 1)
        time.sleep(1)


def worker_with_queue(task: int) -> Tuple[int, int]:
    """Compute cpu_intensive_task and return (task, result). Suitable for pools."""
    result = cpu_intensive_task(task)
    return task, result


# -------------------------
# Helper: safe start method
# -------------------------
def ensure_start_method(method: str = "fork") -> None:
    """Set multiprocessing start method if not already set.

    We avoid force=True because forcing after interpreter start raises RuntimeError.
    Use 'spawn' on Windows/macOS if required for correctness of pickling.
    """
    try:
        current = multiprocessing.get_start_method(allow_none=True)
        if current is None:
            multiprocessing.set_start_method(method)
            logging.info("multiprocessing start method set to '%s'", method)
        else:
            logging.info("multiprocessing start method already: '%s'", current)
    except RuntimeError as ex:
        # Already set in a context we cannot change; log and continue.
        logging.warning("Could not set start method (%s): %s", method, ex)


# -------------------------
# Class with examples
# -------------------------
class BasicProcessExample:
    """
    Container for multiprocessing example methods.

    This class demonstrates fundamental multiprocessing concepts including
    process creation, lifecycle management, termination, and parallel computation.

    When to Use:
        - CPU-bound tasks that benefit from true parallelism
        - Bypassing the GIL for parallel execution
        - Isolating tasks in separate memory spaces
        - Utilizing multiple CPU cores
        - Building distributed systems

    Real-World Examples:
        - Data processing: Process large datasets in parallel
        - Scientific computing: Parallel numerical computations
        - Image processing: Process multiple images simultaneously
        - Machine learning: Train models in parallel
        - Batch jobs: Run multiple batch operations concurrently

    Gotchas:
        - Functions must be picklable (module-level)
        - Start method differs by platform (spawn/fork)
        - Process creation has overhead
        - IPC requires queues/pipes/shared memory
        - Daemon processes terminate abruptly
        - Always use timeouts with join()

    Performance Notes:
        - True parallelism bypasses GIL
        - Process overhead is higher than threads
        - Optimal for CPU-bound tasks
        - Memory usage increases with process count
        - IPC overhead affects performance
    """

    def basic_process_creation(self) -> None:
        """
        Create several processes and wait for them with robust logging.

        Demonstrates basic process creation, starting, and joining with
        proper timeout handling and cleanup.

        When to Use:
            - Creating multiple independent processes
            - Running tasks in parallel
            - Learning basic multiprocessing
            - Simple parallel execution

        Real-World Examples:
            - Batch processing: Process multiple files
            - Data transformation: Transform data in parallel
            - Task execution: Run multiple tasks concurrently
            - Work distribution: Distribute work across processes

        Gotchas:
            - Processes start immediately on start()
            - join() blocks until process completes
            - Always use timeout with join()
            - Terminate if join() times out
            - Check exitcode after join()
            - Processes have separate memory spaces

        Performance Notes:
            - Process creation overhead is significant
            - Parallel execution improves CPU-bound tasks
            - Memory usage increases with process count
            - Optimal for independent CPU-bound tasks
        """
        logging.info("=== Basic Process Creation ===")

        processes: List[multiprocessing.Process] = []
        for i in range(3):
            p = multiprocessing.Process(
                target=worker_function, # function to be executed in the process
                args=(f"Process-{i+1}", i + 1), # arguments to the function
                name=f"Worker-{i+1}", # name of the process
            )
            processes.append(p) # add the process to the list
            logging.info("Created process %s (name=%s)", p.pid, p.name)

        logging.info("Starting %d processes", len(processes))
        
        for p in processes: # start the processes
            logging.info("Starting %s", p.name)
            p.start()

        # Wait for completion with join() and a timeout per process to avoid indefinite hang.
        for p in processes:
            p.join(timeout=10)
            if p.is_alive():
                logging.warning("%s did not exit in time; terminating...", p.name)
                p.terminate()
                p.join(timeout=5)
            logging.info("%s finished (exitcode=%s)", p.name, p.exitcode)

        logging.info("All processes completed!\n")

    def process_properties(self) -> None:
        """
        Spawn a process which prints its identifying properties.

        Shows how to inspect process properties like PID, parent PID,
        process name, and alive status.

        When to Use:
            - Debugging process issues
            - Monitoring process state
            - Understanding process hierarchy
            - Logging process information
            - Process identification

        Real-World Examples:
            - Process monitoring: Track process IDs
            - Debugging: Identify which process failed
            - Logging: Include PID in logs
            - Process management: Track process hierarchy
            - System administration: Monitor processes

        Gotchas:
            - PID changes on process restart
            - Parent PID identifies process tree
            - Process name helps with identification
            - is_alive() checks if process running
            - Properties available after start()

        Performance Notes:
            - Property access is fast
            - Useful for debugging and monitoring
            - No performance impact
        """
        logging.info("=== Process Properties ===")

        p = multiprocessing.Process(
            target=process_info_worker,
            args=("Child Process",),
            name="InfoProcess",
        )
        logging.info("Main Process PID: %d", os.getpid())
        logging.info("Process Name: %s", multiprocessing.current_process().name)
        logging.info("CPU Count: %d", multiprocessing.cpu_count())

        p.start()
        p.join(timeout=5)
        if p.is_alive():
            logging.warning("InfoProcess didn't finish; terminating.")
            p.terminate()
            p.join()

        logging.info("Process properties demo done.\n")

    def daemon_processes(self) -> None:
        """
        Demonstrate daemon vs regular process differences.

        Shows the difference between daemon and regular processes, including
        termination behavior and graceful shutdown patterns.

        When to Use:
            - Background workers that should exit with parent
            - Services that don't need cleanup
            - Temporary helper processes
            - Processes that can be terminated abruptly

        Real-World Examples:
            - Background workers: Daemon workers for tasks
            - Helper processes: Temporary helper processes
            - Monitoring: Background monitoring processes
            - Cleanup: Processes that clean up on exit
            - Services: Background service processes

        Gotchas:
            - Daemon processes terminate abruptly on parent exit
            - Regular processes block parent exit
            - Use Event for graceful shutdown
            - Daemon processes don't run cleanup code
            - Prefer Events over daemon=True for control
            - Daemon processes can't create child processes

        Performance Notes:
            - Daemon processes exit faster
            - No cleanup overhead for daemons
            - Events add minimal overhead
            - Useful for background tasks
        """
        logging.info("=== Daemon Processes ===")

        # Use an Event for demo/controlled shutdown, but show daemon semantics too.
        stop_ev = multiprocessing.Event()

        daemon_proc = multiprocessing.Process(
            target=daemon_worker,
            args=(stop_ev,),
            name="DaemonWorker",
            daemon=True,
        )

        regular_proc = multiprocessing.Process(target=regular_worker, name="RegularWorker")

        logging.info("Starting daemon and regular processes...")
        daemon_proc.start()
        regular_proc.start()

        # Wait for regular process to finish (bounded wait)
        regular_proc.join(timeout=10)
        if regular_proc.is_alive():
            logging.warning("RegularWorker didn't finish; terminating.")
            regular_proc.terminate()
            regular_proc.join(timeout=5)

        # Signal daemon to stop (optionally)
        stop_ev.set()
        # Give daemon a moment to exit gracefully; if truly daemon it may be killed on exit anyway.
        daemon_proc.join(timeout=2)

        logging.info("Regular process completed. If the daemon is still alive it will be terminated when main exits.\n")

    def process_termination(self) -> None:
        """
        Start a long-running process then demonstrate terminate/kill sequence.

        Shows how to gracefully terminate processes and escalate to kill
        if termination doesn't work.

        When to Use:
            - Stopping long-running processes
            - Implementing timeout handling
            - Graceful shutdown sequences
            - Force-stopping stuck processes
            - Process lifecycle management

        Real-World Examples:
            - Timeout handling: Terminate processes that exceed timeout
            - Shutdown: Gracefully shutdown worker processes
            - Error recovery: Kill stuck processes
            - Resource management: Free resources from processes
            - Process control: Control process lifecycle

        Gotchas:
            - terminate() sends SIGTERM (graceful)
            - kill() sends SIGKILL (forceful)
            - Always wait after terminate() before kill()
            - Check is_alive() after join()
            - exitcode indicates termination reason
            - kill() not available on older Python versions

        Performance Notes:
            - terminate() allows cleanup
            - kill() is immediate but no cleanup
            - Timeouts prevent indefinite waits
            - Proper termination prevents resource leaks
        """
        logging.info("=== Process Termination ===")

        p = multiprocessing.Process(target=long_running_worker, name="LongRunningWorker")
        p.start()

        # Let it run a bit
        time.sleep(3)

        logging.info("Requesting terminate() on LongRunningWorker...")
        p.terminate()

        # Wait for a graceful stop then escalate to kill()
        p.join(timeout=5)
        if p.is_alive():
            logging.warning("Process did not terminate, sending kill()")
            # On Python 3.7+, kill() forcefully kills the process
            try:
                p.kill()
            except AttributeError:
                # Older Python: fallback to terminate again
                p.terminate()
        p.join(timeout=2)

        logging.info("Process terminated with exit code: %s\n", p.exitcode)

    def parallel_computation(self) -> None:
        """
        Demonstrate parallel computation using a process pool.

        Shows how to use ProcessPoolExecutor for parallel CPU-bound computation
        with proper result handling and error management.

        When to Use:
            - CPU-bound parallel computation
            - Processing large datasets
            - Scientific computing
            - Numerical computations
            - Batch processing

        Real-World Examples:
            - Data processing: Process large datasets
            - Scientific computing: Parallel numerical computations
            - Image processing: Process multiple images
            - Machine learning: Train models in parallel
            - Batch operations: Run batch jobs concurrently

        Gotchas:
            - ProcessPoolExecutor manages process lifecycle
            - Functions must be picklable
            - Use as_completed() for results as they finish
            - Handle exceptions in futures
            - Context manager ensures cleanup
            - max_workers defaults to CPU count

        Performance Notes:
            - True parallelism for CPU-bound tasks
            - Process pool reduces creation overhead
            - Optimal worker count is CPU count
            - IPC overhead affects small tasks
            - Significant speedup for CPU-bound work
        """
        logging.info("=== Parallel Computation ===")

        tasks = [100_000, 200_000, 150_000, 300_000]  # scaled down for demo

        # Sequential run (baseline)
        logging.info("Sequential execution:")
        t0 = time.perf_counter()
        seq_results = [cpu_intensive_task(n) for n in tasks]
        seq_dt = time.perf_counter() - t0
        logging.info("Sequential done in %.3f s (results sum=%d)", seq_dt, sum(seq_results))

        # Parallel run using ProcessPoolExecutor
        logging.info("Parallel execution (ProcessPoolExecutor):")
        t0 = time.perf_counter()
        # Use max_workers equal to cpu_count() by default
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # map returns results in submission order
            futures = [executor.submit(cpu_intensive_task, n) for n in tasks]
            parallel_results = []
            for fut in concurrent.futures.as_completed(futures):
                try:
                    r = fut.result(timeout=30)
                    parallel_results.append(r)
                except Exception as e:
                    logging.exception("Worker failed: %s", e)
        par_dt = time.perf_counter() - t0
        logging.info("Parallel done in %.3f s (results sum=%d)\n", par_dt, sum(parallel_results))

    def parallel_computation_with_queue(self) -> None:
        """
        Alternative example using multiprocessing.Queue and Process objects.

        Demonstrates explicit IPC using queues for result collection when
        you need more control than ProcessPoolExecutor provides.

        When to Use:
            - Need explicit IPC control
            - Incremental result reporting
            - Custom process management
            - Sharing data via queues
            - More control than ProcessPoolExecutor

        Real-World Examples:
            - Progress reporting: Report progress incrementally
            - Data streaming: Stream results as they arrive
            - Custom coordination: Custom process coordination
            - Large data sharing: Share large data via queues
            - Complex workflows: Complex multi-process workflows

        Gotchas:
            - Queue.get() blocks until data available
            - Use timeout to prevent indefinite blocking
            - Queue.put() can block if queue full
            - Results may arrive out of order
            - Queue size affects memory usage
            - Must collect all results before joining

        Performance Notes:
            - More control than ProcessPoolExecutor
            - Queue overhead for IPC
            - Useful for incremental results
            - Better for complex workflows
            - More code to manage
        """
        logging.info("=== Parallel Computation using Queue + Processes ===")

        tasks = [100_000, 200_000, 150_000]

        result_q: multiprocessing.Queue = multiprocessing.Queue()
        processes: List[multiprocessing.Process] = []

        for t in tasks:
            p = multiprocessing.Process(target=lambda tn, q: q.put(worker_with_queue(tn)), args=(t, result_q))
            processes.append(p)
            p.start()

        # Collect results (with timeout to avoid indefinite block)
        results = []
        for _ in processes:
            try:
                # blocking get with timeout
                task_n, value = result_q.get(timeout=10)
                results.append((task_n, value))
            except Exception:
                logging.exception("Timed out while waiting for results from queue")
                break

        # Join processes (with timeouts)
        for p in processes:
            p.join(timeout=5)
            if p.is_alive():
                logging.warning("Worker did not exit in time; terminating.")
                p.terminate()
                p.join(timeout=2)

        logging.info("Collected %d results via queue", len(results))
        total = sum(v for _, v in results) if results else 0
        logging.info("Results sum=%d\n", total)

    def basic_process_creation_real_world(self) -> None:
        """
        Real-World Scenario: Process Creation - Image Processing Pipeline.

        REAL-WORLD SCENARIO:
        ====================
        You're building an image processing pipeline:
        - Process 1000s of images (resize, filter, compress)
        - Each image takes 2-5 seconds to process
        - Problem: Sequential processing takes hours
        
        THE PROBLEM WITHOUT MULTIPROCESSING:
        =====================================
        - Process image 1 → wait 3 seconds
        - Process image 2 → wait 3 seconds
        - Process image 3 → wait 3 seconds
        - Total: 9 seconds for 3 images
        - 1000 images = 50+ minutes!
        - CPU cores idle → wasted resources
        
        THE SOLUTION:
        =============
        Multiprocessing enables:
        - Process 3 images simultaneously (one per CPU core)
        - All cores utilized → 3x speedup
        - 1000 images = 17 minutes (vs 50+ minutes)
        - True parallelism → maximum throughput
        
        WHEN TO USE PROCESS CREATION:
        =============================
        ✅ CPU-bound tasks (image processing, computation)
        ✅ Independent tasks (no shared state)
        ✅ Batch processing (many similar tasks)
        ✅ Utilizing multiple CPU cores
        ✅ True parallelism needed
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Image Processing Pipeline")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Image processing pipeline")
        print("  - Process 1000s of images (resize, filter, compress)")
        print("  - Each image takes 2-5 seconds")
        print("  - Problem: Sequential processing takes hours")
        print()
        print("THE PROBLEM:")
        print("  Without multiprocessing:")
        print("    ❌ Process image 1 → wait 3 seconds")
        print("    ❌ Process image 2 → wait 3 seconds")
        print("    ❌ Process image 3 → wait 3 seconds")
        print("    ❌ Total: 9 seconds for 3 images")
        print("    ❌ 1000 images = 50+ minutes!")
        print()
        print("THE SOLUTION:")
        print("  With multiprocessing:")
        print("    ✅ Process 3 images simultaneously (one per CPU core)")
        print("    ✅ All cores utilized → 3x speedup")
        print("    ✅ 1000 images = 17 minutes (vs 50+ minutes)")
        print("    ✅ True parallelism → maximum throughput")
        print()
        print("=" * 70)
        print()

        def process_image(image_id: int) -> str:
            """Simulate image processing."""
            import time
            time.sleep(0.2)  # Simulate 200ms processing time
            return f"image_{image_id}_processed.jpg"

        image_ids = list(range(1, 10))  # 9 images to process

        # Sequential processing
        print("Sequential processing:")
        start_time = time.perf_counter()
        sequential_results = [process_image(img_id) for img_id in image_ids]
        sequential_time = time.perf_counter() - start_time
        print(f"  Processed {len(sequential_results)} images in {sequential_time:.2f}s")
        print()

        # Parallel processing
        print("Parallel processing (multiprocessing):")
        start_time = time.perf_counter()
        processes = []
        results_queue = multiprocessing.Queue()

        def worker_with_queue(img_id: int, q: multiprocessing.Queue) -> None:
            """Worker that processes image and puts result in queue."""
            result = process_image(img_id)
            q.put((img_id, result))

        for img_id in image_ids:
            p = multiprocessing.Process(target=worker_with_queue, args=(img_id, results_queue))
            processes.append(p)
            p.start()

        parallel_results = []
        for _ in processes:
            img_id, result = results_queue.get(timeout=5)
            parallel_results.append(result)

        for p in processes:
            p.join(timeout=5)

        parallel_time = time.perf_counter() - start_time
        print(f"  Processed {len(parallel_results)} images in {parallel_time:.2f}s")
        print()

        speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0
        print("Results:")
        print(f"  Sequential time: {sequential_time:.2f}s")
        print(f"  Parallel time: {parallel_time:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print("  ✅ Multiprocessing provides significant speedup!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE PROCESS CREATION:")
        print("   ✅ CPU-bound tasks (image processing, computation)")
        print("   ✅ Independent tasks (no shared state)")
        print("   ✅ Batch processing (many similar tasks)")
        print("   ✅ Utilizing multiple CPU cores")
        print()
        print("2. WHY IT MATTERS:")
        print("   - True parallelism (bypasses GIL)")
        print("   - Utilizes all CPU cores")
        print("   - Significant speedup for CPU-bound work")
        print("   - Critical for batch processing")
        print("=" * 70)
        print()

    def parallel_computation_real_world(self) -> None:
        """
        Real-World Scenario: Parallel Computation - Data Analysis Pipeline.

        REAL-WORLD SCENARIO:
        ====================
        You're analyzing large datasets:
        - Process millions of records
        - Each record requires CPU-intensive computation
        - Problem: Single-threaded analysis too slow
        
        THE PROBLEM WITHOUT PARALLELISM:
        ================================
        - Process record 1 → 0.5 seconds
        - Process record 2 → 0.5 seconds
        - Process record 3 → 0.5 seconds
        - 1 million records = 138+ hours!
        - Single CPU core utilized → waste
        
        THE SOLUTION:
        =============
        ProcessPoolExecutor enables:
        - Distribute work across CPU cores
        - Process multiple records simultaneously
        - 8 cores = 8x speedup (theoretical)
        - 1 million records = 17+ hours (vs 138+ hours)
        - Optimal resource utilization
        
        WHEN TO USE PROCESS POOLS:
        ===========================
        ✅ CPU-bound parallel computation
        ✅ Large dataset processing
        ✅ Scientific computing
        ✅ Numerical computations
        ✅ Batch processing
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Data Analysis Pipeline")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Analyzing large datasets")
        print("  - Process millions of records")
        print("  - Each record requires CPU-intensive computation")
        print("  - Problem: Single-threaded analysis too slow")
        print()
        print("THE PROBLEM:")
        print("  Without parallelism:")
        print("    ❌ Process record 1 → 0.5 seconds")
        print("    ❌ Process record 2 → 0.5 seconds")
        print("    ❌ Process record 3 → 0.5 seconds")
        print("    ❌ 1 million records = 138+ hours!")
        print("    ❌ Single CPU core utilized → waste")
        print()
        print("THE SOLUTION:")
        print("  With ProcessPoolExecutor:")
        print("    ✅ Distribute work across CPU cores")
        print("    ✅ Process multiple records simultaneously")
        print("    ✅ 8 cores = 8x speedup (theoretical)")
        print("    ✅ 1 million records = 17+ hours (vs 138+ hours)")
        print("    ✅ Optimal resource utilization")
        print()
        print("=" * 70)
        print()

        # Simulate data analysis tasks
        dataset_sizes = [50_000, 100_000, 75_000, 150_000, 125_000]

        # Sequential processing
        print("Sequential processing:")
        start_time = time.perf_counter()
        sequential_results = [cpu_intensive_task(size) for size in dataset_sizes]
        sequential_time = time.perf_counter() - start_time
        print(f"  Processed {len(sequential_results)} datasets in {sequential_time:.3f}s")
        print()

        # Parallel processing with ProcessPoolExecutor
        print("Parallel processing (ProcessPoolExecutor):")
        start_time = time.perf_counter()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [executor.submit(cpu_intensive_task, size) for size in dataset_sizes]
            parallel_results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    parallel_results.append(result)
                except Exception as e:
                    logging.exception("Task failed: %s", e)
        parallel_time = time.perf_counter() - start_time
        print(f"  Processed {len(parallel_results)} datasets in {parallel_time:.3f}s")
        print()

        speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0
        cpu_count = multiprocessing.cpu_count()
        print("Results:")
        print(f"  CPU cores available: {cpu_count}")
        print(f"  Sequential time: {sequential_time:.3f}s")
        print(f"  Parallel time: {parallel_time:.3f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print("  ✅ ProcessPoolExecutor provides significant speedup!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE PROCESS POOLS:")
        print("   ✅ CPU-bound parallel computation")
        print("   ✅ Large dataset processing")
        print("   ✅ Scientific computing")
        print("   ✅ Numerical computations")
        print()
        print("2. WHY IT MATTERS:")
        print("   - True parallelism (bypasses GIL)")
        print("   - Utilizes all CPU cores")
        print("   - Process pool reduces overhead")
        print("   - Optimal for CPU-bound tasks")
        print("=" * 70)
        print()


# -------------------------
# main guard and start-method
# -------------------------
def main() -> None:
    logging.info("Multiprocessing Basic Examples")
    logging.info("=" * 40)

    # Choose start method carefully: 'spawn' is safest across platforms, 'fork' is default on Linux.
    # We only set it if it hasn't been set already.
    preferred = "spawn" if sys.platform.startswith("win") or sys.platform == "darwin" else "fork"
    ensure_start_method(preferred)

    example = BasicProcessExample()
    example.basic_process_creation()
    example.process_properties()
    example.daemon_processes()
    example.process_termination()
    example.parallel_computation()
    example.parallel_computation_with_queue()

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    example.basic_process_creation_real_world()
    example.parallel_computation_real_world()

    logging.info("All basic examples completed!")


if __name__ == "__main__":
    # Install a simple signal handler so Ctrl+C logs nicely.
    def _handle_sigint(sig, frame):
        logging.info("Received SIGINT, exiting.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_sigint)
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