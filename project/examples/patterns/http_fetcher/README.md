# HTTP Fetcher Pipeline Stage

A production-ready HTTP client pipeline stage with rate limiting, retry logic, and comprehensive error handling for reliable web data fetching.

## Overview

This mini-project implements an HTTP fetcher pipeline stage that provides:

- **Rate Limiting**: Multiple algorithms (token bucket, fixed window) with configurable limits
- **Retry Logic**: Exponential backoff with jitter and intelligent error classification
- **Error Handling**: Comprehensive exception handling with detailed error reporting
- **Batch Processing**: Concurrent request handling with concurrency control
- **Pipeline Integration**: Seamless integration with the pipeline framework

## Key Concepts Demonstrated

### 1. Rate Limiting Algorithms
- **Token Bucket**: Smooth rate limiting with burst capacity
- **Fixed Window**: Simple time-window based limiting
- **Sliding Window**: Advanced time-window with rolling calculations
- **Configurable Parameters**: Requests per second, burst size, window duration

### 2. Retry Strategies
- **Exponential Backoff**: Progressive delay increases
- **Jitter**: Random delay variation to prevent thundering herd
- **Error Classification**: Intelligent retry based on error types (5xx, 429, network errors)
- **Configurable Conditions**: Selective retry for specific error conditions

### 3. HTTP Client Architecture
- **Dual Implementation**: Requests library with urllib fallback
- **Response Processing**: Automatic content type detection and parsing
- **Header Management**: Custom headers with defaults and overrides
- **Timeout Handling**: Configurable timeouts with proper cleanup

### 4. Pipeline Stage Patterns
- **Transform Stage**: Input to output data transformation
- **Batch Processing**: Concurrent request handling
- **Error Propagation**: Structured error reporting through pipeline
- **Statistics Collection**: Performance and success metrics

## Files Structure

```
http_fetcher/
├── __init__.py              # Module documentation
├── rate_limiter.py          # Rate limiting algorithms and implementations
├── retry_logic.py           # Retry strategies and error classification
├── http_client_core.py      # HTTP client core classes and interfaces
├── http_client_requests.py  # Requests library implementation
├── http_client_urllib.py    # urllib fallback implementation
├── fetcher_stage_batch.py   # Batch HTTP fetcher stage
├── fetcher_stage_utils.py   # HTTP fetcher utility functions
├── demo_basic.py            # Basic HTTP fetching demonstrations
├── demo_advanced.py         # Advanced demonstrations
├── test_basic.py            # Basic unit tests
├── test_advanced_stage.py   # Advanced stage tests
├── test_advanced_integration.py # Integration tests
└── README.md               # This documentation
```

## Usage Examples

### Basic HTTP Fetching

```python
from http_fetcher import HttpFetcherStage
from pipeline_core import PipelineRunner, create_data_message

# Create fetcher stage
fetcher = HttpFetcherStage(
    name="APIFetcher",
    requests_per_second=10.0,  # Rate limit
    max_retries=3              # Retry failed requests
)

# Create pipeline
pipeline = PipelineRunner([fetcher])

# Fetch data
requests = [
    {"url": "https://api.example.com/data/1", "method": "GET"},
    {"url": "https://api.example.com/data/2", "method": "GET"}
]

input_messages = [create_data_message(req) for req in requests]
results = pipeline.run_pipeline(input_messages)
```

### Batch Processing

```python
from http_fetcher import BatchHttpFetcherStage

# Create batch fetcher
batch_fetcher = BatchHttpFetcherStage(
    name="BatchFetcher",
    max_concurrent=5,          # Max concurrent requests
    requests_per_second=20.0,  # Overall rate limit
    max_retries=2
)

# Process batch of requests
batch_requests = [
    {"url": "https://api.example.com/items/1"},
    {"url": "https://api.example.com/items/2"},
    # ... more requests
]

result = batch_fetcher.transform(batch_requests)
# Returns list of responses
```

### Advanced Configuration

```python
from http_fetcher import create_http_client
from rate_limiter import create_rate_limiter
from retry_logic import create_retry_handler

# Custom rate limiter (token bucket with burst)
rate_limiter = create_rate_limiter(
    algorithm="token_bucket",
    requests_per_second=15.0,
    burst_size=30  # Allow bursts up to 30 requests
)

# Custom retry handler
retry_handler = create_retry_handler(
    max_attempts=5,
    strategy="exponential_backoff",
    base_delay=1.0,
    max_delay=30.0,
    jitter=True
)

# Create HTTP client
http_client = HttpClient(
    rate_limiter=rate_limiter,
    retry_handler=retry_handler,
    timeout=45.0,
    user_agent="MyApp/1.0"
)

# Use in custom stage
response = http_client.get("https://api.example.com/data")
```

## Configuration Options

### Rate Limiting

| Algorithm | Description | Parameters |
|-----------|-------------|------------|
| `token_bucket` | Smooth limiting with burst capacity | `requests_per_second`, `burst_size` |
| `fixed_window` | Time-window based limiting | `requests_per_second`, `window_size_seconds` |
| `sliding_window` | Rolling time-window | `requests_per_second`, `window_size_seconds` |

### Retry Strategies

| Strategy | Description | Behavior |
|----------|-------------|----------|
| `fixed` | Constant delay | Same delay for each retry |
| `linear_backoff` | Linear increase | Delay = base_delay * attempt |
| `exponential_backoff` | Exponential growth | Delay = base_delay * 2^(attempt-1) |

### Retry Conditions

- `HTTP_5XX`: Server errors (500-599)
- `HTTP_429`: Rate limiting responses
- `CONNECTION_ERROR`: Network connection failures
- `TIMEOUT`: Request timeouts
- `NETWORK_ERROR`: DNS, SSL, socket errors

