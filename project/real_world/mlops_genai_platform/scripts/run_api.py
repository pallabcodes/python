#!/usr/bin/env python3
"""
Script to run the MLOps + Gen AI Platform API server.

Starts the FastAPI server with all platform capabilities exposed via REST API.
"""

import uvicorn
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from serving.api import app


def main():
    """Run the API server."""
    print("🚀 Starting MLOps + Gen AI Platform API Server")
    print("=" * 60)
    print("API Documentation:")
    print("  Swagger UI: http://localhost:8000/docs")
    print("  ReDoc:      http://localhost:8000/redoc")
    print("  OpenAPI:    http://localhost:8000/openapi.json")
    print("=" * 60)

    # Start server
    uvicorn.run(
        "serving.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )


if __name__ == "__main__":
    main()
