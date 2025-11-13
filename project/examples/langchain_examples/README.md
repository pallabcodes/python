# LangChain Examples - Production-Grade Implementation

Comprehensive LangChain examples following Google SDE-3 production standards.

## Overview

This project demonstrates LangChain framework capabilities with production-ready code:
- **Core Concepts**: LLMs, Prompts, Output Parsers
- **Chains**: Sequential, Router, Custom Chains
- **Agents**: ReAct, Plan-and-Execute, Custom Agents
- **Memory**: Buffer, Summary, Window Memory
- **Tools**: Custom Tools and Toolkits
- **Retrieval**: RAG, Vector Stores, Document Loaders
- **LangGraph**: Complex Workflow Orchestration
- **Evaluation**: Model Evaluation and Testing
- **Production**: Error Handling, Monitoring, Caching

## Architecture

### Core Concepts (`core_concepts.py`)
- **LLMProvider**: Abstract base for LLM providers
- **OpenAIProvider**: OpenAI integration with error handling
- **PromptManager**: Template management and prompt engineering
- **OutputParserManager**: Structured output parsing
- **LLMService**: High-level service combining all concepts

### Chains (`chains.py`)
- **SimpleLLMChainWrapper**: Single LLM call chains
- **SequentialChainWrapper**: Multi-step workflows
- **RouterChainWrapper**: Dynamic chain routing
- **CustomChain**: Custom chain implementations
- **ChainOrchestrator**: Multi-chain coordination

### Agents (`agents.py`)
- **ReActAgentWrapper**: Reasoning + Acting agents
- **PlanAndExecuteAgentWrapper**: Multi-step planning agents
- **CustomTool**: Custom tool implementations
- **AgentOrchestrator**: Multi-agent coordination

### Memory (`memory.py`)
- **ConversationBufferMemoryWrapper**: Full conversation history
- **ConversationSummaryMemoryWrapper**: Summarized history
- **ConversationBufferWindowMemoryWrapper**: Sliding window
- **MemoryManager**: Multi-memory management

### Tools (`tools.py`)
- **CustomTool**: Custom tool creation
- **ToolRegistry**: Tool registration and management

### Retrieval (`retrieval.py`)
- **RAGPipeline**: Retrieval-Augmented Generation

### LangGraph (`langgraph.py`)
- **WorkflowOrchestrator**: Complex workflow orchestration

### Evaluation (`evaluation.py`)
- **Evaluator**: Model evaluation and testing

### Production (`production.py`)
- **ProductionLLMWrapper**: Enterprise-grade wrapper integrating all advanced patterns
- **ExponentialBackoffRetry**: Sophisticated retry with jitter
- **ProductionMetrics**: Comprehensive metrics collection

### Advanced Patterns (`advanced_patterns.py`) ⭐ NEW
- **AdaptiveCircuitBreaker**: Circuit breaker with adaptive thresholds
- **SemanticCache**: Embedding-based similarity caching
- **TokenBucketRateLimiter**: Token bucket with dynamic rate adjustment
- **RequestDeduplicator**: Prevent duplicate expensive operations
- **DistributedTracer**: Distributed tracing for observability
- **IntelligentBatcher**: Dynamic batching based on load and latency
- **ConnectionPool**: Connection pooling with health checking

## Usage

### Basic Example

```python
from langchain_examples.core_concepts import OpenAIProvider, LLMService

# Create provider
provider = OpenAIProvider(model_name="gpt-3.5-turbo")

# Create service
service = LLMService(provider)

# Register prompt template
service.prompt_manager.register_template(
    "analysis",
    "Analyze the following: {input}",
    ["input"]
)

# Generate response
result = await service.generate_with_template(
    "analysis",
    input="Python concurrency patterns"
)
```

### Chain Example

```python
from langchain_examples.chains import SimpleLLMChainWrapper, ChainOrchestrator

# Create chain wrapper
chain = SimpleLLMChainWrapper("analysis_chain", llm_chain)

# Create orchestrator
orchestrator = ChainOrchestrator()
orchestrator.register_chain("analysis", chain)

# Execute chain
result = await orchestrator.execute_chain("analysis", {"input": "..."})
```

### Agent Example

```python
from langchain_examples.agents import ReActAgentWrapper, AgentOrchestrator

# Create agent
agent = ReActAgentWrapper("react_agent", llm)
agent.add_tool(custom_tool)

# Create orchestrator
orchestrator = AgentOrchestrator()
orchestrator.register_agent("react", agent)

# Execute agent
result = await orchestrator.execute_agent("react", "What is Python?")
```

