# Deployment Guide - LangChain Production Patterns

## Overview

This guide covers deploying the LangChain production patterns to production environments, including Docker, Kubernetes, and monitoring setup.

## Prerequisites

- Python 3.8+
- Docker (for containerized deployment)
- Kubernetes cluster (for orchestrated deployment)
- Prometheus (for metrics collection)
- Redis (optional, for distributed locking)

## Environment Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Service Configuration
SERVICE_NAME=llm_service
LOG_LEVEL=INFO

# Cache Configuration
CACHE_SIZE=1000
CACHE_TTL_SECONDS=3600.0
SIMILARITY_THRESHOLD=0.95
ENABLE_SEMANTIC_CACHE=true

# Circuit Breaker Configuration
ENABLE_CIRCUIT_BREAKER=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60.0
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=2

# Rate Limiting Configuration
RATE_LIMIT_PER_SECOND=10.0
RATE_LIMIT_CAPACITY=20.0

# Deduplication Configuration
ENABLE_DEDUPLICATION=true
DEDUPLICATION_WINDOW_SECONDS=60.0

# Tracing Configuration
ENABLE_TRACING=true
TRACE_SAMPLE_RATE=1.0

# Batching Configuration
ENABLE_BATCHING=false
MAX_BATCH_SIZE=32
MIN_BATCH_SIZE=1
MAX_WAIT_SECONDS=0.1

# Connection Pool Configuration
CONNECTION_POOL_MIN_SIZE=2
CONNECTION_POOL_MAX_SIZE=10
CONNECTION_POOL_TIMEOUT=5.0
HEALTH_CHECK_INTERVAL=30.0

# Prometheus Configuration
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=8000

# Error Recovery Configuration
ENABLE_FALLBACK_TO_CACHE=true
ENABLE_REQUEST_QUEUING=true

# Retry Configuration
MAX_RETRIES=3
INITIAL_RETRY_DELAY=0.1
MAX_RETRY_DELAY=10.0
RETRY_EXPONENTIAL_BASE=2.0
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Prometheus metrics port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  llm-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENABLE_PROMETHEUS=true
      - PROMETHEUS_PORT=8000
    volumes:
      - ./config:/app/config
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

volumes:
  prometheus-data:
```

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-service
  template:
    metadata:
      labels:
        app: llm-service
    spec:
      containers:
      - name: llm-service
        image: llm-service:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENABLE_PROMETHEUS
          value: "true"
        - name: PROMETHEUS_PORT
          value: "8000"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: llm-service
spec:
  selector:
    app: llm-service
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: llm-service
spec:
  selector:
    matchLabels:
      app: llm-service
  endpoints:
  - port: http
    path: /metrics
```

## Monitoring Setup

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'llm-service'
    static_configs:
      - targets: ['llm-service:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import the following dashboard JSON for visualization:

```json
{
  "dashboard": {
    "title": "LLM Service Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(requests_total[5m])"
          }
        ]
      },
      {
        "title": "Latency Percentiles",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, request_latency_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Circuit Breaker State",
        "targets": [
          {
            "expr": "circuit_breaker_state"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))"
          }
        ]
      }
    ]
  }
}
```

## Health Checks

### Endpoints

- `/health` - Overall health check
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe

### Health Check Response

```json
{
  "status": "healthy",
  "components": {
    "circuit_breaker": {
      "status": "healthy",
      "message": "Circuit breaker is CLOSED",
      "details": {
        "state": "closed",
        "failure_rate": 0.0
      }
    },
    "connection_pool": {
      "status": "healthy",
      "message": "Connection pool healthy (2 in use, 8 available)",
      "details": {
        "in_use": 2,
        "available": 8,
        "utilization": 0.2
      }
    },
    "cache": {
      "status": "healthy",
      "message": "Cache healthy (500/1000 entries)",
      "details": {
        "size": 500,
        "max_size": 1000,
        "utilization": 0.5
      }
    }
  },
  "metrics": {
    "total_requests": 1000,
    "success_rate": 0.99
  }
}
```

## Scaling

### Horizontal Scaling

The service is stateless and can be scaled horizontally:

```bash
kubectl scale deployment llm-service --replicas=5
```

### Vertical Scaling

Adjust resource limits in the Kubernetes deployment:

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "4000m"
```

## Security

### Secrets Management

Use Kubernetes secrets for sensitive configuration:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: llm-service-secrets
type: Opaque
stringData:
  api-key: "your-api-key"
```

### Network Policies

Restrict network access:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: llm-service-policy
spec:
  podSelector:
    matchLabels:
      app: llm-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: allowed-namespace
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: prometheus
```

## Troubleshooting

### Common Issues

1. **Circuit Breaker Open**
   - Check failure rates
   - Review error logs
   - Adjust failure threshold if needed

2. **Connection Pool Exhausted**
   - Increase pool size
   - Check for connection leaks
   - Review timeout settings

3. **High Latency**
   - Check cache hit rates
   - Review rate limiting settings
   - Monitor connection pool utilization

### Logging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

### Metrics

Access Prometheus metrics:

```bash
curl http://localhost:8000/metrics
```

## Performance Tuning

### Cache Configuration

- Increase `CACHE_SIZE` for better hit rates
- Adjust `SIMILARITY_THRESHOLD` based on use case
- Set appropriate `CACHE_TTL_SECONDS`

### Rate Limiting

- Adjust `RATE_LIMIT_PER_SECOND` based on LLM provider limits
- Set `RATE_LIMIT_CAPACITY` to handle bursts

### Connection Pool

- Set `CONNECTION_POOL_MIN_SIZE` based on baseline load
- Set `CONNECTION_POOL_MAX_SIZE` based on peak load
- Adjust `CONNECTION_POOL_TIMEOUT` based on network latency

## Backup and Recovery

### Configuration Backup

```bash
kubectl get configmap llm-service-config -o yaml > config-backup.yaml
```

### Metrics Backup

Prometheus data is stored in persistent volumes and can be backed up.

## Updates and Rollouts

### Rolling Update

```bash
kubectl set image deployment/llm-service llm-service=llm-service:v2.0.0
kubectl rollout status deployment/llm-service
```

### Rollback

```bash
kubectl rollout undo deployment/llm-service
```

