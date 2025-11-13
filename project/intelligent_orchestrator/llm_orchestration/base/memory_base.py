"""Abstract base class for memory management."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging


class BaseMemory(ABC):
    """Abstract base class for LLM memory management."""

    def __init__(
        self,
        memory_name: str,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize base memory.

        Args:
            memory_name: Name identifier for the memory
            logger: Optional logger instance
        """
        self._memory_name = memory_name
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(
            f"Initializing memory {memory_name}",
            extra={"memory_name": memory_name}
        )

    @property
    def memory_name(self) -> str:
        """Get memory name."""
        return self._memory_name

    @abstractmethod
    def save(self, key: str, value: Any) -> None:
        """Save value to memory.

        Args:
            key: Memory key
            value: Value to save
        """
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """Load value from memory.

        Args:
            key: Memory key

        Returns:
            Stored value or None if not found
        """
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory by query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching memory entries
        """
        pass

    def _log_save(self, key: str) -> None:
        """Log memory save operation.

        Args:
            key: Memory key
        """
        self._logger.debug(
            f"Memory {self._memory_name} saved key {key}",
            extra={"memory_name": self._memory_name, "key": key}
        )

    def _log_load(self, key: str, found: bool) -> None:
        """Log memory load operation.

        Args:
            key: Memory key
            found: Whether key was found
        """
        self._logger.debug(
            f"Memory {self._memory_name} loaded key {key}, found={found}",
            extra={"memory_name": self._memory_name, "key": key, "found": found}
        )

