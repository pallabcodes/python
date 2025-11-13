"""
LangChain Chains - Sequential, Router, and Custom Chains.

Demonstrates:
- LLMChain for simple LLM calls
- SequentialChain for multi-step workflows
- RouterChain for dynamic routing
- Custom chain implementations
- Error handling and retry logic
- Production-grade patterns
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

# LangChain imports (with fallbacks)
try:
    from langchain.chains import LLMChain, SequentialChain, RouterChain
    from langchain.chains.base import Chain
    from langchain.schema import BaseOutputParser
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    class Chain:
        def __init__(self, **kwargs): pass
        def run(self, **kwargs): return {}
        async def arun(self, **kwargs): return {}
    
    class LLMChain(Chain):
        def __init__(self, llm=None, prompt=None, **kwargs): pass
    
    class SequentialChain(Chain):
        def __init__(self, chains=None, **kwargs): pass
    
    class RouterChain(Chain):
        def __init__(self, **kwargs): pass
    
    class BaseOutputParser:
        def parse(self, text: str): return text

logger = logging.getLogger(__name__)


@dataclass
class ChainExecutionResult:
    """Result of chain execution."""
    output: Dict[str, Any]
    execution_time: float
    steps_executed: int
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseChainWrapper(ABC):
    """
    Abstract base class for chain wrappers.
    
    Provides:
    - Error handling
    - Metrics collection
    - Retry logic
    - Logging
    """
    
    def __init__(self, chain_name: str, max_retries: int = 3):
        self.chain_name = chain_name
        self.max_retries = max_retries
        self._logger = logging.getLogger(f"{__name__}.{chain_name}")
        self.execution_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> ChainExecutionResult:
        """Execute the chain."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chain execution statistics."""
        return {
            "chain_name": self.chain_name,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "success_rate": (
                (self.execution_count - self.error_count) / max(1, self.execution_count)
            )
        }


class SimpleLLMChainWrapper(BaseChainWrapper):
    """
    Wrapper for simple LLM chains.
    
    Features:
    - Single LLM call
    - Input/output handling
    - Error recovery
    """
    
    def __init__(
        self,
        chain_name: str,
        llm_chain: Optional[LLMChain] = None,
        max_retries: int = 3
    ):
        super().__init__(chain_name, max_retries)
        self.llm_chain = llm_chain
    
    async def execute(self, inputs: Dict[str, Any]) -> ChainExecutionResult:
        """Execute simple LLM chain."""
        import time
        start_time = time.time()
        self.execution_count += 1
        
        if not HAS_LANGCHAIN or not self.llm_chain:
            # Mock execution
            await asyncio.sleep(0.1)
            return ChainExecutionResult(
                output={"result": "Mock chain output"},
                execution_time=time.time() - start_time,
                steps_executed=1
            )
        
        errors = []
        for attempt in range(self.max_retries):
            try:
                if asyncio.iscoroutinefunction(self.llm_chain.arun):
                    result = await self.llm_chain.arun(**inputs)
                else:
                    result = self.llm_chain.run(**inputs)
                
                execution_time = time.time() - start_time
                
                return ChainExecutionResult(
                    output={"result": result},
                    execution_time=execution_time,
                    steps_executed=1
                )
                
            except Exception as e:
                error_msg = f"Attempt {attempt + 1} failed: {e}"
                errors.append(error_msg)
                self._logger.warning(error_msg)
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        self.error_count += 1
        execution_time = time.time() - start_time
        
        return ChainExecutionResult(
            output={},
            execution_time=execution_time,
            steps_executed=0,
            errors=errors
        )


