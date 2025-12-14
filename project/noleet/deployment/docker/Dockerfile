# Multi-stage Docker build for NoLeet application
# Stage 1: Builder stage for dependencies and compilation
FROM python:3.11-slim as builder

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r noleet && useradd -r -g noleet noleet

# Set work directory
WORKDIR /app

# Copy dependency files first for better caching
COPY requirements.txt test-requirements.txt setup.py pyproject.toml ./

# Install Python dependencies
RUN pip install --user --no-warn-script-location --upgrade pip setuptools wheel && \
    pip install --user --no-warn-script-location -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim as production

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/noleet/.local/bin:$PATH" \
    PYTHONPATH="/app" \
    NOLEET_ENV=production \
    NOLEET_AUTO_OPTIMIZE=true

# Install production system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    lsb-release \
    procps \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Create application user and directories
RUN groupadd -r noleet && useradd -r -g noleet noleet && \
    mkdir -p /app /data /logs /cache && \
    chown -R noleet:noleet /app /data /logs /cache

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/noleet/.local
RUN chown -R noleet:noleet /home/noleet/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=noleet:noleet . .

# Create non-root user directories
RUN mkdir -p /home/noleet/.cache && \
    chown -R noleet:noleet /home/noleet

# Switch to non-root user
USER noleet

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000

# Default command
CMD ["python", "-m", "noleet.cli.main"]

# Labels for container metadata
LABEL maintainer="NoLeet Team" \
      version="1.0.0" \
      description="AI-powered coding project recommendation system" \
      org.opencontainers.image.source="https://github.com/noleet/noleet" \
      org.opencontainers.image.licenses="MIT"
