# Multi-stage Dockerfile for MLOps + Gen AI Platform

# Base stage with Python and dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r mlops && useradd -r -g mlops mlops

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM base as production

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/models /app/logs && \
    chown -R mlops:mlops /app

# Switch to non-root user
USER mlops

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "scripts/run_api.py"]

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    black \
    isort \
    mypy

# Copy application code
COPY . .

# Create development directories
RUN mkdir -p /app/data /app/models /app/logs && \
    chown -R mlops:mlops /app

# Switch to non-root user
USER mlops

# Expose port
EXPOSE 8000

# Development command with reload
CMD ["uvicorn", "serving.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# GPU-enabled stage (optional)
FROM base as gpu

# Install CUDA runtime (adjust version as needed)
RUN apt-get update && apt-get install -y \
    nvidia-cuda-runtime \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA support
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/data /app/models /app/logs && \
    chown -R mlops:mlops /app

# Switch to non-root user
USER mlops

# GPU health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD nvidia-smi || exit 1

EXPOSE 8000

CMD ["python", "scripts/run_api.py"]