class SequentialChainWrapper(BaseChainWrapper):
    """
    Wrapper for sequential chains (multi-step workflows).
    
    Features:
    - Multiple chain steps
    - Output passing between steps
    - Error handling per step
    - Partial execution recovery
    """
    
    def __init__(
        self,
        chain_name: str,
        chains: List[BaseChainWrapper],
        input_variables: List[str],
        output_variables: List[str],
        max_retries: int = 3
    ):
        super().__init__(chain_name, max_retries)
        self.chains = chains
        self.input_variables = input_variables
        self.output_variables = output_variables
    
    async def execute(self, inputs: Dict[str, Any]) -> ChainExecutionResult:
        """Execute sequential chain."""
        import time
        start_time = time.time()
        self.execution_count += 1
        
        current_inputs = inputs.copy()
        steps_executed = 0
        errors = []
        
        for i, chain in enumerate(self.chains):
            try:
                step_result = await chain.execute(current_inputs)
                
                if step_result.errors:
                    errors.extend([f"Step {i+1}: {e}" for e in step_result.errors])
                    break
                
                # Merge outputs into inputs for next step
                current_inputs.update(step_result.output)
                steps_executed += 1
                
            except Exception as e:
                error_msg = f"Step {i+1} failed: {e}"
                errors.append(error_msg)
                self._logger.error(error_msg, exc_info=True)
                break
        
        execution_time = time.time() - start_time
        
        if errors:
            self.error_count += 1
        
        # Extract only requested output variables
        output = {
            key: current_inputs.get(key)
            for key in self.output_variables
            if key in current_inputs
        }
        
        return ChainExecutionResult(
            output=output,
            execution_time=execution_time,
            steps_executed=steps_executed,
            errors=errors
        )


class RouterChainWrapper(BaseChainWrapper):
    """
    Wrapper for router chains (dynamic routing).
    
    Features:
    - Dynamic chain selection
    - Routing logic
    - Fallback handling
    """
    
    def __init__(
        self,
        chain_name: str,
        destination_chains: Dict[str, BaseChainWrapper],
        router_chain: Optional[BaseChainWrapper] = None,
        default_chain: Optional[str] = None,
        max_retries: int = 3
    ):
        super().__init__(chain_name, max_retries)
        self.destination_chains = destination_chains
        self.router_chain = router_chain
        self.default_chain = default_chain or list(destination_chains.keys())[0] if destination_chains else None
    
    async def execute(self, inputs: Dict[str, Any]) -> ChainExecutionResult:
        """Execute router chain."""
        import time
        start_time = time.time()
        self.execution_count += 1
        
        # Determine destination
        destination = self.default_chain
        
        if self.router_chain:
            try:
                router_result = await self.router_chain.execute(inputs)
                if router_result.output and "destination" in router_result.output:
                    destination = router_result.output["destination"]
            except Exception as e:
                self._logger.warning(f"Router chain failed, using default: {e}")
        
        # Execute destination chain
        if destination and destination in self.destination_chains:
            chain = self.destination_chains[destination]
            result = await chain.execute(inputs)
            result.metadata["destination"] = destination
            return result
        else:
            self.error_count += 1
            execution_time = time.time() - start_time
            return ChainExecutionResult(
                output={},
                execution_time=execution_time,
                steps_executed=0,
                errors=[f"Invalid destination: {destination}"]
            )


class CustomChain(BaseChainWrapper):
    """
    Custom chain implementation example.
    
    Demonstrates:
    - Custom chain logic
    - Conditional execution
    - Loop handling
    """
    
    def __init__(
        self,
        chain_name: str,
        steps: List[Callable],
        max_iterations: int = 10,
        max_retries: int = 3
    ):
        super().__init__(chain_name, max_retries)
        self.steps = steps
        self.max_iterations = max_iterations
    
    async def execute(self, inputs: Dict[str, Any]) -> ChainExecutionResult:
        """Execute custom chain."""
        import time
        start_time = time.time()
        self.execution_count += 1
        
        current_state = inputs.copy()
        steps_executed = 0
        errors = []
        
        for iteration in range(self.max_iterations):
            for step in self.steps:
                try:
                    if asyncio.iscoroutinefunction(step):
                        result = await step(current_state)
                    else:
                        result = step(current_state)
                    
                    if isinstance(result, dict):
                        current_state.update(result)
                    
                    steps_executed += 1
                    
                    # Check for termination condition
                    if current_state.get("_terminate", False):
                        break
                        
                except Exception as e:
                    error_msg = f"Step {steps_executed + 1} failed: {e}"
                    errors.append(error_msg)
                    self._logger.error(error_msg, exc_info=True)
                    break
            
            if errors or current_state.get("_terminate", False):
                break
        
        execution_time = time.time() - start_time
        
        if errors:
            self.error_count += 1
        
        # Remove internal state variables
        output = {
            k: v for k, v in current_state.items()
            if not k.startswith("_")
        }
        
        return ChainExecutionResult(
            output=output,
            execution_time=execution_time,
            steps_executed=steps_executed,
            errors=errors,
            metadata={"iterations": iteration + 1}
        )


class ChainOrchestrator:
    """
    Orchestrates multiple chains.
    
    Features:
    - Chain composition
    - Parallel execution
    - Error aggregation
    - Result merging
    """
    
    def __init__(self):
        self.chains: Dict[str, BaseChainWrapper] = {}
        self._logger = logging.getLogger(f"{__name__}.ChainOrchestrator")
    
    def register_chain(self, name: str, chain: BaseChainWrapper):
        """Register a chain."""
        self.chains[name] = chain
        self._logger.info(f"Registered chain: {name}")
    
    async def execute_chain(self, chain_name: str, inputs: Dict[str, Any]) -> ChainExecutionResult:
        """Execute a single chain."""
        if chain_name not in self.chains:
            raise ValueError(f"Chain {chain_name} not found")
        
        return await self.chains[chain_name].execute(inputs)
    
    async def execute_parallel(
        self,
        chain_inputs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, ChainExecutionResult]:
        """Execute multiple chains in parallel."""
        tasks = {
            name: self.execute_chain(name, inputs)
            for name, inputs in chain_inputs.items()
            if name in self.chains
        }
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        return {
            name: result if not isinstance(result, Exception) else ChainExecutionResult(
                output={},
                execution_time=0.0,
                steps_executed=0,
                errors=[str(result)]
            )
            for name, result in zip(tasks.keys(), results)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all chains."""
        return {
            name: chain.get_stats()
            for name, chain in self.chains.items()
        }

    def chain_orchestrator_real_world_example(self) -> None:
        """
        Real-World Scenario: Chain Orchestrator - Document Processing Pipeline.

        REAL-WORLD SCENARIO:
        ====================
        You're building a document processing pipeline:
        - Extract information from documents
        - Analyze and summarize content
        - Generate insights
        - Problem: Multi-step processing workflow
        
        THE PROBLEM WITHOUT CHAIN ORCHESTRATOR:
        =======================================
        - Manual workflow → error-prone
        - No coordination → inconsistent results
        - Sequential processing → slow
        - No error handling → fragile
        - Complex code → hard to maintain
        
        THE SOLUTION:
        =============
        Chain Orchestrator enables:
        - Structured workflows → reliable processing
        - Step coordination → consistent results
        - Parallel execution → faster processing
        - Error handling → robust pipelines
        - Maintainable code → easy to extend
        
        WHEN TO USE CHAIN ORCHESTRATOR:
        ===============================
        ✅ Document processing pipelines
        ✅ Multi-step workflows
        ✅ Data transformation pipelines
        ✅ Complex processing workflows
        ✅ Production data pipelines
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Document Processing Pipeline")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Document processing pipeline")
        print("  - Extract information from documents")
        print("  - Analyze and summarize content")
        print("  - Generate insights")
        print("  - Problem: Multi-step processing workflow")
        print()
        print("THE PROBLEM:")
        print("  Without chain orchestrator:")
        print("    ❌ Manual workflow → error-prone")
        print("    ❌ No coordination → inconsistent results")
        print("    ❌ Sequential processing → slow")
        print("    ❌ No error handling → fragile")
        print()
        print("THE SOLUTION:")
        print("  With chain orchestrator:")
        print("    ✅ Structured workflows → reliable processing")
        print("    ✅ Step coordination → consistent results")
        print("    ✅ Parallel execution → faster processing")
        print("    ✅ Error handling → robust pipelines")
        print()
        print("=" * 70)
        print()

        print("Simulating document processing pipeline...")
        print()

        # Simulate pipeline stages
        stages = [
            ("Extract", "Extracting text from document..."),
            ("Analyze", "Analyzing document content..."),
            ("Summarize", "Generating summary..."),
            ("Insights", "Extracting key insights...")
        ]

        for stage_name, stage_desc in stages:
            print(f"  Stage: {stage_name}")
            print(f"    {stage_desc}")
            # Simulate processing time
            import time
            time.sleep(0.1)
            print(f"    ✅ {stage_name} completed")

        print()
        print("Pipeline results:")
        print("  ✅ Document processed successfully")
        print("  ✅ Summary generated")
        print("  ✅ Insights extracted")
        print()
        print("  ✅ Chain orchestrator enabled structured document processing!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE CHAIN ORCHESTRATOR:")
        print("   ✅ Document processing pipelines")
        print("   ✅ Multi-step workflows")
        print("   ✅ Data transformation pipelines")
        print("   ✅ Complex processing workflows")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Structured workflows")
        print("   - Step coordination")
        print("   - Parallel execution")
        print("   - Robust pipelines")
        print("=" * 70)
        print()

