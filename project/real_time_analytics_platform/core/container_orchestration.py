"""
Container Orchestration for Kubernetes/Docker Scaling.

Demonstrates:
- Kubernetes integration for container orchestration
- Docker container management
- Auto-scaling based on metrics
- Service discovery and health checks
- Graceful degradation when orchestration tools unavailable
"""

import asyncio
import time
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Kubernetes imports (with fallbacks)
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    HAS_KUBERNETES = True
except ImportError:
    HAS_KUBERNETES = False
    client = None
    config = None
    ApiException = Exception

# Docker imports (with fallbacks)
try:
    import docker
    HAS_DOCKER = True
except ImportError:
    HAS_DOCKER = False
    docker = None

logger = logging.getLogger(__name__)


class ScalingStrategy(Enum):
    """Scaling strategy types."""
    CPU_BASED = "cpu_based"
    MEMORY_BASED = "memory_based"
    REQUEST_BASED = "request_based"
    CUSTOM_METRICS = "custom_metrics"


@dataclass
class ScalingPolicy:
    """Policy for auto-scaling."""
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_percent: int = 70
    target_memory_percent: int = 80
    target_requests_per_second: int = 1000
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    scale_up_cooldown: int = 60
    scale_down_cooldown: int = 300
    strategy: ScalingStrategy = ScalingStrategy.CPU_BASED


@dataclass
class ContainerMetrics:
    """Metrics for container scaling decisions."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    request_rate: float = 0.0
    error_rate: float = 0.0
    latency_p95: float = 0.0
    active_connections: int = 0
    queue_depth: int = 0


@dataclass
class ScalingDecision:
    """Scaling decision result."""
    action: str  # "scale_up", "scale_down", "no_action"
    current_replicas: int
    target_replicas: int
    reason: str
    timestamp: float = field(default_factory=time.time)


class KubernetesOrchestrator:
    """
    Kubernetes orchestrator for container management.
    
    Features:
    - Deployment scaling
    - Pod health monitoring
    - Service discovery
    - Auto-scaling based on metrics
    """
    
    def __init__(
        self,
        namespace: str = "default",
        deployment_name: str = "analytics-platform"
    ):
        self.namespace = namespace
        self.deployment_name = deployment_name
        
        # Kubernetes clients
        self.apps_v1 = None
        self.core_v1 = None
        self.metrics_v1beta1 = None
        
        # Scaling policy
        self.scaling_policy = ScalingPolicy()
        
        # State
        self.last_scale_time: Dict[str, float] = {}
        self.running = False
        
        if HAS_KUBERNETES:
            try:
                # Try to load in-cluster config first, then kubeconfig
                try:
                    config.load_incluster_config()
                except:
                    config.load_kube_config()
                
                self.apps_v1 = client.AppsV1Api()
                self.core_v1 = client.CoreV1Api()
                try:
                    self.metrics_v1beta1 = client.MetricsV1beta1Api()
                except:
                    logger.warning("Metrics API not available")
                
                logger.info("Kubernetes client initialized")
            except Exception as e:
                logger.warning(f"Kubernetes not available: {e}")
                HAS_KUBERNETES = False
    
    async def get_deployment_replicas(self) -> int:
        """Get current number of replicas."""
        if not HAS_KUBERNETES or not self.apps_v1:
            return 1  # Mock
        
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=self.deployment_name,
                namespace=self.namespace
            )
            return deployment.spec.replicas or 0
        except ApiException as e:
            logger.error(f"Error getting deployment replicas: {e}")
            return 1
    
    async def scale_deployment(self, target_replicas: int) -> bool:
        """Scale deployment to target number of replicas."""
        if not HAS_KUBERNETES or not self.apps_v1:
            logger.info(f"Mock: Scaling to {target_replicas} replicas")
            return True
        
        try:
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=self.deployment_name,
                namespace=self.namespace
            )
            
            # Update replicas
            deployment.spec.replicas = target_replicas
            
            # Apply update
            self.apps_v1.patch_namespaced_deployment(
                name=self.deployment_name,
                namespace=self.namespace,
                body=deployment
            )
            
            logger.info(f"Scaled deployment to {target_replicas} replicas")
            return True
            
        except ApiException as e:
            logger.error(f"Error scaling deployment: {e}")
            return False
    
    async def get_pod_metrics(self) -> List[ContainerMetrics]:
        """Get metrics for all pods."""
        if not HAS_KUBERNETES or not self.metrics_v1beta1:
            # Return mock metrics
            return [ContainerMetrics(cpu_usage=50.0, memory_usage=60.0)]
        
        try:
            pod_metrics_list = self.metrics_v1beta1.list_namespaced_pod_metrics(
                namespace=self.namespace
            )
            
            metrics_list = []
            for pod_metrics in pod_metrics_list.items:
                cpu_usage = 0.0
                memory_usage = 0.0
                
                for container in pod_metrics.containers:
                    if container.usage.get("cpu"):
                        # Parse CPU (e.g., "100m" -> 0.1)
                        cpu_str = container.usage["cpu"]
                        if cpu_str.endswith("m"):
                            cpu_usage += float(cpu_str[:-1]) / 1000.0
                        else:
                            cpu_usage += float(cpu_str)
                    
                    if container.usage.get("memory"):
                        # Parse memory (e.g., "100Mi" -> bytes)
                        memory_str = container.usage["memory"]
                        # Simplified parsing
                        memory_usage += float(memory_str.replace("Mi", "").replace("Gi", ""))
                
                metrics_list.append(ContainerMetrics(
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage
                ))
            
            return metrics_list
            
        except Exception as e:
            logger.error(f"Error getting pod metrics: {e}")
            return []
    
    async def evaluate_scaling(self, metrics: ContainerMetrics) -> ScalingDecision:
        """Evaluate if scaling is needed."""
        current_replicas = await self.get_deployment_replicas()
        
        # Check cooldown
        last_scale = self.last_scale_time.get(self.deployment_name, 0)
        cooldown = (
            self.scaling_policy.scale_up_cooldown
            if metrics.cpu_usage > self.scaling_policy.target_cpu_percent
            else self.scaling_policy.scale_down_cooldown
        )
        
        if time.time() - last_scale < cooldown:
            return ScalingDecision(
                action="no_action",
                current_replicas=current_replicas,
                target_replicas=current_replicas,
                reason="cooldown_period"
            )
        
        # Evaluate based on strategy
        target_replicas = current_replicas
        
        if self.scaling_policy.strategy == ScalingStrategy.CPU_BASED:
            cpu_ratio = metrics.cpu_usage / self.scaling_policy.target_cpu_percent
            
            if cpu_ratio > self.scaling_policy.scale_up_threshold:
                # Scale up
                target_replicas = min(
                    self.scaling_policy.max_replicas,
                    int(current_replicas * cpu_ratio) + 1
                )
                action = "scale_up"
                reason = f"high_cpu_usage_{metrics.cpu_usage:.1f}%"
            elif cpu_ratio < self.scaling_policy.scale_down_threshold:
                # Scale down
                target_replicas = max(
                    self.scaling_policy.min_replicas,
                    int(current_replicas * cpu_ratio)
                )
                action = "scale_down"
                reason = f"low_cpu_usage_{metrics.cpu_usage:.1f}%"
            else:
                action = "no_action"
                reason = "cpu_within_target"
        
        elif self.scaling_policy.strategy == ScalingStrategy.REQUEST_BASED:
            request_ratio = metrics.request_rate / self.scaling_policy.target_requests_per_second
            
            if request_ratio > self.scaling_policy.scale_up_threshold:
                target_replicas = min(
                    self.scaling_policy.max_replicas,
                    int(current_replicas * request_ratio) + 1
                )
                action = "scale_up"
                reason = f"high_request_rate_{metrics.request_rate:.1f}/s"
            elif request_ratio < self.scaling_policy.scale_down_threshold:
                target_replicas = max(
                    self.scaling_policy.min_replicas,
                    int(current_replicas * request_ratio)
                )
                action = "scale_down"
                reason = f"low_request_rate_{metrics.request_rate:.1f}/s"
            else:
                action = "no_action"
                reason = "request_rate_within_target"
        
        else:
            action = "no_action"
            reason = "unknown_strategy"
        
        # Only scale if target differs from current
        if target_replicas == current_replicas:
            action = "no_action"
            reason = "replicas_at_target"
        
        return ScalingDecision(
            action=action,
            current_replicas=current_replicas,
            target_replicas=target_replicas,
            reason=reason
        )
    
    async def auto_scale_loop(self):
        """Continuous auto-scaling evaluation loop."""
        logger.info("Starting auto-scaling loop...")
        
        while self.running:
            try:
                # Get metrics
                pod_metrics_list = await self.get_pod_metrics()
                
                if not pod_metrics_list:
                    await asyncio.sleep(30)
                    continue
                
                # Aggregate metrics
                avg_cpu = sum(m.cpu_usage for m in pod_metrics_list) / len(pod_metrics_list)
                avg_memory = sum(m.memory_usage for m in pod_metrics_list) / len(pod_metrics_list)
                
                aggregated_metrics = ContainerMetrics(
                    cpu_usage=avg_cpu,
                    memory_usage=avg_memory
                )
                
                # Evaluate scaling
                decision = await self.evaluate_scaling(aggregated_metrics)
                
                # Execute scaling decision
                if decision.action != "no_action":
                    success = await self.scale_deployment(decision.target_replicas)
                    if success:
                        self.last_scale_time[self.deployment_name] = time.time()
                        logger.info(f"Auto-scaling: {decision.action} to {decision.target_replicas} replicas - {decision.reason}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in auto-scaling loop: {e}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the orchestrator."""
        self.running = True
        logger.info("Kubernetes orchestrator started")
    
    async def stop(self):
        """Stop the orchestrator."""
        self.running = False
        logger.info("Kubernetes orchestrator stopped")


