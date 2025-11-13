"""Memory for LLM conversations."""

from typing import Any, Dict, List, Optional
import logging

try:
    from langchain.memory import ConversationBufferMemory
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    ConversationBufferMemory = None

from ..base.memory_base import BaseMemory


class ConversationMemory(BaseMemory):
    """Memory for storing LLM conversation history."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize conversation memory.

        Args:
            logger: Optional logger instance
        """
        super().__init__("conversation", logger)
        self._langchain_memory: Optional[Any] = None
        self._conversations: Dict[str, List[Dict[str, str]]] = {}
        self._initialize()

    def _initialize(self) -> None:
        """Initialize LangChain memory if available."""
        if HAS_LANGCHAIN and ConversationBufferMemory:
            try:
                self._langchain_memory = ConversationBufferMemory()
                self._logger.info("LangChain conversation memory initialized")
            except Exception as e:
                self._logger.error(f"Failed to initialize LangChain memory: {e}")

    def save(self, key: str, value: Any) -> None:
        """Save conversation message to memory.

        Args:
            key: Conversation ID
            value: Message dictionary with 'role' and 'content'
        """
        if key not in self._conversations:
            self._conversations[key] = []
        self._conversations[key].append(value)
        self._log_save(key)
        self._logger.debug(f"Saved conversation message: {key}")

    def load(self, key: str) -> Optional[Any]:
        """Load conversation history from memory.

        Args:
            key: Conversation ID

        Returns:
            List of conversation messages or None
        """
        result = self._conversations.get(key)
        found = result is not None
        self._log_load(key, found)
        return result

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search conversations by query.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching conversations
        """
        matches = []
        query_lower = query.lower()
        for conv_id, messages in self._conversations.items():
            for message in messages:
                content = message.get("content", "")
                if query_lower in content.lower():
                    matches.append({
                        "conversation_id": conv_id,
                        "message": message
                    })
                    if len(matches) >= limit:
                        return matches
        return matches

    def get_conversation(self, conv_id: str) -> List[Dict[str, str]]:
        """Get full conversation history.

        Args:
            conv_id: Conversation ID

        Returns:
            List of conversation messages
        """
        return self._conversations.get(conv_id, [])

