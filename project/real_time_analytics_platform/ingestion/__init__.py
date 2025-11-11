"""
Real-time data ingestion layer using AsyncIO.

Provides REST API ingestion with rate limiting and circuit breakers.
"""

from .api_server import APIServer

__all__ = [
    "APIServer"
]
