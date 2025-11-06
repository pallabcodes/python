"""
AI Agent Framework with tool calling and reasoning.

Provides enterprise-grade AI agent capabilities including:
- Tool orchestration and calling
- Multi-step reasoning and planning
- Agent collaboration and delegation
- Memory and context management
- Safety and alignment mechanisms
"""

import asyncio
import inspect
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable

from pydantic import BaseModel

try:
    from ..core.config import PlatformConfig
except ImportError:
    # Fallback for direct imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from core.config import PlatformConfig


class Tool(BaseModel):
    """Tool definition for agent use."""

    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    requires_confirmation: bool = False
    safety_level: str = "safe"  # safe, moderate, dangerous


class ToolCall(BaseModel):
    """Tool call request."""

    tool_name: str
    parameters: Dict[str, Any]
    reasoning: str


class AgentMessage(BaseModel):
    """Message in agent conversation."""

    role: str  # user, assistant, system, tool
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    timestamp: float


class AgentMemory(BaseModel):
    """Agent memory and context."""

    conversation_history: List[AgentMessage] = []
    working_memory: Dict[str, Any] = {}
    long_term_memory: Dict[str, Any] = {}
    max_history_length: int = 50


class AgentConfig(BaseModel):
    """Configuration for AI agent."""

    name: str
    role: str
    goal: str
    personality: str = "professional"
    max_iterations: int = 10
    temperature: float = 0.7
    enable_reasoning: bool = True
    enable_tool_calling: bool = True
    enable_delegation: bool = False
    safety_mode: str = "moderate"  # strict, moderate, permissive


class AgentResult(BaseModel):
    """Result from agent execution."""

    success: bool
    final_answer: str
    reasoning_trace: List[str]
    tool_calls_made: List[ToolCall]
    iterations_used: int
    execution_time: float
    errors: List[str] = []


