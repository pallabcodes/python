# YAML Pipeline Configuration

A secure, declarative pipeline configuration system using YAML with safe dynamic loading, validation, and environment variable substitution.

## Overview

This mini-project extends the pipeline core framework with YAML-based configuration, providing:

- **Declarative configuration** using YAML syntax
- **Safe dynamic loading** with module and path restrictions
- **Configuration validation** with comprehensive error checking
- **Environment variable substitution** for dynamic values
- **Configuration management** with caching and discovery

## Key Concepts Demonstrated

### 1. Declarative Configuration
- **YAML-based pipeline definition** with human-readable syntax
- **Structured configuration schema** with validation
- **Versioned configurations** for pipeline evolution
- **Metadata and documentation** support

### 2. Safe Dynamic Loading
- **Module security restrictions** to prevent arbitrary code execution
- **Path-based access control** for configuration files
- **Built-in stage registry** for trusted components
- **Instantiation validation** before pipeline execution

### 3. Configuration Validation
- **Schema validation** with detailed error messages
- **Cross-reference checking** between stages and queues
- **Type safety** for configuration parameters
- **Duplicate detection** and naming validation

### 4. Environment Integration
- **Environment variable substitution** in configuration files
- **Secure env var access** with allowlist restrictions
- **Dynamic configuration** based on runtime environment
- **Configuration templating** for different deployments

## Files Structure

```
pipeline_yaml/
├── __init__.py              # Module documentation
├── config_schema.py         # Configuration schema and validation
├── safe_loader.py           # Secure dynamic stage loading
├── pipeline_builder.py      # YAML-driven pipeline builder
├── config_loader_core.py    # Core configuration loading classes
├── config_loader_security.py # Security features for config loading
├── demo_yaml_basic.py       # Basic YAML configuration demonstrations
├── test_yaml_basic.py       # Basic unit tests
├── test_yaml_advanced.py    # Advanced unit tests
└── README.md               # This documentation
```

## Usage Examples

### Basic YAML Pipeline Configuration

Create a `pipeline_config.yaml` file:

```yaml
name: "data_processing_pipeline"
version: "1.0.0"
description: "A complete data processing pipeline"

stages:
  - name: "data_validator"
    type: "filter"
    module: "myapp.stages"
    class_name: "DataValidator"
    parameters:
      required_fields: ["id", "data"]

  - name: "data_transformer"
    type: "transform"
    module: "myapp.stages"
    class_name: "DataTransformer"
    parameters:
      transformation: "normalize"

  - name: "result_sink"
    type: "sink"
    module: "myapp.stages"
    class_name: "DatabaseSink"
    parameters:
      table: "processed_data"

queues:
  - name: "validator-transformer"
    type: "memory"
    maxsize: 1000

  - name: "transformer-sink"
    type: "memory"
    maxsize: 500

global_settings:
  max_workers: 4
  timeout: 300
```

### Building Pipeline from YAML

```python
from pipeline_yaml import build_pipeline_from_file

# Build pipeline from configuration file
runner = build_pipeline_from_file("pipeline_config.yaml")

# Run with input data
from pipeline_core import create_data_message
input_messages = [create_data_message(item) for item in data_items]
results = runner.run_pipeline(input_messages)
```

### Secure Configuration Loading

```python
from pipeline_yaml import create_config_manager

# Create secure configuration manager
manager = create_config_manager(
    config_dirs=["/etc/pipelines", "./configs"],
    allowed_modules=["myapp.stages", "pipeline_core"]
)

# Load and build pipeline
config = manager.load_config("data_processing")
builder = YamlPipelineBuilder(allowed_modules=["myapp.stages"])
runner = builder.build_pipeline(config)
```

## Configuration Schema

### Pipeline Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Pipeline identifier |
| `version` | string | Yes | Configuration version |
| `description` | string | No | Human-readable description |
| `stages` | array | Yes | List of pipeline stages |
| `queues` | array | No | Inter-stage queue definitions |
| `global_settings` | object | No | Global pipeline settings |

### Stage Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Stage identifier |
| `type` | string | Yes | Stage type (transform/filter/sink/custom) |
| `module` | string | Yes | Python module containing stage class |
| `class_name` | string | Yes | Stage class name |
| `parameters` | object | No | Stage initialization parameters |
| `input_queue` | string | No | Input queue name |
| `output_queues` | array | No | Output queue names |

### Queue Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Queue identifier |
| `type` | string | Yes | Queue type (memory only currently) |
| `maxsize` | integer | No | Maximum queue size (0 = unbounded) |
| `parameters` | object | No | Queue-specific parameters |

## Security Features

### Module Restrictions

```python
# Only allow specific modules
builder = YamlPipelineBuilder(
    allowed_modules=["myapp.stages", "pipeline_core.stage_types"]
)
```

### Path Restrictions

```python
# Only load configs from trusted directories
loader = SecureConfigLoader(
    allowed_paths=["/etc/pipelines", "/home/user/configs"]
)
```

### Environment Variable Control

```python
# Only allow specific environment variables
loader = SecureConfigLoader(
    allowed_env_vars=["PIPELINE_", "APP_"]
)
```

## Environment Variable Substitution

### Basic Substitution

```yaml
global_settings:
  max_workers: ${PIPELINE_WORKERS}
  database_url: ${DATABASE_URL}
```

