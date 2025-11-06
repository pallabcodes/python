# 🚀 Deployment Guide for MLOps + Gen AI Platform

This guide covers production deployment of the MLOps + Gen AI Platform using Docker, Kubernetes, and cloud services.

## 📋 Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (optional, for production)
- PostgreSQL database (recommended for production)
- Redis (recommended for caching)
- SSL certificates (for HTTPS)

## 🐳 Quick Start with Docker Compose

### Development Environment

```bash
# Clone repository
git clone <repository-url>
cd mlops-genai-platform

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f mlops-genai-platform-dev

# Access application
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# pgAdmin: http://localhost:5050 (admin@mlops.com / admin)
```

### Production Environment

```bash
# Set environment variables
export POSTGRES_PASSWORD=your_secure_password
export REDIS_PASSWORD=your_secure_password
export GRAFANA_PASSWORD=your_secure_password

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl http://localhost/health/live

# Access services
# API: http://localhost
# Grafana: http://localhost:3000 (admin / your_password)
# Prometheus: http://localhost:9090
```

## ☸️ Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl and helm
# Configure access to your Kubernetes cluster

# Create namespace
kubectl create namespace mlops-platform

# Create secrets
kubectl create secret generic mlops-secrets \
  --from-literal=postgres-password=your_secure_password \
  --from-literal=redis-password=your_secure_password \
  --namespace mlops-platform
```

### Deploy with kubectl

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/deployment.yaml -n mlops-platform

# Check deployment status
kubectl get pods -n mlops-platform
kubectl get services -n mlops-platform

# View logs
kubectl logs -f deployment/mlops-genai-platform -n mlops-platform

# Scale deployment
kubectl scale deployment mlops-genai-platform --replicas=5 -n mlops-platform
```

### Deploy with Helm

```bash
# Add helm repository (if using custom charts)
# helm repo add mlops-platform ./helm-charts

# Install with helm
helm install mlops-platform ./helm-charts \
  --namespace mlops-platform \
  --set postgresql.auth.password=your_secure_password \
  --set redis.auth.password=your_secure_password
```

## 🏗️ Manual Installation

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install optional dependencies (as needed)
pip install torch  # For model training
pip install chromadb  # For vector search
pip install transformers  # For LLM processing
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Example `.env` file:
```bash
# Platform Configuration
MLOPS_PROJECT_NAME=mlops-genai-platform
MLOPS_ENVIRONMENT=production

# Database
MLOPS_DATABASE__CONNECTION_STRING=postgresql://user:password@localhost:5432/mlops_platform

# LLM Configuration
MLOPS_LLM__PROVIDER=openai
MLOPS_LLM__MODEL_NAME=gpt-3.5-turbo
MLOPS_LLM__API_KEY=your_openai_api_key

# Monitoring
MLOPS_MONITORING__ENABLE_TRACING=true
MLOPS_MONITORING__METRICS_INTERVAL=30
```

### 3. Initialize Database

```bash
# Run database migrations (if using SQLAlchemy)
python -c "from core.platform import MLOpsPlatform; p = MLOpsPlatform(); p.initialize()"
```

### 4. Start Application

```bash
# Start API server
python scripts/run_api.py

# Or use uvicorn directly
uvicorn serving.api:app --host 0.0.0.0 --port 8000
```

## ☁️ Cloud Deployment

### Google Cloud Platform (GCP)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/your-project/mlops-genai-platform

# Deploy to Cloud Run
gcloud run deploy mlops-genai-platform \
  --image gcr.io/your-project/mlops-genai-platform \
  --platform managed \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "MLOPS_ENVIRONMENT=production"

# Or deploy to GKE
gcloud container clusters create mlops-cluster --num-nodes=3
kubectl apply -f k8s/deployment.yaml
```

### AWS

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
docker tag mlops-genai-platform:latest your-account.dkr.ecr.us-east-1.amazonaws.com/mlops-genai-platform:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/mlops-genai-platform:latest

# Deploy to ECS/Fargate
aws ecs create-cluster --cluster-name mlops-platform
aws ecs create-service --cluster mlops-platform --service-name mlops-service --task-definition mlops-task
```

