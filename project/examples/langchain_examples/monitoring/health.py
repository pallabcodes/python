"""Health check endpoints for production LLM service."""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """
    Health checker for production LLM service components.
    
    Checks:
    - Circuit breaker health
    - Connection pool health
    - Cache health
    - Rate limiter health
    - Overall service health
    """
    
    def __init__(self, wrapper: Any):
        """
        Initialize health checker.
        
        Args:
            wrapper: ProductionLLMWrapper instance to check
        """
        self.wrapper = wrapper
        self._logger = logging.getLogger(f"{__name__}.HealthChecker")
    
    async def check_circuit_breaker(self) -> ComponentHealth:
        """Check circuit breaker health."""
        if not self.wrapper.circuit_breaker:
            return ComponentHealth(
                name="circuit_breaker",
                status=HealthStatus.HEALTHY,
                message="Circuit breaker not enabled"
            )
        
        try:
            metrics = await self.wrapper.circuit_breaker.get_metrics()
            state = metrics.get("state", "unknown")
            failure_rate = metrics.get("failure_rate", 0.0)
            
            if state == "open":
                status = HealthStatus.UNHEALTHY
                message = f"Circuit breaker is OPEN (failure_rate={failure_rate:.2%})"
            elif state == "half_open":
                status = HealthStatus.DEGRADED
                message = f"Circuit breaker is HALF_OPEN (testing recovery)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Circuit breaker is CLOSED (failure_rate={failure_rate:.2%})"
            
            return ComponentHealth(
                name="circuit_breaker",
                status=status,
                message=message,
                details=metrics
            )
        except Exception as e:
            self._logger.error(f"Error checking circuit breaker: {e}", exc_info=True)
            return ComponentHealth(
                name="circuit_breaker",
                status=HealthStatus.UNHEALTHY,
                message=f"Error checking circuit breaker: {e}"
            )
    
    async def check_connection_pool(self) -> ComponentHealth:
        """Check connection pool health."""
        if not self.wrapper.connection_pool:
            return ComponentHealth(
                name="connection_pool",
                status=HealthStatus.HEALTHY,
                message="Connection pool not enabled"
            )
        
        try:
            pool = self.wrapper.connection_pool
            in_use = len(pool._in_use)
            available = len(pool._pool)
            total = in_use + available
            max_size = pool.max_size
            utilization = total / max_size if max_size > 0 else 0.0
            
            if utilization >= 0.9:
                status = HealthStatus.DEGRADED
                message = f"Connection pool near capacity ({utilization:.1%})"
            elif total == 0:
                status = HealthStatus.DEGRADED
                message = "Connection pool is empty"
            else:
                status = HealthStatus.HEALTHY
                message = f"Connection pool healthy ({in_use} in use, {available} available)"
            
            return ComponentHealth(
                name="connection_pool",
                status=status,
                message=message,
                details={
                    "in_use": in_use,
                    "available": available,
                    "total": total,
                    "max_size": max_size,
                    "utilization": utilization,
                    "waiters": len(pool._waiters) if hasattr(pool, "_waiters") else 0
                }
            )
        except Exception as e:
            self._logger.error(f"Error checking connection pool: {e}", exc_info=True)
            return ComponentHealth(
                name="connection_pool",
                status=HealthStatus.UNHEALTHY,
                message=f"Error checking connection pool: {e}"
            )
    
    async def check_cache(self) -> ComponentHealth:
        """Check cache health."""
        if not self.wrapper.semantic_cache:
            return ComponentHealth(
                name="cache",
                status=HealthStatus.HEALTHY,
                message="Cache not enabled"
            )
        
        try:
            cache = self.wrapper.semantic_cache
            size = len(cache._cache)
            max_size = cache.max_size
            utilization = size / max_size if max_size > 0 else 0.0
            
            if utilization >= 0.95:
                status = HealthStatus.DEGRADED
                message = f"Cache near capacity ({utilization:.1%})"
            else:
                status = HealthStatus.HEALTHY
                message = f"Cache healthy ({size}/{max_size} entries)"
            
            return ComponentHealth(
                name="cache",
                status=status,
                message=message,
                details={
                    "size": size,
                    "max_size": max_size,
                    "utilization": utilization,
                    "embeddings_count": len(cache._embeddings) if hasattr(cache, "_embeddings") else 0
                }
            )
        except Exception as e:
            self._logger.error(f"Error checking cache: {e}", exc_info=True)
            return ComponentHealth(
                name="cache",
                status=HealthStatus.UNHEALTHY,
                message=f"Error checking cache: {e}"
            )
    
    async def check_rate_limiter(self) -> ComponentHealth:
        """Check rate limiter health."""
        if not self.wrapper.rate_limiter:
            return ComponentHealth(
                name="rate_limiter",
                status=HealthStatus.HEALTHY,
                message="Rate limiter not enabled"
            )
        
        try:
            limiter = self.wrapper.rate_limiter
            tokens = limiter.tokens if hasattr(limiter, "tokens") else 0.0
            capacity = limiter.capacity if hasattr(limiter, "capacity") else 0.0
            rate = limiter.rate if hasattr(limiter, "rate") else 0.0
            
            if tokens <= 0:
                status = HealthStatus.DEGRADED
                message = "Rate limiter has no available tokens"
            else:
                status = HealthStatus.HEALTHY
                message = f"Rate limiter healthy ({tokens:.1f}/{capacity:.1f} tokens)"
            
            return ComponentHealth(
                name="rate_limiter",
                status=status,
                message=message,
                details={
                    "tokens": tokens,
                    "capacity": capacity,
                    "rate": rate
                }
            )
        except Exception as e:
            self._logger.error(f"Error checking rate limiter: {e}", exc_info=True)
            return ComponentHealth(
                name="rate_limiter",
                status=HealthStatus.UNHEALTHY,
                message=f"Error checking rate limiter: {e}"
            )
    
    async def check_overall_health(self) -> Dict[str, Any]:
        """
        Check overall service health.
        
        Returns:
            Dictionary with overall status and component health
        """
        components = await asyncio.gather(
            self.check_circuit_breaker(),
            self.check_connection_pool(),
            self.check_cache(),
            self.check_rate_limiter(),
            return_exceptions=True
        )
        
        # Handle exceptions
        component_healths: List[ComponentHealth] = []
        for comp in components:
            if isinstance(comp, Exception):
                component_healths.append(ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Error: {comp}"
                ))
            else:
                component_healths.append(comp)
        
        # Determine overall status
        statuses = [comp.status for comp in component_healths]
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Get metrics
        try:
            metrics = await self.wrapper.get_metrics()
        except Exception as e:
            self._logger.error(f"Error getting metrics: {e}", exc_info=True)
            metrics = {}
        
        return {
            "status": overall_status.value,
            "components": {
                comp.name: {
                    "status": comp.status.value,
                    "message": comp.message,
                    "details": comp.details
                }
                for comp in component_healths
            },
            "metrics": metrics,
            "timestamp": asyncio.get_event_loop().time()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Simple health check endpoint."""
        return await self.check_overall_health()
    
    async def readiness_check(self) -> Dict[str, Any]:
        """Readiness check (can accept traffic)."""
        health = await self.check_overall_health()
        is_ready = health["status"] != HealthStatus.UNHEALTHY.value
        return {
            "ready": is_ready,
            "status": health["status"]
        }
    
    async def liveness_check(self) -> Dict[str, Any]:
        """Liveness check (service is alive)."""
        return {
            "alive": True,
            "status": "healthy"
        }