### Conditional Configuration

```yaml
stages:
  - name: "prod_validator"
    type: "filter"
    module: "myapp.stages"
    class_name: "StrictValidator"
    parameters:
      environment: ${ENVIRONMENT}  # "prod" or "dev"
```

## Running the Examples

### Demonstrations
```bash
cd examples/patterns/pipeline_yaml

# Basic YAML pipeline demo
python demo_yaml_basic.py

# Demonstrates:
# - Simple YAML configuration
# - File-based loading
# - Configuration manager
```

### Tests
```bash
cd examples/patterns/pipeline_yaml

# Run all tests
python -m pytest test_yaml_*.py -v

# Test specific components
python -m pytest test_yaml_basic.py::TestConfigSchema -v
python -m pytest test_yaml_advanced.py::TestSecureConfigLoader -v
```

## Advanced Usage Patterns

### Configuration Inheritance

```python
# Base configuration
base_config = {
    "name": "base_pipeline",
    "stages": [
        # Common stages
    ]
}

# Environment-specific overrides
prod_config = {**base_config, "global_settings": {"max_workers": 10}}
dev_config = {**base_config, "global_settings": {"max_workers": 2}}
```

### Dynamic Stage Loading

```python
# Load stages based on configuration
def load_stages_from_config(config):
    stages = []
    for stage_config in config.stages:
        stage_class = safe_load_stage(stage_config)
        stage = stage_class(**stage_config.parameters)
        stages.append(stage)
    return stages
```

### Configuration Validation

```python
from pipeline_yaml import validate_pipeline_config

def validate_and_build(config_dict):
    # Validate configuration
    config = validate_pipeline_config(config_dict)

    # Additional custom validation
    validate_custom_rules(config)

    # Build pipeline
    return build_pipeline_from_config(config)
```

## Production Considerations

### Configuration Management
- **Version control** all pipeline configurations
- **Configuration testing** with unit tests
- **Environment separation** (dev/staging/prod configs)
- **Configuration audit** logs for changes

### Security Best Practices
- **Minimal module permissions** - only allow necessary modules
- **Path restrictions** - limit configuration file locations
- **Environment variable validation** - restrict env var access
- **Configuration signing** - verify config file integrity

### Performance Optimization
- **Configuration caching** - cache parsed configurations
- **Lazy loading** - load stages only when needed
- **Connection pooling** - reuse database connections
- **Resource limits** - set memory and thread limits

## Error Handling Patterns

### Configuration Errors

```python
try:
    config = load_pipeline_config("pipeline.yaml")
    runner = build_pipeline_from_config(config)
except ConfigValidationError as e:
    logger.error(f"Configuration invalid: {e}")
    # Send alert, use fallback config
except StageLoadError as e:
    logger.error(f"Stage loading failed: {e}")
    # Try alternative stage or skip
```

### Runtime Errors

```python
try:
    results = runner.run_pipeline(messages, timeout=300)
    if not results["success"]:
        logger.warning(f"Pipeline failed: {results['error']}")
        # Handle partial failures, retry logic
except Exception as e:
    logger.critical(f"Pipeline execution failed: {e}")
    # Emergency shutdown, cleanup
```

## Integration with Pipeline Core

### Extending Core Stages

```python
# Custom stage extending core functionality
from pipeline_core.stage_types import TransformStage

class CustomTransformer(TransformStage):
    def transform(self, data):
        # Custom transformation logic
        return process_data(data)
```

### Queue Integration

```python
# Custom queue implementation
from pipeline_core.queue import MessageQueue

class RedisMessageQueue(MessageQueue):
    def __init__(self, redis_client, key):
        self.redis = redis_client
        self.key = key

    def put(self, message, timeout=None):
        # Redis implementation
        pass

    def get(self, timeout=None):
        # Redis implementation
        pass
```

## Debuggability Assessment

✅ **5-20 minute rule compliance**:
- Structured configuration validation with detailed errors
- Safe loading with security logging and audit trails
- Environment variable substitution with validation
- Pipeline building with step-by-step error reporting
- Configuration manager with caching and discovery
- Comprehensive unit tests covering all components

## Next Steps

This YAML configuration system enables:

1. **HTTP Fetcher**: Web scraping stage with rate limiting
2. **HTML Parser**: Content extraction and processing
3. **Datastore Writer**: Database/storage integration
4. **Observability**: Monitoring and metrics collection
5. **Resilience**: Circuit breakers and retry logic
6. **Finance Pipeline**: Complete financial data processing system

## Comparison with Manual Pipeline Creation

| Aspect | Manual Creation | YAML Configuration |
|--------|----------------|-------------------|
| **Maintainability** | ❌ Error-prone | ✅ Declarative |
| **Reusability** | ❌ Code duplication | ✅ Configuration reuse |
| **Testing** | ❌ Integration only | ✅ Config validation |
| **Security** | ❌ Arbitrary code | ✅ Safe loading |
| **Versioning** | ❌ Manual tracking | ✅ Version control |
| **Documentation** | ❌ Inline comments | ✅ Self-documenting |

This YAML configuration system transforms pipeline development from imperative code to declarative configuration, enabling secure, maintainable, and scalable data processing workflows that meet enterprise production standards.

