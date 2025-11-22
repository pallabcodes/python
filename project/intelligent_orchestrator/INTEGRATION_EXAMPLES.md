# Integration Examples - How to Use With Existing Solutions

## Example 1: FastAPI Integration (When Needed)

```python
# fastapi_app.py
from fastapi import FastAPI, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import List

from intelligent_orchestrator.core.orchestrator_factory import OrchestratorFactory

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

orchestrator = OrchestratorFactory.create()

class WorkloadRequest(BaseModel):
    code: str
    description: str = ""

class BatchRequest(BaseModel):
    workloads: List[WorkloadRequest]

@app.post("/optimize")
@limiter.limit("5/day")
def optimize(workload: WorkloadRequest):
    """Optimize a single workload."""
    try:
        result = orchestrator.optimize_workload({
            "code": workload.code,
            "description": workload.description
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/optimize/batch")
@limiter.limit("5/day")
def optimize_batch(batch: BatchRequest):
    """Optimize multiple workloads."""
    results = []
    for workload in batch.workloads:
        result = orchestrator.optimize_workload({
            "code": workload.code,
            "description": workload.description
        })
        results.append(result)
    return {"results": results}
```

## Example 2: Ollama Integration (Local LLM)

```python
# Add to requirements.txt: langchain-ollama

# Modify agent to support Ollama
from langchain_ollama import OllamaLLM

class WorkloadAnalyzerAgent(BaseAgent):
    def __init__(self, use_local: bool = False, ...):
        if use_local:
            llm = OllamaLLM(model="llama2")
        else:
            llm = ChatOpenAI(model="gpt-4")
        # ... rest of initialization
```

## Example 3: CodeRabbit Integration

```python
# Use CodeRabbit API + Our Concurrency Analysis
import requests
from intelligent_orchestrator import OrchestratorFactory

class EnhancedCodeReview:
    def __init__(self, coderabbit_api_key: str):
        self.coderabbit_api_key = coderabbit_api_key
        self.orchestrator = OrchestratorFactory.create()
    
    def review_with_concurrency(self, code: str, file_path: str):
        # Get CodeRabbit general review
        coderabbit_review = self._get_coderabbit_review(code, file_path)
        
        # Get our concurrency-specific analysis
        concurrency_analysis = self.orchestrator.optimize_workload({
            "code": code,
            "description": f"File: {file_path}"
        })
        
        return {
            "general_review": coderabbit_review,
            "concurrency_optimization": concurrency_analysis
        }
    
    def _get_coderabbit_review(self, code: str, file_path: str):
        # Call CodeRabbit API
        response = requests.post(
            "https://api.coderabbit.ai/review",
            headers={"Authorization": f"Bearer {self.coderabbit_api_key}"},
            json={"code": code, "file_path": file_path}
        )
        return response.json()
```

## Example 4: VSCode Extension (Using Our Library)

```typescript
// extension.ts
import * as vscode from 'vscode';
import { PythonShell } from 'python-shell';

export function activate(context: vscode.ExtensionContext) {
    let analyzeCommand = vscode.commands.registerCommand(
        'intelliorch.analyze',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            
            const selectedCode = editor.document.getText(editor.selection);
            
            // Call our Python library
            PythonShell.run('analyze_code.py', {
                args: [selectedCode]
            }, (err, results) => {
                if (err) {
                    vscode.window.showErrorMessage('Analysis failed');
                    return;
                }
                
                // Show suggestions
                const result = JSON.parse(results[0]);
                vscode.window.showInformationMessage(
                    `Recommended: ${result.selection.selected_strategy}`
                );
            });
        }
    );
    
    context.subscriptions.push(analyzeCommand);
}
```

## Example 5: Using Existing Research Implementations

```python
# Instead of implementing CRDTs from scratch
from pycrdt import Doc, Map, Array

# Use existing implementation
class CRDTLLMState:
    def __init__(self):
        self.doc = Doc()
        self.state_map = Map()
        self.doc["state"] = self.state_map
    
    def update_state(self, state: Dict[str, Any]):
        # Use existing CRDT implementation
        self.state_map.update(state)
        return self.state_map.to_dict()
```

## Example 6: Ray Integration (Use Their Library)

```python
# Use Ray directly, don't rebuild
import ray
from intelligent_orchestrator import OrchestratorFactory

class DistributedOptimizer:
    def __init__(self):
        self.orchestrator = OrchestratorFactory.create()
        ray.init()
    
    def optimize_distributed(self, workloads: List[Dict]):
        # Our orchestrator decides strategy
        strategy = self.orchestrator.select_strategy(workloads[0])
        
        if strategy == "distributed":
            # Use Ray's existing functionality
            @ray.remote
            def process_workload(workload):
                return self.orchestrator.optimize_workload(workload)
            
            futures = [process_workload.remote(w) for w in workloads]
            return ray.get(futures)
        else:
            # Use other strategy
            return [self.orchestrator.optimize_workload(w) for w in workloads]
```

## Key Takeaway

**We built a library that can be:**
- ✅ Consumed by FastAPI (Example 1)
- ✅ Extended with local LLMs (Example 2)
- ✅ Integrated with CodeRabbit (Example 3)
- ✅ Used in VSCode extensions (Example 4)
- ✅ Combined with research implementations (Example 5)
- ✅ Wrapped around existing tools like Ray (Example 6)

**This is the right approach** - build our unique value (concurrency optimization) and integrate with everything else.

