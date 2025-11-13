"""
AsyncIO + Multiprocessing Hybrid Patterns.

This module demonstrates how to combine asyncio's I/O handling with
multiprocessing's true parallelism for CPU-bound work, bypassing the GIL.

Key patterns:
- Offloading heavy CPU work to process pools from async code
- Maintaining async responsiveness while doing parallel processing
- Inter-process communication in async context
- Managing process pool lifecycle
"""

import asyncio
import multiprocessing
import concurrent.futures
import threading
import time
import logging
import os
from typing import Any, Callable, List, Dict, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class ProcessTaskResult:
    """Result of a multiprocess task."""
    task_id: str
    result: Any
    execution_time: float
    process_id: int
    is_parallel: bool


class AsyncioMultiprocessingHybrid:
    """
    Hybrid concurrency combining asyncio and multiprocessing.

    This class demonstrates how to:
    - Use asyncio for I/O-bound operations
    - Offload CPU-bound work to process pools (true parallelism)
    - Bypass GIL limitations for CPU-intensive tasks
    - Handle inter-process communication asynchronously

    When to Use:
        - True CPU parallelism needed
        - Bypassing GIL limitations
        - Heavy CPU-bound work
        - Parallel processing with async I/O

    Real-World Examples:
        - Data processing: Parallel CPU + async I/O
        - ML inference: Parallel models + async serving
        - Image processing: Parallel transforms + async I/O
        - Scientific computing: Parallel compute + async I/O

    Gotchas:
        - Process creation overhead
        - Functions must be picklable
        - IPC overhead between processes
        - Memory overhead per process
        - Cross-platform compatibility

    Performance Notes:
        - True parallelism for CPU work
        - Process overhead significant
        - Optimal for heavy CPU-bound tasks
        - Balance process count vs overhead
    """

    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self._process_executor: Optional[ProcessPoolExecutor] = None
        self._running = False
        self._task_counter = 0
        self._lock = threading.Lock()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Start the hybrid executor."""
        if self._process_executor is not None:
            return

        # Create process pool executor
        self._process_executor = ProcessPoolExecutor(
            max_workers=self.max_workers,
            mp_context=multiprocessing.get_context('spawn')  # Cross-platform compatibility
        )
        self._running = True
        logger.info(f"Started AsyncioMultiprocessingHybrid with {self.max_workers} processes")

    async def stop(self):
        """Stop the hybrid executor."""
        if self._process_executor is None:
            return

        self._running = False
        self._process_executor.shutdown(wait=True)
        self._process_executor = None
        logger.info("Stopped AsyncioMultiprocessingHybrid")

    def _get_next_task_id(self) -> str:
        """Get next unique task ID."""
        with self._lock:
            self._task_counter += 1
            return f"process_task_{self._task_counter}"

    async def run_io_task(self, coro: Callable) -> ProcessTaskResult:
        """
        Run an I/O-bound task using asyncio.

        Args:
            coro: Async coroutine function

        Returns:
            ProcessTaskResult with execution details
        """
        if not self._running:
            raise RuntimeError("Hybrid executor not started")

        task_id = self._get_next_task_id()
        start_time = time.time()

        try:
            result = await coro()
            execution_time = time.time() - start_time

            return ProcessTaskResult(
                task_id=task_id,
                result=result,
                execution_time=execution_time,
                process_id=os.getpid(),
                is_parallel=False
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"IO task {task_id} failed: {e}")
            raise

    async def run_parallel_task(self, func: Callable, *args, **kwargs) -> ProcessTaskResult:
        """
        Run a CPU-bound task using process pool (true parallelism).

        Args:
            func: Function to execute (must be picklable)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            ProcessTaskResult with execution details
        """
        if not self._running or self._process_executor is None:
            raise RuntimeError("Hybrid executor not started")

        task_id = self._get_next_task_id()
        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._process_executor, func, *args, **kwargs
            )
            execution_time = time.time() - start_time

            return ProcessTaskResult(
                task_id=task_id,
                result=result,
                execution_time=execution_time,
                process_id=os.getpid(),  # This is the main process ID
                is_parallel=True
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Parallel task {task_id} failed: {e}")
            raise

    async def run_parallel_batch(
        self,
        func: Callable,
        arg_list: List[Tuple]
    ) -> List[ProcessTaskResult]:
        """
        Run multiple parallel tasks as a batch.

        Args:
            func: Function to execute on each item
            arg_list: List of argument tuples

        Returns:
            List of ProcessTaskResult objects
        """
        if not self._running:
            raise RuntimeError("Hybrid executor not started")

        # Submit all tasks
        tasks = []
        for args in arg_list:
            if isinstance(args, tuple):
                task = self.run_parallel_task(func, *args)
            else:
                task = self.run_parallel_task(func, args)
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return successful results
        successful_results = [
            result for result in results
            if not isinstance(result, Exception)
        ]

        return successful_results

    async def run_hybrid_workflow(
        self,
        io_tasks: List[Callable],
        parallel_tasks: List[Tuple[Callable, Tuple]]
    ) -> Dict[str, List[ProcessTaskResult]]:
        """
        Run a hybrid workflow with both I/O and parallel tasks.

        Args:
            io_tasks: List of async coroutines for I/O work
            parallel_tasks: List of (func, args) tuples for CPU work

        Returns:
            Dict with 'io_results' and 'parallel_results' keys
        """
        if not self._running:
            raise RuntimeError("Hybrid executor not started")

        # Run I/O and parallel tasks concurrently
        io_coroutines = [self.run_io_task(coro) for coro in io_tasks]
        parallel_coroutines = [
            self.run_parallel_task(func, *args)
            for func, args in parallel_tasks
        ]

        io_results, parallel_results = await asyncio.gather(
            asyncio.gather(*io_coroutines, return_exceptions=True),
            asyncio.gather(*parallel_coroutines, return_exceptions=True)
        )

        # Filter exceptions
        io_success = [r for r in io_results if not isinstance(r, Exception)]
        parallel_success = [r for r in parallel_results if not isinstance(r, Exception)]

        return {
            'io_results': io_success,
            'parallel_results': parallel_success
        }

    async def run_data_processing_pipeline(
        self,
        fetch_stage: Callable,  # Async I/O
        process_stage: Callable,  # Parallel CPU
        aggregate_stage: Callable,  # Parallel CPU
        data_sources: List[str]
    ) -> List[Any]:
        """
        Run a 3-stage data processing pipeline:
        1. Fetch data (I/O)
        2. Process data (parallel CPU)
        3. Aggregate results (parallel CPU)

        Args:
            fetch_stage: Async function to fetch data
            process_stage: Function to process individual items
            aggregate_stage: Function to aggregate results
            data_sources: List of data source identifiers

        Returns:
            List of final aggregated results
        """
        # Stage 1: Fetch data concurrently (I/O)
        fetch_tasks = [self.run_io_task(lambda src=src: fetch_stage(src))
                      for src in data_sources]
        fetch_results = await asyncio.gather(*fetch_tasks)

        raw_data = [result.result for result in fetch_results]

        # Stage 2: Process data in parallel (CPU)
        process_args = [(item,) for item in raw_data]
        process_results = await self.run_parallel_batch(process_stage, process_args)

        processed_data = [result.result for result in process_results]

        # Stage 3: Aggregate results (could be parallel if aggregation is CPU-intensive)
        if len(processed_data) > 1:
            # Parallel aggregation
            aggregate_result = await self.run_parallel_task(
                aggregate_stage, processed_data
            )
            return [aggregate_result.result]
        else:
            # Single result, no aggregation needed
            return processed_data

    async def asyncio_multiprocessing_real_world_example(self) -> None:
        """
        Real-World Scenario: AsyncIO + Multiprocessing - ML Inference Service.

        REAL-WORLD SCENARIO:
        ====================
        You're building an ML inference service:
        - Receive prediction requests via async API (I/O-bound)
        - Run heavy ML model inference (CPU-bound, needs true parallelism)
        - Problem: GIL limits CPU parallelism, blocking async event loop
        
        THE PROBLEM WITHOUT HYBRID:
        ============================
        - ML inference blocks event loop → no concurrent requests
        - Use pure asyncio → CPU work blocks everything
        - Use threading → GIL prevents true parallelism
        - Single CPU core utilized → slow inference
        - System unresponsive → poor user experience
        
        THE SOLUTION:
        =============
        AsyncIO + Multiprocessing enables:
        - AsyncIO handles requests efficiently (I/O)
        - Process pool runs ML inference in parallel (bypasses GIL)
        - True CPU parallelism → utilizes all CPU cores
        - Event loop stays responsive → concurrent requests
        - Optimal for heavy CPU-bound + I/O workloads
        
        WHEN TO USE ASYNCIO + MULTIPROCESSING:
        =======================================
        ✅ ML inference services
        ✅ Heavy CPU-bound + I/O workloads
        ✅ Need true CPU parallelism
        ✅ Bypassing GIL limitations
        ✅ Scientific computing + async I/O
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: ML Inference Service")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - ML inference service")
        print("  - Receive prediction requests via async API (I/O-bound)")
        print("  - Run heavy ML model inference (CPU-bound, needs true parallelism)")
        print("  - Problem: GIL limits CPU parallelism, blocking async event loop")
        print()
        print("THE PROBLEM:")
        print("  Without hybrid:")
        print("    ❌ ML inference blocks event loop → no concurrent requests")
        print("    ❌ Use pure asyncio → CPU work blocks everything")
        print("    ❌ Use threading → GIL prevents true parallelism")
        print("    ❌ Single CPU core utilized → slow inference")
        print()
        print("THE SOLUTION:")
        print("  With AsyncIO + Multiprocessing:")
        print("    ✅ AsyncIO handles requests efficiently (I/O)")
        print("    ✅ Process pool runs ML inference in parallel (bypasses GIL)")
        print("    ✅ True CPU parallelism → utilizes all CPU cores")
        print("    ✅ Event loop stays responsive → concurrent requests")
        print()
        print("=" * 70)
        print()

        async def handle_prediction_request(request_id: str, input_data: dict) -> dict:
            """Simulate handling a prediction request."""
            # I/O: Receive and validate request (async)
            await asyncio.sleep(0.02)  # Simulate network I/O
            print(f"  Received request {request_id}")

            # CPU: Run ML inference (heavy CPU work, offloaded to process pool)
            def run_ml_inference(data: dict) -> dict:
                # Simulate heavy ML model inference
                result = 0
                for i in range(1000000):  # Heavy computation
                    result += hash(str(data) + str(i)) % 1000
                
                # Simulate model prediction
                prediction = {
                    "request_id": data["request_id"],
                    "prediction": result % 10,
                    "confidence": 0.85 + (result % 15) / 100,
                    "model_version": "v2.1"
                }
                return prediction

            inference_result = await self.run_parallel_task(
                run_ml_inference,
                {"request_id": request_id, "input": input_data}
            )
            
            return inference_result.result

        print("Simulating ML inference service with 4 concurrent requests...")
        print("  (Each request requires heavy CPU inference)")
        print()

        requests = [
            (f"req_{i}", {"features": [i * 0.1, i * 0.2, i * 0.3]})
            for i in range(4)
        ]

        start_time = time.time()

        # Handle requests concurrently
        tasks = [
            handle_prediction_request(req_id, data)
            for req_id, data in requests
        ]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        print()
        print("Results:")
        for result in results:
            print(f"  ✅ {result['request_id']}: Prediction={result['prediction']}, "
                  f"Confidence={result['confidence']:.2f}")
        print(f"\nTotal time: {elapsed:.3f}s")
        print(f"Average per request: {elapsed/len(results):.3f}s")
        print(f"CPU cores utilized: {self.max_workers}")
        print("  ✅ AsyncIO + Multiprocessing enabled parallel ML inference!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE ASYNCIO + MULTIPROCESSING:")
        print("   ✅ ML inference services")
        print("   ✅ Heavy CPU-bound + I/O workloads")
        print("   ✅ Need true CPU parallelism")
        print("   ✅ Bypassing GIL limitations")
        print()
        print("2. WHY IT MATTERS:")
        print("   - True CPU parallelism (bypasses GIL)")
        print("   - Utilizes all CPU cores")
        print("   - Event loop stays responsive")
        print("   - Optimal for heavy CPU workloads")
        print("=" * 70)
        print()


