"""Pytest configuration and fixtures for DocuMind."""

import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/documind_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for fast testing
    test_db_url = "sqlite+aiosqlite:///:memory:"

    engine = create_async_engine(
        test_db_url,
        echo=False,
        future=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_factory = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        try:
            yield session
            await session.rollback()  # Rollback changes after test
        finally:
            await session.close()


@pytest.fixture
def test_settings():
    """Test settings fixture."""
    return Settings(
        DEBUG=True,
        SECRET_KEY="test_secret_key_for_testing_only",
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
    )


@pytest.fixture
def sample_repository_data():
    """Sample repository data for testing."""
    return {
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "description": "A test repository",
        "url": "https://github.com/testuser/test-repo",
        "clone_url": "https://github.com/testuser/test-repo.git",
        "platform": "github",
        "owner": "testuser",
        "language": "python",
        "is_active": True,
        "analysis_enabled": True,
    }


@pytest.fixture
def sample_code_entity_data():
    """Sample code entity data for testing."""
    return {
        "entity_type": "function",
        "name": "calculate_total",
        "qualified_name": "utils.calculate_total",
        "file_path": "utils.py",
        "start_line": 10,
        "end_line": 20,
        "language": "python",
        "complexity_score": 3.0,
        "parameter_count": 2,
        "source_code": "def calculate_total(a, b):\n    return a + b",
        "signature": "def calculate_total(a, b)",
    }


@pytest.fixture
def sample_documentation_data():
    """Sample documentation data for testing."""
    return {
        "title": "calculate_total function",
        "content": "# calculate_total\n\nCalculates the total of two numbers.",
        "summary": "Calculates the total of two numbers",
        "doc_type": "api",
        "format": "markdown",
        "language": "python",
        "generated_by": "ai",
        "generation_model": "gpt-4",
        "quality_score": 0.9,
        "status": "published",
        "is_auto_generated": "True",
    }
