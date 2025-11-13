# API Reference

## Core API

### OrchestratorFactory

Factory for creating orchestrator instances.

```python
from intelligent_orchestrator.core.orchestrator_factory import OrchestratorFactory

orchestrator = OrchestratorFactory.create()
```

### OrchestratorAPI

Main public API for intelligent orchestrator.

#### optimize_workload(workload: Dict[str, Any]) -> Dict[str, Any]

Optimize a workload using intelligent orchestration.

**Parameters:**
- `workload`: Dictionary with workload information
  - `code` (optional): Python code string
  - `description` (optional): Natural language description

**Returns:**
- Dictionary containing:
  - `analysis`: Workload analysis results
  - `selection`: Selected strategy
  - `result`: Optimization results
  - `explanation`: Natural language explanation (if enabled)

**Example:**
```python
result = orchestrator.optimize_workload({
    "code": "def process(data): ...",
    "description": "CPU-intensive workload"
})
```

## Intelligence Layer

### WorkloadAnalyzerLLM

LLM-powered workload analyzer.

```python
from intelligent_orchestrator.intelligence.workload_analyzer_llm import WorkloadAnalyzerLLM

analyzer = WorkloadAnalyzerLLM()
analysis = analyzer.analyze(workload)
```

### StrategySelectorLLM

LLM-powered strategy selector.

```python
from intelligent_orchestrator.intelligence.strategy_selector_llm import StrategySelectorLLM

selector = StrategySelectorLLM()
selection = selector.select(analysis, strategies)
```

## Configuration

### OrchestratorConfig

Configuration for orchestrator.

```python
from intelligent_orchestrator.core.orchestrator_config import OrchestratorConfig

config = OrchestratorConfig(
    llm_model="gpt-4",
    enable_learning=True,
    enable_explanations=True,
    max_workers=4
)
```

