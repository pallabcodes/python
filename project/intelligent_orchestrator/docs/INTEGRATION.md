# Integration Guide

## Concurrency Framework Integration

The orchestrator integrates with the adaptive concurrency framework:

```python
from intelligent_orchestrator.integration.concurrency_adapter import FrameworkAdapter

adapter = FrameworkAdapter()
result = adapter.optimize(workload, strategy)
```

## Examples Integration

All concurrency examples are integrated through integrators:

### Threading

```python
from intelligent_orchestrator.integration.examples_integration import ThreadingIntegrator

integrator = ThreadingIntegrator()
techniques = integrator.get_available_techniques()
strategy = integrator.create_strategy("thread_pools", config)
```

### Multiprocessing

```python
from intelligent_orchestrator.integration.examples_integration import MultiprocessingIntegrator

integrator = MultiprocessingIntegrator()
strategy = integrator.create_strategy("process_pools", config)
```

### Asyncio

```python
from intelligent_orchestrator.integration.examples_integration import AsyncioIntegrator

integrator = AsyncioIntegrator()
strategy = integrator.create_strategy("async_io", config)
```

## Research Paper Integration

### Timestamp Tokens

```python
from intelligent_orchestrator.integration.research_integration import TimestampTokensLLM

tokens = TimestampTokensLLM()
coordinated_task = tokens.coordinate_task(task)
```

### CRDT State

```python
from intelligent_orchestrator.integration.research_integration import CRDTLLMState

crdt = CRDTLLMState()
merged_state = crdt.update_state(state)
```

### Consensus Protocol

```python
from intelligent_orchestrator.integration.research_integration import ConsensusLLM

consensus = ConsensusLLM()
agreed = consensus.reach_consensus(proposals)
```

## Open-Source Techniques

### Ray Inference

```python
from intelligent_orchestrator.integration.opensource_integration import RayInference

ray = RayInference()
results = ray.distribute_inference(tasks, num_workers=4)
```

### Celery Queue

```python
from intelligent_orchestrator.integration.opensource_integration import CeleryLLMQueue

queue = CeleryLLMQueue()
task_id = queue.enqueue(task)
```

### Dask Graph

```python
from intelligent_orchestrator.integration.opensource_integration import DaskLLMGraph

dask = DaskLLMGraph()
graph = dask.build_graph(operations)
```

