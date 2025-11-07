"""
Container-Aware Concurrency Patterns.

This module provides concurrency patterns optimized for containerized
environments including Docker and Kubernetes integration.

Features:
- Docker container communication
- Kubernetes pod-to-pod concurrency
- Service discovery integration
- Container lifecycle management
"""

import asyncio
import threading
import time
import logging
import json
import socket
from typing import Any, Callable, List, Dict, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Optional container imports
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    docker = None
    DOCKER_AVAILABLE = False

try:
    from kubernetes import client, config
    KUBERNETES_AVAILABLE = True
except ImportError:
    client = None
    config = None
    KUBERNETES_AVAILABLE = False


@dataclass
class ContainerInfo:
    """Information about a container."""
    container_id: str
    name: str
    image: str
    status: str
    ports: Dict[str, Any]
    networks: List[str]
    ip_address: Optional[str] = None


class DockerCommunicator:
    """Docker container communication and management."""

    def __init__(self, docker_url: str = "unix://var/run/docker.sock"):
        if not DOCKER_AVAILABLE:
            raise ImportError("Docker SDK not available")

        self.docker_client = docker.DockerClient(base_url=docker_url)
        self._running = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start Docker communicator."""
        if self._running:
            return

        try:
            # Test connection
            self.docker_client.ping()
            self._running = True
            logger.info("Started DockerCommunicator")
        except Exception as e:
            logger.error(f"Docker connection failed: {e}")
            raise

    async def stop(self):
        """Stop Docker communicator."""
        if not self._running:
            return

        self.docker_client.close()
        self._running = False
        logger.info("Stopped DockerCommunicator")

    def list_containers(self, filters: Optional[Dict] = None) -> List[ContainerInfo]:
        """List running containers."""
        containers = self.docker_client.containers.list(filters=filters or {})

        result = []
        for container in containers:
            networks = list(container.attrs['NetworkSettings']['Networks'].keys())

            # Get IP address
            ip_address = None
            if networks:
                network_name = networks[0]
                network_info = container.attrs['NetworkSettings']['Networks'].get(network_name)
                if network_info:
                    ip_address = network_info.get('IPAddress')

            info = ContainerInfo(
                container_id=container.id,
                name=container.name,
                image=container.attrs['Config']['Image'],
                status=container.status,
                ports=container.ports,
                networks=networks,
                ip_address=ip_address
            )
            result.append(info)

        return result

    async def execute_in_container(self, container_id: str, command: str) -> str:
        """Execute command in container."""
        def run_command():
            container = self.docker_client.containers.get(container_id)
            result = container.exec_run(command)
            return result.output.decode('utf-8')

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_command)

    async def create_worker_container(self, image: str, command: List[str]) -> str:
        """Create worker container for distributed tasks."""
        def create_container():
            container = self.docker_client.containers.run(
                image=image,
                command=command,
                detach=True,
                remove=True  # Auto-remove when stopped
            )
            return container.id

        loop = asyncio.get_event_loop()
        container_id = await loop.run_in_executor(None, create_container)

        # Wait for container to start
        await asyncio.sleep(1.0)

        return container_id

    async def monitor_containers(self, callback: Callable[[List[ContainerInfo]], None]):
        """Monitor container status changes."""
        last_containers = set()

        while self._running:
            try:
                containers = self.list_containers()
                current_ids = {c.container_id for c in containers}

                # Check for changes
                if current_ids != last_containers:
                    callback(containers)
                    last_containers = current_ids

            except Exception as e:
                logger.error(f"Container monitoring error: {e}")

            await asyncio.sleep(5.0)  # Check every 5 seconds


class KubernetesCoordinator:
    """Kubernetes-aware task coordination."""

    def __init__(self, namespace: str = "default"):
        if not KUBERNETES_AVAILABLE:
            raise ImportError("Kubernetes client not available")

        self.namespace = namespace
        self._k8s_client = None
        self._running = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start Kubernetes coordinator."""
        if self._running:
            return

        try:
            # Load configuration
            config.load_incluster_config()
            self._k8s_client = client.CoreV1Api()
            self._running = True
            logger.info(f"Started KubernetesCoordinator in namespace {self.namespace}")
        except Exception as e:
            logger.error(f"Kubernetes connection failed: {e}")
            raise

    async def stop(self):
        """Stop Kubernetes coordinator."""
        self._running = False
        logger.info("Stopped KubernetesCoordinator")

    def get_pods(self, labels: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Get pods with optional label filtering."""
        if not self._k8s_client:
            return []

        try:
            label_selector = ",".join(f"{k}={v}" for k, v in (labels or {}).items())
            pods = self._k8s_client.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=label_selector
            )

            result = []
            for pod in pods.items:
                result.append({
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip,
                    "node": pod.spec.node_name,
                    "labels": pod.metadata.labels or {},
                    "containers": [c.name for c in pod.spec.containers]
                })

            return result

        except Exception as e:
            logger.error(f"Pod listing failed: {e}")
            return []

    async def create_job(self, job_name: str, image: str, command: List[str]) -> str:
        """Create Kubernetes job for task execution."""
        if not self._k8s_client:
            raise RuntimeError("Kubernetes client not initialized")

        # Create job specification
        job_manifest = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": job_name,
                "namespace": self.namespace
            },
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "name": "worker",
                            "image": image,
                            "command": command
                        }],
                        "restartPolicy": "Never"
                    }
                }
            }
        }

        def create_job():
            batch_client = client.BatchV1Api()
            batch_client.create_namespaced_job(
                namespace=self.namespace,
                body=job_manifest
            )
            return job_name

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, create_job)

    async def wait_for_job_completion(self, job_name: str, timeout: float = 300.0) -> Dict[str, Any]:
        """Wait for job completion."""
        if not self._k8s_client:
            raise RuntimeError("Kubernetes client not initialized")

        start_time = time.time()

        def check_job_status():
            batch_client = client.BatchV1Api()
            job = batch_client.read_namespaced_job(
                name=job_name,
                namespace=self.namespace
            )

            # Check if job completed
            if job.status.succeeded is not None and job.status.succeeded > 0:
                return {"status": "completed", "succeeded": job.status.succeeded}
            elif job.status.failed is not None and job.status.failed > 0:
                return {"status": "failed", "failed": job.status.failed}
            else:
                return {"status": "running"}

        while time.time() - start_time < timeout:
            status = await asyncio.get_event_loop().run_in_executor(None, check_job_status)

            if status["status"] in ["completed", "failed"]:
                return status

            await asyncio.sleep(5.0)

        return {"status": "timeout", "message": "Job did not complete within timeout"}

    async def scale_deployment(self, deployment_name: str, replicas: int) -> bool:
        """Scale Kubernetes deployment."""
        if not self._k8s_client:
            raise RuntimeError("Kubernetes client not initialized")

        try:
            apps_client = client.AppsV1Api()

            # Get current deployment
            deployment = apps_client.read_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace
            )

            # Update replicas
            deployment.spec.replicas = replicas

            # Apply changes
            apps_client.patch_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace,
                body=deployment
            )

            logger.info(f"Scaled deployment {deployment_name} to {replicas} replicas")
            return True

        except Exception as e:
            logger.error(f"Deployment scaling failed: {e}")
            return False


class ServiceDiscovery:
    """Service discovery for distributed systems."""

    def __init__(self, registry_type: str = "kubernetes"):
        self.registry_type = registry_type
        self._services: Dict[str, List[Dict[str, Any]]] = {}
        self._k8s_coordinator: Optional[KubernetesCoordinator] = None

    async def initialize(self):
        """Initialize service discovery."""
        if self.registry_type == "kubernetes":
            self._k8s_coordinator = KubernetesCoordinator()
            await self._k8s_coordinator.start()

    async def register_service(self, service_name: str, endpoint: Dict[str, Any]):
        """Register service endpoint."""
        if service_name not in self._services:
            self._services[service_name] = []

        self._services[service_name].append(endpoint)

    async def discover_service(self, service_name: str) -> List[Dict[str, Any]]:
        """Discover service endpoints."""
        # Check local registry first
        if service_name in self._services:
            return self._services[service_name]

        # Check Kubernetes if available
        if self._k8s_coordinator:
            pods = await asyncio.get_event_loop().run_in_executor(
                None, self._k8s_coordinator.get_pods,
                {"app": service_name}
            )

            endpoints = []
            for pod in pods:
                if pod["status"] == "Running":
                    endpoints.append({
                        "host": pod["ip"],
                        "port": 8080,  # Default port
                        "metadata": pod
                    })

            return endpoints

        return []

    async def health_check_service(self, service_name: str) -> Dict[str, Any]:
        """Health check service endpoints."""
        endpoints = await self.discover_service(service_name)

        healthy = []
        unhealthy = []

        for endpoint in endpoints:
            try:
                # Simple TCP health check
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                result = sock.connect_ex((endpoint["host"], endpoint["port"]))
                sock.close()

                if result == 0:
                    healthy.append(endpoint)
                else:
                    unhealthy.append(endpoint)

            except Exception:
                unhealthy.append(endpoint)

        return {
            "service": service_name,
            "total_endpoints": len(endpoints),
            "healthy_endpoints": len(healthy),
            "unhealthy_endpoints": len(unhealthy),
            "health_percentage": (len(healthy) / len(endpoints) * 100) if endpoints else 0
        }


class ContainerLifecycleManager:
    """Manage container lifecycle for distributed workloads."""

    def __init__(self):
        self._docker: Optional[DockerCommunicator] = None
        self._kubernetes: Optional[KubernetesCoordinator] = None
        self._running = False

    async def initialize(self, use_docker: bool = True, use_kubernetes: bool = False):
        """Initialize container managers."""
        if use_docker and DOCKER_AVAILABLE:
            self._docker = DockerCommunicator()
            await self._docker.start()

        if use_kubernetes and KUBERNETES_AVAILABLE:
            self._kubernetes = KubernetesCoordinator()
            await self._kubernetes.start()

        self._running = True

    async def create_worker_pool(self, image: str, pool_size: int,
                               platform: str = "docker") -> List[str]:
        """Create pool of worker containers."""
        worker_ids = []

        if platform == "docker" and self._docker:
            for i in range(pool_size):
                worker_id = await self._docker.create_worker_container(
                    image=image,
                    command=["python", "-c", f"print('Worker {i} ready')"]
                )
                worker_ids.append(worker_id)

        elif platform == "kubernetes" and self._kubernetes:
            for i in range(pool_size):
                job_name = f"worker-job-{i}-{int(time.time())}"
                await self._kubernetes.create_job(
                    job_name=job_name,
                    image=image,
                    command=["python", "-c", f"print('K8s Worker {i} ready')"]
                )
                worker_ids.append(job_name)

        return worker_ids

    async def distribute_task(self, task_data: Any, worker_ids: List[str],
                            platform: str = "docker") -> Dict[str, Any]:
        """Distribute task to worker containers."""
        results = {}

        if platform == "docker" and self._docker:
            for worker_id in worker_ids:
                # Execute task in container
                result = await self._docker.execute_in_container(
                    worker_id,
                    f"python -c \"print('Processing: {task_data}')\""
                )
                results[worker_id] = result

        elif platform == "kubernetes" and self._kubernetes:
            for job_name in worker_ids:
                # Wait for job completion
                status = await self._kubernetes.wait_for_job_completion(job_name, timeout=60.0)
                results[job_name] = status

        return results

    async def cleanup_workers(self, worker_ids: List[str], platform: str = "docker"):
        """Clean up worker containers."""
        if platform == "docker" and self._docker:
            # Docker containers are auto-removed
            pass

        elif platform == "kubernetes" and self._kubernetes:
            # Kubernetes jobs are cleaned up by Kubernetes
            pass


async def demonstrate_container_patterns():
    """Demonstrate container-aware concurrency patterns."""
    print("🐳 Container-Aware Concurrency Demonstration")
    print("=" * 50)

    # Service discovery demonstration
    print("\n1. Service Discovery:")
    discovery = ServiceDiscovery()

    # Mock service registration
    await discovery.register_service("web-api", {"host": "web-api-1", "port": 8080})
    await discovery.register_service("web-api", {"host": "web-api-2", "port": 8080})

    services = await discovery.discover_service("web-api")
    print(f"   Discovered {len(services)} web-api endpoints")

    health = await discovery.health_check_service("web-api")
    print(f"   Health check: {health['healthy_endpoints']}/{health['total_endpoints']} healthy")

    # Container lifecycle demonstration
    print("\n2. Container Lifecycle Management:")

    manager = ContainerLifecycleManager()

    try:
        # Try to initialize (may fail if Docker/K8s not available)
        await manager.initialize(use_docker=DOCKER_AVAILABLE, use_kubernetes=KUBERNETES_AVAILABLE)

        if DOCKER_AVAILABLE:
            print("   Docker integration available")
            containers = await asyncio.get_event_loop().run_in_executor(
                None, manager._docker.list_containers if manager._docker else lambda: []
            )
            print(f"   Found {len(containers)} running containers")
        else:
            print("   Docker not available (mock mode)")

        if KUBERNETES_AVAILABLE and manager._kubernetes:
            print("   Kubernetes integration available")
            pods = await asyncio.get_event_loop().run_in_executor(
                None, manager._kubernetes.get_pods
            )
            print(f"   Found {len(pods)} pods in namespace")
        else:
            print("   Kubernetes not available (mock mode)")

    except Exception as e:
        print(f"   Container integration failed: {e}")

    print("\n✅ Container-aware concurrency demonstration complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demonstrate_container_patterns())