### Memory Example

```python
from langchain_examples.memory import ConversationBufferMemoryWrapper, MemoryManager

# Create memory
memory = ConversationBufferMemoryWrapper("conversation")

# Save context
memory.save_context({"input": "Hello"}, {"output": "Hi there!"})

# Load memory
variables = memory.load_memory_variables({})
```

## Production Standards

All code follows:
- ✅ **OOP Principles**: Classes, inheritance, abstraction
- ✅ **Type Hints**: Full type coverage
- ✅ **Error Handling**: Comprehensive exception handling
- ✅ **Logging**: Structured logging with context
- ✅ **Documentation**: Complete docstrings
- ✅ **Testing**: Production-ready patterns
- ✅ **No TODOs**: All code is production-ready
- ✅ **Graceful Degradation**: Fallbacks when dependencies unavailable

## Dependencies

### Required
- Python 3.8+
- langchain (optional, with graceful fallbacks)

### Optional
- openai (for OpenAI integration)
- anthropic (for Anthropic integration)
- pydantic (for output parsing)

## Running Examples

```bash
# Run all examples
python run_examples.py

# Run specific module
python run_examples.py core
python run_examples.py chains
python run_examples.py agents
```

## File Structure

```
langchain_examples/
├── __init__.py
├── README.md
├── DEPLOYMENT.md         # Deployment guide
├── core_concepts.py      # LLMs, Prompts, Output Parsers
├── chains.py             # Chain implementations
├── agents.py             # Agent implementations
├── memory.py             # Memory management
├── tools.py              # Tools and toolkits
├── retrieval.py          # RAG and retrieval
├── langgraph.py          # LangGraph workflows
├── evaluation.py         # Evaluation patterns
├── production.py         # Production patterns
├── advanced_patterns.py  # Advanced production patterns
├── run_examples.py       # Example runner
├── config/               # Configuration management
│   ├── __init__.py
│   └── settings.py
├── monitoring/           # Monitoring and observability
│   ├── __init__.py
│   ├── prometheus_metrics.py
│   └── health.py
├── distributed/          # Distributed systems patterns
│   ├── __init__.py
│   └── redis_lock.py
└── tests/                # Test suite
    ├── __init__.py
    ├── conftest.py
    ├── test_advanced_patterns.py
    └── test_production.py
```

## Learning Path

1. **Start with Core Concepts**: Understand LLMs, prompts, and output parsing
2. **Learn Chains**: Build simple to complex chains
3. **Explore Agents**: Understand agent reasoning and tool usage
4. **Master Memory**: Learn conversation memory management
5. **Build Tools**: Create custom tools for agents
6. **Implement RAG**: Build retrieval-augmented generation systems
7. **Use LangGraph**: Orchestrate complex workflows
8. **Evaluate**: Test and evaluate your models
9. **Production**: Deploy with error handling and monitoring

## Testing

Run tests with pytest:

```bash
pytest tests/
```

### Test Coverage

The test suite includes:
- Unit tests for all advanced patterns
- Integration tests for ProductionLLMWrapper
- Load tests for performance validation
- Thread-safety tests for concurrent operations

## Monitoring

### Prometheus Metrics

Enable Prometheus metrics export:

```python
wrapper = ProductionLLMWrapper(
    llm_factory=llm_factory,
    enable_prometheus=True
)
```

Metrics are available at `/metrics` endpoint.

### Health Checks

Use the HealthChecker for service health monitoring:

```python
from monitoring.health import HealthChecker

checker = HealthChecker(wrapper)
health = await checker.check_overall_health()
```

Health check endpoints:
- `/health` - Overall health
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe

## Configuration

### Environment Variables

See `DEPLOYMENT.md` for complete environment variable documentation.

### Configuration Management

Use the configuration management system:

```python
from config.settings import get_config

config = get_config()
wrapper = ProductionLLMWrapper(
    llm_factory=llm_factory,
    cache_size=config.cache_size,
    enable_semantic_cache=config.enable_semantic_cache,
    # ... other config options
)
```

## Deployment

See `DEPLOYMENT.md` for detailed deployment instructions including:
- Docker deployment
- Kubernetes deployment
- Monitoring setup
- Health checks
- Scaling strategies
- Security best practices

## Best Practices

- Always use error handling and retry logic
- Implement proper logging for debugging
- Use type hints for better code clarity
- Cache responses when appropriate
- Monitor metrics and performance
- Follow OOP principles for maintainability

## License

This project follows the same license as the parent project.

