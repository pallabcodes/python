"""Monitoring, logging, and observability for DocuMind."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from functools import wraps

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


# Configure structured logging
def setup_logging():
    """Setup structured logging with appropriate formatters."""
    import structlog

    # Configure standard logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


# Metrics and monitoring
class MetricsCollector:
    """Collect and expose application metrics."""

    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_duration_seconds": [],
            "errors_total": 0,
            "active_connections": 0,
            "repositories_analyzed": 0,
            "documents_generated": 0,
        }

    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric."""
        if name in self.metrics:
            self.metrics[name] += value

    def record_duration(self, name: str, duration: float):
        """Record a duration metric."""
        if name in self.metrics:
            self.metrics[name].append(duration)

    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        return self.metrics.copy()

    def reset(self):
        """Reset all metrics."""
        for key in self.metrics:
            if isinstance(self.metrics[key], list):
                self.metrics[key] = []
            else:
                self.metrics[key] = 0


# Global metrics instance
metrics = MetricsCollector()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests."""

    async def dispatch(self, request: Request, call_next):
        import structlog

        logger = structlog.get_logger()

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            "request_started",
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            client_ip=request.client.host if request.client else None,
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Update metrics
            metrics.increment_counter("requests_total")
            metrics.record_duration("requests_duration_seconds", duration)

            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration=duration,
            )

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Update error metrics
            metrics.increment_counter("errors_total")

            # Log error
            logger.error(
                "request_error",
                method=request.method,
                url=str(request.url),
                error=str(e),
                duration=duration,
                exc_info=True,
            )

            raise


class HealthChecker:
    """Health check utilities."""

    def __init__(self):
        self.checks = {
            "database": self._check_database,
            "external_services": self._check_external_services,
        }

    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}

        for check_name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[check_name] = {
                    "status": "healthy" if result else "unhealthy",
                    "timestamp": time.time(),
                }
            except Exception as e:
                results[check_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": time.time(),
                }

        # Overall status
        all_healthy = all(r["status"] == "healthy" for r in results.values())
        results["overall"] = "healthy" if all_healthy else "unhealthy"

        return results

    async def _check_database(self) -> bool:
        """Check database connectivity."""
        try:
            from app.db.session import engine

            async with engine.begin() as conn:
                await conn.execute("SELECT 1")

            return True
        except Exception:
            return False

    async def _check_external_services(self) -> bool:
        """Check external service connectivity."""
        # Check OpenAI if configured
        if settings.OPENAI_API_KEY:
            try:
                import openai
                openai.api_key = settings.OPENAI_API_KEY
                # Simple API check (doesn't cost credits)
                await openai.Engine.list()
                return True
            except Exception:
                return False

        return True  # If no external services configured, consider healthy


# Global health checker
health_checker = HealthChecker()


def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        import structlog

        logger = structlog.get_logger()
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                "function_completed",
                function=func.__name__,
                duration=duration,
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                "function_error",
                function=func.__name__,
                duration=duration,
                error=str(e),
                exc_info=True,
            )

            raise

    return wrapper


@asynccontextmanager
async def lifespan_monitoring():
    """Lifespan context manager for monitoring setup."""
    import structlog

    logger = structlog.get_logger()

    logger.info("application_startup", version="0.1.0")

    # Setup monitoring
    setup_logging()

    # Log startup metrics
    logger.info(
        "monitoring_setup_complete",
        log_level="INFO",
        metrics_enabled=True,
    )

    yield

    # Shutdown logging
    logger.info("application_shutdown")


def log_audit_event(
    event: str,
    user_id: Optional[int] = None,
    resource_type: str = "",
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None,
):
    """Log an audit event."""
    import structlog

    logger = structlog.get_logger()

    log_data = {
        "event": event,
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "success": success,
    }

    if details:
        log_data["details"] = details

    if error_message:
        log_data["error"] = error_message

    if success:
        logger.info("audit_event", **log_data)
    else:
        logger.error("audit_event", **log_data)