# Module-level functions for multiprocessing (must be picklable)
def cpu_intensive_calculation(data: str, iterations: int = 50000) -> Dict[str, Any]:
    """CPU-intensive calculation that benefits from multiprocessing."""
    import math

    result = 0
    computations = []

    # Perform CPU-intensive calculations
    for i in range(iterations):
        # Complex mathematical operations
        x = hash(data + str(i)) % 1000
        result += math.sin(x) * math.cos(x) * math.sqrt(abs(x) + 1)
        computations.append(result)

    return {
        'input': data,
        'result': result,
        'computations': len(computations),
        'process_id': os.getpid()
    }

def aggregate_results(results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate results from multiple calculations."""
    total_result = sum(item['result'] for item in results_list)
    total_computations = sum(item['computations'] for item in results_list)

    return {
        'total_result': total_result,
        'total_computations': total_computations,
        'num_sources': len(results_list),
        'avg_result': total_result / len(results_list) if results_list else 0,
        'aggregated_by': os.getpid()
    }


async def simulate_data_fetch(source: str) -> Dict[str, Any]:
    """Simulate async data fetching."""
    await asyncio.sleep(0.1)  # Simulate I/O delay
    return {
        'source': source,
        'data': f"data_from_{source}",
        'timestamp': time.time(),
        'fetched_by': os.getpid()
    }


async def demonstrate_asyncio_multiprocessing_hybrid():
    """Demonstrate AsyncIO + Multiprocessing hybrid patterns."""

    print("🔄 AsyncIO + Multiprocessing Hybrid Demonstration")
    print("=" * 55)

    async with AsyncioMultiprocessingHybrid(max_workers=3) as hybrid:

        print("\n1. Basic I/O and parallel task execution:")
        print("-" * 45)

        # Run I/O task
        io_result = await hybrid.run_io_task(
            lambda: simulate_data_fetch("source_1")
        )
        print(f"IO task: {io_result.result} ({io_result.execution_time:.3f}s, "
              f"process={io_result.process_id}, parallel={io_result.is_parallel})")

        # Run parallel CPU task
        cpu_result = await hybrid.run_parallel_task(
            cpu_intensive_calculation, "test_data", 10000
        )
        print(f"Parallel task: {cpu_result.result} ({cpu_result.execution_time:.3f}s, "
              f"process={cpu_result.process_id}, parallel={cpu_result.is_parallel})")

        print("\n2. Batch parallel processing:")
        print("-" * 32)

        # Run batch of CPU tasks
        batch_args = [
            ("batch_data_1", 15000),
            ("batch_data_2", 15000),
            ("batch_data_3", 15000),
        ]

        start_time = time.time()
        batch_results = await hybrid.run_parallel_batch(
            cpu_intensive_calculation, batch_args
        )
        batch_time = time.time() - start_time

        print(f"Processed {len(batch_results)} items in {batch_time:.3f}s")
        for result in batch_results:
            data = result.result
            print(f"  {data['input']}: result={data['result']:.3f}, "
                  f"computations={data['computations']}, process={data['process_id']}")

        print("\n3. Hybrid workflow (I/O + Parallel):")
        print("-" * 38)

        # Run hybrid workflow
        io_tasks = [
            lambda: simulate_data_fetch(f"api_{i}")
            for i in range(3)
        ]
        parallel_tasks = [
            (cpu_intensive_calculation, ("parallel_data_1", 20000)),
            (cpu_intensive_calculation, ("parallel_data_2", 20000)),
        ]

        workflow_results = await hybrid.run_hybrid_workflow(
            io_tasks, parallel_tasks
        )

        print(f"I/O tasks completed: {len(workflow_results['io_results'])}")
        print(f"Parallel tasks completed: {len(workflow_results['parallel_results'])}")

        print("\n4. Data processing pipeline:")
        print("-" * 30)

        # Full pipeline demonstration
        data_sources = ["db1", "db2", "api1", "api2"]

        pipeline_results = await hybrid.run_data_processing_pipeline(
            simulate_data_fetch,
            lambda data: cpu_intensive_calculation(data['data'], 10000),
            aggregate_results,
            data_sources
        )

        print(f"Pipeline completed with {len(pipeline_results)} final results")
        if pipeline_results:
            final_result = pipeline_results[0]
            print(f"Total computations: {final_result['total_computations']}")
            print(f"Total result: {final_result['total_result']:.2f}")

    print("\n✅ AsyncIO + Multiprocessing hybrid demonstration complete!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Run demonstration (requires __main__ guard for multiprocessing)
    asyncio.run(demonstrate_asyncio_multiprocessing_hybrid())
