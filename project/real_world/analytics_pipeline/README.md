# Real-Time Multi-Source Analytics Pipeline

A production-ready, enterprise-grade analytics pipeline for processing real-time data from multiple sources including RSS feeds, REST APIs, and log files. Built with Google SDE-3 standards and designed for high-performance, scalable data processing.

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/github/actions/workflow/status/your-org/analytics-pipeline/ci-cd.yml/badge.svg)](https://github.com/your-org/analytics-pipeline/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)]()

## 🚀 Features

### Core Capabilities
- **Real-time Data Ingestion**: RSS feeds, REST APIs, log file tailing
- **Advanced Processing**: Enrichment, transformation, aggregation, quality validation
- **Multi-Backend Storage**: SQLite, PostgreSQL, JSON files, Redis cache
- **Data Export**: CSV, JSON, Parquet formats with compression
- **REST API**: Complete programmatic access with FastAPI
- **Real-time Dashboard**: Live metrics with Grafana integration
- **Pipeline Orchestration**: Complete lifecycle management

### Enterprise Features
- **High Performance**: Async processing with connection pooling
- **Fault Tolerance**: Circuit breakers, retries, graceful degradation
- **Monitoring**: Prometheus metrics, health checks, alerting
- **Scalability**: Docker containerization, horizontal scaling
- **Security**: Authentication, authorization, input validation
- **CI/CD**: GitHub Actions, automated testing and deployment
- **Observability**: Structured logging, tracing, performance monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Processing      │───▶│   Storage       │
│                 │    │  Stages          │    │   Backends      │
│ • RSS Feeds     │    │                  │    │                 │
│ • REST APIs     │    │ • Enrichment     │    │ • SQLite        │
│ • Log Files     │    │ • Transformation │    │ • JSON Files    │
│                 │    │ • Aggregation    │    │ • Cache         │
└─────────────────┘    │ • Quality Check  │    └─────────────────┘
                       └──────────────────┘             │
┌─────────────────┐    ┌──────────────────┐             ▼
│   Orchestrator  │◀──▶│   Output         │    ┌─────────────────┐
│   & Control     │    │   Interfaces     │    │   Export &      │
│                 │    │                  │    │   Visualization │
│ • Pipeline Mgmt │    │ • REST API       │    │                 │
│ • Auto-scaling  │    │ • Dashboard      │    │ • CSV/JSON      │
│ • Circuit Brkrs │    │ • Metrics        │    │ • Parquet       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/your-org/analytics-pipeline.git
cd analytics-pipeline

# Install dependencies
pip install -r requirements.txt

# Run with demo configuration
python scripts/run_pipeline.py --demo

# Access interfaces
open http://localhost:8000  # Dashboard & API
open http://localhost:8000/docs  # API Documentation
```

### Docker Deployment
```bash
# Quick start with Docker Compose
docker-compose up -d

# Access services
open http://localhost:8000  # Application
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
```

### Production Deployment
```bash
# Deploy to production
./scripts/deploy/deploy.sh production

# Or use Docker Compose for production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📋 Requirements

### System Requirements
- **Python**: 3.11+ (recommended)
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+ (for multi-service deployment)
- **Memory**: 2GB minimum, 4GB recommended
- **Storage**: 5GB minimum for data and logs

### Python Dependencies
```bash
pip install -r requirements.txt
```

### Docker Setup (Recommended)
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🚀 Quick Start

### 1. Basic Pipeline Setup

```python
from analytics_pipeline.output import PipelineOrchestrator, PipelineConfig

# Create pipeline configuration
config = PipelineConfig(
    name="My Analytics Pipeline",
    enable_dashboard=True,
    enable_monitoring=True
)

# Initialize and start pipeline
orchestrator = PipelineOrchestrator(config)
orchestrator.start()

print("Pipeline started successfully!")
```

### 2. Using Demo Sources

```python
from analytics_pipeline.sources import create_demo_sources

# Create demo data sources
sources = create_demo_sources()

# Sources include:
# - RSS feeds (BBC, CNN, NPR)
# - Mock API endpoints
# - Sample log files

for name, source in sources.items():
    print(f"Created source: {name}")
```

### 3. Export Data

```python
from analytics_pipeline.output import ExportManager

# Create export manager
exporter = ExportManager()

# Export data to CSV
metrics = exporter.export_from_storage(
    storage_backend=orchestrator.storage_backends['default'],
    collection='messages',
    format_type='csv',
    output_path='data/export.csv'
)

print(f"Exported {metrics.records_exported} records")
```

## 🔧 Configuration

### Pipeline Configuration

```python
from analytics_pipeline.output import PipelineConfig

config = PipelineConfig(
    name="Production Pipeline",
    max_workers=20,
    batch_size=500,
    processing_timeout=60.0,
    enable_monitoring=True,
    enable_dashboard=True,

    # Storage backends
    storage_backends={
        'primary': {
            'backend_type': 'sqlite',
            'connection_string': 'sqlite:///data/pipeline.db'
        },
        'cache': {
            'backend_type': 'cache',
            'connection_string': 'cache://memory',
            'max_size': 10000
        }
    },

    # Processing stages
    processing_stages=[
        {
            'type': 'enrichment',
            'name': 'data_enrichment',
            'config': {'add_timestamps': True, 'add_message_hash': True}
        },
        {
            'type': 'quality',
            'name': 'data_quality',
            'config': {'required_fields': ['timestamp', 'source']}
        }
    ]
)
```

### Source Configuration

```python
# RSS Feed Source
rss_config = {
    'name': 'news_feeds',
    'feed_urls': [
        'https://feeds.bbci.co.uk/news/rss.xml',
        'https://rss.cnn.com/rss/edition.rss.xml'
    ],
    'feed_names': ['bbc_news', 'cnn_news'],
    'poll_interval': 300,  # 5 minutes
    'max_entries': 50
}

# API Source
api_config = {
    'name': 'weather_api',
    'endpoints': [
        {
            'name': 'current_weather',
            'url': 'https://api.weatherapi.com/v1/current.json',
            'method': 'GET',
            'auth_type': 'api_key',
            'auth_config': {'param_name': 'key', 'api_key': 'your_api_key'}
        }
    ]
}

# Log File Source
log_config = {
    'name': 'app_logs',
    'files': [
        {
            'path': '/var/log/application.log',
            'name': 'app_log',
            'pattern': r'ERROR|WARN|INFO'
        }
    ]
}
```

## 📊 REST API

The pipeline provides a complete REST API for data access and monitoring.

### Base URL
```
http://localhost:8000/api/v1
```

### Health & Status Endpoints

```bash
# System health
GET /health

# Pipeline status
GET /status

# Stage metrics
GET /metrics
GET /metrics/{stage_name}

# Storage metrics
GET /storage/metrics
GET /storage/metrics/{backend_name}
```

### Data Access Endpoints

```bash
# Query data
GET /data/{backend}/{collection}?filters=[...]&limit=100&offset=0

# Get specific record
GET /data/{backend}/{collection}/{record_id}

# List collections
GET /collections/{backend}

# Collection statistics
GET /collections/{backend}/{collection}/stats
```

### Example API Usage

```python
import requests

# Get pipeline status
response = requests.get('http://localhost:8000/api/v1/status')
status = response.json()

# Query recent messages
params = {
    'filters': '[{"field": "timestamp", "operator": "gt", "value": 1640995200}]',
    'limit': 50
}
response = requests.get('http://localhost:8000/api/v1/data/default/messages', params=params)
messages = response.json()
```

## 📈 Dashboard

The pipeline includes a built-in dashboard for real-time monitoring.

### Accessing the Dashboard

```python
from analytics_pipeline.output import DashboardInterface

# Get dashboard HTML
dashboard = DashboardInterface(orchestrator.dashboard)
html_content = dashboard.get_html_dashboard()

# Or get JSON data
json_data = dashboard.get_json_dashboard()
```

### Dashboard Features

- **Real-time Metrics**: Pipeline throughput, error rates, stage performance
- **Health Monitoring**: System status, component health checks
- **Alert System**: Configurable alerts with severity levels
- **Historical Data**: Time-series metrics with configurable retention
- **Interactive Charts**: Visual representation of key metrics

### Custom Alerts

```python
from analytics_pipeline.output import Alert

# Create custom alert
high_error_alert = Alert(
    name='high_error_rate',
    condition=lambda m: m.get('error_rate', 0) > 0.05,
    message='Error rate exceeds 5%',
    severity='warning'
)

dashboard.add_alert(high_error_alert)
```

## 📤 Data Export

### Export Formats

The pipeline supports multiple export formats:

```python
from analytics_pipeline.output import ExportManager

exporter = ExportManager()

# CSV Export
exporter.export_from_storage(
    storage_backend,
    collection='messages',
    format_type='csv',
    output_path='exports/messages.csv',
    filters=[{'field': 'timestamp', 'operator': 'gt', 'value': yesterday}]
)

# JSON Export
exporter.export_from_storage(
    storage_backend,
    collection='metrics',
    format_type='json',
    output_path='exports/metrics.json.gz',
    compression='gzip'
)

# Parquet Export (requires pandas, pyarrow)
exporter.export_from_storage(
    storage_backend,
    collection='analytics',
    format_type='parquet',
    output_path='exports/analytics.parquet',
    compression='snappy'
)
```

## 🛠️ Development

### Project Structure

```
analytics_pipeline/
├── core/                 # Core pipeline components
│   ├── orchestrator_*.py # Pipeline orchestration
│   ├── router_*.py      # Message routing
│   ├── autoscaler_*.py  # Auto-scaling logic
│   └── circuit_breaker_*.py # Fault tolerance
├── sources/             # Data source implementations
│   ├── rss_feed_*.py    # RSS feed ingestion
│   ├── api_client_*.py  # API client functionality
│   └── log_file_*.py    # Log file tailing
├── processing/          # Data processing stages
│   ├── enrichment_*.py  # Data enrichment
│   ├── transformation_*.py # Data transformation
│   ├── aggregation_*.py # Real-time aggregation
│   ├── windowing_*.py   # Windowing operations
│   └── quality_*.py     # Data quality validation
├── storage/             # Storage backend implementations
│   ├── sqlite_*.py      # SQLite backend
│   ├── json_*.py        # JSON file backend
│   └── cache_*.py       # In-memory cache backend
└── output/              # Output and integration
    ├── export_*.py      # Data export functionality
    ├── api_*.py         # REST API endpoints
    ├── dashboard_*.py   # Dashboard interface
    └── orchestrator_*.py # Pipeline orchestration
```

### Coding Standards

This project follows Google SDE-3 production standards:

- **File Size**: Maximum 200 lines per file
- **SOLID Principles**: Clean architecture with proper separation of concerns
- **Type Hints**: Complete type annotations throughout
- **Documentation**: Google-style docstrings
- **Error Handling**: Comprehensive exception handling
- **Concurrency**: Thread-safe implementations
- **Testing**: Unit and integration test coverage

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=analytics_pipeline

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/performance/
```

## 🚀 Deployment

### Environment Overview

The pipeline supports multiple deployment environments:

- **Development**: Local development with hot reload
- **Staging**: Pre-production testing environment
- **Production**: Full production deployment with monitoring

### Docker Compose Deployment

#### Development Environment
```bash
# Start development stack
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f analytics-pipeline

# Access services
open http://localhost:8000  # Application
open http://localhost:3000  # Grafana Dashboard
open http://localhost:9090  # Prometheus Metrics
```

#### Production Environment
```bash
# Start production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check health
curl http://localhost/health

# View logs
docker-compose logs -f
```

### Automated Deployment

#### Using Deployment Script
```bash
# Deploy to different environments
./scripts/deploy/deploy.sh development
./scripts/deploy/deploy.sh staging
./scripts/deploy/deploy.sh production

# Check deployment status
docker-compose ps
```

#### CI/CD with GitHub Actions
The pipeline includes automated CI/CD:

- **Code Quality**: Black, isort, mypy, flake8
- **Security**: Bandit security scanning
- **Testing**: Pytest with coverage reporting
- **Docker**: Automated image building and publishing
- **Deployment**: Environment-specific deployments

### Kubernetes Deployment

#### Basic Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-pipeline
  labels:
    app: analytics-pipeline
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analytics-pipeline
  template:
    metadata:
      labels:
        app: analytics-pipeline
    spec:
      containers:
      - name: pipeline
        image: analytics-pipeline:latest
        ports:
        - containerPort: 8000
        env:
        - name: PIPELINE_CONFIG
          value: "/app/config/production.yaml"
        - name: PYTHONPATH
          value: "/app"
        resources:
          limits:
            memory: "1Gi"
            cpu: "500m"
          requests:
            memory: "512Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: data
          mountPath: /data
        - name: config
          mountPath: /app/config
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: analytics-data
      - name: config
        configMap:
          name: analytics-config
---
apiVersion: v1
kind: Service
metadata:
  name: analytics-pipeline
spec:
  selector:
    app: analytics-pipeline
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Production Considerations

- **Monitoring**: Integrate with Prometheus/Grafana for metrics
- **Logging**: Use structured logging with ELK stack
- **Scaling**: Implement horizontal pod autoscaling
- **Security**: Enable authentication and authorization
- **Backup**: Regular data backups and disaster recovery
- **Performance**: Tune connection pools and worker threads

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow the established coding standards
- Add comprehensive tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting PR
- Follow conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Google SDE-3 production standards
- Inspired by modern data pipeline architectures
- Thanks to the open-source community for amazing libraries

## 📞 Support

For questions, issues, or contributions:

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [Full Documentation](https://your-docs-site.com)
- **Community**: [Discussion Forum](https://your-forum.com)

---

**Ready to build powerful analytics pipelines?** 🚀

The Real-Time Multi-Source Analytics Pipeline provides enterprise-grade data processing capabilities with production-ready reliability, monitoring, and scalability. Start building your analytics infrastructure today!
