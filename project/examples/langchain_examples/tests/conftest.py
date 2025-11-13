"""Pytest configuration and fixtures for LangChain examples tests."""

import pytest
import asyncio
from typing import Callable, Any
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_factory():
    """Create mock LLM factory."""
    def factory():
        llm = Mock()
        llm.invoke = AsyncMock(return_value="Mock LLM response")
        llm.generate = AsyncMock(return_value=Mock(generations=[[Mock(text="Mock response")]]))
        return llm
    return factory


@pytest.fixture
def mock_async_llm_factory():
    """Create async mock LLM factory."""
    async def factory():
        llm = Mock()
        llm.invoke = AsyncMock(return_value="Mock LLM response")
        llm.generate = AsyncMock(return_value=Mock(generations=[[Mock(text="Mock response")]]))
        return llm
    return factory

