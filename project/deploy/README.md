# Production Deployment Guide

This directory contains production-ready deployment configurations for the AI Platform.

## 📋 Deployment Options

### 1. Docker Compose (Development/Staging)

**Quick start for development and testing:**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services included:**
- **API Service** (FastAPI) - Main application server
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **TorchServe** - Model serving for ML models
- **Prometheus** - Metrics collection
- **Grafana** - Monitoring dashboard
- **Nginx** - Load balancer and reverse proxy

### 2. Kubernetes (Production)

**Production deployment with high availability:**

```bash
# Deploy to Kubernetes cluster
kubectl apply -f kubernetes/

# Check deployment status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/ai-platform-api
```

**Components:**
- **Horizontal Pod Autoscaling** - Automatic scaling based on CPU/memory
- **Persistent Volumes** - Data persistence for database and models
- **ConfigMaps/Secrets** - Secure configuration management
- **Ingress** - External access with SSL termination

## 🚀 Quick Start

### Prerequisites

1. **Docker & Docker Compose** (for local development)
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Kubernetes** (for production)
   ```bash
   # Install kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   ```

### Environment Setup

1. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Database initialization:**
   ```bash
   # For Docker Compose
   docker-compose exec db psql -U user -d app -f /docker-entrypoint-initdb.d/init.sql

   # For Kubernetes
   kubectl exec -it $(kubectl get pods -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U user -d app
   ```

## 📊 Monitoring & Observability

### Health Checks

**API Endpoints:**
- `GET /health` - General health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe
- `GET /metrics` - Prometheus metrics

### Monitoring Stack

1. **Access Grafana:**
   - Docker: http://localhost:3000 (admin/admin)
   - Kubernetes: Check ingress configuration

2. **View Prometheus metrics:**
   - Docker: http://localhost:9090
   - Kubernetes: Check service configuration

3. **Application metrics:**
   - Available at `/metrics` endpoint
   - Includes request counts, durations, and health status

## 🔧 Configuration

### Environment Variables

**Required:**
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@db:5432/app
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
```

**Optional:**
```bash
LOG_LEVEL=INFO
MAX_WORKERS=4
MODEL_CACHE_SIZE=100
```

### Secrets Management

**Docker Compose:**
```yaml
secrets:
  db-secret:
    environment: "DATABASE_URL"
```

**Kubernetes:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  username: <base64-encoded>
  password: <base64-encoded>
  database_url: <base64-encoded>
```

## 🚦 Scaling

### Horizontal Scaling

**Docker Compose:**
```yaml
services:
  api:
    deploy:
      replicas: 3
```

**Kubernetes:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-platform-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Vertical Scaling

**Resource limits:**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

## 🔒 Security

### SSL/TLS Configuration

**Nginx with SSL:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://api_backend;
    }
}
```

### Network Security

**Kubernetes Network Policies:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: ai-platform-api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx
```

## 📈 Performance Optimization

### Database Optimization

1. **Connection pooling:**
   ```python
   # Use SQLAlchemy with connection pooling
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=10,
       max_overflow=20
   )
   ```

2. **Indexing:**
   ```sql
   CREATE INDEX idx_timestamp ON events (timestamp);
   CREATE INDEX idx_user_id ON users (user_id);
   ```

### Caching Strategy

1. **Redis caching:**
   ```python
   # Cache expensive operations
   @redis_cache(expire=300)
   async def expensive_operation(data):
       return await compute_expensive_result(data)
   ```

2. **Application-level caching:**
   ```python
   # Cache model predictions
   @lru_cache(maxsize=1000)
   def predict_cached(input_data):
       return model.predict(input_data)
   ```

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   # Check logs
   docker-compose logs api
   kubectl logs -f deployment/ai-platform-api
   ```

2. **Database connection issues:**
   ```bash
   # Test database connectivity
   docker-compose exec db pg_isready -U user -d app
   ```

3. **High memory usage:**
   ```bash
   # Check resource usage
   docker stats
   kubectl top pods
   ```

### Debug Commands

```bash
# Docker Compose
docker-compose ps                    # List services
docker-compose exec api bash        # Access container shell
docker-compose logs -f api          # Follow logs

# Kubernetes
kubectl get pods                    # List pods
kubectl describe pod <pod-name>     # Pod details
kubectl logs -f <pod-name>          # Follow logs
kubectl exec -it <pod-name> -- bash # Access pod shell
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

## 🤝 Support

For deployment issues:
1. Check the troubleshooting section
2. Review logs for error messages
3. Verify configuration settings
4. Ensure all prerequisites are met

---

**Ready to deploy?** Start with Docker Compose for development, then move to Kubernetes for production! 🚀