class DockerOrchestrator:
    """
    Docker orchestrator for container management.
    
    Features:
    - Container lifecycle management
    - Health checks
    - Scaling via docker-compose or swarm
    """
    
    def __init__(self):
        self.client = None
        if HAS_DOCKER:
            try:
                self.client = docker.from_env()
                logger.info("Docker client initialized")
            except Exception as e:
                logger.warning(f"Docker not available: {e}")
    
    async def get_container_count(self, service_name: str) -> int:
        """Get number of running containers for a service."""
        if not self.client:
            return 1  # Mock
        
        try:
            containers = self.client.containers.list(
                filters={"name": service_name},
                all=False
            )
            return len(containers)
        except Exception as e:
            logger.error(f"Error getting container count: {e}")
            return 0
    
    async def scale_service(self, service_name: str, replicas: int) -> bool:
        """Scale a Docker service."""
        if not self.client:
            logger.info(f"Mock: Scaling {service_name} to {replicas} replicas")
            return True
        
        try:
            # In Docker Swarm mode
            service = self.client.services.get(service_name)
            service.scale(replicas)
            logger.info(f"Scaled service {service_name} to {replicas} replicas")
            return True
        except Exception as e:
            logger.error(f"Error scaling service: {e}")
            return False


# Export orchestrators
if not HAS_KUBERNETES:
    logger.warning("Kubernetes not available. Install kubernetes client for orchestration.")
if not HAS_DOCKER:
    logger.warning("Docker not available. Install docker-py for container management.")