## Running the Examples

### Demonstrations
```bash
cd examples/patterns/http_fetcher

# Basic HTTP fetching demo
python demo_basic.py

# Advanced demonstrations
python demo_advanced.py

# Demonstrates:
# - Basic HTTP requests with rate limiting
# - Batch processing with concurrency control
# - Error handling and retry logic
# - Rate limiting behavior
# - Custom headers and authentication
```

### Tests
```bash
cd examples/patterns/http_fetcher

# Run all tests
python -m pytest test_*.py -v

# Test specific components
python -m pytest test_basic.py::TestRateLimiter -v
python -m pytest test_basic.py::TestRetryLogic -v
python -m pytest test_advanced_stage.py::TestHttpFetcherStageAdvanced -v
```

## Production Considerations

### Rate Limiting Best Practices
- **Start Conservative**: Begin with lower limits and increase based on API capacity
- **Monitor Usage**: Track rate limiter statistics and adjust limits dynamically
- **Respect API Limits**: Never exceed documented API rate limits
- **Burst Handling**: Use token bucket for APIs that allow occasional bursts

### Retry Logic Guidelines
- **Exponential Backoff**: Prevents overwhelming failing services
- **Jitter**: Avoids synchronized retry storms across multiple clients
- **Error Classification**: Only retry recoverable errors, not client errors (4xx except 429)
- **Circuit Breakers**: Consider implementing circuit breaker pattern for persistent failures

### Error Handling Patterns
```python
# In pipeline processing
def process_response(self, data):
    if isinstance(data, dict) and data.get("error"):
        # Handle fetch errors
        self._logger.error(f"Fetch failed: {data['error_message']}")
        return self._handle_fetch_error(data)

    # Process successful responses
    return self._process_successful_response(data)
```

### Monitoring and Observability
```python
# Track fetcher performance
stats = fetcher.get_stats()
metrics.gauge("http_requests_total", stats["requests_made"])
metrics.gauge("http_requests_success", stats["requests_successful"])
metrics.gauge("http_requests_failed", stats["requests_failed"])
metrics.gauge("http_success_rate", stats["success_rate"])
```

## Performance Characteristics

### Rate Limiting Overhead
- **Token Bucket**: Minimal CPU overhead, O(1) operations
- **Fixed Window**: Low memory usage, simple calculations
- **Thread Safety**: All limiters are thread-safe for concurrent use

### Retry Logic Impact
- **Memory**: Minimal additional memory for retry state
- **Latency**: Retry delays add to total request time
- **Throughput**: Failed requests reduce effective throughput
- **Backoff**: Exponential backoff prevents retry storms

### HTTP Client Performance
- **Connection Reuse**: Session-based connection pooling when available
- **Concurrent Requests**: Batch processing with configurable concurrency
- **Timeout Handling**: Proper cleanup on timeouts and cancellations
- **Memory Management**: Streaming responses for large content

## Debuggability Assessment

✅ **5-20 minute rule compliance**:
- Structured logging with request IDs and timing information
- Rate limiter statistics with current state and limits
- Retry attempt logging with attempt numbers and delays
- HTTP response metadata with status codes and headers
- Error context with stack traces and request details
- Pipeline integration with correlation through message passing

## Integration with Pipeline Framework

### YAML Configuration
```yaml
name: "web_scraper_pipeline"
version: "1.0.0"

stages:
  - name: "url_fetcher"
    type: "custom"
    module: "http_fetcher.fetcher_stage"
    class_name: "HttpFetcherStage"
    parameters:
      requests_per_second: 10.0
      max_retries: 3
      base_url: "https://api.example.com"

  - name: "content_processor"
    type: "transform"
    module: "myapp.processors"
    class_name: "ContentProcessor"
    parameters: {}

queues:
  - name: "fetch-process"
    type: "memory"
    maxsize: 100

global_settings:
  max_workers: 4
```

### Error Recovery Patterns
```python
class ResilientPipeline:
    def __init__(self):
        self.fetcher = HttpFetcherStage(
            name="ResilientFetcher",
            requests_per_second=5.0,
            max_retries=5
        )
        self.dead_letter_queue = []  # Store failed requests

    def process_with_recovery(self, requests):
        results = []
        for request in requests:
            try:
                result = self.fetcher.transform(request)
                if isinstance(result, dict) and result.get("error"):
                    # Store for later retry
                    self.dead_letter_queue.append(request)
                    results.append(self._create_error_result(result))
                else:
                    results.append(result)
            except Exception as e:
                self.dead_letter_queue.append(request)
                results.append({"error": str(e), "request": request})

        return results
```

## Security Considerations

### Header Injection Prevention
- **Header Validation**: Sanitize custom headers to prevent injection
- **Authorization Security**: Secure storage of API keys and tokens
- **URL Validation**: Validate and sanitize URLs to prevent SSRF attacks

### Rate Limiting Security
- **DoS Protection**: Rate limiting prevents abuse and DoS attacks
- **Resource Exhaustion**: Prevents overwhelming downstream services
- **Fair Usage**: Ensures equitable access to rate-limited resources

### Error Information Leakage
- **Sensitive Data**: Avoid logging sensitive information in errors
- **Stack Trace Filtering**: Filter sensitive information from error messages
- **Response Sanitization**: Remove sensitive data from logged responses

This HTTP fetcher implementation provides enterprise-grade web data fetching capabilities with comprehensive reliability, performance, and security features suitable for production pipeline systems. The modular design enables easy customization and extension for specific use cases while maintaining clean separation of concerns and robust error handling.

