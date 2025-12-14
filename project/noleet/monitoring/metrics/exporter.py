"""
Metrics exporter for exposing Prometheus metrics.
Provides HTTP endpoint for metrics collection.
"""

import asyncio
from typing import Optional
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .collector import metrics_collector


class MetricsExporter:
    """Exports Prometheus metrics via HTTP endpoint."""

    def __init__(self, collector=None):
        self.collector = collector or metrics_collector

    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        return self.collector.get_metrics()

    def get_metrics_bytes(self) -> bytes:
        """Get all metrics as bytes."""
        return generate_latest()

    async def handle_metrics_request(self) -> tuple[bytes, str]:
        """Handle metrics HTTP request."""
        metrics_data = self.get_metrics_bytes()
        return metrics_data, CONTENT_TYPE_LATEST


# FastAPI integration
def create_metrics_endpoint():
    """Create FastAPI endpoint for metrics."""
    try:
        from fastapi import Response
        from fastapi.responses import PlainTextResponse

        exporter = MetricsExporter()

        async def metrics_endpoint():
            """Prometheus metrics endpoint."""
            metrics_data, content_type = await exporter.handle_metrics_request()
            return Response(
                content=metrics_data,
                media_type=content_type
            )

        return metrics_endpoint

    except ImportError:
        # FastAPI not available, return None
        return None


# Flask integration
def create_flask_metrics_endpoint():
    """Create Flask endpoint for metrics."""
    try:
        from flask import Response

        exporter = MetricsExporter()

        def metrics_endpoint():
            """Prometheus metrics endpoint."""
            metrics_data, content_type = asyncio.run(exporter.handle_metrics_request())
            return Response(
                response=metrics_data,
                content_type=content_type
            )

        return metrics_endpoint

    except ImportError:
        # Flask not available, return None
        return None


# Standalone HTTP server
def start_metrics_server(host: str = '0.0.0.0', port: int = 8000):
    """Start a standalone HTTP server for metrics."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    class MetricsHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/metrics':
                exporter = MetricsExporter()
                metrics_data, content_type = asyncio.run(exporter.handle_metrics_request())

                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(metrics_data)
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found\n')

        def log_message(self, format, *args):
            # Suppress default logging
            pass

    def run_server():
        server = HTTPServer((host, port), MetricsHandler)
        print(f"Metrics server started on http://{host}:{port}/metrics")
        server.serve_forever()

    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    return server_thread


# Health check endpoint
def create_health_endpoint():
    """Create health check endpoint."""
    try:
        from fastapi import Response

        async def health_endpoint():
            """Application health check."""
            return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}

        return health_endpoint

    except ImportError:
        return None


# Readiness check endpoint
def create_readiness_endpoint():
    """Create readiness check endpoint."""
    try:
        from fastapi import Response

        async def readiness_endpoint():
            """Application readiness check."""
            # Check if all critical services are available
            # This would include database, cache, LLM providers, etc.
            return {"status": "ready", "timestamp": asyncio.get_event_loop().time()}

        return readiness_endpoint

    except ImportError:
        return None
