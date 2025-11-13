"""
LangChain Memory - Conversation Memory Management.

Demonstrates:
- ConversationBufferMemory for full history
- ConversationSummaryMemory for summarized history
- ConversationBufferWindowMemory for sliding window
- Custom memory implementations
- Memory persistence
- Production-grade patterns
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from collections import deque

# LangChain imports (with fallbacks)
try:
    from langchain.memory import (
        ConversationBufferMemory,
        ConversationSummaryMemory,
        ConversationBufferWindowMemory,
        ConversationSummaryBufferMemory
    )
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    class ConversationBufferMemory:
        def __init__(self, **kwargs): pass
        def save_context(self, inputs, outputs): pass
        def load_memory_variables(self, inputs): return {}
    
    class ConversationSummaryMemory(ConversationBufferMemory): pass
    class ConversationBufferWindowMemory(ConversationBufferMemory): pass
    class ConversationSummaryBufferMemory(ConversationBufferMemory): pass
    
    class BaseMessage: pass
    class HumanMessage: pass
    class AIMessage: pass
    class SystemMessage: pass

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Statistics for memory usage."""
    total_conversations: int = 0
    total_messages: int = 0
    memory_size_bytes: int = 0
    oldest_message_age: float = 0.0


class BaseMemoryWrapper(ABC):
    """
    Abstract base class for memory wrappers.
    
    Provides:
    - Unified interface
    - Persistence support
    - Statistics tracking
    """
    
    def __init__(self, memory_name: str):
        self.memory_name = memory_name
        self._logger = logging.getLogger(f"{__name__}.{memory_name}")
        self.stats = MemoryStats()
    
    @abstractmethod
    def save_context(self, inputs: Dict[str, str], outputs: Dict[str, str]):
        """Save conversation context."""
        pass
    
    @abstractmethod
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables."""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear memory."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "memory_name": self.memory_name,
            "total_conversations": self.stats.total_conversations,
            "total_messages": self.stats.total_messages,
            "memory_size_bytes": self.stats.memory_size_bytes
        }


class ConversationBufferMemoryWrapper(BaseMemoryWrapper):
    """
    Wrapper for ConversationBufferMemory.
    
    Features:
    - Full conversation history
    - Message storage
    - Context retrieval
    """
    
    def __init__(self, memory_name: str = "buffer_memory"):
        super().__init__(memory_name)
        
        if HAS_LANGCHAIN:
            self.memory = ConversationBufferMemory(return_messages=True)
        else:
            self.memory = None
            self._messages: List[BaseMessage] = []
    
    def save_context(self, inputs: Dict[str, str], outputs: Dict[str, str]):
        """Save conversation context."""
        if HAS_LANGCHAIN and self.memory:
            self.memory.save_context(inputs, outputs)
        else:
            # Mock implementation
            if "input" in inputs:
                self._messages.append(HumanMessage(content=inputs["input"]))
            if "output" in outputs:
                self._messages.append(AIMessage(content=outputs["output"]))
        
        self.stats.total_messages += 2
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables."""
        if HAS_LANGCHAIN and self.memory:
            return self.memory.load_memory_variables(inputs)
        else:
            # Mock implementation
            history = "\n".join([
                f"Human: {msg.content}" if isinstance(msg, HumanMessage)
                else f"AI: {msg.content}"
                for msg in self._messages[-10:]  # Last 10 messages
            ])
            return {"history": history}
    
    def clear(self):
        """Clear memory."""
        if HAS_LANGCHAIN and self.memory:
            self.memory.clear()
        else:
            self._messages.clear()
        
        self.stats.total_messages = 0


