# NoLeet Production Deployment Guide

This guide covers the production deployment of NoLeet using Docker, Kubernetes, and Helm for a scalable, secure, and maintainable setup.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
- [Deployment Methods](#deployment-methods)
- [Monitoring & Observability](#monitoring--observability)
- [Security Considerations](#security-considerations)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)
- [Scaling](#scaling)

## Prerequisites

### System Requirements

- **Kubernetes Cluster**: 1.19+ with RBAC enabled
- **Helm**: 3.0+
- **Docker**: 20.10+
- **kubectl**: Configured for your cluster
- **SSL Certificate**: For HTTPS (Let's Encrypt recommended)

### Infrastructure Requirements

- **CPU**: Minimum 4 cores, recommended 8+ cores
- **Memory**: Minimum 8GB, recommended 16GB+
- **Storage**: Minimum 100GB SSD, recommended 500GB+
- **Network**: Stable internet connection for API calls

### External Services

- **Domain Name**: For API and monitoring access
- **SSL Certificates**: For HTTPS encryption
- **Database**: PostgreSQL (managed or self-hosted)
- **Cache**: Redis (managed or self-hosted)
- **Monitoring**: Prometheus, Grafana (included)
- **Logging**: Elasticsearch, Kibana (included)

## Quick Start

1. **Clone and configure:**
   ```bash
   git clone https://github.com/noleet/noleet.git
   cd noleet/deployment
   cp env.example .env
   # Edit .env with your configuration
   ```

2. **Deploy to Kubernetes:**
   ```bash
   ./scripts/deploy.sh
   ```

3. **Verify deployment:**
   ```bash
   kubectl get pods -n noleet
   kubectl get ingress -n noleet
   ```

## Architecture Overview

### Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   NGINX Ingress │────│  NoLeet App      │────│   PostgreSQL    │
│                 │    │  (Python/FastAPI)│    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Cert Manager   │    │     Redis        │    │   Prometheus    │
│   (SSL/TLS)     │    │     Cache        │    │   Monitoring    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    Grafana      │────│  Elasticsearch   │────│     Kibana      │
│  Dashboards     │    │     Logging      │    │   Analytics     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Network Flow

1. **External Traffic** → NGINX Ingress → NoLeet App
2. **API Calls** → NoLeet App → External APIs (OpenAI, LeetCode)
3. **Metrics** → Prometheus → Grafana Dashboards
4. **Logs** → Logstash → Elasticsearch → Kibana

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Core Configuration
NOLEET_ENV=production
DOMAIN=your-domain.com

# Database
POSTGRES_PASSWORD=your-secure-password
DATABASE_URL=postgresql://noleet:${POSTGRES_PASSWORD}@db-host:5432/noleet

# API Keys
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key

# Monitoring
GRAFANA_PASSWORD=admin-password
```

### Helm Values

Customize `helm/values.yaml` for your environment:

```yaml
app:
  replicaCount: 3
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"

ingress:
  hosts:
    - host: your-domain.com
```

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

```bash
# Full deployment
./scripts/deploy.sh

# Individual steps
./scripts/deploy.sh build    # Build and push Docker image
./scripts/deploy.sh deploy   # Deploy to Kubernetes
./scripts/deploy.sh test     # Run post-deployment tests
```

### Method 2: Manual Helm Deployment

```bash
# Add required repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Deploy
helm install noleet ./helm -f helm-values.yaml
```

### Method 3: Docker Compose (Development/Staging)

```bash
# For development testing
cd docker
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring & Observability

### Accessing Monitoring Stack

```bash
# Port forward services
kubectl port-forward -n noleet svc/noleet-grafana 3000:3000
kubectl port-forward -n noleet svc/noleet-prometheus 9090:9090
kubectl port-forward -n noleet svc/noleet-kibana 5601:5601

# Access URLs
# Grafana: http://localhost:3000 (admin/admin-password)
# Prometheus: http://localhost:9090
# Kibana: http://localhost:5601
```

### Key Metrics to Monitor

- **Application Performance**: Response time, throughput, error rates
- **System Resources**: CPU, memory, disk usage
- **Database**: Connection pool, query performance
- **Cache**: Hit rates, eviction rates
- **External APIs**: Success rates, latency

### Alerting

Configure alerts in Prometheus for:
- High error rates (>5%)
- High latency (>2s)
- Resource exhaustion (>90% usage)
- Service downtime

## Security Considerations

### SSL/TLS Encryption

- Automatic SSL certificates via cert-manager
- HTTPS redirect enforced
- TLS 1.3 preferred

### Network Security

```bash
# Enable network policies
kubectl apply -f kubernetes/network-policy.yaml

# Security contexts
kubectl apply -f kubernetes/security-context.yaml
```

### API Security

- JWT authentication for API access
- Rate limiting (100 requests/minute)
- Input validation and sanitization
- CORS configuration

### Secret Management

- Kubernetes secrets for sensitive data
- External secret management (Vault, AWS Secrets Manager)
- Rotate secrets regularly

## Backup & Recovery

### Database Backups

```bash
# Automated daily backups
kubectl apply -f kubernetes/backup-job.yaml

# Manual backup
kubectl exec -n noleet deployment/noleet-postgres -- pg_dump -U noleet noleet > backup.sql
```

### Configuration Backups

```bash
# Backup Helm releases
helm list -n noleet
helm get values noleet -n noleet > values-backup.yaml
```

### Disaster Recovery

1. **Database Recovery**: Restore from latest backup
2. **Application Recovery**: Redeploy from Helm chart
3. **Configuration Recovery**: Reapply saved configurations

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check pod status
kubectl describe pod -n noleet -l app=noleet

# Check logs
kubectl logs -n noleet deployment/noleet-app -f

# Check events
kubectl get events -n noleet --sort-by=.metadata.creationTimestamp
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -n noleet deployment/noleet-postgres -- pg_isready -U noleet

# Check database logs
kubectl logs -n noleet deployment/noleet-postgres -f
```

#### Ingress Issues
```bash
# Check ingress status
kubectl describe ingress -n noleet

# Test connectivity
curl -I https://your-domain.com/health
```

### Debug Commands

```bash
# Get all resources
kubectl get all -n noleet

# Describe problematic pod
kubectl describe pod/pod-name -n noleet

# Check resource usage
kubectl top pods -n noleet
kubectl top nodes

# View logs with context
kubectl logs -n noleet deployment/noleet-app --previous
```

## Scaling

### Horizontal Pod Autoscaling

```bash
# Enable HPA
kubectl apply -f kubernetes/hpa.yaml

# Check HPA status
kubectl get hpa -n noleet
kubectl describe hpa noleet-app-hpa -n noleet
```

### Vertical Scaling

```bash
# Update resource limits
kubectl patch deployment noleet-app -n noleet --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "4Gi"}]'
```

### Database Scaling

```bash
# Scale PostgreSQL
kubectl scale deployment noleet-postgres --replicas=2 -n noleet

# Add read replicas for read-heavy workloads
kubectl apply -f kubernetes/postgres-replica.yaml
```

## Maintenance

### Updates

```bash
# Update application
./scripts/deploy.sh

# Update Helm dependencies
helm dependency update ./helm

# Update Kubernetes manifests
kubectl apply -k kubernetes/
```

### Log Rotation

```bash
# Configure log rotation
kubectl apply -f kubernetes/log-rotation.yaml

# Manual log cleanup
kubectl exec -n noleet deployment/noleet-app -- find /app/logs -name "*.log" -mtime +7 -delete
```

### Performance Tuning

- Monitor resource usage trends
- Adjust Gunicorn worker count based on load
- Optimize database queries
- Implement caching strategies

## Support

### Documentation
- [API Documentation](./docs/api.md)
- [Troubleshooting Guide](./docs/troubleshooting.md)
- [Configuration Reference](./docs/configuration.md)

### Getting Help
1. Check logs and monitoring dashboards
2. Review Kubernetes events and pod status
3. Consult the troubleshooting section above
4. Check GitHub issues for known problems

---

For additional support, please contact the NoLeet team or create an issue on GitHub.
