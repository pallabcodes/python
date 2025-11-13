"""
Dashboard API for Live Metrics and Monitoring.

Demonstrates:
- RESTful API for real-time dashboard data
- WebSocket support for live updates
- Aggregated metrics from all platform components
- Historical data queries
- Health checks and system status
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# FastAPI imports (with fallbacks)
try:
    from fastapi import FastAPI, WebSocket, HTTPException
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    class FastAPI:
        def __init__(self, **kwargs): pass
        def get(self, *args, **kwargs): return lambda f: f
        def post(self, *args, **kwargs): return lambda f: f
        def websocket(self, *args, **kwargs): return lambda f: f
        def add_middleware(self, *args, **kwargs): pass
    
    class WebSocket:
        def __init__(self): pass
        async def accept(self): pass
        async def send_json(self, data: dict): pass
        async def receive_json(self): return {}
        async def close(self): pass
    
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
    
    class JSONResponse:
        def __init__(self, content: dict): self.content = content
    
    class CORSMiddleware:
        pass

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Aggregated dashboard metrics."""
    timestamp: float
    platform_stats: Dict[str, Any] = field(default_factory=dict)
    ingestion_stats: Dict[str, Any] = field(default_factory=dict)
    processing_stats: Dict[str, Any] = field(default_factory=dict)
    analytics_stats: Dict[str, Any] = field(default_factory=dict)
    monitoring_stats: Dict[str, Any] = field(default_factory=dict)
    ml_stats: Dict[str, Any] = field(default_factory=dict)
    system_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HistoricalDataPoint:
    """Historical data point for time series."""
    timestamp: float
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


