"""Base memory system for agents."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging


class ConversationMemory:
    """Memory for storing conversation history."""

    def __init__(self, max_entries: int = 100):
        """
        Initialize conversation memory.

        Args:
            max_entries: Maximum number of entries to store
        """
        self._conversations: List[Dict[str, Any]] = []
        self._max_entries = max_entries
        self._logger = logging.getLogger(__name__)

    def add_interaction(
        self,
        user_input: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add interaction to memory.

        Args:
            user_input: User's input
            agent_response: Agent's response
            metadata: Additional metadata
        """
        entry = {
            "user_input": user_input,
            "agent_response": agent_response,
            "timestamp": self._get_timestamp(),
            "metadata": metadata or {}
        }

        self._conversations.append(entry)

        # Maintain size limit
        if len(self._conversations) > self._max_entries:
            self._conversations = self._conversations[-self._max_entries:]

    def get_recent_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation context.

        Args:
            limit: Maximum number of entries to return

        Returns:
            Recent conversation entries
        """
        return self._conversations[-limit:]

    def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar past interactions.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            Similar conversation entries
        """
        query_lower = query.lower()
        matches = []

        for entry in self._conversations:
            if (query_lower in entry["user_input"].lower() or
                query_lower in entry["agent_response"].lower()):
                matches.append(entry)

        return matches[-limit:]

    def clear(self):
        """Clear all memory."""
        self._conversations.clear()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


class TaskMemory:
    """Memory for storing task execution history."""

    def __init__(self, max_entries: int = 50):
        """
        Initialize task memory.

        Args:
            max_entries: Maximum number of task entries to store
        """
        self._tasks: List[Dict[str, Any]] = []
        self._max_entries = max_entries
        self._logger = logging.getLogger(__name__)

    def add_task_execution(
        self,
        task_name: str,
        success: bool,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add task execution to memory.

        Args:
            task_name: Name of the executed task
            success: Whether the task succeeded
            input_data: Task input data
            output_data: Task output data
            execution_time: Time taken to execute
            metadata: Additional metadata
        """
        entry = {
            "task_name": task_name,
            "success": success,
            "input_data": input_data,
            "output_data": output_data,
            "execution_time": execution_time,
            "timestamp": self._get_timestamp(),
            "metadata": metadata or {}
        }

        self._tasks.append(entry)

        # Maintain size limit
        if len(self._tasks) > self._max_entries:
            self._tasks = self._tasks[-self._max_entries:]

    def get_task_history(self, task_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get task execution history.

        Args:
            task_name: Filter by specific task name (optional)
            limit: Maximum entries to return

        Returns:
            Task execution history
        """
        tasks = self._tasks
        if task_name:
            tasks = [t for t in tasks if t["task_name"] == task_name]

        return tasks[-limit:]

    def get_success_rate(self, task_name: Optional[str] = None) -> float:
        """
        Get success rate for tasks.

        Args:
            task_name: Filter by specific task name (optional)

        Returns:
            Success rate (0.0 to 1.0)
        """
        tasks = self._tasks
        if task_name:
            tasks = [t for t in tasks if t["task_name"] == task_name]

        if not tasks:
            return 0.0

        successful = sum(1 for t in tasks if t["success"])
        return successful / len(tasks)

    def clear(self):
        """Clear all task memory."""
        self._tasks.clear()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


class BaseMemory(ABC):
    """Base memory system combining conversation and task memory."""

    def __init__(self):
        """Initialize base memory."""
        self._conversation_memory = ConversationMemory()
        self._task_memory = TaskMemory()
        self._logger = logging.getLogger(__name__)

    def add_interaction(
        self,
        user_input: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add conversation interaction to memory.

        Args:
            user_input: User's input
            agent_response: Agent's response
            metadata: Additional metadata
        """
        self._conversation_memory.add_interaction(user_input, agent_response, metadata)

    def add_task_execution(
        self,
        task_name: str,
        success: bool,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add task execution to memory.

        Args:
            task_name: Name of the executed task
            success: Whether the task succeeded
            input_data: Task input data
            output_data: Task output data
            execution_time: Time taken to execute
            metadata: Additional metadata
        """
        self._task_memory.add_task_execution(
            task_name, success, input_data, output_data, execution_time, metadata
        )

    def get_recent_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation context.

        Args:
            limit: Maximum entries to return

        Returns:
            Recent conversation entries
        """
        return self._conversation_memory.get_recent_context(limit)

    def get_task_history(self, task_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get task execution history.

        Args:
            task_name: Filter by specific task name (optional)
            limit: Maximum entries to return

        Returns:
            Task execution history
        """
        return self._task_memory.get_task_history(task_name, limit)

    def get_success_rate(self, task_name: Optional[str] = None) -> float:
        """
        Get success rate for tasks.

        Args:
            task_name: Filter by specific task name (optional)

        Returns:
            Success rate (0.0 to 1.0)
        """
        return self._task_memory.get_success_rate(task_name)

    def search_similar_conversations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar past conversations.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            Similar conversation entries
        """
        return self._conversation_memory.search_similar(query, limit)

    def clear(self):
        """Clear all memory."""
        self._conversation_memory.clear()
        self._task_memory.clear()

