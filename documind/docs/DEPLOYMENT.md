# DocuMind Production Deployment Guide

## Overview

This guide covers deploying DocuMind to production environments with high availability, security, and scalability.

## Prerequisites

- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- SSL certificates (Let's Encrypt recommended)
- Domain name
- SMTP server for notifications

## Quick Start with Docker Compose

### 1. Clone and Configure

```bash
git clone https://github.com/yourusername/documind.git
cd documind
cp env.example .env
```

### 2. Edit Environment Variables

Edit `.env` with your production values:

```bash
# Database
POSTGRES_PASSWORD=your_secure_db_password
SECRET_KEY=your_32_char_secret_key

# AI Services
OPENAI_API_KEY=sk-your_openai_key

# Domain
ALLOWED_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com
```

### 3. Initialize Database

```bash
# Start only database
docker-compose up -d db redis

# Initialize database schema
docker-compose run --rm app python scripts/init_db.py

# Stop database
docker-compose down
```

### 4. Start Production Stack

```bash
# Start all services
docker-compose up -d

# Check health
curl https://yourdomain.com/health
```

## Production Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   CDN (CloudFlare) │
│    (Nginx)      │    │                   │
└─────────────────┘    └─────────────────┘
          │                       │
          ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   DocuMind App  │    │   Static Assets │
│   (3 instances) │    │   (S3/CloudFront)│
└─────────────────┘    └─────────────────┘
          │
          ▼
┌─────────────────┐    ┌─────────────────┐
│   Redis Cluster │    │ PostgreSQL      │
│   (3 nodes)     │    │ (Primary +      │
└─────────────────┘    │  2 Replicas)    │
                       └─────────────────┘
```

## Detailed Configuration

### Database Setup

#### PostgreSQL Configuration

```sql
-- Create production database
CREATE DATABASE documind OWNER documind;
GRANT ALL PRIVILEGES ON DATABASE documind TO documind;

-- Enable extensions
\c documind
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
```

#### Connection Pooling

Use PgBouncer for connection pooling:

```ini
[databases]
documind = host=postgres port=5432 user=documind password=secret

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = md5
auth_file = userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
reserve_pool_size = 5
```

### Redis Configuration

#### Production Redis Cluster

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass your_redis_password
    volumes:
      - redis_master_data:/data

  redis-slave-1:
    image: redis:7-alpine
    command: redis-server --slaveof redis-master 6379 --requirepass your_redis_password
    depends_on:
      - redis-master

  redis-slave-2:
    image: redis:7-alpine
    command: redis-server --slaveof redis-master 6379 --requirepass your_redis_password
    depends_on:
      - redis-master
```

### Application Configuration

#### Environment Variables

```bash
# Production .env
DEBUG=false
SECRET_KEY=your_32_char_minimum_secret_key_here
HOST=0.0.0.0
PORT=8000

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=documind
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=documind

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Security
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,app.yourdomain.com,api.yourdomain.com

# File Storage
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=52428800

# AI Services
OPENAI_API_KEY=sk-your_openai_key
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key

# Monitoring
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project_id
NEW_RELIC_LICENSE_KEY=your_new_relic_key

# Email
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
```

### Reverse Proxy Configuration

#### Nginx Configuration

```nginx
# nginx.conf
upstream documind_app {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload";

    location / {
        proxy_pass http://documind_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://documind_app;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### SSL Certificate Setup

#### Let's Encrypt with Certbot

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d yourdomain.com

# Setup auto-renewal
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring & Observability

### Application Monitoring

#### Sentry for Error Tracking

```python
# Already configured in app/core/monitoring.py
import sentry_sdk
sentry_sdk.init(dsn=settings.SENTRY_DSN, environment="production")
```

#### New Relic for Performance Monitoring

```python
# Already configured in app/core/monitoring.py
import newrelic.agent
newrelic.agent.initialize(config_file='newrelic.ini')
```

### Infrastructure Monitoring

#### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'documind'
    static_configs:
      - targets: ['app1:8000', 'app2:8000', 'app3:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']
```

#### Grafana Dashboards

Import the provided dashboard JSON files:
- DocuMind Application Metrics
- PostgreSQL Database Metrics
- Redis Cache Metrics
- System Resources

### Log Aggregation

#### ELK Stack Setup

```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false

  logstash:
    image: logstash:8.11.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
```

## Backup Strategy

### Database Backups

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h postgres -U documind documind > /backups/documind_$DATE.sql
gzip /backups/documind_$DATE.sql

# Upload to S3
aws s3 cp /backups/documind_$DATE.sql.gz s3://your-backup-bucket/

# Clean old backups (keep 30 days)
find /backups -name "documind_*.sql.gz" -mtime +30 -delete
```

### File Backups

```bash
# Backup uploaded files
aws s3 sync /app/uploads s3://your-backup-bucket/uploads/
```

### Automated Backups with Cron

```bash
# crontab
0 2 * * * /path/to/backup_script.sh  # Daily at 2 AM
0 3 * * 0 /path/to/weekly_cleanup.sh  # Weekly cleanup
```

## Scaling Strategy

### Horizontal Scaling

#### Application Scaling

```bash
# Scale to 5 instances
docker-compose up -d --scale app=5
```

#### Load Balancing

Use Nginx or AWS ALB for load balancing across multiple instances.

### Database Scaling

#### Read Replicas

```sql
-- Create replication user
CREATE USER replicator REPLICATION LOGIN PASSWORD 'replication_password';

-- Configure primary
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 3;
ALTER SYSTEM SET wal_keep_size = '64MB';
```

#### Connection Pooling

Use PgBouncer or AWS RDS Proxy for connection pooling.

### Caching Strategy

#### Redis Cluster

```yaml
# Redis cluster configuration
redis-cluster:
  image: redis:7-alpine
  command: redis-server /etc/redis/redis.conf
  volumes:
    - ./redis/redis.conf:/etc/redis/redis.conf
    - redis_data:/data
```

## Security Hardening

### Network Security

#### Firewall Configuration

```bash
# UFW rules
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
ufw --force enable
```

#### Security Groups (AWS)

```
Inbound Rules:
- 80, 443 from 0.0.0.0/0 (HTTP/HTTPS)
- 22 from your_ip/32 (SSH)

Outbound Rules:
- All traffic
```

### Application Security

#### Rate Limiting

```python
# Redis-based rate limiting
from redis import Redis
import time

redis = Redis(host='redis', password=settings.REDIS_PASSWORD)

def rate_limit(key: str, limit: int = 100, window: int = 60):
    current = int(time.time() // window)
    redis_key = f"rate_limit:{key}:{current}"

    count = redis.incr(redis_key)
    redis.expire(redis_key, window)

    return count <= limit
```

#### API Key Rotation

```python
# Rotate API keys every 90 days
from datetime import datetime, timedelta

def should_rotate_api_key(created_at: datetime) -> bool:
    return datetime.utcnow() - created_at > timedelta(days=90)
```

### Data Protection

#### Encryption at Rest

```sql
-- Enable PostgreSQL encryption
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/postgres.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/postgres.key';
```

#### Backup Encryption

```bash
# Encrypt backups
openssl enc -aes-256-cbc -salt -in backup.sql -out backup.sql.enc -k your_backup_password
```

## Performance Optimization

### Database Optimization

#### Indexing Strategy

```sql
-- Performance indexes
CREATE INDEX CONCURRENTLY idx_code_entities_repo_lang ON code_entities(repository_id, language);
CREATE INDEX CONCURRENTLY idx_documentations_repo_type ON documentations(repository_id, doc_type);
CREATE INDEX CONCURRENTLY idx_analysis_runs_repo_status ON analysis_runs(repository_id, status);

-- Text search indexes
CREATE INDEX CONCURRENTLY idx_documentations_content_gin ON documentations USING gin(to_tsvector('english', content));
```

#### Query Optimization

```sql
-- Use EXPLAIN ANALYZE to optimize slow queries
EXPLAIN ANALYZE SELECT * FROM code_entities WHERE repository_id = $1;

-- Add composite indexes for common query patterns
CREATE INDEX idx_code_entities_composite ON code_entities(repository_id, entity_type, language);
```

### Application Optimization

#### Async Processing

```python
# Move heavy operations to background tasks
from celery import Celery

app = Celery('documind', broker=settings.CELERY_BROKER_URL)

@app.task
def analyze_repository_async(repo_id: int, repo_path: str):
    # Heavy analysis in background
    pass
```

#### Caching Strategy

```python
from redis import Redis
import json

redis = Redis(host=settings.REDIS_HOST, password=settings.REDIS_PASSWORD)

def cache_result(key: str, data: dict, ttl: int = 3600):
    redis.setex(key, ttl, json.dumps(data))

def get_cached_result(key: str) -> dict:
    data = redis.get(key)
    return json.loads(data) if data else None
```

## Disaster Recovery

### Backup Restore

```bash
# Restore from backup
gunzip backup.sql.gz
psql -h postgres -U documind -d documind < backup.sql
```

### Failover Strategy

#### Database Failover

```sql
-- Promote replica to primary
pg_ctl promote -D /var/lib/postgresql/data
```

#### Application Failover

Use Kubernetes or Docker Swarm for automatic failover:

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: documind
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
  template:
    spec:
      containers:
      - name: documind
        image: documind/app:latest
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Maintenance Procedures

### Regular Maintenance

#### Database Maintenance

```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Reindex
REINDEX DATABASE documind;

-- Update statistics
ANALYZE;
```

#### Application Updates

```bash
# Zero-downtime deployment
docker-compose pull
docker-compose up -d --scale app=6  # Add extra capacity
docker-compose up -d --scale app=3  # Remove old instances
```

### Monitoring Alerts

#### Critical Alerts

- Application down (ping /health)
- Database connection failures
- High error rates (>5%)
- Disk space >90%
- Memory usage >85%

#### Warning Alerts

- Response time >2s
- CPU usage >70%
- Database slow queries
- Failed background jobs

## Troubleshooting

### Common Issues

#### High Memory Usage

```bash
# Check memory usage
docker stats

# Restart containers
docker-compose restart app

# Scale up if needed
docker-compose up -d --scale app=4
```

#### Slow Queries

```sql
-- Find slow queries
SELECT query, total_time, calls FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_slow_query ON table_name(column_name);
```

#### Connection Pool Exhaustion

```yaml
# Increase pool size
environment:
  - DATABASE_POOL_SIZE=20
  - DATABASE_MAX_OVERFLOW=30
```

## Compliance & Security

### GDPR Compliance

- Data encryption at rest and in transit
- Right to erasure (data deletion)
- Audit logging for all data access
- Consent management for data processing

### SOC 2 Compliance

- Access controls and authentication
- Change management procedures
- Incident response plan
- Regular security assessments

### HIPAA Compliance (if handling health data)

- PHI encryption and access controls
- Audit trails for data access
- Business associate agreements
- Data retention policies

## Cost Optimization

### Resource Optimization

#### Auto Scaling

```yaml
# AWS Auto Scaling Group
resource "aws_autoscaling_group" "documind" {
  min_size         = 3
  max_size         = 10
  desired_capacity = 3

  # Scale based on CPU utilization
  policy {
    type               = "TargetTrackingScaling"
    target_tracking_configuration {
      predefined_metric_specification {
        predefined_metric_type = "ASGAverageCPUUtilization"
      }
      target_value = 70.0
    }
  }
}
```

#### Reserved Instances

```bash
# AWS Reserved Instances for cost savings
aws ec2 purchase-reserved-instances-offering \
  --instance-count 3 \
  --reserved-instances-offering-id offering-id
```

### Monitoring Costs

#### CloudWatch Cost Allocation

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetUsageAndCosts"
      ],
      "Resource": "*"
    }
  ]
}
```

## Support & Maintenance

### Regular Tasks

- [ ] Weekly: Review error logs and fix issues
- [ ] Monthly: Update dependencies and security patches
- [ ] Quarterly: Performance optimization and scaling review
- [ ] Annually: Security audit and compliance review

### Emergency Contacts

- **On-call Engineer**: +1-555-0123
- **DevOps Team**: devops@yourcompany.com
- **Security Team**: security@yourcompany.com
- **Database Admin**: dba@yourcompany.com

### Escalation Procedures

1. **Level 1**: Application alerts - On-call engineer responds within 15 minutes
2. **Level 2**: Database issues - DBA team responds within 30 minutes
3. **Level 3**: Security incidents - Security team responds immediately
4. **Level 4**: Complete outage - Full incident response team activated

---

**🎉 Your DocuMind production deployment is now complete!**

Monitor your application closely in the first 24-48 hours and adjust scaling as needed. Regular maintenance and monitoring will ensure high availability and performance.
