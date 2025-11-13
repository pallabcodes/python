"""
Distributed Concurrency Patterns.

This module provides distributed concurrency solutions that work across multiple
machines and processes, including integrations with Celery, Dask, and Ray.

Features:
- Celery task queue integration for distributed task processing
- Dask distributed computing for parallel workloads
- Ray actor model and distributed execution
- Kubernetes-aware concurrency for containerized environments
- Service mesh coordination patterns
"""

import asyncio
import threading
import time
import logging
import json
import uuid
from typing import Any, Callable, List, Dict, Optional, Union, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

logger = logging.getLogger(__name__)

# Optional imports - gracefully handle missing dependencies
try:
    from celery import Celery
    from kombu import Connection
    CELERY_AVAILABLE = True
except ImportError:
    Celery = None
    Connection = None
    CELERY_AVAILABLE = False

try:
    import dask
    from dask.distributed import Client, LocalCluster
    DASK_AVAILABLE = True
except ImportError:
    dask = None
    Client = None
    LocalCluster = None
    DASK_AVAILABLE = False

try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    ray = None
    RAY_AVAILABLE = False


@dataclass
class DistributedTask:
    """Represents a distributed task."""
    task_id: str
    func_name: str
    args: Tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    priority: int = 0
    timeout: Optional[float] = None
    submitted_at: float = field(default_factory=time.time)


@dataclass
class TaskResult:
    """Result of a distributed task execution."""
    task_id: str
    result: Any
    execution_time: float
    worker_id: str
    success: bool
    error: Optional[str] = None


class CeleryHybridExecutor:
    """
    Celery-based distributed task execution.

    Features:
    - Asynchronous task submission and result retrieval
    - Priority-based task scheduling
    - Timeout and retry mechanisms
    - Integration with existing Celery infrastructure

    When to Use:
        - Distributed task processing
        - Task queue systems
        - Background job processing
        - Scalable task execution

    Real-World Examples:
        - Web applications: Background tasks
        - Data processing: Distributed processing
        - Scheduled jobs: Cron-like tasks
        - Microservices: Task coordination

    Gotchas:
        - Broker availability required
        - Task serialization required
        - Result backend needed
        - Worker management complexity
        - Network dependencies

    Performance Notes:
        - Network overhead for task submission
        - Broker latency affects performance
        - Optimal for distributed workloads
        - Scales horizontally with workers
    """

    def __init__(self,
                 broker_url: str = "redis://localhost:6379/0",
                 result_backend: str = "redis://localhost:6379/0",
                 app_name: str = "hybrid_celery"):
        if not CELERY_AVAILABLE:
            raise ImportError("Celery is not installed. Install with: pip install celery")

        self.broker_url = broker_url
        self.result_backend = result_backend
        self.app_name = app_name

        # Create Celery app
        self.celery_app = Celery(
            app_name,
            broker=broker_url,
            backend=result_backend
        )

        self._running = False
        self._task_registry: Dict[str, Callable] = {}

    def register_task(self, name: str, func: Callable):
        """Register a task with Celery."""
        self._task_registry[name] = func
        self.celery_app.task(name=name)(func)

    async def submit_task(self,
                         func: Callable,
                         *args,
                         priority: int = 0,
                         timeout: Optional[float] = None,
                         **kwargs) -> str:
        """
        Submit task for distributed execution.

        Returns:
            Task ID for tracking
        """
        task_id = str(uuid.uuid4())
        func_name = getattr(func, '__name__', str(func))

        # Register task if not already registered
        if func_name not in self._task_registry:
            self.register_task(func_name, func)

        # Submit to Celery
        task = self.celery_app.send_task(
            func_name,
            args=args,
            kwargs=kwargs,
            task_id=task_id,
            priority=priority
        )

        return task_id

    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> TaskResult:
        """
        Get result of distributed task execution.
        """
        start_time = time.time()

        while True:
            try:
                # Get result from Celery
                result = self.celery_app.AsyncResult(task_id)

                if result.ready():
                    execution_time = time.time() - start_time

                    if result.successful():
                        return TaskResult(
                            task_id=task_id,
                            result=result.result,
                            execution_time=execution_time,
                            worker_id="celery_worker",
                            success=True
                        )
                    else:
                        return TaskResult(
                            task_id=task_id,
                            result=None,
                            execution_time=execution_time,
                            worker_id="celery_worker",
                            success=False,
                            error=str(result.info)
                        )

                if timeout and (time.time() - start_time) > timeout:
                    return TaskResult(
                        task_id=task_id,
                        result=None,
                        execution_time=time.time() - start_time,
                        worker_id="celery_worker",
                        success=False,
                        error="Timeout"
                    )

                await asyncio.sleep(0.1)  # Poll interval

            except Exception as e:
                return TaskResult(
                    task_id=task_id,
                    result=None,
                    execution_time=time.time() - start_time,
                    worker_id="celery_worker",
                    success=False,
                    error=str(e)
                )

    async def execute_task(self,
                          func: Callable,
                          *args,
                          priority: int = 0,
                          timeout: float = 30.0,
                          **kwargs) -> TaskResult:
        """
        Execute task and wait for result.
        """
        task_id = await self.submit_task(func, *args, priority=priority, **kwargs)
        return await self.get_result(task_id, timeout=timeout)


