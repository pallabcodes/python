# Usage Guide

## Installation

```bash
cd project/intelligent_orchestrator
pip install -r requirements.txt
```

## Basic Usage

### Simple Optimization

```python
from intelligent_orchestrator.core.orchestrator_factory import OrchestratorFactory

# Create orchestrator
orchestrator = OrchestratorFactory.create()

# Optimize workload
workload = {
    "code": """
def process_data(items):
    results = []
    for item in items:
        result = expensive_computation(item)
        results.append(result)
    return results
""",
    "description": "CPU-intensive data processing"
}

result = orchestrator.optimize_workload(workload)
print(f"Selected Strategy: {result['selection']['selected_strategy']}")
```

### With Configuration

```python
from intelligent_orchestrator.core.orchestrator_config import OrchestratorConfig
from intelligent_orchestrator.core.orchestrator_factory import OrchestratorFactory

config = OrchestratorConfig(
    llm_model="gpt-4",
    enable_learning=True,
    enable_explanations=True
)

orchestrator = OrchestratorFactory.create(config=config)
```

### Natural Language Only

```python
workload = {
    "description": "I need to fetch data from multiple APIs concurrently"
}

result = orchestrator.optimize_workload(workload)
```

## Advanced Usage

### Custom Workload Analysis

```python
from intelligent_orchestrator.intelligence.workload_analyzer_llm import WorkloadAnalyzerLLM

analyzer = WorkloadAnalyzerLLM()
analysis = analyzer.analyze(workload)
```

### Strategy Selection

```python
from intelligent_orchestrator.intelligence.strategy_selector_llm import StrategySelectorLLM

selector = StrategySelectorLLM()
selection = selector.select(analysis, ["threading", "asyncio", "multiprocessing"])
```

### Learning from Results

```python
from intelligent_orchestrator.intelligence.learning_system import LearningSystem

learning = LearningSystem()
insights = learning.learn_from_results(optimization_result)
```

## Environment Variables

```bash
export LLM_MODEL="gpt-4"
export ENABLE_LEARNING="true"
export ENABLE_EXPLANATIONS="true"
export MAX_WORKERS="4"
export LOG_LEVEL="INFO"
```

