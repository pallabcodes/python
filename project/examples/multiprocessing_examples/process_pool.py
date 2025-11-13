"""
Robust Process Pool examples.

Covers:
- concurrent.futures.ProcessPoolExecutor usage (recommended)
- multiprocessing.Pool usage (legacy)
- map / starmap / apply_async patterns
- error handling and timeouts
- resource/configuration tips (chunksize, max_workers)

This file is written so examples are portable (module-level worker functions),
safe under 'spawn', and demonstrate practical defensive patterns (timeouts,
exception handling, proper shutdown).
"""

from __future__ import annotations

import concurrent.futures
import logging
import multiprocessing
import os
import sys
import time
from typing import Any, List, Optional, Tuple

# ---- CONFIG / demo scale ----
SCALE = 20_000  # scale down for quick demo; increase for heavier load
LOG_LEVEL = logging.INFO

# ---- logging ----
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [pid:%(process)d] %(message)s",
    datefmt="%H:%M:%S",
)


# -------------------------
# Module-level worker funcs
# -------------------------
def cpu_bound_task(x: int) -> int:
    """Simple CPU-bound function: sum of squares up to x-1.

    Module-level so it's picklable when using spawn.
    """
    acc = 0
    for i in range(x):
        acc += i * i
    return acc


def io_bound_task(filename: str, sleep: float = 0.05) -> dict:
    """Simulated I/O-bound work (sleep + metadata)."""
    time.sleep(sleep)
    return {"filename": filename, "size": len(filename) * 100, "processed_at": time.time()}


def multiply_task(x: int, multiplier: int) -> int:
    """Used with starmap; uses module-level cpu_bound_task for picklability."""
    return cpu_bound_task(x) * multiplier


def task_that_may_fail(x: int) -> int:
    """Task that will raise for certain inputs to demonstrate error handling."""
    if x == (SCALE * 2):  # demo failing input
        raise ValueError(f"Task failed for {x}")
    return cpu_bound_task(x)


# -------------------------
# Utilities
# -------------------------
def ensure_start_method(preferred: Optional[str] = None) -> None:
    """Set start method if not already set.

    Avoid forcing a start method if one is set already to prevent RuntimeError.
    """
    try:
        current = multiprocessing.get_start_method(allow_none=True)
        if current is None and preferred:
            multiprocessing.set_start_method(preferred)
            logging.info("set multiprocessing start method -> %s", preferred)
        else:
            logging.info("multiprocessing start method already: %s", current)
    except RuntimeError as e:
        # start method was set earlier; just warn
        logging.warning("cannot set start method (%s)", e)


