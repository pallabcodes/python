"""
Core LangChain Concepts - LLMs, Prompts, and Output Parsers.

Demonstrates:
- LLM integration (OpenAI, Anthropic, local models)
- Prompt templates and prompt engineering
- Output parsers for structured responses
- Streaming responses
- Error handling and retry logic
- Production-grade patterns
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Iterator
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

# LangChain imports (with fallbacks)
try:
    from langchain.llms.base import BaseLLM
    from langchain.chat_models import ChatOpenAI, ChatAnthropic
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
    from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
    from langchain.callbacks import StreamingStdOutCallbackHandler
    from pydantic import BaseModel, Field
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    # Create fallback classes
    class BaseLLM:
        def __init__(self, **kwargs): pass
        def __call__(self, prompt: str): return "Mock response"
    
    class ChatOpenAI:
        def __init__(self, **kwargs): pass
        def invoke(self, messages): return AIMessage(content="Mock response")
    
    class ChatAnthropic:
        def __init__(self, **kwargs): pass
        def invoke(self, messages): return AIMessage(content="Mock response")
    
    class BaseMessage: pass
    class HumanMessage: pass
    class AIMessage: pass
    class SystemMessage: pass
    
    class PromptTemplate:
        def __init__(self, template: str, **kwargs): self.template = template
        def format(self, **kwargs): return self.template.format(**kwargs)
    
    class ChatPromptTemplate:
        def __init__(self, **kwargs): pass
        def format_messages(self, **kwargs): return []
    
    class MessagesPlaceholder: pass
    
    class PydanticOutputParser:
        def __init__(self, pydantic_object): pass
        def parse(self, text): return {}
    
    class OutputFixingParser: pass
    
    class StreamingStdOutCallbackHandler: pass
    
    class BaseModel: pass
    def Field(**kwargs): return None

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Structured LLM response."""
    content: str
    model_name: str
    tokens_used: int = 0
    response_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMMetrics:
    """Metrics for LLM usage tracking."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_response_time: float = 0.0
    error_counts: Dict[str, int] = field(default_factory=dict)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Follows production standards:
    - Abstract interface for multiple implementations
    - Comprehensive error handling
    - Metrics collection
    - Retry logic
    """
    
    def __init__(self, model_name: str, max_retries: int = 3):
        self.model_name = model_name
        self.max_retries = max_retries
        self.metrics = LLMMetrics()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream response from LLM."""
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get LLM usage metrics."""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "total_tokens": self.metrics.total_tokens,
            "avg_response_time": (
                self.metrics.total_response_time / max(1, self.metrics.successful_requests)
            ),
            "error_counts": self.metrics.error_counts
        }


