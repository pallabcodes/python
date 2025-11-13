"""Memory for optimization history."""

from typing import Any, Dict, List, Optional
import logging

try:
    from langchain.memory import ConversationBufferMemory
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    ConversationBufferMemory = None

from ..base.memory_base import BaseMemory


class OptimizationMemory(BaseMemory):
    """Memory for storing optimization history."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize optimization memory.

        Args:
            logger: Optional logger instance
        """
        super().__init__("optimization", logger)
        self._storage: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []

    def save(self, key: str, value: Any) -> None:
        """Save optimization result to memory.

        Args:
            key: Memory key (e.g., workload_id)
            value: Optimization result to save
        """
        self._storage[key] = value
        self._history.append({"key": key, "value": value})
        self._log_save(key)
        self._logger.info(f"Saved optimization result: {key}")

    def load(self, key: str) -> Optional[Any]:
        """Load optimization result from memory.

        Args:
            key: Memory key

        Returns:
            Stored optimization result or None
        """
        result = self._storage.get(key)
        found = result is not None
        self._log_load(key, found)
        return result

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search optimization history by query.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching optimization results
        """
        matches = []
        query_lower = query.lower()
        for entry in self._history:
            key = entry.get("key", "")
            if query_lower in key.lower():
                matches.append(entry)
                if len(matches) >= limit:
                    break
        return matches

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get optimization history.

        Args:
            limit: Maximum number of entries (None for all)

        Returns:
            List of optimization history entries
        """
        if limit is None:
            return self._history
        return self._history[-limit:]