class BaseAgent(ABC):
    """Base class for AI agents."""

    def __init__(self, config: AgentConfig, platform_config: PlatformConfig):
        self.config = config
        self.platform_config = platform_config
        self.logger = logging.getLogger(f"{platform_config.project_name}.Agent.{config.name}")

        self.memory = AgentMemory()
        self.available_tools: Dict[str, Tool] = {}
        self.llm_manager = None

    @abstractmethod
    async def think(self, task: str) -> str:
        """Core reasoning method."""
        pass

    @abstractmethod
    async def act(self, reasoning: str, available_tools: List[Tool]) -> Union[str, ToolCall]:
        """Action selection method."""
        pass

    async def execute(self, task: str) -> AgentResult:
        """Execute agent on a task."""
        start_time = asyncio.get_event_loop().time()
        result = AgentResult(
            success=False,
            final_answer="",
            reasoning_trace=[],
            tool_calls_made=[],
            iterations_used=0,
            execution_time=0.0
        )

        try:
            self.logger.info(f"Starting task execution: {task}")

            # Add initial user message
            await self._add_message("user", task)

            for iteration in range(self.config.max_iterations):
                result.iterations_used = iteration + 1

                # Think about current situation
                reasoning = await self.think(task)
                result.reasoning_trace.append(reasoning)

                # Decide on action
                action = await self.act(reasoning, list(self.available_tools.values()))

                if isinstance(action, str):
                    # Final answer
                    result.success = True
                    result.final_answer = action
                    await self._add_message("assistant", action)
                    break

                elif isinstance(action, ToolCall):
                    # Execute tool
                    result.tool_calls_made.append(action)

                    if await self._should_execute_tool(action):
                        tool_result = await self._execute_tool(action)
                        await self._add_message("tool", json.dumps(tool_result), tool_results=[tool_result])
                    else:
                        await self._add_message("assistant", f"Tool call rejected: {action.tool_name}")

                else:
                    result.errors.append(f"Invalid action type: {type(action)}")
                    break

            if not result.success:
                result.final_answer = "Task could not be completed within iteration limit"
                result.errors.append("Maximum iterations reached")

        except Exception as e:
            result.errors.append(f"Execution error: {str(e)}")
            self.logger.error(f"Agent execution failed: {e}")

        result.execution_time = asyncio.get_event_loop().time() - start_time
        return result

    async def _add_message(
        self,
        role: str,
        content: str,
        tool_calls: Optional[List[ToolCall]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add message to conversation history."""
        message = AgentMessage(
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_results=tool_results,
            timestamp=asyncio.get_event_loop().time()
        )

        self.memory.conversation_history.append(message)

        # Maintain history length
        if len(self.memory.conversation_history) > self.memory.max_history_length:
            self.memory.conversation_history = self.memory.conversation_history[-self.memory.max_history_length:]

    async def _should_execute_tool(self, tool_call: ToolCall) -> bool:
        """Determine if tool should be executed based on safety settings."""
        if tool_call.tool_name not in self.available_tools:
            return False

        tool = self.available_tools[tool_call.tool_name]

        if self.config.safety_mode == "strict":
            return tool.safety_level == "safe"
        elif self.config.safety_mode == "moderate":
            return tool.safety_level in ["safe", "moderate"]
        else:  # permissive
            return True

    async def _execute_tool(self, tool_call: ToolCall) -> Dict[str, Any]:
        """Execute a tool call."""
        try:
            tool = self.available_tools[tool_call.tool_name]

            # Validate parameters
            if not self._validate_tool_parameters(tool, tool_call.parameters):
                return {"error": "Invalid tool parameters"}

            # Execute tool
            result = await tool.function(**tool_call.parameters)

            return {"success": True, "result": result}

        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}

    def _validate_tool_parameters(self, tool: Tool, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters."""
        try:
            # Basic validation - check required parameters
            required_params = tool.parameters.get("required", [])
            for param in required_params:
                if param not in parameters:
                    return False

            # Type checking would go here
            return True

        except Exception:
            return False

    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the agent's toolkit."""
        self.available_tools[tool.name] = tool
        self.logger.info(f"Added tool: {tool.name}")

    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent's toolkit."""
        if tool_name in self.available_tools:
            del self.available_tools[tool_name]
            self.logger.info(f"Removed tool: {tool_name}")

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of agent memory."""
        return {
            "conversation_length": len(self.memory.conversation_history),
            "working_memory_keys": list(self.memory.working_memory.keys()),
            "long_term_memory_keys": list(self.memory.long_term_memory.keys()),
            "available_tools": list(self.available_tools.keys()),
        }

    def clear_memory(self) -> None:
        """Clear agent memory."""
        self.memory = AgentMemory()
        self.logger.info("Agent memory cleared")


class ReasoningAgent(BaseAgent):
    """Agent with advanced reasoning capabilities."""

    async def think(self, task: str) -> str:
        """Advanced reasoning about current situation."""
        # Get recent conversation context
        recent_messages = self.memory.conversation_history[-5:]

        context = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in recent_messages
        ])

        thinking_prompt = f"""
You are {self.config.name}, a {self.config.role}.
Your goal: {self.config.goal}

Current task: {task}
Recent conversation:
{context}

Working memory: {json.dumps(self.memory.working_memory)}

Available tools: {list(self.available_tools.keys())}

Think step by step about what to do next. Consider:
1. What progress have I made so far?
2. What information do I still need?
3. What tools might help me?
4. Am I ready to provide a final answer?

Provide your reasoning:
"""

        if self.llm_manager:
            response = await self.llm_manager.generate_text(thinking_prompt)
            return response.content if hasattr(response, 'content') else str(response)
        else:
            # Fallback reasoning
            return f"Analyzing task: {task}. I have {len(self.available_tools)} tools available."

    async def act(self, reasoning: str, available_tools: List[Tool]) -> Union[str, ToolCall]:
        """Decide on next action based on reasoning."""
        if "final answer" in reasoning.lower() or "complete" in reasoning.lower():
            # Extract final answer
            return self._extract_final_answer(reasoning)

        # Look for tool usage in reasoning
        for tool in available_tools:
            if tool.name.lower() in reasoning.lower():
                # Create tool call
                tool_call = ToolCall(
                    tool_name=tool.name,
                    parameters=self._extract_tool_parameters(reasoning, tool),
                    reasoning=reasoning
                )
                return tool_call

        # Default to providing answer
        return reasoning

    def _extract_final_answer(self, reasoning: str) -> str:
        """Extract final answer from reasoning."""
        # Simple extraction - look for answer indicators
        lines = reasoning.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['answer:', 'final:', 'result:']):
                return line.split(':', 1)[1].strip()

        return reasoning

    def _extract_tool_parameters(self, reasoning: str, tool: Tool) -> Dict[str, Any]:
        """Extract tool parameters from reasoning."""
        # Simple parameter extraction - would need more sophisticated NLP in production
        params = {}

        # Look for common parameter patterns in reasoning
        if "search" in tool.name.lower() and "query" in reasoning.lower():
            # Extract query parameter
            params["query"] = reasoning.split("query")[-1].strip()[:100]

        return params


class AIAgentFramework:
    """
    Framework for managing and orchestrating AI agents.

    Features:
    - Agent creation and management
    - Tool registration and orchestration
    - Multi-agent collaboration
    - Performance monitoring and optimization
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize AI agent framework.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.AIAgentFramework")

        self.agents: Dict[str, BaseAgent] = {}
        self.available_tools: Dict[str, Tool] = {}
        self.llm_manager = None

    async def initialize(self) -> None:
        """Initialize agent framework."""
        self.logger.info("Initializing AI Agent Framework...")

        # Register built-in tools
        await self._register_builtin_tools()

        self.logger.info(f"Agent framework initialized with {len(self.available_tools)} tools")

    async def _register_builtin_tools(self) -> None:
        """Register built-in tools."""
        # Search tool
        search_tool = Tool(
            name="web_search",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            },
            function=self._web_search,
            safety_level="safe"
        )
        self.register_tool(search_tool)

        # Calculator tool
        calc_tool = Tool(
            name="calculator",
            description="Perform mathematical calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression"}
                },
                "required": ["expression"]
            },
            function=self._calculate,
            safety_level="safe"
        )
        self.register_tool(calc_tool)

        # File operations tool
        file_tool = Tool(
            name="read_file",
            description="Read content from a file",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file"}
                },
                "required": ["file_path"]
            },
            function=self._read_file,
            safety_level="moderate"
        )
        self.register_tool(file_tool)

    async def create_agent(
        self,
        agent_type: str,
        config: AgentConfig,
        tools: Optional[List[str]] = None
    ) -> BaseAgent:
        """
        Create a new agent.

        Args:
            agent_type: Type of agent to create
            config: Agent configuration
            tools: List of tool names to equip the agent with

        Returns:
            Created agent instance
        """
        self.logger.info(f"Creating agent: {config.name} ({agent_type})")

        # Create agent based on type
        if agent_type == "reasoning":
            agent = ReasoningAgent(config, self.config)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Set LLM manager reference
        agent.llm_manager = self.llm_manager

        # Equip with tools
        if tools:
            for tool_name in tools:
                if tool_name in self.available_tools:
                    agent.add_tool(self.available_tools[tool_name])

        # Register agent
        self.agents[config.name] = agent

        self.logger.info(f"Created agent {config.name} with {len(agent.available_tools)} tools")
        return agent

    def register_tool(self, tool: Tool) -> None:
        """Register a tool in the framework."""
        self.available_tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")

    async def execute_task(
        self,
        agent_name: str,
        task: str,
        timeout: Optional[float] = None
    ) -> AgentResult:
        """
        Execute a task using a specific agent.

        Args:
            agent_name: Name of the agent to use
            task: Task description
            timeout: Optional timeout in seconds

        Returns:
            Task execution result
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")

        agent = self.agents[agent_name]
        self.logger.info(f"Executing task with agent {agent_name}: {task}")

        # Execute with timeout if specified
        if timeout:
            try:
                result = await asyncio.wait_for(agent.execute(task), timeout=timeout)
            except asyncio.TimeoutError:
                result = AgentResult(
                    success=False,
                    final_answer="Task timed out",
                    reasoning_trace=["Execution timed out"],
                    tool_calls_made=[],
                    iterations_used=agent.memory.conversation_history[-1].iterations_used if agent.memory.conversation_history else 0,
                    execution_time=timeout,
                    errors=["Timeout exceeded"]
                )
        else:
            result = await agent.execute(task)

        self.logger.info(f"Task completed with success: {result.success}")
        return result

    async def collaborate(
        self,
        agent_names: List[str],
        task: str,
        strategy: str = "sequential"
    ) -> Dict[str, AgentResult]:
        """
        Execute task with multiple agents collaborating.

        Args:
            agent_names: List of agent names to collaborate
            task: Task to execute
            strategy: Collaboration strategy (sequential, parallel, debate)

        Returns:
            Results from all agents
        """
        self.logger.info(f"Starting collaboration on task: {task}")

        results = {}

        if strategy == "parallel":
            # Execute all agents in parallel
            tasks = [
                self.execute_task(agent_name, task)
                for agent_name in agent_names
            ]
            agent_results = await asyncio.gather(*tasks)

            for agent_name, result in zip(agent_names, agent_results):
                results[agent_name] = result

        elif strategy == "sequential":
            # Execute agents sequentially, passing results
            current_task = task

            for agent_name in agent_names:
                result = await self.execute_task(agent_name, current_task)
                results[agent_name] = result

                # Update task with previous result
                if result.success:
                    current_task = f"Previous result: {result.final_answer}\n\nOriginal task: {task}"

        else:
            raise ValueError(f"Unknown collaboration strategy: {strategy}")

        return results

    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents."""
        status = {}
        for name, agent in self.agents.items():
            status[name] = {
                "config": agent.config.dict(),
                "memory_summary": agent.get_memory_summary(),
                "active": True,
            }
        return status

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [
            {
                "name": name,
                "type": type(agent).__name__,
                "role": agent.config.role,
                "tools": list(agent.available_tools.keys()),
            }
            for name, agent in self.agents.items()
        ]

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "safety_level": tool.safety_level,
                "requires_confirmation": tool.requires_confirmation,
            }
            for tool in self.available_tools.values()
        ]

    # Built-in tool implementations
    async def _web_search(self, query: str) -> Dict[str, Any]:
        """Web search tool implementation."""
        # Placeholder - would integrate with actual search API
        return {
            "query": query,
            "results": [
                {"title": f"Result for {query}", "url": f"https://example.com/{query}", "snippet": f"Sample result about {query}"}
            ],
            "total_results": 1
        }

    async def _calculate(self, expression: str) -> Dict[str, Any]:
        """Calculator tool implementation."""
        try:
            # Safe evaluation with limited scope
            allowed_names = {"__builtins__": {}}
            result = eval(expression, allowed_names)
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"expression": expression, "error": str(e)}

    async def _read_file(self, file_path: str) -> Dict[str, Any]:
        """File reading tool implementation."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return {
                "file_path": file_path,
                "content": content[:1000],  # Limit content length
                "truncated": len(content) > 1000
            }
        except Exception as e:
            return {"file_path": file_path, "error": str(e)}

    async def shutdown(self) -> None:
        """Shutdown agent framework."""
        self.logger.info("Shutting down AI Agent Framework...")

        # Clear agents
        for agent in self.agents.values():
            agent.clear_memory()

        self.agents.clear()
        self.available_tools.clear()

        self.logger.info("AI Agent Framework shutdown complete")