class DashboardAPI:
    """
    Dashboard API for real-time analytics platform monitoring.
    
    Features:
    - RESTful endpoints for metrics
    - WebSocket streaming for live updates
    - Historical data queries
    - Health checks
    - System status endpoints
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8081):
        self.host = host
        self.port = port
        
        # Metrics storage (in production, would use time-series DB)
        self.historical_data: List[HistoricalDataPoint] = []
        self.metrics_history_max = 10000
        
        # WebSocket connections for live updates
        self.websocket_connections: List[WebSocket] = []
        
        # Component references (set by platform)
        self.platform = None
        self.ingestion_server = None
        self.websocket_handler = None
        self.kafka_consumer = None
        self.analytics_engine = None
        self.ml_processor = None
        self.actor_system = None
        
        # FastAPI app
        if HAS_FASTAPI:
            self.app = self._create_app()
        else:
            self.app = None
            logger.warning("FastAPI not available, using mock dashboard")
        
        self.running = False
    
    def _create_app(self) -> FastAPI:
        """Create FastAPI application with dashboard endpoints."""
        app = FastAPI(
            title="Analytics Platform Dashboard API",
            description="Real-time metrics and monitoring dashboard",
            version="1.0.0"
        )
        
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Health check
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "uptime": self._get_uptime()
            }
        
        # System status
        @app.get("/api/v1/status")
        async def get_status():
            """Get overall system status."""
            return await self._get_system_status()
        
        # Real-time metrics
        @app.get("/api/v1/metrics")
        async def get_metrics():
            """Get current metrics snapshot."""
            return await self._get_current_metrics()
        
        # Historical metrics
        @app.get("/api/v1/metrics/history")
        async def get_historical_metrics(
            metric_name: Optional[str] = None,
            start_time: Optional[float] = None,
            end_time: Optional[float] = None,
            limit: int = 1000
        ):
            """Get historical metrics."""
            return await self._get_historical_metrics(
                metric_name, start_time, end_time, limit
            )
        
        # Component-specific metrics
        @app.get("/api/v1/metrics/ingestion")
        async def get_ingestion_metrics():
            """Get ingestion layer metrics."""
            if self.ingestion_server:
                return self.ingestion_server.get_metrics()
            return {"error": "Ingestion server not available"}
        
        @app.get("/api/v1/metrics/processing")
        async def get_processing_metrics():
            """Get processing layer metrics."""
            return {"message": "Processing metrics endpoint"}
        
        @app.get("/api/v1/metrics/analytics")
        async def get_analytics_metrics():
            """Get analytics layer metrics."""
            if self.analytics_engine:
                return self.analytics_engine.get_stats()
            return {"error": "Analytics engine not available"}
        
        @app.get("/api/v1/metrics/ml")
        async def get_ml_metrics():
            """Get ML processor metrics."""
            if self.ml_processor:
                return self.ml_processor.get_metrics()
            return {"error": "ML processor not available"}
        
        @app.get("/api/v1/metrics/monitoring")
        async def get_monitoring_metrics():
            """Get monitoring layer metrics."""
            if self.actor_system:
                return self.actor_system.get_system_metrics()
            return {"error": "Actor system not available"}
        
        # WebSocket endpoint for live updates
        @app.websocket("/ws/metrics")
        async def websocket_metrics(websocket: WebSocket):
            """WebSocket endpoint for live metrics streaming."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Send metrics update every second
                    metrics = await self._get_current_metrics()
                    await websocket.send_json(metrics)
                    await asyncio.sleep(1.0)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
        
        return app
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        status = {
            "platform_running": False,
            "components": {},
            "timestamp": time.time()
        }
        
        if self.platform:
            platform_stats = await self.platform.get_platform_stats()
            status["platform_running"] = platform_stats.get("platform", {}).get("running", False)
            status["components"]["platform"] = "running" if status["platform_running"] else "stopped"
        
        status["components"]["ingestion"] = "available" if self.ingestion_server else "unavailable"
        status["components"]["websocket"] = "available" if self.websocket_handler else "unavailable"
        status["components"]["kafka"] = "available" if self.kafka_consumer else "unavailable"
        status["components"]["analytics"] = "available" if self.analytics_engine else "unavailable"
        status["components"]["ml"] = "available" if self.ml_processor else "unavailable"
        status["components"]["monitoring"] = "available" if self.actor_system else "unavailable"
        
        return status
    
    async def _get_current_metrics(self) -> DashboardMetrics:
        """Get current metrics snapshot."""
        metrics = DashboardMetrics(timestamp=time.time())
        
        # Platform stats
        if self.platform:
            platform_stats = await self.platform.get_platform_stats()
            metrics.platform_stats = platform_stats
        
        # Ingestion stats
        if self.ingestion_server:
            metrics.ingestion_stats = self.ingestion_server.get_metrics()
        
        if self.websocket_handler:
            metrics.ingestion_stats["websocket"] = self.websocket_handler.get_metrics()
        
        if self.kafka_consumer:
            metrics.ingestion_stats["kafka"] = self.kafka_consumer.get_metrics()
        
        # Analytics stats
        if self.analytics_engine:
            metrics.analytics_stats = self.analytics_engine.get_stats()
        
        # ML stats
        if self.ml_processor:
            metrics.ml_stats = self.ml_processor.get_metrics()
        
        # Monitoring stats
        if self.actor_system:
            metrics.monitoring_stats = self.actor_system.get_system_metrics()
        
        # System stats
        metrics.system_stats = self._get_system_stats()
        
        # Store in history
        self._store_metrics(metrics)
        
        return metrics
    
    def _get_system_stats(self) -> Dict[str, Any]:
        """Get system-level statistics."""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "network_sent": psutil.net_io_counters().bytes_sent,
                "network_recv": psutil.net_io_counters().bytes_recv
            }
        except ImportError:
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "disk_percent": 0.0,
                "network_sent": 0,
                "network_recv": 0
            }
    
    async def _get_historical_metrics(
        self,
        metric_name: Optional[str],
        start_time: Optional[float],
        end_time: Optional[float],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get historical metrics."""
        filtered = self.historical_data
        
        # Filter by metric name
        if metric_name:
            filtered = [d for d in filtered if d.metric_name == metric_name]
        
        # Filter by time range
        if start_time:
            filtered = [d for d in filtered if d.timestamp >= start_time]
        if end_time:
            filtered = [d for d in filtered if d.timestamp <= end_time]
        
        # Sort by timestamp and limit
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        filtered = filtered[:limit]
        
        # Convert to dict
        return [
            {
                "timestamp": d.timestamp,
                "metric_name": d.metric_name,
                "value": d.value,
                "tags": d.tags
            }
            for d in filtered
        ]
    
    def _store_metrics(self, metrics: DashboardMetrics):
        """Store metrics in history."""
        # Extract key metrics and store as data points
        if metrics.platform_stats:
            self._add_data_point("events_processed", metrics.platform_stats.get("platform", {}).get("events_processed", 0))
            self._add_data_point("avg_processing_time", metrics.platform_stats.get("platform", {}).get("avg_processing_time", 0))
        
        if metrics.ingestion_stats:
            self._add_data_point("ingestion_requests", metrics.ingestion_stats.get("total_requests", 0))
            self._add_data_point("ingestion_success_rate", metrics.ingestion_stats.get("success_rate", 0))
        
        if metrics.ml_stats:
            self._add_data_point("ml_predictions", metrics.ml_stats.get("total_predictions", 0))
            self._add_data_point("ml_avg_time", metrics.ml_stats.get("avg_processing_time", 0))
        
        # Limit history size
        if len(self.historical_data) > self.metrics_history_max:
            self.historical_data = self.historical_data[-self.metrics_history_max:]
    
    def _add_data_point(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Add a data point to history."""
        self.historical_data.append(
            HistoricalDataPoint(
                timestamp=time.time(),
                metric_name=metric_name,
                value=float(value),
                tags=tags or {}
            )
        )
    
    def _get_uptime(self) -> float:
        """Get platform uptime."""
        if hasattr(self, 'start_time'):
            return time.time() - self.start_time
        return 0.0
    
    async def start(self):
        """Start the dashboard API server."""
        if not HAS_FASTAPI:
            logger.error("FastAPI not available. Install with: pip install fastapi uvicorn")
            return
        
        import uvicorn
        self.start_time = time.time()
        self.running = True
        
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        logger.info(f"Starting Dashboard API on {self.host}:{self.port}")
        await server.serve()
    
    async def stop(self):
        """Stop the dashboard API."""
        self.running = False
        
        # Close WebSocket connections
        for ws in self.websocket_connections:
            try:
                await ws.close()
            except Exception:
                pass
        
        logger.info("Dashboard API stopped")
    
    def register_component(self, component_type: str, component: Any):
        """Register a platform component for metrics collection."""
        if component_type == "platform":
            self.platform = component
        elif component_type == "ingestion":
            self.ingestion_server = component
        elif component_type == "websocket":
            self.websocket_handler = component
        elif component_type == "kafka":
            self.kafka_consumer = component
        elif component_type == "analytics":
            self.analytics_engine = component
        elif component_type == "ml":
            self.ml_processor = component
        elif component_type == "monitoring":
            self.actor_system = component


# Export API
if not HAS_FASTAPI:
    logger.warning("FastAPI not available. Install FastAPI for dashboard functionality.")

