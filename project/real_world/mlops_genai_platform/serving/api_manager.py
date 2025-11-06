"""
API Manager for coordinating FastAPI endpoints with platform components.

Provides request routing, response formatting, error handling,
and API-level orchestration for the MLOps + Gen AI platform.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

try:
    from ..core.config import PlatformConfig
except ImportError:
    # Fallback for direct imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from core.config import PlatformConfig


class APIManager:
    """
    API request/response manager and coordinator.

    Features:
    - Request validation and preprocessing
    - Response formatting and postprocessing
    - Error handling and logging
    - Rate limiting and throttling
    - API metrics collection
    - Request tracing and correlation
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize API manager.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.APIManager")

        # Request tracking
        self._active_requests: Dict[str, Dict[str, Any]] = {}
        self._request_count = 0
        self._error_count = 0

        # Performance tracking
        self._response_times: list = []
        self._endpoint_stats: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize API manager."""
        self.logger.info("Initializing API manager...")

        # Setup endpoint statistics
        endpoints = [
            "/health", "/generate", "/experiments", "/models",
            "/agents", "/search", "/finetune", "/process"
        ]

        for endpoint in endpoints:
            self._endpoint_stats[endpoint] = {
                "requests": 0,
                "errors": 0,
                "avg_response_time": 0.0,
                "total_response_time": 0.0
            }

        self.logger.info("API manager initialized")

    async def handle_request(
        self,
        endpoint: str,
        request_data: Dict[str, Any],
        handler_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle API request with tracking and error handling.

        Args:
            endpoint: API endpoint path
            request_data: Request data for logging
            handler_func: Handler function to call
            *args, **kwargs: Arguments for handler function

        Returns:
            Response data
        """
        request_id = f"req_{int(time.time() * 1000000)}"
        start_time = time.time()

        # Track active request
        self._active_requests[request_id] = {
            "endpoint": endpoint,
            "start_time": start_time,
            "request_data": self._sanitize_request_data(request_data)
        }

        self._request_count += 1
        self._endpoint_stats[endpoint]["requests"] += 1

        try:
            self.logger.info(f"Handling request {request_id} to {endpoint}")

            # Call handler function
            result = await handler_func(*args, **kwargs)

            # Calculate response time
            response_time = time.time() - start_time
            self._response_times.append(response_time)

            # Update endpoint stats
            self._update_endpoint_stats(endpoint, response_time, False)

            # Clean up active request
            del self._active_requests[request_id]

            self.logger.info(f"Request {request_id} completed in {response_time:.3f}s")

            return {
                "success": True,
                "data": result,
                "request_id": request_id,
                "processing_time": response_time
            }

        except Exception as e:
            # Calculate response time for error
            response_time = time.time() - start_time

            # Update error stats
            self._error_count += 1
            self._endpoint_stats[endpoint]["errors"] += 1
            self._update_endpoint_stats(endpoint, response_time, True)

            # Log error
            self.logger.error(f"Request {request_id} failed: {e}")

            # Clean up active request
            del self._active_requests[request_id]

            return {
                "success": False,
                "error": str(e),
                "request_id": request_id,
                "processing_time": response_time
            }

    def _sanitize_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize request data for logging (remove sensitive info)."""
        sanitized = data.copy()

        # Remove or mask sensitive fields
        sensitive_fields = ['password', 'token', 'key', 'secret', 'api_key']
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "***masked***"

        # Truncate large fields
        for key, value in sanitized.items():
            if isinstance(value, str) and len(value) > 100:
                sanitized[key] = value[:100] + "..."

        return sanitized

    def _update_endpoint_stats(self, endpoint: str, response_time: float, is_error: bool) -> None:
        """Update endpoint performance statistics."""
        stats = self._endpoint_stats[endpoint]

        # Update response time stats
        stats["total_response_time"] += response_time
        stats["avg_response_time"] = stats["total_response_time"] / stats["requests"]

        if is_error:
            stats["errors"] += 1

    async def validate_request(
        self,
        endpoint: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate API request.

        Args:
            endpoint: API endpoint
            request_data: Request data to validate

        Returns:
            Validation result
        """
        # Basic validation rules per endpoint
        validation_rules = {
            "/generate": {
                "required": ["prompt"],
                "max_lengths": {"prompt": 10000}
            },
            "/experiments": {
                "required": ["name"],
                "max_lengths": {"name": 100, "description": 500}
            },
            "/models/register": {
                "required": ["name", "version", "model_path"],
                "max_lengths": {"name": 100}
            }
        }

        if endpoint in validation_rules:
            rules = validation_rules[endpoint]

            # Check required fields
            for field in rules.get("required", []):
                if field not in request_data:
                    return {
                        "valid": False,
                        "error": f"Missing required field: {field}"
                    }

            # Check max lengths
            for field, max_len in rules.get("max_lengths", {}).items():
                if field in request_data and len(str(request_data[field])) > max_len:
                    return {
                        "valid": False,
                        "error": f"Field {field} exceeds maximum length of {max_len}"
                    }

        return {"valid": True}

    async def rate_limit_check(
        self,
        client_id: str,
        endpoint: str
    ) -> Dict[str, Any]:
        """
        Check rate limiting for client.

        Args:
            client_id: Client identifier
            endpoint: API endpoint

        Returns:
            Rate limit check result
        """
        # Simple in-memory rate limiting (would use Redis in production)
        # For demo, allow unlimited requests

        return {
            "allowed": True,
            "remaining": 1000,
            "reset_time": int(time.time()) + 3600
        }

    def get_api_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        total_response_time = sum(self._response_times) if self._response_times else 0
        avg_response_time = total_response_time / len(self._response_times) if self._response_times else 0

        return {
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / self._request_count if self._request_count > 0 else 0,
            "avg_response_time": avg_response_time,
            "active_requests": len(self._active_requests),
            "endpoint_stats": self._endpoint_stats.copy()
        }

    def get_active_requests(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active requests."""
        return self._active_requests.copy()

    async def cancel_request(self, request_id: str) -> bool:
        """
        Cancel an active request.

        Args:
            request_id: Request ID to cancel

        Returns:
            True if cancelled, False otherwise
        """
        if request_id in self._active_requests:
            # In a real implementation, this would signal the handler to cancel
            del self._active_requests[request_id]
            self.logger.info(f"Cancelled request {request_id}")
            return True

        return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform API manager health check."""
        return {
            "healthy": True,
            "active_requests": len(self._active_requests),
            "total_requests": self._request_count,
            "error_rate": self._error_count / self._request_count if self._request_count > 0 else 0
        }

    async def shutdown(self) -> None:
        """Shutdown API manager."""
        self.logger.info("Shutting down API manager...")

        # Wait for active requests to complete (with timeout)
        timeout = 30  # seconds
        start_time = time.time()

        while self._active_requests and (time.time() - start_time) < timeout:
            await asyncio.sleep(1)

        if self._active_requests:
            self.logger.warning(f"Force shutdown with {len(self._active_requests)} active requests")

        # Clear state
        self._active_requests.clear()
        self._response_times.clear()

        self.logger.info("API manager shutdown complete")
