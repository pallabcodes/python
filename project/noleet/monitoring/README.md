# NoLeet Monitoring Stack

Enterprise-grade monitoring solution for NoLeet application with comprehensive observability, alerting, and visualization capabilities.

## 🏗️ Architecture

The monitoring stack consists of:

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and management
- **Elasticsearch**: Log storage and search
- **Logstash**: Log processing and ingestion
- **Kibana**: Log visualization
- **cAdvisor**: Container metrics
- **Node Exporter**: System metrics
- **Redis Exporter**: Cache metrics

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available
- Ports 3000, 5601, 9090, 9200 available

### Setup and Launch

```bash
# Navigate to monitoring directory
cd monitoring

# Setup monitoring components
python setup_monitoring.py setup

# Start the monitoring stack
python setup_monitoring.py start

# Or run in foreground for debugging
python setup_monitoring.py start --attached
```

### Access URLs

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200

## 📊 Dashboards

### Application Overview Dashboard

**URL**: http://localhost:3000/d/noleet-overview

**Metrics Included:**
- HTTP request rate and latency (95th, 99th percentiles)
- Error rates (4xx, 5xx)
- LLM operations (requests, tokens, costs)
- Cache performance (hit rates, operations)
- Agent interactions
- System resources (CPU, memory, disk)

### LLM Performance Dashboard

**URL**: http://localhost:3000/d/noleet-llm-performance

**Metrics Included:**
- Request rates by provider (OpenAI, Ollama, Together, Gemini)
- Response times by provider and model
- Token usage and costs
- Cache performance for LLM operations
- Provider availability status
- Model usage distribution

## 📈 Metrics Collection

### Application Metrics

The application exposes Prometheus metrics at `/metrics` endpoint:

```bash
# Application metrics
curl http://localhost:8000/metrics

# LLM service metrics
curl http://localhost:8001/metrics

# Agent service metrics
curl http://localhost:8002/metrics

# Cache service metrics
curl http://localhost:8003/metrics
```

### Available Metrics

#### HTTP Metrics
- `noleet_http_requests_total{method, endpoint, status}`
- `noleet_http_request_duration_seconds{method, endpoint, status}`

#### LLM Metrics
- `noleet_llm_requests_total{provider, model, operation}`
- `noleet_llm_request_duration_seconds{provider, model, operation}`
- `noleet_llm_tokens_used_total{provider, model, token_type}`
- `noleet_llm_cost_usd_total{provider, model}`

#### Cache Metrics
- `noleet_cache_operations_total{cache_name, operation, result}`
- `noleet_cache_hit_rate_percent{cache_name}`
- `noleet_cache_size_items{cache_name}`
- `noleet_cache_memory_usage_bytes{cache_name}`

#### Agent Metrics
- `noleet_agent_requests_total{agent_name, agent_type, request_type}`
- `noleet_agent_completions_total{agent_name, agent_type, outcome}`
- `noleet_agent_active_requests{agent_name}`

#### Business Metrics
- `noleet_user_sessions_total{user_type, device_type}`
- `noleet_recommendations_served_total{recommendation_type, algorithm}`
- `noleet_projects_created_total{project_type, user_type}`

## 🚨 Alerting

### Configured Alerts

#### Critical Alerts
- **High Error Rate**: >5% error rate over 5 minutes
- **High Latency**: 95th percentile >2s over 5 minutes
- **Service Down**: LLM/Agent services unavailable
- **Low Disk Space**: <10% disk space available

#### Warning Alerts
- **Low Cache Hit Rate**: <70% hit rate over 10 minutes
- **High Resource Usage**: CPU >80%, Memory >85%
- **Performance Regression**: Detected performance degradation

#### Info Alerts
- **Low User Engagement**: Below normal activity levels

### Alert Routing

Alerts are routed based on severity:
- **Critical**: Slack #noleet-critical + email
- **Warning**: Slack #noleet-warnings
- **Info**: Slack #noleet-general

### Alertmanager Configuration

Alerts can be configured in `prometheus/alertmanager.yml`:
- Email notifications (SMTP)
- Slack webhooks
- PagerDuty integration
- Custom routing rules

## 📋 Logging

### Log Collection

Application logs are collected via:

1. **HTTP Endpoint**: POST logs to Logstash at `localhost:8080`
2. **File Monitoring**: Monitor log files in `/var/log/noleet/`
3. **TCP Socket**: Send logs to `localhost:5000`

### Log Processing

Logstash pipeline processes logs with:
- JSON parsing and field extraction
- GeoIP enrichment for IP addresses
- User agent parsing
- Error categorization
- Sensitive data removal

### Log Storage