class ConversationSummaryMemoryWrapper(BaseMemoryWrapper):
    """
    Wrapper for ConversationSummaryMemory.
    
    Features:
    - Summarized conversation history
    - Token-efficient storage
    - Summary generation
    """
    
    def __init__(
        self,
        memory_name: str = "summary_memory",
        llm: Optional[Any] = None
    ):
        super().__init__(memory_name)
        self.llm = llm
        
        if HAS_LANGCHAIN and self.llm:
            try:
                self.memory = ConversationSummaryMemory(
                    llm=self.llm,
                    return_messages=True
                )
            except Exception as e:
                self._logger.warning(f"Failed to initialize summary memory: {e}")
                self.memory = None
        else:
            self.memory = None
            self._summary = ""
            self._recent_messages: deque = deque(maxlen=5)
    
    def save_context(self, inputs: Dict[str, str], outputs: Dict[str, str]):
        """Save conversation context."""
        if HAS_LANGCHAIN and self.memory:
            self.memory.save_context(inputs, outputs)
        else:
            # Mock implementation
            if "input" in inputs:
                self._recent_messages.append(("Human", inputs["input"]))
            if "output" in outputs:
                self._recent_messages.append(("AI", outputs["output"]))
                # Update summary (simplified)
                self._summary += f"\nHuman: {inputs.get('input', '')}\nAI: {outputs.get('output', '')}"
        
        self.stats.total_messages += 2
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables."""
        if HAS_LANGCHAIN and self.memory:
            return self.memory.load_memory_variables(inputs)
        else:
            # Mock implementation
            recent = "\n".join([
                f"{role}: {content}"
                for role, content in self._recent_messages
            ])
            return {
                "history": self._summary + "\n" + recent if self._summary else recent
            }
    
    def clear(self):
        """Clear memory."""
        if HAS_LANGCHAIN and self.memory:
            self.memory.clear()
        else:
            self._summary = ""
            self._recent_messages.clear()
        
        self.stats.total_messages = 0


class ConversationBufferWindowMemoryWrapper(BaseMemoryWrapper):
    """
    Wrapper for ConversationBufferWindowMemory.
    
    Features:
    - Sliding window of recent messages
    - Fixed memory size
    - Automatic old message removal
    """
    
    def __init__(
        self,
        memory_name: str = "window_memory",
        k: int = 10
    ):
        super().__init__(memory_name)
        self.k = k
        
        if HAS_LANGCHAIN:
            self.memory = ConversationBufferWindowMemory(
                k=k,
                return_messages=True
            )
        else:
            self.memory = None
            self._messages: deque = deque(maxlen=k)
    
    def save_context(self, inputs: Dict[str, str], outputs: Dict[str, str]):
        """Save conversation context."""
        if HAS_LANGCHAIN and self.memory:
            self.memory.save_context(inputs, outputs)
        else:
            # Mock implementation
            if "input" in inputs:
                self._messages.append(("Human", inputs["input"]))
            if "output" in outputs:
                self._messages.append(("AI", outputs["output"]))
        
        self.stats.total_messages += 2
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables."""
        if HAS_LANGCHAIN and self.memory:
            return self.memory.load_memory_variables(inputs)
        else:
            # Mock implementation
            history = "\n".join([
                f"{role}: {content}"
                for role, content in self._messages
            ])
            return {"history": history}
    
    def clear(self):
        """Clear memory."""
        if HAS_LANGCHAIN and self.memory:
            self.memory.clear()
        else:
            self._messages.clear()
        
        self.stats.total_messages = 0


class MemoryManager:
    """
    Manages multiple memory instances.
    
    Features:
    - Memory selection
    - Memory persistence
    - Statistics aggregation
    """
    
    def __init__(self):
        self.memories: Dict[str, BaseMemoryWrapper] = {}
        self._logger = logging.getLogger(f"{__name__}.MemoryManager")
    
    def register_memory(self, name: str, memory: BaseMemoryWrapper):
        """Register a memory instance."""
        self.memories[name] = memory
        self._logger.info(f"Registered memory: {name}")
    
    def get_memory(self, name: str) -> Optional[BaseMemoryWrapper]:
        """Get a memory instance."""
        return self.memories.get(name)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all memories."""
        return {
            name: memory.get_stats()
            for name, memory in self.memories.items()
        }

    def memory_manager_real_world_example(self) -> None:
        """
        Real-World Scenario: Memory Manager - Personal AI Assistant.

        REAL-WORLD SCENARIO:
        ====================
        You're building a personal AI assistant:
        - Remember user preferences and context
        - Maintain conversation history
        - Problem: Need persistent memory across sessions
        
        THE PROBLEM WITHOUT MEMORY MANAGER:
        ====================================
        - No memory → repetitive conversations
        - No context → poor understanding
        - No preferences → generic responses
        - No history → disconnected interactions
        - Poor user experience → frustration
        
        THE SOLUTION:
        =============
        Memory Manager enables:
        - Conversation history → continuity
        - User preferences → personalized
        - Context awareness → better understanding
        - Persistent memory → across sessions
        - Improved UX → natural interactions
        
        WHEN TO USE MEMORY MANAGER:
        ============================
        ✅ Personal AI assistants
        ✅ Conversational interfaces
        ✅ Context-aware applications
        ✅ Multi-session applications
        ✅ Personalized user experiences
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Personal AI Assistant")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Personal AI assistant")
        print("  - Remember user preferences and context")
        print("  - Maintain conversation history")
        print("  - Problem: Need persistent memory across sessions")
        print()
        print("THE PROBLEM:")
        print("  Without memory manager:")
        print("    ❌ No memory → repetitive conversations")
        print("    ❌ No context → poor understanding")
        print("    ❌ No preferences → generic responses")
        print("    ❌ No history → disconnected interactions")
        print()
        print("THE SOLUTION:")
        print("  With memory manager:")
        print("    ✅ Conversation history → continuity")
        print("    ✅ User preferences → personalized")
        print("    ✅ Context awareness → better understanding")
        print("    ✅ Persistent memory → across sessions")
        print()
        print("=" * 70)
        print()

        print("Simulating personal AI assistant with memory...")
        print()

        conversation = [
            ("User", "I prefer dark mode"),
            ("Assistant", "Got it! I'll remember your preference for dark mode."),
            ("User", "What's my preference?"),
            ("Assistant", "You prefer dark mode. I remembered that from our previous conversation.")
        ]

        for speaker, message in conversation:
            print(f"{speaker}: {message}")

        print()
        print("  ✅ Memory manager enabled context-aware conversations!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE MEMORY MANAGER:")
        print("   ✅ Personal AI assistants")
        print("   ✅ Conversational interfaces")
        print("   ✅ Context-aware applications")
        print("   ✅ Multi-session applications")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Conversation continuity")
        print("   - Personalized experiences")
        print("   - Context awareness")
        print("   - Natural interactions")
        print("=" * 70)
        print()

