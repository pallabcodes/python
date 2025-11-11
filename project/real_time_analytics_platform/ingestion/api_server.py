"""
AsyncIO-powered REST API server for real-time analytics ingestion.

Demonstrates:
- AsyncIO for concurrent request handling
- FastAPI for high-performance web framework
- Request validation and error handling
- Metrics collection and monitoring
- Rate limiting and circuit breakers
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

# FastAPI imports (with fallbacks)
try:
    from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, validator
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    # Create dummy classes for demonstration
    class FastAPI:
        def __init__(self, **kwargs): pass
        def get(self, *args, **kwargs): return lambda f: f
        def post(self, *args, **kwargs): return lambda f: f
        def on_event(self, *args, **kwargs): return lambda f: f

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail

    class Request:
        def __init__(self): pass

    class BackgroundTasks:
        def add_task(self, func, *args): pass

    class BaseModel: pass

    def Field(**kwargs): return lambda: None
    def validator(*args, **kwargs): return lambda f: f

logger = logging.getLogger(__name__)


@dataclass
class IngestionMetrics:
    """Metrics for ingestion performance tracking."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_processing_time: float = 0.0
    peak_concurrent_requests: int = 0
    rate_limited_requests: int = 0
    error_counts: Dict[str, int] = field(default_factory=dict)


@dataclass
class AnalyticsEvent:
    """Analytics event data structure."""
    event_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    source: str = "api"
    priority: int = Field(default=1, ge=1, le=3)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @validator('event_type')
    def validate_event_type(cls, v):
        allowed_types = ["user_action", "system_metrics", "custom_event", "business_metric"]
        if v not in allowed_types:
            raise ValueError(f"event_type must be one of: {allowed_types}")
        return v


