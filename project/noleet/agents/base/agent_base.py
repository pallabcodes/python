"""Base agent class with LangChain integration."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
import logging
from dataclasses import dataclass, field

from ...llm.llm_factory import LLMFactory
from ...llm.llm_config import LLMConfig


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool:
    """Base class for agent tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool."""
        pass

    def to_langchain_tool(self) -> Any:
        """Convert to LangChain tool format."""
        try:
            from langchain.tools import Tool
            return Tool(
                name=self.name,
                description=self.description,
                func=self.execute
            )
        except ImportError:
            return None


class BaseMemory:
    """Base class for agent memory."""

    def __init__(self):
        self._conversations: List[Dict[str, Any]] = []
        self._max_history = 100

    def add_interaction(self, user_input: str, agent_response: str, metadata: Optional[Dict] = None):
        """Add interaction to memory."""
        self._conversations.append({
            "user_input": user_input,
            "agent_response": agent_response,
            "timestamp": self._get_timestamp(),
            "metadata": metadata or {}
        })

        # Keep only recent conversations
        if len(self._conversations) > self._max_history:
            self._conversations = self._conversations[-self._max_history:]

    def get_recent_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation context."""
        return self._conversations[-limit:]

    def clear(self):
        """Clear memory."""
        self._conversations.clear()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


class BaseAgent(ABC):
    """Base agent class with LangChain integration."""

    def __init__(
        self,
        agent_type: str,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize base agent.

        Args:
            agent_type: Type of agent (e.g., 'recommendation', 'analysis')
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        self._agent_type = agent_type
        self._llm_config = llm_config or LLMConfig()
        self._llm_factory = LLMFactory(self._llm_config, logger)
        self._logger = logger or logging.getLogger(f"{__name__}.{agent_type}")
        self._memory = BaseMemory()
        self._tools: List[BaseTool] = []

        # LangChain components
        self._llm = None
        self._agent_executor = None

        self._initialize()

    def _initialize(self):
        """Initialize agent components."""
        try:
            self._llm = self._llm_factory.create_llm()
            self._setup_tools()
            self._setup_langchain_agent()
            self._logger.info(f"{self._agent_type} agent initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize agent: {e}")

    def _setup_tools(self):
        """Setup agent tools. Override in subclasses."""
        pass

    def _setup_langchain_agent(self):
        """Setup LangChain agent executor."""
        try:
            from langchain.agents import initialize_agent, AgentType

            langchain_tools = []
            for tool in self._tools:
                lc_tool = tool.to_langchain_tool()
                if lc_tool:
                    langchain_tools.append(lc_tool)

            if self._llm and hasattr(self._llm, 'generate'):
                # Convert our LLM to LangChain format if needed
                from langchain.llms.base import BaseLLM
                if not isinstance(self._llm, BaseLLM):
                    # Create a wrapper
                    self._llm = self._create_langchain_llm_wrapper()

                if langchain_tools:
                    self._agent_executor = initialize_agent(
                        tools=langchain_tools,
                        llm=self._llm,
                        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                        verbose=True
                    )
        except ImportError:
            self._logger.warning("LangChain not available, using direct LLM calls")

    def _create_langchain_llm_wrapper(self):
        """Create LangChain LLM wrapper for our LLM."""
        try:
            from langchain.llms.base import BaseLLM
            from langchain.schema import LLMResult, Generation

            class LLMWrapper(BaseLLM):
                def __init__(self, llm):
                    super().__init__()
                    self._llm = llm

                @property
                def _llm_type(self):
                    return "custom"

                def _generate(self, prompts, stop=None):
                    generations = []
                    for prompt in prompts:
                        response = self._llm.generate(prompt)
                        generations.append(Generation(text=response))
                    return LLMResult(generations=generations)

            return LLMWrapper(self._llm)
        except ImportError:
            return None

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute agent logic.

        Args:
            input_data: Input data for agent

        Returns:
            Agent execution result
        """
        pass

    def _add_to_memory(self, user_input: str, response: str, metadata: Optional[Dict] = None):
        """Add interaction to memory."""
        self._memory.add_interaction(user_input, response, metadata)

    def get_memory_context(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent memory context."""
        return self._memory.get_recent_context(limit)

    def clear_memory(self):
        """Clear agent memory."""
        self._memory.clear()

    def is_available(self) -> bool:
        """Check if agent is available for use."""
        return self._llm is not None and self._llm.is_available()

    @property
    def agent_type(self) -> str:
        """Get agent type."""
        return self._agent_type