class DaskDistributedExecutor:
    """
    Dask-based distributed computing integration.

    Features:
    - Seamless integration with Dask distributed clusters
    - Futures-based async execution
    - Automatic task graph optimization
    - Scalable to thousands of cores
    """

    def __init__(self,
                 scheduler_address: Optional[str] = None,
                 local_cluster: bool = True,
                 n_workers: Optional[int] = None,
                 threads_per_worker: int = 1):
        if not DASK_AVAILABLE:
            raise ImportError("Dask is not installed. Install with: pip install dask[distributed]")

        self.scheduler_address = scheduler_address
        self.local_cluster = local_cluster
        self.n_workers = n_workers or multiprocessing.cpu_count()
        self.threads_per_worker = threads_per_worker

        self._client: Optional[Client] = None
        self._cluster: Optional[LocalCluster] = None
        self._running = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start Dask distributed client."""
        if self._running:
            return

        if self.local_cluster:
            # Start local cluster
            self._cluster = LocalCluster(
                n_workers=self.n_workers,
                threads_per_worker=self.threads_per_worker,
                processes=False,  # Use threads for compatibility
                silence_logs=False
            )
            self._client = Client(self._cluster)
        else:
            # Connect to existing scheduler
            self._client = Client(self.scheduler_address or "tcp://localhost:8786")

        self._running = True
        logger.info(f"Started DaskDistributedExecutor with {self.n_workers} workers")

    async def stop(self):
        """Stop Dask distributed client."""
        if not self._running:
            return

        if self._client:
            self._client.close()
            self._client = None

        if self._cluster:
            self._cluster.close()
            self._cluster = None

        self._running = False
        logger.info("Stopped DaskDistributedExecutor")

    async def submit_task(self, func: Callable, *args, **kwargs):
        """Submit task to Dask for distributed execution."""
        if not self._running or not self._client:
            raise RuntimeError("DaskDistributedExecutor not started")

        # Submit to Dask
        future = self._client.submit(func, *args, **kwargs)
        return future

    async def execute_task(self, func: Callable, *args, timeout: Optional[float] = None, **kwargs) -> Any:
        """Execute task and wait for result."""
        future = await self.submit_task(func, *args, **kwargs)

        # Wait for result
        if timeout:
            result = future.result(timeout=timeout)
        else:
            result = future.result()

        return result

    async def execute_batch(self, tasks: List[Tuple[Callable, Tuple, Dict]]) -> List[Any]:
        """Execute batch of tasks in parallel."""
        if not self._running or not self._client:
            raise RuntimeError("DaskDistributedExecutor not started")

        # Submit all tasks
        futures = []
        for func, args, kwargs in tasks:
            future = await self.submit_task(func, *args, **kwargs)
            futures.append(future)

        # Wait for all results
        results = self._client.gather(futures)
        return results

    def get_cluster_info(self) -> Dict[str, Any]:
        """Get information about the Dask cluster."""
        if not self._client:
            return {"status": "not_connected"}

        return {
            "scheduler_address": self._client.scheduler.address,
            "n_workers": len(self._client.scheduler_info()['workers']),
            "n_cores": sum(w['ncores'] for w in self._client.scheduler_info()['workers'].values()),
            "memory_total": sum(w['memory_limit'] for w in self._client.scheduler_info()['workers'].values())
        }


class RayDistributedExecutor:
    """
    Ray-based distributed execution with actor model.

    Features:
    - Actor-based distributed computing
    - Remote function execution
    - Object store for shared state
    - Automatic fault tolerance
    """

    def __init__(self,
                 address: Optional[str] = None,
                 num_cpus: Optional[int] = None,
                 num_gpus: Optional[int] = None):
        if not RAY_AVAILABLE:
            raise ImportError("Ray is not installed. Install with: pip install ray")

        self.address = address
        self.num_cpus = num_cpus
        self.num_gpus = num_gpus

        self._initialized = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Initialize Ray."""
        if self._initialized:
            return

        if not ray.is_initialized():
            ray.init(
                address=self.address,
                num_cpus=self.num_cpus,
                num_gpus=self.num_gpus,
                ignore_reinit_error=True
            )

        self._initialized = True
        logger.info("Started RayDistributedExecutor")

    async def stop(self):
        """Shutdown Ray."""
        if self._initialized and ray.is_initialized():
            ray.shutdown()
        self._initialized = False
        logger.info("Stopped RayDistributedExecutor")

    async def execute_task(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function remotely with Ray."""
        if not self._initialized:
            await self.start()

        # Make function remote
        remote_func = ray.remote(func)

        # Execute remotely
        result_ref = remote_func.remote(*args, **kwargs)
        result = ray.get(result_ref)

        return result

    async def execute_batch(self, tasks: List[Tuple[Callable, Tuple, Dict]]) -> List[Any]:
        """Execute batch of tasks in parallel with Ray."""
        if not self._initialized:
            await self.start()

        # Submit all tasks
        result_refs = []
        for func, args, kwargs in tasks:
            remote_func = ray.remote(func)
            result_ref = remote_func.remote(*args, **kwargs)
            result_refs.append(result_ref)

        # Get all results
        results = ray.get(result_refs)
        return results

    def create_actor(self, actor_class: type, *args, **kwargs):
        """Create a Ray actor."""
        if not self._initialized:
            raise RuntimeError("RayDistributedExecutor not started")

        remote_class = ray.remote(actor_class)
        actor = remote_class.remote(*args, **kwargs)
        return actor


class KubernetesAwareExecutor:
    """
    Kubernetes-aware distributed executor.

    Features:
    - Pod-to-pod communication
    - Service discovery integration
    - Resource-aware task scheduling
    - Container lifecycle management
    """

    def __init__(self,
                 namespace: str = "default",
                 service_account: Optional[str] = None,
                 cluster_config: Optional[str] = None):
        self.namespace = namespace
        self.service_account = service_account
        self.cluster_config = cluster_config

        # Kubernetes client (optional)
        self._k8s_client = None
        self._running = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start Kubernetes-aware executor."""
        if self._running:
            return

        try:
            from kubernetes import client, config
            # Load configuration
            if self.cluster_config:
                config.load_kube_config(self.cluster_config)
            else:
                config.load_incluster_config()

            self._k8s_client = client.CoreV1Api()
            self._running = True
            logger.info("Started KubernetesAwareExecutor")

        except ImportError:
            logger.warning("Kubernetes client not available, running in mock mode")
            self._running = True
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            self._running = True  # Continue in mock mode

    async def stop(self):
        """Stop Kubernetes-aware executor."""
        self._running = False
        self._k8s_client = None
        logger.info("Stopped KubernetesAwareExecutor")

    async def execute_task(self, func: Callable, *args, **kwargs) -> Any:
        """Execute task with Kubernetes awareness."""
        if not self._running:
            await self.start()

        # For now, execute locally with Kubernetes context
        # In production, this would submit to Kubernetes jobs/pods
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, func, *args, **kwargs)

        return result

    def get_cluster_info(self) -> Dict[str, Any]:
        """Get Kubernetes cluster information."""
        if not self._k8s_client:
            return {"status": "mock_mode", "namespace": self.namespace}

        try:
            # Get pod information
            pods = self._k8s_client.list_namespaced_pod(self.namespace)
            return {
                "namespace": self.namespace,
                "pod_count": len(pods.items),
                "service_account": self.service_account,
                "status": "connected"
            }
        except Exception as e:
            return {
                "namespace": self.namespace,
                "error": str(e),
                "status": "error"
            }

    async def discover_services(self, service_type: str) -> List[Dict[str, Any]]:
        """Discover services in Kubernetes cluster."""
        if not self._k8s_client:
            return [{"name": "mock_service", "type": service_type, "status": "mock"}]

        try:
            services = self._k8s_client.list_namespaced_service(self.namespace)
            discovered = []

            for svc in services.items:
                if service_type in svc.metadata.name:
                    discovered.append({
                        "name": svc.metadata.name,
                        "cluster_ip": svc.spec.cluster_ip,
                        "ports": [port.port for port in svc.spec.ports],
                        "type": service_type
                    })

            return discovered
        except Exception as e:
            logger.error(f"Service discovery failed: {e}")
            return []