class RateLimiter:
    """Simple rate limiter for API protection."""

    def __init__(self, requests_per_minute: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()

    async def check_rate_limit(self, client_id: str) -> bool:
        """Check if request should be rate limited."""
        async with self.lock:
            current_time = time.time()
            # Remove old requests (older than 1 minute)
            self.requests = [req for req in self.requests if current_time - req < 60]

            if len(self.requests) >= self.requests_per_minute:
                return False

            self.requests.append(current_time)
            return True


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")

        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise e


class APIServer:
    """
    High-performance AsyncIO API server for analytics ingestion.

    Features:
    - Concurrent request handling with AsyncIO
    - Rate limiting and circuit breakers
    - Request validation and error handling
    - Metrics collection and monitoring
    - Background task processing
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.metrics = IngestionMetrics()
        self.rate_limiter = RateLimiter(requests_per_minute=1000)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

        # Event queue for processed events
        self.event_queue = asyncio.Queue(maxsize=10000)
        self.processing_task = None

        # FastAPI app (with fallback)
        if HAS_FASTAPI:
            self.app = self._create_fastapi_app()
        else:
            self.app = None
            logger.warning("FastAPI not available, using mock implementation")

    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application with all endpoints."""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info("Starting API Server...")
            self.processing_task = asyncio.create_task(self._process_events_loop())

            # Track concurrent requests
            self._concurrent_requests = 0
            self._max_concurrent_requests = 0

            yield

            # Shutdown
            logger.info("Shutting down API Server...")
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass

        app = FastAPI(
            title="Real-Time Analytics Ingestion API",
            description="High-performance API for real-time analytics data ingestion",
            version="1.0.0",
            lifespan=lifespan
        )

        # Middleware for metrics collection
        @app.middleware("http")
        async def metrics_middleware(request: Request, call_next):
            start_time = time.time()

            # Track concurrent requests
            self._concurrent_requests += 1
            self._max_concurrent_requests = max(self._max_concurrent_requests, self._concurrent_requests)

            try:
                response = await call_next(request)
                self.metrics.successful_requests += 1
                return response
            except Exception as e:
                self.metrics.failed_requests += 1
                error_type = type(e).__name__
                self.metrics.error_counts[error_type] = self.metrics.error_counts.get(error_type, 0) + 1
                raise
            finally:
                processing_time = time.time() - start_time
                self.metrics.total_requests += 1
                self.metrics.total_processing_time += processing_time
                self._concurrent_requests -= 1

        # Health check endpoint
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "metrics": {
                    "total_requests": self.metrics.total_requests,
                    "success_rate": self.metrics.successful_requests / max(1, self.metrics.total_requests),
                    "avg_response_time": self.metrics.total_processing_time / max(1, self.metrics.total_requests)
                }
            }

        # Single event ingestion
        @app.post("/events")
        async def ingest_event(
            event: AnalyticsEvent,
            request: Request,
            background_tasks: BackgroundTasks
        ):
            """Ingest a single analytics event."""
            try:
                # Rate limiting check
                client_id = request.client.host if request.client else "unknown"
                if not await self.rate_limiter.check_rate_limit(client_id):
                    self.metrics.rate_limited_requests += 1
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")

                # Circuit breaker protection
                result = await self.circuit_breaker.call(
                    self._process_single_event, event
                )

                return {
                    "status": "ingested",
                    "event_id": event.event_id,
                    "processing_id": result
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error processing event {event.event_id}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        # Bulk event ingestion
        @app.post("/events/bulk")
        async def ingest_events_bulk(
            events: List[AnalyticsEvent],
            request: Request,
            background_tasks: BackgroundTasks
        ):
            """Ingest multiple analytics events in bulk."""
            if len(events) > 1000:
                raise HTTPException(status_code=413, detail="Too many events (max 1000)")

            try:
                # Rate limiting check
                client_id = request.client.host if request.client else "unknown"
                if not await self.rate_limiter.check_rate_limit(client_id):
                    self.metrics.rate_limited_requests += 1
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")

                # Process events concurrently
                tasks = [self._process_single_event(event) for event in events]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                successful = sum(1 for r in results if not isinstance(r, Exception))
                failed = len(results) - successful

                return {
                    "status": "bulk_ingested",
                    "total_events": len(events),
                    "successful": successful,
                    "failed": failed,
                    "processing_ids": [r for r in results if not isinstance(r, Exception)]
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error processing bulk events: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        # Metrics endpoint
        @app.get("/metrics")
        async def get_metrics():
            """Get ingestion metrics."""
            avg_response_time = (
                self.metrics.total_processing_time / max(1, self.metrics.total_requests)
            )

            return {
                "ingestion_metrics": {
                    "total_requests": self.metrics.total_requests,
                    "successful_requests": self.metrics.successful_requests,
                    "failed_requests": self.metrics.failed_requests,
                    "rate_limited_requests": self.metrics.rate_limited_requests,
                    "avg_response_time": avg_response_time,
                    "success_rate": self.metrics.successful_requests / max(1, self.metrics.total_requests),
                    "error_counts": self.metrics.error_counts,
                    "peak_concurrent_requests": getattr(self, '_max_concurrent_requests', 0)
                },
                "circuit_breaker": {
                    "state": self.circuit_breaker.state,
                    "failure_count": self.circuit_breaker.failure_count
                },
                "queue_size": self.event_queue.qsize()
            }

        return app

    async def _process_single_event(self, event: AnalyticsEvent) -> str:
        """Process a single analytics event."""
        # Add to processing queue
        processing_id = f"proc_{event.event_id}_{int(time.time()*1000)}"

        try:
            await self.event_queue.put({
                "processing_id": processing_id,
                "event": event,
                "received_at": time.time()
            })
            return processing_id
        except asyncio.QueueFull:
            raise HTTPException(status_code=503, detail="Ingestion queue full")

    async def _process_events_loop(self):
        """Background loop to process events from queue."""
        logger.info("Starting event processing loop...")

        while True:
            try:
                # Get event from queue
                event_data = await self.event_queue.get()

                # Simulate processing (in real implementation, this would route to analytics)
                processing_time = time.time() - event_data["received_at"]

                logger.debug(f"Processed event {event_data['event'].event_id} "
                           f"in {processing_time:.3f}s")

                # Mark task as done
                self.event_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Event processing loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(1)  # Brief pause on error

    async def start(self):
        """Start the API server."""
        if not HAS_FASTAPI:
            logger.error("FastAPI not available. Install with: pip install fastapi uvicorn")
            return

        import uvicorn
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)

        logger.info(f"Starting API server on {self.host}:{self.port}")
        await server.serve()

    def get_metrics(self) -> Dict[str, Any]:
        """Get current ingestion metrics."""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "rate_limited_requests": self.metrics.rate_limited_requests,
            "avg_response_time": (
                self.metrics.total_processing_time / max(1, self.metrics.total_requests)
            ),
            "success_rate": (
                self.metrics.successful_requests / max(1, self.metrics.total_requests)
            ),
            "error_counts": self.metrics.error_counts,
            "queue_size": self.event_queue.qsize()
        }


# Fallback mock server for demonstration when FastAPI is not available
class MockAPIServer:
    """Mock API server for demonstration purposes."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.metrics = IngestionMetrics()
        logger.warning("Using mock API server - install FastAPI for full functionality")

    async def start(self):
        """Mock server startup."""
        logger.info(f"Mock API server would start on {self.host}:{self.port}")
        # Simulate some activity
        for i in range(10):
            await asyncio.sleep(1)
            logger.info(f"Mock server: processed {i+1} events")

    def get_metrics(self) -> Dict[str, Any]:
        """Get mock metrics."""
        return {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "rate_limited_requests": 0,
            "avg_response_time": 0.05,
            "success_rate": 0.95,
            "queue_size": 0
        }


# Export the appropriate server class
APIServer = APIServer if HAS_FASTAPI else MockAPIServer
