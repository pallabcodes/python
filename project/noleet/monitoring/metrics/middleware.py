"""
Metrics middleware for automatic metrics collection.
Integrates with web frameworks to collect HTTP metrics automatically.
"""

import time
from typing import Callable, Optional
from .collector import metrics_collector


class MetricsMiddleware:
    """Middleware for automatic metrics collection."""

    def __init__(self, collector=None):
        self.collector = collector or metrics_collector

    # FastAPI middleware
    def create_fastapi_middleware(self):
        """Create FastAPI middleware for metrics collection."""
        try:
            from fastapi import Request, Response
            from starlette.middleware.base import BaseHTTPMiddleware

            class MetricsHTTPMiddleware(BaseHTTPMiddleware):
                def __init__(self, app, collector=None):
                    super().__init__(app)
                    self.collector = collector or metrics_collector

                async def dispatch(self, request: Request, call_next):
                    start_time = time.time()

                    # Process the request
                    response = await call_next(request)

                    # Record metrics
                    duration = time.time() - start_time
                    self.collector.record_http_request(
                        method=request.method,
                        endpoint=request.url.path,
                        status=response.status_code,
                        duration=duration
                    )

                    return response

            return MetricsHTTPMiddleware

        except ImportError:
            return None

    # Flask middleware
    def create_flask_middleware(self):
        """Create Flask middleware for metrics collection."""
        try:
            from flask import request, g
            from functools import wraps

            def metrics_middleware(app):
                @app.before_request
                def before_request():
                    g.start_time = time.time()

                @app.after_request
                def after_request(response):
                    if hasattr(g, 'start_time'):
                        duration = time.time() - g.start_time
                        self.collector.record_http_request(
                            method=request.method,
                            endpoint=request.path,
                            status=response.status_code,
                            duration=duration
                        )
                    return response

                return app

            return metrics_middleware

        except ImportError:
            return None

    # Generic WSGI middleware
    def create_wsgi_middleware(self, app):
        """Create WSGI middleware for metrics collection."""
        def middleware(environ, start_response):
            start_time = time.time()

            # Capture the response
            response_status = [None]
            response_headers = [None]

            def custom_start_response(status, headers):
                response_status[0] = status
                response_headers[0] = headers
                return start_response(status, headers)

            # Call the app
            response_iter = app(environ, custom_start_response)

            # Record metrics after response starts
            if response_status[0]:
                duration = time.time() - start_time
                status_code = int(response_status[0].split()[0])

                self.collector.record_http_request(
                    method=environ.get('REQUEST_METHOD', 'UNKNOWN'),
                    endpoint=environ.get('PATH_INFO', '/'),
                    status=status_code,
                    duration=duration
                )

            return response_iter

        return middleware


# Decorator for function-level metrics
def record_metrics(operation_name: str, **labels):
    """Decorator to record metrics for function execution."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Record success metrics
                duration = time.time() - start_time
                # This would be extended to record custom metrics based on labels

                return result

            except Exception as e:
                # Record error metrics
                duration = time.time() - start_time
                # This would record error metrics

                raise e

        return wrapper
    return decorator


# Context manager for custom metrics recording
class MetricsContext:
    """Context manager for recording custom metrics."""

    def __init__(self, operation_name: str, **labels):
        self.operation_name = operation_name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time

            if exc_type is not None:
                # Record error metrics
                pass
            else:
                # Record success metrics
                pass


# Health check utilities
def perform_health_checks():
    """Perform comprehensive health checks."""
    checks = {
        'database': check_database_health(),
        'cache': check_cache_health(),
        'llm_providers': check_llm_providers_health(),
        'external_services': check_external_services_health()
    }

    overall_health = all(checks.values())
    return {
        'healthy': overall_health,
        'checks': checks,
        'timestamp': time.time()
    }


def check_database_health() -> bool:
    """Check database connectivity."""
    try:
        # Implement database health check
        return True
    except Exception:
        return False


def check_cache_health() -> bool:
    """Check cache connectivity."""
    try:
        # Implement cache health check
        return True
    except Exception:
        return False


def check_llm_providers_health() -> bool:
    """Check LLM provider availability."""
    try:
        # Implement LLM provider health checks
        return True
    except Exception:
        return False


def check_external_services_health() -> bool:
    """Check external service availability."""
    try:
        # Implement external service health checks
        return True
    except Exception:
        return False