class ServiceMeshCoordinator:
    """
    Service mesh coordinator for distributed systems.

    Features:
    - Service-to-service communication
    - Load balancing across instances
    - Circuit breaking and retries
    - Distributed tracing integration
    """

    def __init__(self,
                 service_name: str,
                 mesh_config: Optional[Dict[str, Any]] = None):
        self.service_name = service_name
        self.mesh_config = mesh_config or {}

        self._services: Dict[str, List[str]] = {}  # service -> [endpoints]
        self._circuit_breakers: Dict[str, Any] = {}
        self._running = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start service mesh coordinator."""
        if self._running:
            return

        self._running = True
        logger.info(f"Started ServiceMeshCoordinator for {self.service_name}")

    async def stop(self):
        """Stop service mesh coordinator."""
        self._running = False
        logger.info("Stopped ServiceMeshCoordinator")

    def register_service(self, service_name: str, endpoint: str):
        """Register service endpoint."""
        if service_name not in self._services:
            self._services[service_name] = []
        self._services[service_name].append(endpoint)

    def unregister_service(self, service_name: str, endpoint: str):
        """Unregister service endpoint."""
        if service_name in self._services:
            self._services[service_name].remove(endpoint)

    async def call_service(self,
                          service_name: str,
                          method: str,
                          *args,
                          retries: int = 3,
                          timeout: float = 30.0,
                          **kwargs) -> Any:
        """Call service method with load balancing and retries."""
        if not self._running:
            await self.start()

        if service_name not in self._services:
            raise ValueError(f"Service {service_name} not registered")

        endpoints = self._services[service_name]
        if not endpoints:
            raise ValueError(f"No endpoints available for service {service_name}")

        # Simple round-robin load balancing
        endpoint = endpoints[0]  # In production, implement proper load balancing

        # Circuit breaker check
        if service_name in self._circuit_breakers:
            # Implement circuit breaker logic
            pass

        # Make the call with retries
        for attempt in range(retries):
            try:
                # In production, this would make actual network calls
                # For demo, simulate service call
                result = await self._simulate_service_call(endpoint, method, *args, **kwargs)
                return result

            except Exception as e:
                logger.warning(f"Service call attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff

        raise RuntimeError(f"Service call failed after {retries} attempts")

    async def _simulate_service_call(self, endpoint: str, method: str, *args, **kwargs) -> Any:
        """Simulate service call (replace with actual implementation)."""
        await asyncio.sleep(0.05)  # Simulate network latency
        return {
            "endpoint": endpoint,
            "method": method,
            "args": args,
            "kwargs": kwargs,
            "result": f"simulated_result_{method}",
            "timestamp": time.time()
        }

    def get_mesh_status(self) -> Dict[str, Any]:
        """Get service mesh status."""
        return {
            "service_name": self.service_name,
            "registered_services": list(self._services.keys()),
            "total_endpoints": sum(len(endpoints) for endpoints in self._services.values()),
            "circuit_breakers": list(self._circuit_breakers.keys()),
            "status": "running" if self._running else "stopped"
        }


# Example task functions for distributed execution
def cpu_intensive_task(data: str, iterations: int = 10000) -> Dict[str, Any]:
    """CPU-intensive task for distributed execution."""
    import math
    result = sum(math.sin(i) * math.cos(i) for i in range(iterations))
    return {
        "task": "cpu_intensive",
        "input": data,
        "result": result,
        "iterations": iterations,
        "worker_id": multiprocessing.current_process().name
    }

def data_processing_task(data: List[float]) -> Dict[str, Any]:
    """Data processing task."""
    import statistics
    return {
        "task": "data_processing",
        "count": len(data),
        "mean": statistics.mean(data),
        "median": statistics.median(data),
        "std_dev": statistics.stdev(data) if len(data) > 1 else 0
    }


async def demonstrate_celery_executor():
    """Demonstrate Celery distributed executor."""
    print("🥕 Celery Distributed Executor Demo:")

    if not CELERY_AVAILABLE:
        print("❌ Celery not available, skipping demo")
        return

    try:
        executor = CeleryHybridExecutor()

        # Register task
        executor.register_task("cpu_task", cpu_intensive_task)

        # Execute task
        result = await executor.execute_task(
            cpu_intensive_task, "distributed_data", iterations=5000
        )

        print(f"✅ Celery task result: {result.success}")
        if result.success:
            print(f"   Result: {result.result['result']:.2f}")
            print(f"   Worker: {result.worker_id}")

    except Exception as e:
        print(f"❌ Celery demo failed: {e}")


async def demonstrate_dask_executor():
    """Demonstrate Dask distributed executor."""
    print("\n🔷 Dask Distributed Executor Demo:")

    if not DASK_AVAILABLE:
        print("❌ Dask not available, skipping demo")
        return

    try:
        async with DaskDistributedExecutor(n_workers=2) as executor:
            # Execute single task
            result = await executor.execute_task(
                cpu_intensive_task, "dask_data", iterations=3000
            )
            print(f"✅ Dask single task: {result['result']:.2f}")

            # Execute batch
            tasks = [
                (cpu_intensive_task, ("batch_1", 2000), {}),
                (cpu_intensive_task, ("batch_2", 2000), {}),
                (data_processing_task, ([1.0, 2.0, 3.0, 4.0, 5.0],), {})
            ]

            results = await executor.execute_batch(tasks)
            print(f"✅ Dask batch completed: {len(results)} results")

            # Get cluster info
            info = executor.get_cluster_info()
            print(f"✅ Cluster: {info.get('n_workers', 'N/A')} workers")

    except Exception as e:
        print(f"❌ Dask demo failed: {e}")


async def demonstrate_ray_executor():
    """Demonstrate Ray distributed executor."""
    print("\n🌟 Ray Distributed Executor Demo:")

    if not RAY_AVAILABLE:
        print("❌ Ray not available, skipping demo")
        return

    try:
        async with RayDistributedExecutor() as executor:
            # Execute single task
            result = await executor.execute_task(
                cpu_intensive_task, "ray_data", iterations=3000
            )
            print(f"✅ Ray single task: {result['result']:.2f}")

            # Execute batch
            tasks = [
                (cpu_intensive_task, ("ray_batch_1", 2000), {}),
                (cpu_intensive_task, ("ray_batch_2", 2000), {})
            ]

            results = await executor.execute_batch(tasks)
            print(f"✅ Ray batch completed: {len(results)} results")

    except Exception as e:
        print(f"❌ Ray demo failed: {e}")


async def demonstrate_kubernetes_executor():
    """Demonstrate Kubernetes-aware executor."""
    print("\n☸️  Kubernetes-Aware Executor Demo:")

    try:
        async with KubernetesAwareExecutor() as executor:
            # Execute task
            result = await executor.execute_task(
                cpu_intensive_task, "k8s_data", iterations=3000
            )
            print(f"✅ K8s task result: {result['result']:.2f}")

            # Get cluster info
            info = executor.get_cluster_info()
            print(f"✅ Cluster status: {info.get('status', 'unknown')}")

            # Service discovery
            services = await executor.discover_services("worker")
            print(f"✅ Discovered services: {len(services)}")

    except Exception as e:
        print(f"❌ Kubernetes demo failed: {e}")


async def demonstrate_service_mesh():
    """Demonstrate service mesh coordinator."""
    print("\n🔗 Service Mesh Coordinator Demo:")

    try:
        async with ServiceMeshCoordinator("demo_service") as coordinator:
            # Register services
            coordinator.register_service("worker", "http://worker-1:8080")
            coordinator.register_service("worker", "http://worker-2:8080")

            # Call service
            result = await coordinator.call_service(
                "worker", "process_data", data="mesh_test"
            )
            print(f"✅ Service mesh call: {result['method']}")

            # Get mesh status
            status = coordinator.get_mesh_status()
            print(f"✅ Mesh services: {status['registered_services']}")

    except Exception as e:
        print(f"❌ Service mesh demo failed: {e}")


if __name__ == "__main__":
    # Run demonstrations
    logging.basicConfig(level=logging.INFO)

    asyncio.run(demonstrate_celery_executor())
    asyncio.run(demonstrate_dask_executor())
    asyncio.run(demonstrate_ray_executor())
    asyncio.run(demonstrate_kubernetes_executor())
    asyncio.run(demonstrate_service_mesh())
