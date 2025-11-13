"""
LangChain Tools and Toolkits - Custom Tools and Tool Integration.

Demonstrates:
- Custom tool creation
- Tool registration and management
- Tool error handling
- Tool chaining
- Production-grade patterns
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

# LangChain imports (with fallbacks)
try:
    from langchain.tools import BaseTool, Tool
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    class BaseTool:
        def __init__(self, name: str, description: str): pass
        def run(self, query: str): return "Mock result"
    
    class Tool(BaseTool): pass

logger = logging.getLogger(__name__)


class CustomTool(BaseTool):
    """Custom tool implementation following production standards."""
    
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


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._logger = logging.getLogger(f"{__name__}.ToolRegistry")
    
    def register(self, tool: BaseTool):
        """Register a tool."""
        self.tools[tool.name] = tool
        self._logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self.tools.values())

