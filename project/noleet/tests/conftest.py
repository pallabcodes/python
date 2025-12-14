"""
Pytest configuration and shared fixtures for NoLeet testing.
"""

import asyncio
import os
import tempfile
import pytest
from pathlib import Path
from typing import Dict, Any, Optional, Generator
from unittest.mock import MagicMock, AsyncMock

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from noleet.app.core.config import Settings
from noleet.app.db.base import Base
from noleet.app.db.session import get_db


# Test Database Configuration
@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Create an in-memory SQLite database for testing."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_db_url: str):
    """Create test database engine."""
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False} if "sqlite" in test_db_url else {},
        echo=False
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def override_get_db(test_db_session: Session):
    """Override the get_db dependency for testing."""
    def _get_test_db():
        try:
            yield test_db_session
        finally:
            pass

    return _get_test_db


# Mock LLM Configuration
@pytest.fixture
def mock_openai_response() -> Dict[str, Any]:
    """Mock OpenAI API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "Mock LLM response for testing",
                    "role": "assistant"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@pytest.fixture
def mock_llm_client(mock_openai_response: Dict[str, Any]) -> MagicMock:
    """Mock LLM client for testing."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
    return mock_client


@pytest.fixture
def mock_embedding_response() -> Dict[str, Any]:
    """Mock embedding API response."""
    return {
        "data": [
            {
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5] * 100,  # 500-dimensional vector
                "index": 0
            }
        ],
        "usage": {"total_tokens": 5}
    }


@pytest.fixture
def mock_embedding_client(mock_embedding_response: Dict[str, Any]) -> MagicMock:
    """Mock embedding client for testing."""
    mock_client = MagicMock()
    mock_client.embeddings.create = AsyncMock(return_value=mock_embedding_response)
    return mock_client


# Test Configuration
@pytest.fixture
def test_settings() -> Settings:
    """Test settings with mock configurations."""
    return Settings(
        # Database
        database_url="sqlite:///:memory:",

        # LLM Configuration
        openai_api_key="test-openai-key",
        openai_model="gpt-4",
        ollama_base_url="http://localhost:11434",
        ollama_model="llama2",

        # Security
        secret_key="test-secret-key",
        jwt_secret_key="test-jwt-secret",
        jwt_algorithm="HS256",

        # Application
        debug=True,
        environment="testing",
        cors_origins=["http://localhost:3000"],

        # Colab Detection (mock)
        colab_environment=False,
    )


# Test Data Fixtures
@pytest.fixture
def sample_leetcode_question() -> Dict[str, Any]:
    """Sample LeetCode question data."""
    return {
        "id": "1",
        "title": "Two Sum",
        "titleSlug": "two-sum",
        "content": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        "difficulty": "Easy",
        "tags": ["Array", "Hash Table"],
        "examples": [
            {
                "input": "nums = [2,7,11,15], target = 9",
                "output": "[0,1]",
                "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."
            }
        ],
        "hints": ["Try using a hash table"],
        "constraints": [
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "-10^9 <= target <= 10^9"
        ]
    }


@pytest.fixture
def sample_project_data() -> Dict[str, Any]:
    """Sample project data for testing."""
    return {
        "id": "project-1",
        "title": "Advanced Data Structures Implementation",
        "description": "Implement various advanced data structures with comprehensive testing",
        "topics": ["Trees", "Graphs", "Heaps"],
        "difficulty": "Intermediate",
        "estimated_time": "4-6 weeks",
        "prerequisites": ["Basic DSA", "Python"],
        "learning_objectives": [
            "Master advanced data structures",
            "Understand algorithmic complexity",
            "Implement efficient solutions"
        ],
        "resources": [
            {"title": "CLRS Textbook", "url": "https://example.com/clrs"},
            {"title": "MIT OCW", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/"}
        ]
    }


@pytest.fixture
def sample_user_profile() -> Dict[str, Any]:
    """Sample user profile data."""
    return {
        "user_id": "user-123",
        "experience_level": "Intermediate",
        "preferred_topics": ["Arrays", "Strings", "Dynamic Programming"],
        "completed_projects": ["two-sum", "valid-parentheses"],
        "learning_goals": ["System Design", "Advanced Algorithms"],
        "time_commitment": "10-15 hours/week",
        "preferred_difficulty": "Medium"
    }


@pytest.fixture
def sample_research_paper() -> Dict[str, Any]:
    """Sample research paper data."""
    return {
        "title": "A New Approach to Graph Algorithms",
        "authors": ["Alice Smith", "Bob Johnson"],
        "abstract": "This paper presents a novel approach to solving graph traversal problems...",
        "year": 2023,
        "venue": "ACM Transactions on Algorithms",
        "topics": ["Graph Theory", "Algorithms", "Complexity"],
        "doi": "10.1145/example.doi",
        "url": "https://example.com/paper.pdf",
        "citations": 45
    }


# Async Test Support
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Temporary Directory Fixture
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# Environment Variable Management
@pytest.fixture(autouse=True)
def clean_env():
    """Clean up environment variables before and after tests."""
    # Store original environment
    original_env = dict(os.environ)

    # Clean up test-related environment variables
    test_vars = [
        'OPENAI_API_KEY', 'OLLAMA_BASE_URL', 'DATABASE_URL',
        'SECRET_KEY', 'JWT_SECRET_KEY', 'DEBUG'
    ]

    for var in test_vars:
        os.environ.pop(var, None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Mock Colab Environment
@pytest.fixture
def mock_colab_env(monkeypatch):
    """Mock Google Colab environment."""
    monkeypatch.setattr('noleet.colab.colab_detector.is_running_in_colab', lambda: True)
    monkeypatch.setattr('torch.cuda.is_available', lambda: True)
    monkeypatch.setattr('torch.cuda.device_count', lambda: 1)


# Performance Testing Fixtures
@pytest.fixture
def performance_baseline():
    """Performance baseline data for regression testing."""
    return {
        "llm_response_time": 2.0,  # seconds
        "embedding_generation": 0.5,  # seconds
        "semantic_search": 0.1,  # seconds
        "database_query": 0.05,  # seconds
        "memory_usage": 100,  # MB
    }


# Security Testing Fixtures
@pytest.fixture
def malicious_input():
    """Malicious input data for security testing."""
    return {
        "sql_injection": "'; DROP TABLE users; --",
        "xss_payload": "<script>alert('XSS')</script>",
        "path_traversal": "../../../etc/passwd",
        "command_injection": "; rm -rf /",
        "large_payload": "A" * 1000000,  # 1MB string
    }


@pytest.fixture
def security_headers():
    """Expected security headers for API responses."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubdomains",
        "Content-Security-Policy": "default-src 'self'",
    }
