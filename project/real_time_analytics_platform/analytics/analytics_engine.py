"""
Analytics Engine with Multiprocessing for Heavy Computations.

Demonstrates:
- Multiprocessing for CPU-intensive analytics
- Process pool management
- Load balancing across CPU cores
- GPU acceleration (when available)
- Performance monitoring
- Error handling and recovery
"""

import asyncio
import time
import math
import statistics
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing

# Optional ML libraries
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    import sklearn.ensemble
    import sklearn.preprocessing
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsResult:
    """Result of analytics computation."""
    task_id: str
    result: Any
    computation_time: float
    method_used: str  # 'multiprocessing', 'threading', 'gpu'
    worker_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsMetrics:
    """Metrics for analytics performance."""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_computation_time: float = 0.0
    avg_task_time: float = 0.0
    max_concurrent_workers: int = 0
    method_usage: Dict[str, int] = field(default_factory=dict)


class AnalyticsEngine:
    """
    High-performance analytics engine using multiprocessing.

    Features:
    - Automatic workload routing (CPU vs GPU vs Threading)
    - Process pool management with load balancing
    - ML model training and inference
    - Statistical analysis and anomaly detection
    - Performance monitoring and optimization
    """

    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.metrics = AnalyticsMetrics()

        # Executors for different types of work
        self._process_executor = ProcessPoolExecutor(max_workers=self.max_workers)
        self._thread_executor = ThreadPoolExecutor(max_workers=self.max_workers * 2)

        # GPU support (if available)
        self._gpu_available = self._check_gpu_availability()
        self._gpu_executor = None  # Would initialize GPU context

        # Task tracking
        self._active_tasks: Dict[str, asyncio.Future] = {}
        self._task_lock = asyncio.Lock()

        logger.info(f"Initialized AnalyticsEngine with {self.max_workers} workers "
                   f"(GPU: {'available' if self._gpu_available else 'unavailable'})")

    def _check_gpu_availability(self) -> bool:
        """Check if GPU acceleration is available."""
        try:
            # Check for CUDA availability (simplified)
            import subprocess
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    async def execute_analytics(
        self,
        task_func: Callable,
        data: Any,
        task_id: Optional[str] = None,
        priority: str = "normal"
    ) -> AnalyticsResult:
        """
        Execute analytics task with automatic workload routing.

        Args:
            task_func: Function to execute
            data: Input data for the task
            task_id: Optional task identifier
            priority: Task priority ('low', 'normal', 'high', 'critical')
        """
        if task_id is None:
            task_id = f"task_{int(time.time()*1000)}_{id(data)}"

        start_time = time.time()

        try:
            # Determine execution method based on task characteristics
            method = self._determine_execution_method(task_func, data, priority)

            # Execute task using appropriate method
            if method == "multiprocessing":
                result = await self._execute_with_process_pool(task_func, data, task_id)
            elif method == "gpu":
                result = await self._execute_with_gpu(task_func, data, task_id)
            else:  # threading or fallback
                result = await self._execute_with_thread_pool(task_func, data, task_id)

            computation_time = time.time() - start_time

            # Update metrics
            self.metrics.total_tasks += 1
            self.metrics.successful_tasks += 1
            self.metrics.total_computation_time += computation_time
            self.metrics.avg_task_time = (
                self.metrics.total_computation_time / self.metrics.total_tasks
            )
            self.metrics.method_usage[method] = self.metrics.method_usage.get(method, 0) + 1

            return AnalyticsResult(
                task_id=task_id,
                result=result,
                computation_time=computation_time,
                method_used=method,
                metadata={"priority": priority}
            )

        except Exception as e:
            computation_time = time.time() - start_time
            self.metrics.total_tasks += 1
            self.metrics.failed_tasks += 1

            logger.error(f"Analytics task {task_id} failed: {e}")

            return AnalyticsResult(
                task_id=task_id,
                result=None,
                computation_time=computation_time,
                method_used="failed",
                metadata={"error": str(e), "priority": priority}
            )

    def _determine_execution_method(self, task_func: Callable, data: Any, priority: str) -> str:
        """Determine the best execution method for a task."""
        func_name = getattr(task_func, '__name__', str(task_func)).lower()

        # High priority tasks get dedicated processing
        if priority in ["high", "critical"]:
            return "multiprocessing"

        # ML/AI tasks benefit from GPU if available
        if self._gpu_available and any(keyword in func_name for keyword in
                                     ["ml", "predict", "train", "model", "neural", "tensor"]):
            return "gpu"

        # CPU-intensive tasks (math, statistics, large data processing)
        if any(keyword in func_name for keyword in
               ["statistics", "math", "analyze", "compute", "heavy", "cpu"]):
            return "multiprocessing"

        # Large data processing
        if isinstance(data, (list, dict)) and len(str(data)) > 10000:  # Rough size estimate
            return "multiprocessing"

        # I/O bound or light CPU tasks use threading
        return "threading"

    async def _execute_with_process_pool(self, task_func: Callable, data: Any, task_id: str) -> Any:
        """Execute task using process pool."""
        async with self._task_lock:
            self._active_tasks[task_id] = asyncio.Future()

        try:
            # Submit to process pool
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(self._process_executor, task_func, data)

            result = await future
            self._active_tasks[task_id].set_result(result)
            return result

        finally:
            async with self._task_lock:
                del self._active_tasks[task_id]

    async def _execute_with_thread_pool(self, task_func: Callable, data: Any, task_id: str) -> Any:
        """Execute task using thread pool."""
        async with self._task_lock:
            self._active_tasks[task_id] = asyncio.Future()

        try:
            # Submit to thread pool
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(self._thread_executor, task_func, data)

            result = await future
            self._active_tasks[task_id].set_result(result)
            return result

        finally:
            async with self._task_lock:
                del self._active_tasks[task_id]

    async def _execute_with_gpu(self, task_func: Callable, data: Any, task_id: str) -> Any:
        """Execute task with GPU acceleration (simplified)."""
        # In real implementation, this would use CUDA, TensorFlow GPU, etc.
        # For demo, we'll simulate GPU processing with a slight performance boost
        logger.info(f"Executing {task_id} with GPU acceleration")

        async with self._task_lock:
            self._active_tasks[task_id] = asyncio.Future()

        try:
            # Simulate GPU processing (faster than CPU for ML tasks)
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(self._process_executor, task_func, data)

            result = await future
            self._active_tasks[task_id].set_result(result)
            return result

        finally:
            async with self._task_lock:
                del self._active_tasks[task_id]

    async def execute_batch(
        self,
        tasks: List[tuple],
        priority: str = "normal"
    ) -> List[AnalyticsResult]:
        """
        Execute multiple analytics tasks in batch.

        Args:
            tasks: List of (task_func, data, task_id) tuples
            priority: Batch priority
        """
        logger.info(f"Executing batch of {len(tasks)} analytics tasks")

        # Execute all tasks concurrently
        batch_tasks = [
            self.execute_analytics(task_func, data, task_id, priority)
            for task_func, data, task_id in tasks
        ]

        results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create failed result for exceptions
                task_func, data, task_id = tasks[i]
                processed_results.append(AnalyticsResult(
                    task_id=task_id or f"batch_task_{i}",
                    result=None,
                    computation_time=0.0,
                    method_used="failed",
                    metadata={"error": str(result)}
                ))
            else:
                processed_results.append(result)

        return processed_results

    def get_metrics(self) -> Dict[str, Any]:
        """Get analytics engine performance metrics."""
        return {
            "total_tasks": self.metrics.total_tasks,
            "successful_tasks": self.metrics.successful_tasks,
            "failed_tasks": self.metrics.failed_tasks,
            "success_rate": (
                self.metrics.successful_tasks / max(1, self.metrics.total_tasks)
            ),
            "avg_task_time": self.metrics.avg_task_time,
            "total_computation_time": self.metrics.total_computation_time,
            "method_usage": self.metrics.method_usage,
            "active_tasks": len(self._active_tasks),
            "max_workers": self.max_workers,
            "gpu_available": self._gpu_available
        }

    async def shutdown(self):
        """Shutdown the analytics engine."""
        logger.info("Shutting down AnalyticsEngine...")

        # Cancel active tasks
        async with self._task_lock:
            for task_id, future in self._active_tasks.items():
                if not future.done():
                    future.cancel()

        # Shutdown executors
        self._process_executor.shutdown(wait=True)
        self._thread_executor.shutdown(wait=True)

        logger.info("AnalyticsEngine shutdown complete")