### Azure

```bash
# Build and push to ACR
az acr build --registry your-registry --image mlops-genai-platform:latest .

# Deploy to AKS
az aks create --resource-group mlops-rg --name mlops-cluster --node-count 3
kubectl apply -f k8s/deployment.yaml
```

## 🔒 Security Configuration

### SSL/TLS Setup

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Or use Let's Encrypt
certbot certonly --webroot -w /var/www/html -d your-domain.com

# Update nginx configuration with SSL
# Edit nginx/nginx.conf and uncomment SSL server block
```

### Environment Variables

```bash
# Database credentials
POSTGRES_PASSWORD=secure_password_here
REDIS_PASSWORD=secure_password_here

# API Keys (use secret management)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Application secrets
SECRET_KEY=your-secret-key-here
```

### Network Security

```bash
# Configure firewall
ufw allow 80
ufw allow 443
ufw allow 22

# Use security groups in cloud environments
# Configure VPC, subnets, and NACLs appropriately
```

## 📊 Monitoring Setup

### Prometheus & Grafana

```bash
# Access Grafana
# URL: http://localhost:3000
# Username: admin
# Password: your_grafana_password

# Import dashboards for MLOps metrics
# Dashboard ID: 12345 (example)
```

### Health Checks

```bash
# Liveness probe
curl http://localhost/health/live

# Readiness probe
curl http://localhost/health/ready

# Detailed health check
curl http://localhost/health

# Metrics endpoint
curl http://localhost/metrics
```

## 🔧 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port
   lsof -i :8000
   # Kill process or change port
   ```

2. **Database connection failed**
   ```bash
   # Check database status
   docker-compose logs postgres
   # Verify connection string
   ```

3. **Out of memory**
   ```bash
   # Increase Docker memory limits
   # Or reduce batch sizes in configuration
   ```

4. **Model loading issues**
   ```bash
   # Check model file paths
   # Verify model compatibility
   # Check available disk space
   ```

### Logs and Debugging

```bash
# View application logs
docker-compose logs mlops-genai-platform

# View specific service logs
docker-compose logs postgres redis

# Enable debug logging
export MLOPS_LOGGING__LEVEL=DEBUG
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale with Docker Compose
docker-compose up -d --scale mlops-genai-platform=3

# Scale with Kubernetes
kubectl scale deployment mlops-genai-platform --replicas=5
```

### Vertical Scaling

```bash
# Increase resources in docker-compose.yml
services:
  mlops-genai-platform:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

### Load Balancing

```bash
# Use nginx as load balancer
# Configure upstream servers in nginx.conf

# Or use cloud load balancers
# AWS ALB, GCP Load Balancer, Azure Load Balancer
```

## 🔄 Updates and Rollbacks

### Rolling Updates

```bash
# Update Docker image
docker-compose pull
docker-compose up -d

# Zero-downtime deployment with Kubernetes
kubectl set image deployment/mlops-genai-platform mlops-genai-platform=new-image:tag
kubectl rollout status deployment/mlops-genai-platform
```

### Rollbacks

```bash
# Rollback with Docker Compose
docker-compose down
docker tag previous-image:latest mlops-genai-platform:latest
docker-compose up -d

# Rollback with Kubernetes
kubectl rollout undo deployment/mlops-genai-platform
```

## 📞 Support

For deployment issues:
1. Check the logs: `docker-compose logs`
2. Verify configuration in `.env`
3. Check system resources
4. Review network connectivity
5. Consult the troubleshooting section above

## 🚀 Next Steps

After successful deployment:
1. Configure monitoring dashboards
2. Set up alerting rules
3. Configure backup strategies
4. Implement CI/CD pipelines
5. Set up log aggregation
6. Configure auto-scaling policies

---

**🎯 Your MLOps + Gen AI Platform is now production-ready!**