# -------------------------
# Examples (class wrapper)
# -------------------------
class ProcessPoolExample:
    """
    Collection of process-pool related demos.

    This class demonstrates process pool patterns using both ProcessPoolExecutor
    (recommended) and multiprocessing.Pool (legacy) with proper error handling,
    timeouts, and resource management.

    When to Use:
        - CPU-bound parallel computation
        - Processing large datasets in parallel
        - Batch processing operations
        - Scientific computing workloads
        - Image/video processing

    Real-World Examples:
        - Data processing: Process large datasets
        - Scientific computing: Parallel numerical computations
        - Image processing: Process multiple images
        - Machine learning: Train models in parallel
        - Batch jobs: Run batch operations concurrently

    Gotchas:
        - Functions must be picklable (module-level)
        - ProcessPoolExecutor is preferred over Pool
        - Always use timeouts with result retrieval
        - Handle exceptions per task/future
        - Proper cleanup with context managers
        - Chunksize affects performance

    Performance Notes:
        - Process pools reuse workers (reduces overhead)
        - Optimal worker count is CPU count
        - Chunksize reduces IPC overhead
        - ProcessPoolExecutor is more efficient
        - Pool overhead is significant for small tasks
    """

    @staticmethod
    def executor_basic_demo() -> None:
        """
        ProcessPoolExecutor: submit + as_completed with safe result handling.

        Demonstrates basic ProcessPoolExecutor usage with submit() and
        as_completed() for processing results as they finish.

        When to Use:
            - Processing tasks as they complete
            - When order doesn't matter
            - Maximizing throughput
            - Learning ProcessPoolExecutor basics

        Real-World Examples:
            - Data processing: Process data as it arrives
            - Image processing: Process images as they finish
            - Batch operations: Process batches concurrently
            - Task queues: Process tasks as they complete

        Gotchas:
            - submit() returns Future immediately
            - as_completed() yields futures as they finish
            - Use timeout with as_completed() and result()
            - Handle exceptions per future
            - Results arrive in completion order, not submission order
            - Context manager ensures cleanup

        Performance Notes:
            - Processes results as they complete (low latency)
            - Better throughput than sequential processing
            - Optimal for CPU-bound independent tasks
            - Timeouts prevent indefinite blocking
        """
        logging.info("=== ProcessPoolExecutor Basic Demo ===")

        # numbers is the list of inputs we will process sequentially and then in parallel.
        # SCALE is a module-level constant used to make the demo easy to scale up/down.
        numbers = [SCALE, SCALE * 2, SCALE * 3, SCALE * 4]

         # baseline sequential that records a high-resolution start time to measure sequential execution time
        t0 = time.perf_counter()
        # run cpu_bound_task for each input in the current (main) process, synchronously.
        # This runs in the main process (M1) on the main thread (T_main).
        seq = [cpu_bound_task(n) for n in numbers]
        # Record the end time and calculate the duration.
        logging.info("sequential: %.3fs (sum=%d)", time.perf_counter() - t0, sum(seq))

        # parallel with ProcessPoolExecutor -------------------------------------
        # choose a sensible worker count (cap at 4 for demo). os.cpu_count() is used
        # to detect available CPU cores. If it returns None, fallback to 1.
        max_workers = min(4, (os.cpu_count() or 1))
        logging.info("Using ProcessPoolExecutor with max_workers=%d", max_workers)
        
        #  record start time for parallel run
        t0 = time.perf_counter()
        
        results = []  # will collect completed result values

        # create the ProcessPoolExecutor context manager. When entering the with-block:
        # - the executor will spawn up to `max_workers` worker processes (W1..Wk).
        # -  Each worker is a separate OS process with its own memory and PID.
        # - the main process (M1) keeps running its main thread (T_main) and also
        # -  the executor itself uses background thread(s) in M1 to manage workers & I/O.
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as ex:
            # submit returns a Future object immediately (future lives in main process).
            # the actual cpu_bound_task(n) is scheduled to run in one of the worker processes.
            
            futures = [ex.submit(cpu_bound_task, n) for n in numbers]
            # At this point:
            #  - main thread (T_main) created N futures and returned quickly.
            #  - up to `max_workers` worker processes (W1..Wk) start pulling tasks and run cpu_bound_task.
            #  - results will be transported back to M1 via pickling/unpickling.

            #  -------------------------------------------------------------
            # concurrent.futures.as_completed yields futures as they finish (completion order).
            # The optional timeout=60 applies to the whole iterator: if not all futures
            # complete within 60s, as_completed raises TimeoutError.
            # as_completed yields Future objects in the order they become done.
            
            for fut in concurrent.futures.as_completed(futures, timeout=60):
                # for each finished future we call fut.result(timeout=10) to retrieve the
                # actual value; fut.result might raise if the worker raised, or
                # TimeoutError if the result isn't available within the per-future timeout.
                # The timeout=10 here is per-future (not overall).
                try:
                    r = fut.result(timeout=10)  # extra per-future defensive timeout
                    results.append(r)
                except concurrent.futures.TimeoutError:
                      # per-future timeout — means we waited 10s to get result and it didn't arrive.
                      # This could indicate worker slowness or stuck IPC; log and continue.
                    logging.error("A worker timed out.")
                except Exception as exc:
                    # other exceptions (ValueError, etc.) are propagated up to the main thread.
                    logging.exception("Worker raised: %s", exc)
        
        # executor context manager exits here: it will attempt a clean shutdown of workers.
        # This includes waiting for any pending tasks to complete and terminating worker processes. 
        # Leaving the with block triggers executor.shutdown(wait=True) by default: it will wait for tasks to finish (unless you pass wait=False). After shutdown, worker processes exit (unless reused elsewhere).
        logging.info("parallel: %.3fs (got %d results)", time.perf_counter() - t0, len(results))
        logging.info("=== done ===")

    @staticmethod
    def executor_map_demo() -> None:
        """
        Demonstrate executor.map with chunksize and preserved ordering.

        Shows how to use executor.map() for parallel processing with
        preserved input/output ordering and chunksize optimization.

        When to Use:
            - When order matters
            - Processing iterables in parallel
            - Simple parallel map operations
            - Batch processing with ordering

        Real-World Examples:
            - Data transformation: Transform data preserving order
            - Batch processing: Process batches in order
            - Pipeline stages: Process pipeline stages in order
            - Sequential operations: Parallelize sequential operations

        Gotchas:
            - map() preserves input/output order
            - Iterator waits for earlier results if later ones finish first
            - chunksize reduces IPC overhead for small tasks
            - Larger chunksize = less overhead but less parallelism
            - Optimal chunksize depends on task size

        Performance Notes:
            - chunksize reduces IPC overhead significantly
            - Preserving order adds latency
            - Optimal for ordered batch processing
            - Better than sequential for CPU-bound tasks
        """
        logging.info("=== ProcessPoolExecutor.map Demo ===")
        nums = list(range(10, 15))
        logging.info("input: %s", nums)
        max_workers = min(4, (os.cpu_count() or 1))

        # chunksize can drastically reduce overhead for many small tasks
        chunksize = 1
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as ex:
            # chunksize=1 means each task is sent individually. Larger chunksize sends blocks of tasks at once (reduces per-task IPC/pickling overhead, increases per-worker contiguous work).
            # ex.map schedules the cpu_bound_task to each element of nums in parallel.
            # ex.map returns an iterator that yields results in the same order as the inputs (ordering preserved). Important: ordering is preserved even if a later input finishes earlier on a worker; the iterator will wait for earlier results to become available before yielding them.
            results = list(ex.map(cpu_bound_task, nums, chunksize=chunksize))
        logging.info("results: %s", results)

        # verify
        for n, r in zip(nums, results):
            expected = sum(i * i for i in range(n))
            logging.info("  %d -> %d (expected %d) %s", n, r, expected, "OK" if r == expected else "MISMATCH")
        logging.info("=== done ===")

    @staticmethod
    def executor_async_callbacks_demo() -> None:
        """
        Demonstrate submit + callbacks and robust waiting.

        Shows how to use callbacks with futures for asynchronous result
        handling and proper timeout management.

        When to Use:
            - Asynchronous result processing
            - Event-driven processing
            - Progress reporting
            - Result aggregation
            - Notification systems

        Real-World Examples:
            - Progress tracking: Report progress as tasks complete
            - Event processing: Process events as they arrive
            - Result aggregation: Aggregate results as they arrive
            - Notification systems: Notify on completion
            - Pipeline processing: Process pipeline stages asynchronously

        Gotchas:
            - Callbacks run in main process thread
            - Callbacks execute when future completes
            - Handle exceptions in callbacks
            - Use timeout with as_completed()
            - Callbacks don't block other futures
            - Order of callback execution is not guaranteed

        Performance Notes:
            - Callbacks enable asynchronous processing
            - No blocking on result retrieval
            - Useful for progress reporting
            - Minimal overhead
        """
        logging.info("=== Executor async submit + callback Demo ===")

        def _cb(fut: concurrent.futures.Future) -> None:
            try:
                v = fut.result()
                logging.info("callback result=%s", v)
            except Exception as e:
                logging.exception("callback exception: %s", e)

        max_workers = min(3, (os.cpu_count() or 1))
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as ex:
            futures = []
            for i in range(5):
                n = SCALE + (i * SCALE)
                fut = ex.submit(cpu_bound_task, n)
                fut.add_done_callback(_cb)
                futures.append(fut)

            # wait defensively with a timeout
            try:
                for fut in concurrent.futures.as_completed(futures, timeout=60):
                    # results handled in callback; here we ensure they complete
                    pass
            except concurrent.futures.TimeoutError:
                logging.warning("Some futures did not complete in time.")
        logging.info("=== done ===")

    @staticmethod
    def multiprocessing_pool_basic_demo() -> None:
        """
        Basic multiprocessing.Pool.map usage with safe get/timeouts.

        Demonstrates legacy multiprocessing.Pool usage with map_async()
        and proper timeout handling. Prefer ProcessPoolExecutor for new code.

        When to Use:
            - Legacy code compatibility
            - Need Pool-specific features
            - More control than ProcessPoolExecutor
            - Working with existing Pool code

        Real-World Examples:
            - Legacy systems: Maintain existing Pool code
            - Specialized pools: Custom pool configurations
            - Advanced features: Use Pool-specific features
            - Migration: Transitioning from Pool to Executor

        Gotchas:
            - Pool is legacy (prefer ProcessPoolExecutor)
            - map_async() returns AsyncResult
            - get() blocks until all results ready
            - Use timeout with get() to prevent blocking
            - Exceptions raised in get()
            - Context manager ensures cleanup

        Performance Notes:
            - Similar performance to ProcessPoolExecutor
            - More overhead than Executor
            - Still efficient for CPU-bound tasks
            - Consider migrating to ProcessPoolExecutor
        """
        logging.info("=== multiprocessing.Pool map Demo ===")

        numbers = [SCALE // 2, SCALE, SCALE + 5_000]

        # choose worker count
        processes = min(4, (os.cpu_count() or 1))
        logging.info("Pool processes=%d", processes)

        # Use chunksize to reduce IPC overhead for many small tasks
        chunksize = 1

        # create the pool context; on enter it spawns worker processes W1..Wk
        with multiprocessing.Pool(processes=processes) as pool:
            # map_async schedules the entire iterable to workers and returns immediately
            # AsyncResult lives in the parent process (M1) and will be used to .get() results later.
            async_res = pool.map_async(cpu_bound_task, numbers, chunksize=chunksize)
            try:
                # .get(timeout=60) blocks the calling thread (T_main in M1) until:
                #  - all tasks finish and the aggregated list of results is available, OR
                #  - timeout is reached, OR
                #  - a worker raised an exception (re-raised here).
                results = async_res.get(timeout=60)
                logging.info("map results: %s", results)
            except multiprocessing.TimeoutError:
                logging.error("Pool.map timed out.")
            except Exception as exc:
                logging.exception("Pool.map raised: %s", exc)

        logging.info("=== done ===")

    @staticmethod
    def multiprocessing_pool_advanced_demo() -> None:
        """
        Demonstrate apply_async, map_async and starmap with safe result handling.

        Shows advanced Pool patterns including apply_async for individual tasks,
        map_async for parallel mapping, and starmap for multiple arguments.

        When to Use:
            - Individual task submission
            - Multiple arguments per task
            - Advanced pool control
            - Custom task coordination
            - Legacy Pool code

        Real-World Examples:
            - Task queues: Submit individual tasks
            - Multi-arg operations: Operations with multiple arguments
            - Custom workflows: Complex multi-step workflows
            - Legacy systems: Maintain existing Pool code
            - Specialized processing: Custom processing patterns

        Gotchas:
            - apply_async() submits single task
            - map_async() processes iterable
            - starmap() unpacks tuples as arguments
            - get() blocks until result ready
            - Use timeout with get()
            - Handle exceptions per AsyncResult

        Performance Notes:
            - apply_async() useful for individual tasks
            - starmap() efficient for multi-arg operations
            - Similar performance to ProcessPoolExecutor
            - Consider migrating to ProcessPoolExecutor
        """
        logging.info("=== multiprocessing.Pool advanced Demo ===")

        numbers = [SCALE // 2, SCALE, SCALE + 2_000]
        files = [f"file_{i}.txt" for i in range(len(numbers))]

        processes = min(4, (os.cpu_count() or 1))

        with multiprocessing.Pool(processes=processes) as pool:
            # -------------------------
            # apply_async per-task
            # -------------------------
            logging.info("Using apply_async per-task")
            # apply_async returns an AsyncResult immediately for each task (non-blocking).
            apply_futures = [pool.apply_async(cpu_bound_task, args=(n,)) for n in numbers]

            apply_results = []
            # Here we iterate over AsyncResult objects and call .get(timeout=30) for each:
            # This blocks T_main per get() call until the corresponding worker result arrives.
            for i, f in enumerate(apply_futures):
            try:
                    result = f.get(timeout=30)  # blocks up to 30s for this one result
                    apply_results.append(result)
            except Exception as exc:
                    logging.exception("apply_async[%d] error: %s", i, exc)

            logging.info("apply_async results: %s (got %d/%d)", apply_results, len(apply_results), len(apply_futures))

            # -------------------------
            # map_async example
            # -------------------------
            logging.info("Using map_async")
            try:
                map_res = pool.map_async(io_bound_task, files)
                map_results = map_res.get(timeout=30)  # blocks until all file tasks finish
                logging.info("map_async results: %s", map_results)
            except Exception as exc:
                logging.exception("map_async error: %s", exc)

            # -------------------------
            # starmap example
            # -------------------------
            logging.info("Using starmap")
            try:
                tasks = [(n, 2) for n in numbers[:2]]
                starmap_results = pool.starmap(multiply_task, tasks)  # synchronous: blocks until done
                logging.info("starmap results: %s", starmap_results)
            except Exception as exc:
                logging.exception("starmap error: %s", exc)

        logging.info("=== done ===")


    @staticmethod
    def pool_resource_demo() -> None:
        """
        Show resource-sizing examples and recommended defaults.

        Demonstrates different pool configurations and their impact on
        performance, helping choose optimal worker counts.

        When to Use:
            - Optimizing pool size
            - Resource planning
            - Performance tuning
            - Capacity planning
            - Understanding pool behavior

        Real-World Examples:
            - Performance tuning: Optimize worker count
            - Resource planning: Plan resource usage
            - Capacity planning: Plan for load
            - Benchmarking: Measure performance
            - Optimization: Find optimal configuration

        Gotchas:
            - Default workers = CPU count
            - More workers != always better
            - Optimal depends on task characteristics
            - Too many workers cause overhead
            - Too few workers underutilize CPU
            - Consider I/O wait times

        Performance Notes:
            - Optimal worker count is CPU count
            - More workers add overhead
            - Fewer workers underutilize resources
            - Balance workers vs overhead
            - Measure to find optimal
        """
        logging.info("=== Pool resource demo ===")
        cpu = os.cpu_count() or 1
        logging.info("cpu_count=%d", cpu)

        numbers = [SCALE // 2, SCALE, SCALE + 5_000]

        configs = [
            ("default", None),
            ("limited 2", 2),
            ("max-min-8", min(cpu, 8)),
        ]

        for label, workers in configs:
            workers_used = workers or cpu
            logging.info("config=%s workers=%s", label, workers_used)
            with multiprocessing.Pool(processes=workers) as pool:
                try:
                    res = pool.map(cpu_bound_task, numbers)
                    logging.info("  -> results len=%d", len(res))
                except Exception as exc:
                    logging.exception("  pool.map error: %s", exc)

        logging.info("=== done ===")

    @staticmethod
    def error_handling_demo() -> None:
        """
        Show how to handle errors robustly in both executor and Pool.

        Demonstrates proper error handling patterns for both ProcessPoolExecutor
        and multiprocessing.Pool to prevent crashes and handle failures gracefully.

        When to Use:
            - Building robust systems
            - Handling partial failures
            - Error recovery
            - Fault-tolerant processing
            - Production systems

        Real-World Examples:
            - Data processing: Handle invalid data gracefully
            - Batch operations: Continue on partial failures
            - Task queues: Handle task failures
            - Distributed systems: Handle node failures
            - Production systems: Robust error handling

        Gotchas:
            - Exceptions raised in result()/get()
            - Handle exceptions per task/future
            - Use try/except around result retrieval
            - Timeout exceptions are different
            - Worker crashes don't crash pool
            - Log errors for debugging

        Performance Notes:
            - Error handling overhead is minimal
            - Critical for production systems
            - Prevents cascading failures
            - Enables partial success patterns
        """
        logging.info("=== Error handling demo ===")

        numbers = [SCALE // 2, SCALE * 2, SCALE + 2_000]

        # 1) concurrent.futures: per-future try/except
        logging.info("ProcessPoolExecutor error handling")
        with concurrent.futures.ProcessPoolExecutor() as ex:
            futures = [ex.submit(task_that_may_fail, n) for n in numbers]
            for i, fut in enumerate(futures):
                try:
                    val = fut.result(timeout=20)
                    logging.info("future[%d] result: %s", i, val)
                except Exception as exc:
                    logging.error("future[%d] failed: %s", i, exc)

        # 2) multiprocessing.Pool: use apply_async/get per-task to capture exceptions
        logging.info("multiprocessing.Pool error handling (apply_async)")
        with multiprocessing.Pool(processes=min(4, os.cpu_count() or 1)) as pool:
            async_futs = [pool.apply_async(task_that_may_fail, (n,)) for n in numbers]
            for i, f in enumerate(async_futs):
                try:
                    logging.info("apply_async[%d] -> %s", i, f.get(timeout=30))
                except Exception as exc:
                    logging.error("apply_async[%d] failed: %s", i, exc)

        logging.info("=== done ===")

    def executor_basic_real_world(self) -> None:
        """
        Real-World Scenario: ProcessPoolExecutor - Batch Data Processing.

        REAL-WORLD SCENARIO:
        ====================
        You're building a batch data processing system:
        - Process thousands of data files
        - Each file takes 2-10 seconds to process
        - Problem: Sequential processing too slow
        
        THE PROBLEM WITHOUT PROCESS POOL:
        ===================================
        - Process file 1 → wait 5 seconds
        - Process file 2 → wait 5 seconds
        - Process file 3 → wait 5 seconds
        - 1000 files = 83+ minutes!
        - Single CPU core utilized → waste
        
        THE SOLUTION:
        =============
        ProcessPoolExecutor enables:
        - Process multiple files simultaneously
        - Distribute work across CPU cores
        - 8 cores = 8x speedup (theoretical)
        - 1000 files = 10+ minutes (vs 83+ minutes)
        - Optimal resource utilization
        
        WHEN TO USE PROCESS POOL:
        ==========================
        ✅ CPU-bound parallel computation
        ✅ Batch processing operations
        ✅ Processing large datasets
        ✅ Independent tasks
        ✅ Maximizing throughput
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Batch Data Processing System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Batch data processing system")
        print("  - Process thousands of data files")
        print("  - Each file takes 2-10 seconds to process")
        print("  - Problem: Sequential processing too slow")
        print()
        print("THE PROBLEM:")
        print("  Without process pool:")
        print("    ❌ Process file 1 → wait 5 seconds")
        print("    ❌ Process file 2 → wait 5 seconds")
        print("    ❌ Process file 3 → wait 5 seconds")
        print("    ❌ 1000 files = 83+ minutes!")
        print("    ❌ Single CPU core utilized → waste")
        print()
        print("THE SOLUTION:")
        print("  With ProcessPoolExecutor:")
        print("    ✅ Process multiple files simultaneously")
        print("    ✅ Distribute work across CPU cores")
        print("    ✅ 8 cores = 8x speedup (theoretical)")
        print("    ✅ 1000 files = 10+ minutes (vs 83+ minutes)")
        print("    ✅ Optimal resource utilization")
        print()
        print("=" * 70)
        print()

        def process_data_file(file_id: int) -> dict:
            """Simulate processing a data file."""
            processing_time = 0.1 + (file_id % 3) * 0.05  # Variable processing time
            time.sleep(processing_time)
            return {
                "file_id": file_id,
                "status": "processed",
                "records": file_id * 100,
                "processing_time": processing_time
            }

        file_ids = list(range(1, 13))  # 12 files to process

        # Sequential processing
        print("Sequential processing:")
        start_time = time.perf_counter()
        sequential_results = [process_data_file(fid) for fid in file_ids]
        sequential_time = time.perf_counter() - start_time
        print(f"  Processed {len(sequential_results)} files in {sequential_time:.2f}s")
        print()

        # Parallel processing with ProcessPoolExecutor
        print("Parallel processing (ProcessPoolExecutor):")
        max_workers = min(4, (os.cpu_count() or 1))
        start_time = time.perf_counter()
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_data_file, fid) for fid in file_ids]
            parallel_results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    parallel_results.append(result)
                except Exception as e:
                    logging.exception("File processing failed: %s", e)
        
        parallel_time = time.perf_counter() - start_time
        print(f"  Processed {len(parallel_results)} files in {parallel_time:.2f}s")
        print()

        speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0
        print("Results:")
        print(f"  CPU cores used: {max_workers}")
        print(f"  Sequential time: {sequential_time:.2f}s")
        print(f"  Parallel time: {parallel_time:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print("  ✅ ProcessPoolExecutor provides significant speedup!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE PROCESS POOL:")
        print("   ✅ CPU-bound parallel computation")
        print("   ✅ Batch processing operations")
        print("   ✅ Processing large datasets")
        print("   ✅ Independent tasks")
        print()
        print("2. WHY IT MATTERS:")
        print("   - True parallelism (bypasses GIL)")
        print("   - Reuses worker processes (reduces overhead)")
        print("   - Automatic load balancing")
        print("   - Optimal resource utilization")
        print("=" * 70)
        print()

    def executor_map_real_world(self) -> None:
        """
        Real-World Scenario: ProcessPoolExecutor.map() - Data Transformation Pipeline.

        REAL-WORLD SCENARIO:
        ====================
        You're building a data transformation pipeline:
        - Transform thousands of records
        - Each record needs CPU-intensive transformation
        - Problem: Need ordered results
        
        THE PROBLEM WITHOUT MAP:
        =========================
        - Transform records one by one → slow
        - Use submit() → results out of order
        - Need to sort results → extra overhead
        - Complex result handling → error-prone
        
        THE SOLUTION:
        =============
        map() enables:
        - Transform records in parallel
        - Results returned in input order
        - Simple API → easy to use
        - Automatic error handling
        - Optimal for ordered transformations
        
        WHEN TO USE MAP:
        ================
        ✅ Ordered results needed
        ✅ Simple parallel transformations
        ✅ Data transformation pipelines
        ✅ One-to-one transformations
        ✅ When order matters
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Data Transformation Pipeline")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Data transformation pipeline")
        print("  - Transform thousands of records")
        print("  - Each record needs CPU-intensive transformation")
        print("  - Problem: Need ordered results")
        print()
        print("THE PROBLEM:")
        print("  Without map():")
        print("    ❌ Transform records one by one → slow")
        print("    ❌ Use submit() → results out of order")
        print("    ❌ Need to sort results → extra overhead")
        print("    ❌ Complex result handling → error-prone")
        print()
        print("THE SOLUTION:")
        print("  With map():")
        print("    ✅ Transform records in parallel")
        print("    ✅ Results returned in input order")
        print("    ✅ Simple API → easy to use")
        print("    ✅ Automatic error handling")
        print("    ✅ Optimal for ordered transformations")
        print()
        print("=" * 70)
        print()

        def transform_record(record_id: int) -> dict:
            """Transform a single record."""
            # Simulate CPU-intensive transformation
            result = cpu_bound_task(record_id * 100)
            return {
                "record_id": record_id,
                "transformed_value": result,
                "status": "transformed"
            }

        record_ids = list(range(1, 9))  # 8 records to transform

        # Sequential transformation
        print("Sequential transformation:")
        start_time = time.perf_counter()
        sequential_results = [transform_record(rid) for rid in record_ids]
        sequential_time = time.perf_counter() - start_time
        print(f"  Transformed {len(sequential_results)} records in {sequential_time:.3f}s")
        print(f"  Results order: {[r['record_id'] for r in sequential_results]}")
        print()

        # Parallel transformation with map()
        print("Parallel transformation (map):")
        max_workers = min(4, (os.cpu_count() or 1))
        start_time = time.perf_counter()
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            parallel_results = list(executor.map(transform_record, record_ids, timeout=30))
        
        parallel_time = time.perf_counter() - start_time
        print(f"  Transformed {len(parallel_results)} records in {parallel_time:.3f}s")
        print(f"  Results order: {[r['record_id'] for r in parallel_results]}")
        print()

        speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0
        print("Results:")
        print(f"  Sequential time: {sequential_time:.3f}s")
        print(f"  Parallel time: {parallel_time:.3f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print("  ✅ map() provides ordered results with parallel speedup!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE MAP:")
        print("   ✅ Ordered results needed")
        print("   ✅ Simple parallel transformations")
        print("   ✅ Data transformation pipelines")
        print("   ✅ One-to-one transformations")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Results in input order (no sorting needed)")
        print("   - Simple API (like built-in map)")
        print("   - Automatic error handling")
        print("   - Optimal for ordered transformations")
        print("=" * 70)
        print()

    def error_handling_real_world(self) -> None:
        """
        Real-World Scenario: Error Handling - Robust Task Processing System.

        REAL-WORLD SCENARIO:
        ====================
        You're building a robust task processing system:
        - Process thousands of tasks
        - Some tasks may fail
        - Problem: One failure shouldn't stop all processing
        
        THE PROBLEM WITHOUT ERROR HANDLING:
        ====================================
        - Task 1 fails → entire batch stops
        - No partial results → wasted work
        - System fragile → single point of failure
        - No visibility → don't know what failed
        - Poor user experience
        
        THE SOLUTION:
        =============
        Proper error handling enables:
        - Process all tasks independently
        - Collect successful results
        - Log failures for investigation
        - Continue processing despite failures
        - System resilience → robust operation
        
        WHEN TO USE ERROR HANDLING:
        ===========================
        ✅ Robust task processing
        ✅ Partial failures acceptable
        ✅ Need failure visibility
        ✅ Production systems
        ✅ Batch processing with failures
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Robust Task Processing System")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Robust task processing system")
        print("  - Process thousands of tasks")
        print("  - Some tasks may fail")
        print("  - Problem: One failure shouldn't stop all processing")
        print()
        print("THE PROBLEM:")
        print("  Without error handling:")
        print("    ❌ Task 1 fails → entire batch stops")
        print("    ❌ No partial results → wasted work")
        print("    ❌ System fragile → single point of failure")
        print("    ❌ No visibility → don't know what failed")
        print()
        print("THE SOLUTION:")
        print("  With error handling:")
        print("    ✅ Process all tasks independently")
        print("    ✅ Collect successful results")
        print("    ✅ Log failures for investigation")
        print("    ✅ Continue processing despite failures")
        print("    ✅ System resilience → robust operation")
        print()
        print("=" * 70)
        print()

        def process_task(task_id: int) -> dict:
            """Process a task that may fail."""
            if task_id == 5:  # Simulate failure
                raise ValueError(f"Task {task_id} failed: Simulated error")
            
            time.sleep(0.05)  # Simulate processing
            return {"task_id": task_id, "status": "completed", "result": task_id * 10}

        task_ids = list(range(1, 11))  # 10 tasks, task 5 will fail

        print("Processing tasks with error handling...")
        print("  (Task 5 will fail to demonstrate error handling)")
        print()

        successful_results = []
        failed_tasks = []

        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(process_task, tid): tid for tid in task_ids}
            
            for future in concurrent.futures.as_completed(futures):
                task_id = futures[future]
                try:
                    result = future.result(timeout=10)
                    successful_results.append(result)
                    print(f"  ✅ Task {task_id}: Completed successfully")
                except Exception as e:
                    failed_tasks.append((task_id, str(e)))
                    print(f"  ❌ Task {task_id}: Failed - {e}")

        print()
        print("Results:")
        print(f"  Total tasks: {len(task_ids)}")
        print(f"  Successful: {len(successful_results)}")
        print(f"  Failed: {len(failed_tasks)}")
        print(f"  Success rate: {(len(successful_results)/len(task_ids)*100):.1f}%")
        print("  ✅ Error handling enabled robust processing!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. ERROR HANDLING BEST PRACTICES:")
        print("   ✅ Handle exceptions per task/future")
        print("   ✅ Collect successful results")
        print("   ✅ Log failures for investigation")
        print("   ✅ Continue processing despite failures")
        print()
        print("2. WHY IT MATTERS:")
        print("   - System resilience")
        print("   - Partial results better than none")
        print("   - Failure visibility")
        print("   - Production-ready systems")
        print("=" * 70)
        print()


# -------------------------
# Main runner
# -------------------------
def main() -> None:
    # choose start method for cross-platform safety; don't force if already set
    # Windows and macOS default to 'spawn'; Linux/Unix use 'fork'
    if sys.platform.startswith("win") or sys.platform == "darwin":
        preferred = "spawn"
    else:
        preferred = "fork"
    ensure_start_method(preferred)

    logging.info("Process pool examples starting (SCALE=%d)", SCALE)

    ex = ProcessPoolExample()
    ex.executor_basic_demo()
    ex.executor_map_demo()
    ex.executor_async_callbacks_demo()
    ex.multiprocessing_pool_basic_demo()
    ex.multiprocessing_pool_advanced_demo()
    ex.pool_resource_demo()
    ex.error_handling_demo()

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("RUNNING REAL-WORLD SCENARIOS")
    print("=" * 70 + "\n")
    ex.executor_basic_real_world()
    ex.executor_map_real_world()
    ex.error_handling_real_world()

    logging.info("All process pool examples finished.")


if __name__ == "__main__":
    main()

"""
🎯 Key Process Pool Concepts Demonstrated:
ProcessPoolExecutor - High-level interface for process pools
Pool.map() - Parallel map operations with ordered results
submit() & as_completed() - Asynchronous task submission and collection
Callbacks - Automatic handling of task completion
multiprocessing.Pool - Lower-level pool control
apply_async() - Individual asynchronous task submission
starmap() - Map with multiple arguments per task
Resource Management - Pool sizing and configuration
Error Handling - Different strategies for ProcessPoolExecutor vs Pool
🔑 Why Process Pools Matter:
Abstraction - Hide complexity of process management
Performance - Automatic load balancing across workers
Resource Efficiency - Reuse worker processes
Scalability - Easy to adjust pool size
Error Isolation - Worker failures don't crash entire pool
Memory Safety - Each worker has isolated memory space
"""