# Examples Guide

## Available Examples

### Basic Optimization Demo

```bash
python examples/basic_optimization_demo.py
```

Demonstrates basic workload optimization with code analysis.

### LLM Analysis Demo

```bash
python examples/llm_analysis_demo.py
```

Shows LLM-powered workload analysis with AST parsing and NLP.

### Strategy Selection Demo

```bash
python examples/strategy_selection_demo.py
```

Demonstrates intelligent strategy selection with trade-off analysis.

### Multi-Workload Demo

```bash
python examples/multi_workload_demo.py
```

Shows optimization of multiple workloads with different characteristics.

### Learning Demo

```bash
python examples/learning_demo.py
```

Demonstrates adaptive learning from optimization results.

### Explainability Demo

```bash
python examples/explainability_demo.py
```

Shows natural language explanations, reports, and Q&A system.

## Example Workloads

### CPU-Bound Workload

```python
workload = {
    "code": "def compute(n): return sum(i*i for i in range(n))",
    "description": "CPU-intensive computation"
}
```

### I/O-Bound Workload

```python
workload = {
    "code": "import requests; requests.get('http://example.com')",
    "description": "I/O-bound HTTP request"
}
```

### Async Workload

```python
workload = {
    "code": """
import asyncio
async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
""",
    "description": "Async I/O workload"
}
```