Logs are indexed in Elasticsearch with:
- Daily indices: `noleet-YYYY.MM.dd`
- Error logs: `noleet-errors-YYYY.MM.dd`
- Performance logs: `noleet-performance-YYYY.MM.dd`
- LLM logs: `noleet-llm-YYYY.MM.dd`

### Log Visualization

Use Kibana to explore logs:
- **Discover**: Search and filter logs
- **Visualize**: Create charts and graphs
- **Dashboard**: Build custom dashboards

## 🔧 Configuration

### Environment Variables

```bash
# Prometheus
PROMETHEUS_RETENTION=200h
PROMETHEUS_STORAGE_PATH=/prometheus

# Grafana
GF_SECURITY_ADMIN_PASSWORD=your-secure-password
GF_USERS_ALLOW_SIGN_UP=false

# Elasticsearch
ES_JAVA_OPTS=-Xms512m -Xmx512m
xpack.security.enabled=false

# Redis (for caching)
REDIS_PASSWORD=your-redis-password
```

### Scaling Configuration

For production deployment:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  prometheus:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  elasticsearch:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

## 📊 Custom Metrics

### Adding Application Metrics

```python
from monitoring.metrics import metrics_collector

# Record HTTP request
metrics_collector.record_http_request(
    method="POST",
    endpoint="/api/recommend",
    status=200,
    duration=0.145
)

# Record business event
from monitoring.metrics.business_metrics import business_metrics

business_metrics.record_recommendation_served(
    recommendation_type="project",
    algorithm="semantic_matching"
)
```

### Custom Dashboards

Create custom dashboards in Grafana:

1. **Import Dashboard**: Use JSON files in `grafana/dashboards/`
2. **Data Source**: Use Prometheus as data source
3. **Queries**: Use PromQL for metrics queries
4. **Variables**: Add dashboard variables for filtering

## 🐳 Docker Integration

### Application Integration

Add metrics endpoint to your application:

```python
from monitoring.metrics.exporter import create_metrics_endpoint
from monitoring.metrics.middleware import MetricsMiddleware

# FastAPI example
app = FastAPI()
app.add_middleware(MetricsMiddleware().create_fastapi_middleware())
app.add_route("/metrics", create_metrics_endpoint())
```

### Health Checks

```python
from monitoring.metrics.exporter import create_health_endpoint

app.add_route("/health", create_health_endpoint())
app.add_route("/ready", create_readiness_endpoint())
```

## 🔍 Troubleshooting

### Common Issues

**Grafana not accessible:**
```bash
# Check if container is running
docker ps | grep grafana

# Check logs
docker logs noleet-grafana
```

**Metrics not appearing:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check application metrics endpoint
curl http://localhost:8000/metrics
```

**Logs not appearing in Kibana:**
```bash
# Check Logstash pipeline
curl http://localhost:9600/_node/stats

# Check Elasticsearch indices
curl http://localhost:9200/_cat/indices
```

### Performance Tuning

**Prometheus:**
- Increase `storage.tsdb.retention.time` for longer data retention
- Adjust `scrape_interval` based on metric volume

**Elasticsearch:**
- Increase heap size: `ES_JAVA_OPTS=-Xms2g -Xmx2g`
- Configure index templates for optimal mapping

**Grafana:**
- Enable query caching
- Use dashboard variables to reduce query load

## 📚 API Reference

### Metrics Endpoints

- `GET /metrics`: Prometheus metrics
- `GET /health`: Application health
- `GET /ready`: Application readiness

### Alertmanager API

- `GET /api/v2/alerts`: Current alerts
- `POST /api/v2/alerts`: Create alert

### Elasticsearch API

- `GET /_cat/indices`: List indices
- `POST /_search`: Search logs
- `POST /_bulk`: Bulk operations

## 🤝 Contributing

### Adding New Metrics

1. Define metric in appropriate collector
2. Update Prometheus configuration if needed
3. Add to Grafana dashboards
4. Update documentation

### Adding New Alerts

1. Define alert in `prometheus/alert_rules.yml`
2. Configure routing in `alertmanager.yml`
3. Test alert conditions
4. Update runbooks

### Custom Dashboards

1. Create dashboard JSON in `grafana/dashboards/`
2. Test queries in Prometheus
3. Add to provisioning configuration
4. Document dashboard usage

---

## 📞 Support

For monitoring setup issues:
1. Check container logs: `docker logs <container_name>`
2. Verify configuration files
3. Check network connectivity between services
4. Review Prometheus targets and alerting rules

For application integration:
1. Ensure metrics middleware is properly configured
2. Verify metric names match Prometheus queries
3. Check log format matches Logstash pipeline
4. Validate alert thresholds and routing
