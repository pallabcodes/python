"""Main FastAPI application for DocuMind."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from rich.console import Console
from rich.logging import RichHandler
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import DocuMindException
from app.core.monitoring import RequestLoggingMiddleware, health_checker, lifespan_monitoring
from app.db.session import engine
from app.db.base import Base

# Setup rich logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("🚀 Starting DocuMind...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ Database initialized")

    yield

    logger.info("🛑 Shutting down DocuMind...")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DocuMind API",
        description="AI-Powered Documentation Assistant",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan_monitoring,
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add trusted host middleware
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )

    # Add monitoring middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Health check endpoints
    @app.get("/health")
    async def basic_health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check with component status."""
        health_status = await health_checker.check_all()
        return health_status

    @app.get("/health/database")
    async def database_health_check():
        """Database-specific health check."""
        try:
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            return {"status": "healthy", "component": "database"}
        except Exception as e:
            return {"status": "unhealthy", "component": "database", "error": str(e)}

    @app.get("/metrics")
    async def metrics_endpoint():
        """Application metrics endpoint."""
        from app.core.monitoring import metrics
        return metrics.get_metrics()

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "DocuMind",
            "description": "AI-Powered Documentation Assistant",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    # Exception handlers
    @app.exception_handler(DocuMindException)
    async def documind_exception_handler(request: Request, exc: DocuMindException):
        """Handle DocuMind-specific exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
            },
        )

    # Include API routers
    app.include_router(api_router, prefix="/api/v1")

    logger.info("✅ FastAPI application created")
    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    console.print("[green]🚀 Starting DocuMind Server[/green]")
    console.print(f"[dim]API docs: http://localhost:{settings.PORT}/docs[/dim]")
    console.print(f"[dim]Health check: http://localhost:{settings.PORT}/health[/dim]")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )
