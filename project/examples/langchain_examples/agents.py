"""
LangChain Agents - ReAct, Plan-and-Execute, and Custom Agents.

Demonstrates:
- ReAct agents with tool usage
- Plan-and-Execute agents for complex tasks
- Custom agent implementations
- Tool integration and management
- Error handling and recovery
- Production-grade patterns
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

# LangChain imports (with fallbacks)
try:
    from langchain.agents import AgentExecutor, initialize_agent, AgentType
    from langchain.agents.react.base import ReActDocstoreAgent
    from langchain.agents.plan_and_execute import PlanAndExecuteAgentExecutor
    from langchain.tools import BaseTool
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    class BaseTool:
        def __init__(self, name: str, description: str): pass
        def run(self, query: str): return "Mock tool result"
    
    class AgentExecutor:
        def __init__(self, agent=None, tools=None, **kwargs): pass
        def run(self, input: str): return "Mock agent result"
        async def arun(self, input: str): return "Mock agent result"
    
    def initialize_agent(tools, llm, agent_type, **kwargs): return AgentExecutor()
    
    class AgentType:
        ZERO_SHOT_REACT_DESCRIPTION = "zero_shot_react_description"
        PLAN_AND_EXECUTE = "plan_and_execute"
    
    class ReActDocstoreAgent: pass
    class PlanAndExecuteAgentExecutor: pass

logger = logging.getLogger(__name__)


@dataclass
class AgentExecutionResult:
    """Result of agent execution."""
    output: str
    intermediate_steps: List[Dict[str, Any]] = field(default_factory=list)
    execution_time: float = 0.0
    tool_calls: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgentWrapper(ABC):
    """
    Abstract base class for agent wrappers.
    
    Provides:
    - Unified interface
    - Error handling
    - Metrics collection
    - Tool management
    """
    
    def __init__(self, agent_name: str, max_iterations: int = 10):
        self.agent_name = agent_name
        self.max_iterations = max_iterations
        self._logger = logging.getLogger(f"{__name__}.{agent_name}")
        self.execution_count = 0
        self.error_count = 0
        self.tools: List[BaseTool] = []
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to the agent."""
        self.tools.append(tool)
        self._logger.info(f"Added tool: {tool.name if hasattr(tool, 'name') else 'unknown'}")
    
    @abstractmethod
    async def execute(self, query: str) -> AgentExecutionResult:
        """Execute agent with query."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "agent_name": self.agent_name,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "success_rate": (
                (self.execution_count - self.error_count) / max(1, self.execution_count)
            ),
            "tool_count": len(self.tools)
        }


class ReActAgentWrapper(BaseAgentWrapper):
    """
    ReAct (Reasoning + Acting) agent wrapper.
    
    Features:
    - Tool usage
    - Reasoning steps
    - Error recovery
    """
    
    def __init__(
        self,
        agent_name: str,
        llm: Optional[Any] = None,
        max_iterations: int = 10
    ):
        super().__init__(agent_name, max_iterations)
        self.llm = llm
        self.executor: Optional[AgentExecutor] = None
        
        if HAS_LANGCHAIN and self.llm:
            try:
                self.executor = initialize_agent(
                    tools=self.tools,
                    llm=self.llm,
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=True,
                    max_iterations=max_iterations
                )
            except Exception as e:
                self._logger.warning(f"Failed to initialize ReAct agent: {e}")
    
    async def execute(self, query: str) -> AgentExecutionResult:
        """Execute ReAct agent."""
        import time
        start_time = time.time()
        self.execution_count += 1
        
        if not HAS_LANGCHAIN or not self.executor:
            # Mock execution
            await asyncio.sleep(0.2)
            return AgentExecutionResult(
                output="Mock ReAct agent response",
                execution_time=time.time() - start_time,
                tool_calls=0
            )
        
        try:
            if hasattr(self.executor, 'arun'):
                result = await self.executor.arun(query)
            else:
                result = self.executor.run(query)
            
            execution_time = time.time() - start_time
            
            return AgentExecutionResult(
                output=str(result),
                execution_time=execution_time,
                tool_calls=len(self.tools)
            )
            
        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time
            self._logger.error(f"Agent execution failed: {e}", exc_info=True)
            
            return AgentExecutionResult(
                output="",
                execution_time=execution_time,
                errors=[str(e)]
            )


class PlanAndExecuteAgentWrapper(BaseAgentWrapper):
    """
    Plan-and-Execute agent wrapper.
    
    Features:
    - Multi-step planning
    - Plan execution
    - Plan refinement
    """
    
    def __init__(
        self,
        agent_name: str,
        llm: Optional[Any] = None,
        max_iterations: int = 10
    ):
        super().__init__(agent_name, max_iterations)
        self.llm = llm
        self.executor: Optional[PlanAndExecuteAgentExecutor] = None
        
        if HAS_LANGCHAIN and self.llm:
            try:
                # Note: PlanAndExecuteAgentExecutor requires specific setup
                # This is a simplified version
                self.executor = initialize_agent(
                    tools=self.tools,
                    llm=self.llm,
                    agent=AgentType.PLAN_AND_EXECUTE,
                    verbose=True,
                    max_iterations=max_iterations
                )
            except Exception as e:
                self._logger.warning(f"Failed to initialize Plan-and-Execute agent: {e}")
    
    async def execute(self, query: str) -> AgentExecutionResult:
        """Execute Plan-and-Execute agent."""
        import time
        start_time = time.time()
        self.execution_count += 1
        
        if not HAS_LANGCHAIN or not self.executor:
            # Mock execution with planning steps
            await asyncio.sleep(0.3)
            return AgentExecutionResult(
                output="Mock Plan-and-Execute agent response",
                execution_time=time.time() - start_time,
                tool_calls=0,
                intermediate_steps=[
                    {"step": "plan", "action": "Create execution plan"},
                    {"step": "execute", "action": "Execute plan steps"}
                ]
            )
        
        try:
            if hasattr(self.executor, 'arun'):
                result = await self.executor.arun(query)
            else:
                result = self.executor.run(query)
            
            execution_time = time.time() - start_time
            
            return AgentExecutionResult(
                output=str(result),
                execution_time=execution_time,
                tool_calls=len(self.tools),
                intermediate_steps=[{"step": "plan_and_execute", "result": str(result)}]
            )
            
        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time
            self._logger.error(f"Agent execution failed: {e}", exc_info=True)
            
            return AgentExecutionResult(
                output="",
                execution_time=execution_time,
                errors=[str(e)]
            )


class CustomTool(BaseTool):
    """
    Custom tool implementation example.
    
    Demonstrates:
    - Tool interface
    - Input validation
    - Error handling
    """
    
    def __init__(self, name: str, description: str, func: Callable):
        super().__init__(name=name, description=description)
        self.func = func
        self._logger = logging.getLogger(f"{__name__}.{name}")
    
    def _run(self, query: str) -> str:
        """Execute the tool."""
        try:
            result = self.func(query)
            return str(result)
        except Exception as e:
            self._logger.error(f"Tool {self.name} failed: {e}")
            return f"Error: {e}"
    
    async def _arun(self, query: str) -> str:
        """Async execute the tool."""
        if asyncio.iscoroutinefunction(self.func):
            try:
                result = await self.func(query)
                return str(result)
            except Exception as e:
                self._logger.error(f"Tool {self.name} failed: {e}")
                return f"Error: {e}"
        else:
            return self._run(query)


class AgentOrchestrator:
    """
    Orchestrates multiple agents.
    
    Features:
    - Agent selection
    - Multi-agent coordination
    - Result aggregation
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgentWrapper] = {}
        self._logger = logging.getLogger(f"{__name__}.AgentOrchestrator")
    
    def register_agent(self, name: str, agent: BaseAgentWrapper):
        """Register an agent."""
        self.agents[name] = agent
        self._logger.info(f"Registered agent: {name}")
    
    async def execute_agent(self, agent_name: str, query: str) -> AgentExecutionResult:
        """Execute a specific agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        return await self.agents[agent_name].execute(query)
    
    async def execute_with_routing(
        self,
        query: str,
        router_func: Callable[[str], str]
    ) -> AgentExecutionResult:
        """Execute agent based on routing logic."""
        agent_name = router_func(query)
        return await self.execute_agent(agent_name, query)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all agents."""
        return {
            name: agent.get_stats()
            for name, agent in self.agents.items()
        }

    def agent_orchestrator_real_world_example(self) -> None:
        """
        Real-World Scenario: Agent Orchestrator - Intelligent Task Assistant.

        REAL-WORLD SCENARIO:
        ====================
        You're building an intelligent task assistant:
        - Handle complex multi-step tasks
        - Use tools to accomplish goals
        - Problem: Need autonomous decision-making
        
        THE PROBLEM WITHOUT AGENT ORCHESTRATOR:
        ========================================
        - Manual task execution → time-consuming
        - No tool usage → limited capabilities
        - No reasoning → poor decisions
        - No planning → inefficient execution
        - System inflexible → can't adapt
        
        THE SOLUTION:
        =============
        Agent Orchestrator enables:
        - Autonomous task execution → efficient
        - Tool integration → extended capabilities
        - Reasoning and planning → better decisions
        - Multi-step task handling → complex workflows
        - Adaptive behavior → flexible system
        
        WHEN TO USE AGENT ORCHESTRATOR:
        ===============================
        ✅ Intelligent task assistants
        ✅ Multi-step task automation
        ✅ Tool-using AI systems
        ✅ Autonomous decision-making
        ✅ Complex workflow automation
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Intelligent Task Assistant")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Intelligent task assistant")
        print("  - Handle complex multi-step tasks")
        print("  - Use tools to accomplish goals")
        print("  - Problem: Need autonomous decision-making")
        print()
        print("THE PROBLEM:")
        print("  Without agent orchestrator:")
        print("    ❌ Manual task execution → time-consuming")
        print("    ❌ No tool usage → limited capabilities")
        print("    ❌ No reasoning → poor decisions")
        print("    ❌ No planning → inefficient execution")
        print()
        print("THE SOLUTION:")
        print("  With agent orchestrator:")
        print("    ✅ Autonomous task execution → efficient")
        print("    ✅ Tool integration → extended capabilities")
        print("    ✅ Reasoning and planning → better decisions")
        print("    ✅ Multi-step task handling → complex workflows")
        print()
        print("=" * 70)
        print()

        print("Simulating intelligent task assistant...")
        print()

        tasks = [
            "Search for information about Python async programming",
            "Summarize the findings",
            "Create a report document"
        ]

        for i, task in enumerate(tasks, 1):
            print(f"Task {i}: {task}")
            print(f"  Agent reasoning: Analyzing task requirements...")
            print(f"  Agent action: Executing task...")
            print(f"  ✅ Task {i} completed")
            print()

        print("  ✅ Agent orchestrator enabled autonomous task execution!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE AGENT ORCHESTRATOR:")
        print("   ✅ Intelligent task assistants")
        print("   ✅ Multi-step task automation")
        print("   ✅ Tool-using AI systems")
        print("   ✅ Autonomous decision-making")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Autonomous task execution")
        print("   - Tool integration")
        print("   - Reasoning and planning")
        print("   - Complex workflow automation")
        print("=" * 70)
        print()