# Pre-built analytics functions for demonstration
def statistical_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform statistical analysis on data."""
    # Simulate CPU-intensive statistical computation
    time.sleep(0.1)  # Simulate processing time

    if "values" in data and isinstance(data["values"], list):
        values = data["values"]
        if len(values) > 1:
            return {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values),
                "min": min(values),
                "max": max(values),
                "quartiles": statistics.quantiles(values, n=4)
            }

    return {"error": "Invalid data format for statistical analysis"}


def anomaly_detection(data: Dict[str, Any]) -> Dict[str, Any]:
    """Detect anomalies in data using statistical methods."""
    # Simulate ML-style anomaly detection
    time.sleep(0.15)  # Simulate heavier computation

    if "metrics" in data and isinstance(data["metrics"], list):
        metrics = data["metrics"]
        if len(metrics) > 0:
            # Simple anomaly detection based on standard deviations
            mean_val = statistics.mean(metrics)
            std_dev = statistics.stdev(metrics) if len(metrics) > 1 else 0

            anomalies = []
            for i, val in enumerate(metrics):
                z_score = abs(val - mean_val) / max(std_dev, 0.001)
                if z_score > 3.0:  # 3 standard deviations
                    anomalies.append({
                        "index": i,
                        "value": val,
                        "z_score": z_score,
                        "severity": "high" if z_score > 5 else "medium"
                    })

            return {
                "total_points": len(metrics),
                "anomalies_detected": len(anomalies),
                "anomaly_rate": len(anomalies) / len(metrics),
                "anomalies": anomalies[:10],  # Limit for performance
                "mean": mean_val,
                "std_dev": std_dev
            }

    return {"error": "Invalid data format for anomaly detection"}


def predictive_analytics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform predictive analytics."""
    # Simulate predictive modeling
    time.sleep(0.2)  # Simulate complex computation

    if HAS_NUMPY and HAS_SKLEARN and "features" in data:
        try:
            features = np.array(data["features"])
            # Simple random forest prediction simulation
            predictions = np.random.rand(len(features)) * 100

            return {
                "predictions": predictions.tolist(),
                "model_type": "random_forest",
                "confidence": np.random.rand(len(features)).tolist(),
                "feature_importance": np.random.rand(features.shape[1]).tolist()
            }
        except Exception as e:
            return {"error": f"ML prediction failed: {e}"}

    # Fallback without ML libraries
    if "features" in data and isinstance(data["features"], list):
        predictions = [sum(row) * 0.1 + 50 for row in data["features"]]
        return {
            "predictions": predictions,
            "model_type": "linear_fallback",
            "note": "Install numpy, scikit-learn for full ML capabilities"
        }

    return {"error": "Invalid data format for predictive analytics"}


def user_behavior_analytics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze user behavior patterns."""
    # Simulate user analytics
    time.sleep(0.05)  # Lighter computation

    user_id = data.get("user_id", "unknown")
    actions = data.get("actions", [])
    revenue = data.get("revenue", 0)

    # Behavioral scoring
    engagement_score = min(100, len(actions) * 10)
    loyalty_score = min(100, revenue / 10)
    risk_score = 20 if revenue > 500 else 5  # High spenders might be risky

    return {
        "user_id": user_id,
        "engagement_score": engagement_score,
        "loyalty_score": loyalty_score,
        "risk_score": risk_score,
        "segment": "premium" if loyalty_score > 70 else "standard",
        "recommendations": [
            "Increase engagement" if engagement_score < 50 else None,
            "Risk mitigation needed" if risk_score > 50 else None
        ]
    }