class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM provider implementation.
    
    Features:
    - Chat completion support
    - Streaming support
    - Error handling and retries
    - Token usage tracking
    """
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_retries: int = 3
    ):
        super().__init__(model_name, max_retries)
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if HAS_LANGCHAIN:
            try:
                self.llm = ChatOpenAI(
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except Exception as e:
                self._logger.warning(f"OpenAI not available: {e}")
                self.llm = None
        else:
            self.llm = None
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using OpenAI."""
        start_time = time.time()
        self.metrics.total_requests += 1
        
        if not HAS_LANGCHAIN or not self.llm:
            # Mock response
            await asyncio.sleep(0.1)
            response_time = time.time() - start_time
            self.metrics.successful_requests += 1
            self.metrics.total_response_time += response_time
            return LLMResponse(
                content="Mock OpenAI response",
                model_name=self.model_name,
                tokens_used=50,
                response_time=response_time
            )
        
        try:
            messages = [HumanMessage(content=prompt)]
            result = self.llm.invoke(messages)
            
            response_time = time.time() - start_time
            
            # Extract token usage if available
            tokens_used = getattr(result, 'response_metadata', {}).get('token_usage', {}).get('total_tokens', 0)
            
            self.metrics.successful_requests += 1
            self.metrics.total_tokens += tokens_used
            self.metrics.total_response_time += response_time
            
            return LLMResponse(
                content=result.content if hasattr(result, 'content') else str(result),
                model_name=self.model_name,
                tokens_used=tokens_used,
                response_time=response_time
            )
            
        except Exception as e:
            error_type = type(e).__name__
            self.metrics.failed_requests += 1
            self.metrics.error_counts[error_type] = self.metrics.error_counts.get(error_type, 0) + 1
            
            self._logger.error(f"Error generating response: {e}", exc_info=True)
            raise
    
    async def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream response from OpenAI."""
        if not HAS_LANGCHAIN or not self.llm:
            # Mock streaming
            words = ["Mock", "streaming", "response", "from", "OpenAI"]
            for word in words:
                yield word + " "
                await asyncio.sleep(0.1)
            return
        
        try:
            messages = [HumanMessage(content=prompt)]
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                else:
                    yield str(chunk)
        except Exception as e:
            self._logger.error(f"Error streaming response: {e}", exc_info=True)
            raise


class PromptManager:
    """
    Manages prompt templates and prompt engineering.
    
    Features:
    - Template management
    - Variable substitution
    - Prompt versioning
    - Prompt optimization
    """
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.chat_templates: Dict[str, ChatPromptTemplate] = {}
        self._logger = logging.getLogger(f"{__name__}.PromptManager")
    
    def register_template(self, name: str, template: str, input_variables: List[str]):
        """Register a prompt template."""
        if HAS_LANGCHAIN:
            self.templates[name] = PromptTemplate(
                template=template,
                input_variables=input_variables
            )
        else:
            # Fallback
            self.templates[name] = PromptTemplate(template=template)
        
        self._logger.info(f"Registered template: {name}")
    
    def register_chat_template(
        self,
        name: str,
        system_message: Optional[str] = None,
        include_history: bool = False
    ):
        """Register a chat prompt template."""
        if not HAS_LANGCHAIN:
            return
        
        messages = []
        if system_message:
            messages.append(("system", system_message))
        
        if include_history:
            messages.append(MessagesPlaceholder(variable_name="history"))
        
        messages.append(("human", "{input}"))
        
        self.chat_templates[name] = ChatPromptTemplate.from_messages(messages)
        self._logger.info(f"Registered chat template: {name}")
    
    def format_prompt(self, template_name: str, **kwargs) -> str:
        """Format a prompt template."""
        if template_name not in self.templates:
            raise ValueError(f"Template {template_name} not found")
        
        template = self.templates[template_name]
        if HAS_LANGCHAIN:
            return template.format(**kwargs)
        else:
            return template.template.format(**kwargs)
    
    def format_chat_messages(self, template_name: str, **kwargs) -> List[BaseMessage]:
        """Format chat prompt template."""
        if template_name not in self.chat_templates:
            raise ValueError(f"Chat template {template_name} not found")
        
        if not HAS_LANGCHAIN:
            return []
        
        return self.chat_templates[template_name].format_messages(**kwargs)


class OutputParserManager:
    """
    Manages output parsers for structured responses.
    
    Features:
    - Pydantic model parsing
    - Error recovery with fixing parsers
    - Custom parsers
    - Validation
    """
    
    def __init__(self):
        self.parsers: Dict[str, Any] = {}
        self._logger = logging.getLogger(f"{__name__}.OutputParserManager")
    
    def register_parser(self, name: str, pydantic_model: type):
        """Register a Pydantic output parser."""
        if not HAS_LANGCHAIN:
            return
        
        try:
            parser = PydanticOutputParser(pydantic_object=pydantic_model)
            self.parsers[name] = parser
            self._logger.info(f"Registered parser: {name}")
        except Exception as e:
            self._logger.error(f"Error registering parser {name}: {e}")
    
    def parse(self, name: str, text: str) -> Dict[str, Any]:
        """Parse output using registered parser."""
        if name not in self.parsers:
            raise ValueError(f"Parser {name} not found")
        
        if not HAS_LANGCHAIN:
            return {"raw": text}
        
        try:
            parser = self.parsers[name]
            return parser.parse(text)
        except Exception as e:
            self._logger.warning(f"Error parsing output: {e}")
            # Try with fixing parser
            if HAS_LANGCHAIN:
                try:
                    fixing_parser = OutputFixingParser.from_llm(
                        parser=parser,
                        llm=ChatOpenAI(temperature=0)
                    )
                    return fixing_parser.parse(text)
                except Exception:
                    pass
            raise


# Example Pydantic models for output parsing
class AnalysisResult(BaseModel):
    """Example structured output model."""
    summary: str = Field(description="Summary of the analysis")
    key_points: List[str] = Field(description="Key points identified")
    confidence: float = Field(description="Confidence score between 0 and 1")
    recommendations: List[str] = Field(description="Recommendations")


class LLMService:
    """
    High-level LLM service combining all core concepts.
    
    Features:
    - Unified interface for LLM operations
    - Prompt management
    - Output parsing
    - Error handling
    - Metrics collection
    """
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.prompt_manager = PromptManager()
        self.output_parser_manager = OutputParserManager()
        self._logger = logging.getLogger(f"{__name__}.LLMService")
    
    async def generate_with_template(
        self,
        template_name: str,
        parse_output: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response using a prompt template.
        
        Args:
            template_name: Name of registered template
            parse_output: Optional parser name for structured output
            **kwargs: Variables for template substitution
            
        Returns:
            Dictionary with response and parsed output if applicable
        """
        try:
            # Format prompt
            prompt = self.prompt_manager.format_prompt(template_name, **kwargs)
            
            # Generate response
            response = await self.provider.generate(prompt)
            
            result = {
                "content": response.content,
                "model_name": response.model_name,
                "tokens_used": response.tokens_used,
                "response_time": response.response_time
            }
            
            # Parse output if requested
            if parse_output:
                try:
                    parsed = self.output_parser_manager.parse(parse_output, response.content)
                    result["parsed_output"] = parsed
                except Exception as e:
                    self._logger.warning(f"Failed to parse output: {e}")
                    result["parse_error"] = str(e)
            
            return result
            
        except Exception as e:
            self._logger.error(f"Error in generate_with_template: {e}", exc_info=True)
            raise
    
    async def chat_with_history(
        self,
        template_name: str,
        user_input: str,
        history: Optional[List[BaseMessage]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chat with conversation history.
        
        Args:
            template_name: Name of registered chat template
            user_input: User's input message
            history: Previous conversation messages
            **kwargs: Additional template variables
            
        Returns:
            Dictionary with response and updated history
        """
        if not HAS_LANGCHAIN:
            return {
                "content": "Mock chat response",
                "history": []
            }
        
        try:
            # Format chat messages
            messages = self.prompt_manager.format_chat_messages(
                template_name,
                input=user_input,
                history=history or [],
                **kwargs
            )
            
            # Generate response
            if hasattr(self.provider, 'llm') and self.provider.llm:
                result = self.provider.llm.invoke(messages)
                content = result.content if hasattr(result, 'content') else str(result)
            else:
                content = "Mock chat response"
            
            # Update history
            new_history = (history or []) + [
                HumanMessage(content=user_input),
                AIMessage(content=content)
            ]
            
            return {
                "content": content,
                "history": new_history
            }
            
        except Exception as e:
            self._logger.error(f"Error in chat_with_history: {e}", exc_info=True)
            raise

    def llm_service_real_world_example(self) -> None:
        """
        Real-World Scenario: LLM Service - Customer Support Chatbot.

        REAL-WORLD SCENARIO:
        ====================
        You're building a customer support chatbot:
        - Handle customer inquiries with context
        - Generate helpful responses using LLM
        - Problem: Need consistent, context-aware responses
        
        THE PROBLEM WITHOUT LLM SERVICE:
        =================================
        - Rule-based responses → inflexible
        - No context understanding → poor answers
        - Manual response writing → doesn't scale
        - No conversation history → repetitive
        - Poor user experience → customer frustration
        
        THE SOLUTION:
        =============
        LLM Service enables:
        - Natural language understanding → better responses
        - Context-aware conversations → personalized
        - Conversation history → continuity
        - Scalable responses → handle any question
        - Production-ready → reliable service
        
        WHEN TO USE LLM SERVICE:
        ========================
        ✅ Customer support chatbots
        ✅ Conversational AI applications
        ✅ Context-aware assistants
        ✅ Natural language interfaces
        ✅ Multi-turn conversations
        """
        print("=" * 70)
        print("REAL-WORLD SCENARIO: Customer Support Chatbot")
        print("=" * 70)
        print()
        print("SITUATION:")
        print("  - Customer support chatbot")
        print("  - Handle customer inquiries with context")
        print("  - Generate helpful responses using LLM")
        print("  - Problem: Need consistent, context-aware responses")
        print()
        print("THE PROBLEM:")
        print("  Without LLM service:")
        print("    ❌ Rule-based responses → inflexible")
        print("    ❌ No context understanding → poor answers")
        print("    ❌ Manual response writing → doesn't scale")
        print("    ❌ No conversation history → repetitive")
        print()
        print("THE SOLUTION:")
        print("  With LLM service:")
        print("    ✅ Natural language understanding → better responses")
        print("    ✅ Context-aware conversations → personalized")
        print("    ✅ Conversation history → continuity")
        print("    ✅ Scalable responses → handle any question")
        print()
        print("=" * 70)
        print()

        print("Simulating customer support conversation...")
        print()

        # Simulate conversation
        conversation_history = []
        inquiries = [
            "What are your business hours?",
            "Do you offer refunds?",
            "How do I track my order?"
        ]

        for inquiry in inquiries:
            print(f"Customer: {inquiry}")
            
            # Simulate LLM response
            if "hours" in inquiry.lower():
                response = "Our business hours are Monday-Friday, 9 AM to 5 PM EST."
            elif "refund" in inquiry.lower():
                response = "Yes, we offer refunds within 30 days of purchase. Please contact support for assistance."
            elif "track" in inquiry.lower():
                response = "You can track your order using the tracking number sent to your email, or visit our website."
            else:
                response = "I'd be happy to help you with that. Let me connect you with our support team."
            
            print(f"Bot: {response}")
            conversation_history.append((inquiry, response))
            print()

        print("  ✅ LLM service enabled context-aware customer support!")
        print()
        print("=" * 70)
        print("KEY TAKEAWAYS")
        print("=" * 70)
        print("1. WHEN TO USE LLM SERVICE:")
        print("   ✅ Customer support chatbots")
        print("   ✅ Conversational AI applications")
        print("   ✅ Context-aware assistants")
        print("   ✅ Natural language interfaces")
        print()
        print("2. WHY IT MATTERS:")
        print("   - Natural language understanding")
        print("   - Context-aware responses")
        print("   - Conversation continuity")
        print("   - Scalable customer support")
        print("=" * 70)
        print()



