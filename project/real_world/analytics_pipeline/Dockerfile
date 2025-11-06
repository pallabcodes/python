"""
Dockerfile for Real-Time Multi-Source Analytics Pipeline

This Dockerfile creates a production-ready container for the analytics pipeline
with optimized Python environment and all dependencies.
"""

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r pipeline && useradd -r -g pipeline pipeline

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/exports /app/config

# Set permissions
RUN chown -R pipeline:pipeline /app
USER pipeline

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port for API/dashboard
EXPOSE 8000

# Default command
CMD ["python", "scripts/run_pipeline.py", "--config", "config/pipeline.yaml"]
