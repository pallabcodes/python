"""
ML-Specific Concurrency Patterns.

This module provides concurrency patterns optimized for machine learning
workloads including GPU/TPU utilization, model inference pipelines,
and distributed training coordination.

Features:
- GPU/TPU concurrency management
- Model inference pipelines
- Distributed training coordination
- Data loader optimization
- Accelerator resource management
"""

import asyncio
import threading
import time
import logging
import multiprocessing
from typing import Any, Callable, List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue

logger = logging.getLogger(__name__)

# Optional ML imports
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    nn = None
    TORCH_AVAILABLE = False

try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    tf = None
    TENSORFLOW_AVAILABLE = False

try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    ray = None
    RAY_AVAILABLE = False


@dataclass
class GPUInfo:
    """GPU device information."""
    device_id: int
    name: str
    memory_total: int  # MB
    memory_free: int   # MB
    utilization: float # Percentage


class GPUConcurrencyManager:
    """GPU resource management for concurrent ML workloads."""

    def __init__(self):
        self._gpu_devices: Dict[int, GPUInfo] = {}
        self._device_locks: Dict[int, threading.Lock] = {}
        self._running = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start GPU manager."""
        if self._running:
            return

        await self._discover_gpus()
        self._running = True
        logger.info(f"Started GPUConcurrencyManager with {len(self._gpu_devices)} GPUs")

    async def stop(self):
        """Stop GPU manager."""
        self._running = False
        logger.info("Stopped GPUConcurrencyManager")

    async def _discover_gpus(self):
        """Discover available GPU devices."""
        if TORCH_AVAILABLE and torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                memory_info = torch.cuda.mem_get_info(i)

                gpu_info = GPUInfo(
                    device_id=i,
                    name=props.name,
                    memory_total=memory_info[1] // 1024 // 1024,  # Convert to MB
                    memory_free=memory_info[0] // 1024 // 1024,
                    utilization=0.0  # Placeholder
                )

                self._gpu_devices[i] = gpu_info
                self._device_locks[i] = threading.Lock()

        elif TENSORFLOW_AVAILABLE:
            gpus = tf.config.list_physical_devices('GPU')
            for i, gpu in enumerate(gpus):
                # TensorFlow GPU info is limited
                gpu_info = GPUInfo(
                    device_id=i,
                    name=f"GPU_{i}",
                    memory_total=0,  # Not easily available in TF
                    memory_free=0,
                    utilization=0.0
                )
                self._gpu_devices[i] = gpu_info
                self._device_locks[i] = threading.Lock()

    def get_available_gpus(self) -> List[GPUInfo]:
        """Get list of available GPUs."""
        return list(self._gpu_devices.values())

    async def execute_on_gpu(self, gpu_id: int, func: Callable, *args, **kwargs) -> Any:
        """Execute function on specific GPU."""
        if gpu_id not in self._gpu_devices:
            raise ValueError(f"GPU {gpu_id} not available")

        with self._device_locks[gpu_id]:
            # Set GPU device context
            if TORCH_AVAILABLE:
                with torch.cuda.device(gpu_id):
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, func, *args, **kwargs)
            else:
                # Fallback execution
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)

            return result

    async def execute_batch_inference(self, model_func: Callable,
                                    input_batches: List[Any],
                                    max_concurrent: int = 4) -> List[Any]:
        """Execute batch inference across available GPUs."""
        if not self._gpu_devices:
            # Fallback to CPU execution
            logger.warning("No GPUs available, falling back to CPU")
            results = []
            for batch in input_batches:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, model_func, batch
                )
                results.append(result)
            return results

        # Distribute across GPUs
        semaphore = asyncio.Semaphore(max_concurrent)
        gpu_ids = list(self._gpu_devices.keys())

        async def process_batch(batch: Any, gpu_id: int) -> Any:
            async with semaphore:
                return await self.execute_on_gpu(gpu_id, model_func, batch)

        tasks = []
        for i, batch in enumerate(input_batches):
            gpu_id = gpu_ids[i % len(gpu_ids)]  # Round-robin GPU assignment
            task = process_batch(batch, gpu_id)
            tasks.append(task)

        return await asyncio.gather(*tasks)

    def get_gpu_utilization(self) -> Dict[int, float]:
        """Get current GPU utilization."""
        utilization = {}
        for gpu_id in self._gpu_devices:
            # In production, would use nvidia-ml-py or similar
            utilization[gpu_id] = 0.0  # Placeholder
        return utilization


class ModelInferencePipeline:
    """Optimized pipeline for model inference with concurrency."""

    def __init__(self, gpu_manager: Optional[GPUConcurrencyManager] = None):
        self.gpu_manager = gpu_manager
        self._preprocessing_queue: asyncio.Queue = asyncio.Queue()
        self._inference_queue: asyncio.Queue = asyncio.Queue()
        self._postprocessing_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

        # Worker counts
        self._preprocessing_workers = 4
        self._inference_workers = min(2, len(gpu_manager.get_available_gpus()) if gpu_manager else 1)
        self._postprocessing_workers = 4

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start inference pipeline."""
        if self._running:
            return

        self._running = True

        # Start pipeline stages
        asyncio.create_task(self._preprocessing_stage())
        asyncio.create_task(self._inference_stage())
        asyncio.create_task(self._postprocessing_stage())

        logger.info("Started ModelInferencePipeline")

    async def stop(self):
        """Stop inference pipeline."""
        self._running = False
        logger.info("Stopped ModelInferencePipeline")

    async def submit_inference_request(self, input_data: Any) -> str:
        """Submit inference request."""
        request_id = f"req_{int(time.time() * 1000000)}"
        await self._preprocessing_queue.put((request_id, input_data))
        return request_id

    async def get_inference_result(self, request_id: str, timeout: float = 30.0) -> Optional[Any]:
        """Get inference result."""
        # In production, would use a results dictionary with request_id keys
        # For demo, just return a mock result
        await asyncio.sleep(0.1)  # Simulate processing time
        return f"Mock inference result for {request_id}"

    async def _preprocessing_stage(self):
        """Preprocessing stage."""
        while self._running:
            try:
                request_id, input_data = await self._preprocessing_queue.get()

                # Simulate preprocessing
                processed_data = await self._preprocess_data(input_data)
                await self._inference_queue.put((request_id, processed_data))

                self._preprocessing_queue.task_done()

            except Exception as e:
                logger.error(f"Preprocessing error: {e}")

    async def _inference_stage(self):
        """Inference stage with GPU acceleration."""
        while self._running:
            try:
                request_id, processed_data = await self._inference_queue.get()

                # Run inference
                if self.gpu_manager and self.gpu_manager.get_available_gpus():
                    # Use GPU for inference
                    gpu_id = 0  # Use first GPU
                    result = await self.gpu_manager.execute_on_gpu(
                        gpu_id, self._run_inference, processed_data
                    )
                else:
                    # CPU fallback
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, self._run_inference, processed_data
                    )

                await self._postprocessing_queue.put((request_id, result))
                self._inference_queue.task_done()

            except Exception as e:
                logger.error(f"Inference error: {e}")

    async def _postprocessing_stage(self):
        """Postprocessing stage."""
        while self._running:
            try:
                request_id, inference_result = await self._postprocessing_queue.get()

                # Simulate postprocessing
                final_result = await self._postprocess_result(inference_result)

                # Store result (in production, would use a results dict)
                logger.info(f"Inference complete for {request_id}: {final_result}")

                self._postprocessing_queue.task_done()

            except Exception as e:
                logger.error(f"Postprocessing error: {e}")

    async def _preprocess_data(self, data: Any) -> Any:
        """Preprocess input data."""
        # Simulate preprocessing
        await asyncio.sleep(0.05)
        return f"preprocessed_{data}"

    def _run_inference(self, data: Any) -> Any:
        """Run model inference."""
        # Simulate GPU/CPU intensive inference
        time.sleep(0.1)  # Simulate inference time
        return f"inference_result_{data}"

    async def _postprocess_result(self, result: Any) -> Any:
        """Postprocess inference result."""
        # Simulate postprocessing
        await asyncio.sleep(0.02)
        return f"final_{result}"


class DistributedTrainingCoordinator:
    """Coordinate distributed model training across multiple nodes."""

    def __init__(self, world_size: int = 1, rank: int = 0):
        self.world_size = world_size
        self.rank = rank
        self._workers: List[Dict[str, Any]] = []
        self._running = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start distributed training coordinator."""
        if self._running:
            return

        self._running = True

        if RAY_AVAILABLE:
            # Initialize Ray for distributed training
            if not ray.is_initialized():
                ray.init(ignore_reinit_error=True)

        logger.info(f"Started DistributedTrainingCoordinator (rank {self.rank}/{self.world_size})")

    async def stop(self):
        """Stop distributed training coordinator."""
        self._running = False

        if RAY_AVAILABLE and ray.is_initialized():
            ray.shutdown()

        logger.info("Stopped DistributedTrainingCoordinator")

    async def coordinate_training_step(self, step_func: Callable, *args, **kwargs) -> Any:
        """Coordinate training step across workers."""
        if not self._running:
            await self.start()

        if self.world_size == 1:
            # Single node training
            return await asyncio.get_event_loop().run_in_executor(
                None, step_func, *args, **kwargs
            )

        # Distributed training coordination
        if RAY_AVAILABLE:
            # Use Ray for distributed coordination
            remote_func = ray.remote(step_func)

            # Submit to remote workers
            futures = []
            for i in range(self.world_size):
                if i != self.rank:  # Don't submit to self
                    future = remote_func.remote(*args, **kwargs)
                    futures.append(future)

            # Wait for all workers
            results = ray.get(futures)
            return results

        else:
            # Fallback: run locally
            return await asyncio.get_event_loop().run_in_executor(
                None, step_func, *args, **kwargs
            )

    def get_worker_status(self) -> List[Dict[str, Any]]:
        """Get status of all workers."""
        # In production, would query actual worker status
        return [
            {"worker_id": i, "status": "active", "rank": i}
            for i in range(self.world_size)
        ]

    async def synchronize_gradients(self, gradients: Any) -> Any:
        """Synchronize gradients across workers (AllReduce operation)."""
        if self.world_size == 1:
            return gradients

        # In production, would implement actual gradient synchronization
        # For demo, just return gradients unchanged
        return gradients


class DataLoaderOptimizer:
    """Optimize data loading for ML training with concurrency."""

    def __init__(self, batch_size: int = 32, num_workers: int = 4, prefetch_factor: int = 2):
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.prefetch_factor = prefetch_factor

        self._data_queue: asyncio.Queue = asyncio.Queue(maxsize=batch_size * prefetch_factor)
        self._batch_queue: asyncio.Queue = asyncio.Queue(maxsize=10)
        self._running = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start optimized data loading."""
        if self._running:
            return

        self._running = True

        # Start data loading workers
        for i in range(self.num_workers):
            asyncio.create_task(self._data_loading_worker(i))

        # Start batching worker
        asyncio.create_task(self._batching_worker())

        logger.info(f"Started DataLoaderOptimizer with {self.num_workers} workers")

    async def stop(self):
        """Stop data loading."""
        self._running = False
        logger.info("Stopped DataLoaderOptimizer")

    async def get_batch(self) -> Optional[Any]:
        """Get next batch of data."""
        try:
            return await asyncio.wait_for(self._batch_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    def add_data_source(self, data_source: Callable):
        """Add data source for loading."""
        # In production, would add to a list of data sources
        # For demo, just store the callable
        self._data_source = data_source

    async def _data_loading_worker(self, worker_id: int):
        """Individual data loading worker."""
        while self._running:
            try:
                if hasattr(self, '_data_source'):
                    # Load data from source
                    data = await asyncio.get_event_loop().run_in_executor(
                        None, self._data_source
                    )
                    await self._data_queue.put(data)
                else:
                    # Generate mock data
                    data = f"sample_data_{worker_id}_{int(time.time() * 1000)}"
                    await self._data_queue.put(data)
                    await asyncio.sleep(0.1)  # Simulate I/O time

            except Exception as e:
                logger.error(f"Data loading worker {worker_id} error: {e}")

    async def _batching_worker(self):
        """Worker that creates batches from loaded data."""
        while self._running:
            try:
                batch = []
                for _ in range(self.batch_size):
                    try:
                        data = await asyncio.wait_for(self._data_queue.get(), timeout=0.1)
                        batch.append(data)
                    except asyncio.TimeoutError:
                        break

                if batch:
                    # Create batch
                    batched_data = {
                        "batch": batch,
                        "size": len(batch),
                        "timestamp": time.time()
                    }
                    await self._batch_queue.put(batched_data)

            except Exception as e:
                logger.error(f"Batching worker error: {e}")


class AcceleratorManager:
    """Unified manager for different accelerators (GPU, TPU, etc.)."""

    def __init__(self):
        self._accelerators: Dict[str, Any] = {}
        self._device_assignments: Dict[str, str] = {}

    async def discover_accelerators(self):
        """Discover available accelerators."""
        accelerators = {}

        # GPU discovery
        if TORCH_AVAILABLE and torch.cuda.is_available():
            accelerators["gpu"] = [f"cuda:{i}" for i in range(torch.cuda.device_count())]

        # TPU discovery (if available)
        try:
            import torch_xla.core.xla_model as xm
            accelerators["tpu"] = [f"tpu:{i}" for i in range(8)]  # Assume 8 TPUs
        except ImportError:
            pass

        self._accelerators = accelerators
        logger.info(f"Discovered accelerators: {accelerators}")

    async def assign_task_to_accelerator(self, task_id: str, preferred_type: str = "gpu") -> Optional[str]:
        """Assign task to available accelerator."""
        if preferred_type not in self._accelerators:
            return None

        devices = self._accelerators[preferred_type]
        if not devices:
            return None

        # Simple round-robin assignment
        device_index = hash(task_id) % len(devices)
        device = devices[device_index]

        self._device_assignments[task_id] = device
        return device

    def get_accelerator_stats(self) -> Dict[str, Any]:
        """Get accelerator statistics."""
        return {
            "available_accelerators": self._accelerators,
            "active_assignments": len(self._device_assignments),
            "assignments": dict(self._device_assignments)
        }


# Mock data source for demonstration
def mock_data_source():
    """Mock data loading function."""
    time.sleep(0.05)  # Simulate I/O
    return f"data_{int(time.time() * 1000)}"


async def demonstrate_ml_patterns():
    """Demonstrate ML-specific concurrency patterns."""
    print("🤖 ML-Specific Concurrency Patterns Demonstration")
    print("=" * 55)

    # GPU Manager demonstration
    print("\n1. GPU Concurrency Manager:")
    gpu_manager = GPUConcurrencyManager()

    try:
        await gpu_manager.start()
        gpus = gpu_manager.get_available_gpus()
        print(f"   Available GPUs: {len(gpus)}")

        if gpus:
            for gpu in gpus:
                print(f"   GPU {gpu.device_id}: {gpu.name} ({gpu.memory_total}MB)")
        else:
            print("   No GPUs available (CPU fallback mode)")

        # Test GPU execution
        if gpus:
            result = await gpu_manager.execute_on_gpu(0, lambda: "GPU test")
            print(f"   GPU execution result: {result}")

    except Exception as e:
        print(f"   GPU manager error: {e}")

    # Model Inference Pipeline demonstration
    print("\n2. Model Inference Pipeline:")
    pipeline = ModelInferencePipeline(gpu_manager)

    await pipeline.start()

    # Submit inference requests
    request_ids = []
    for i in range(5):
        request_id = await pipeline.submit_inference_request(f"input_{i}")
        request_ids.append(request_id)
        print(f"   Submitted request: {request_id}")

    # Wait for processing
    await asyncio.sleep(1.0)

    # Get results
    for request_id in request_ids:
        result = await pipeline.get_inference_result(request_id)
        print(f"   Result for {request_id}: {result}")

    await pipeline.stop()

    # Data Loader Optimizer demonstration
    print("\n3. Data Loader Optimizer:")
    data_loader = DataLoaderOptimizer(batch_size=4, num_workers=2)

    await data_loader.start()
    data_loader.add_data_source(mock_data_source)

    # Get some batches
    for i in range(3):
        batch = await data_loader.get_batch()
        if batch:
            print(f"   Batch {i+1}: {batch['size']} items")
        else:
            print(f"   Batch {i+1}: timeout")

    await data_loader.stop()

    # Distributed Training demonstration
    print("\n4. Distributed Training Coordinator:")
    training_coordinator = DistributedTrainingCoordinator(world_size=1, rank=0)

    await training_coordinator.start()

    # Mock training step
    def training_step():
        time.sleep(0.1)  # Simulate training step
        return "training_complete"

    result = await training_coordinator.coordinate_training_step(training_step)
    print(f"   Training step result: {result}")

    worker_status = training_coordinator.get_worker_status()
    print(f"   Worker status: {len(worker_status)} workers active")

    await training_coordinator.stop()

    # Accelerator Manager demonstration
    print("\n5. Accelerator Manager:")
    accel_manager = AcceleratorManager()
    await accel_manager.discover_accelerators()

    stats = accel_manager.get_accelerator_stats()
    print(f"   Accelerators discovered: {stats['available_accelerators']}")

    print("\n✅ ML-specific concurrency patterns demonstration complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demonstrate_ml_patterns())
