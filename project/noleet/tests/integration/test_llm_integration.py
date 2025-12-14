"""
Integration tests for LLM integration components.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any

from noleet.llm.llm_factory import LLMFactory
from noleet.llm.llm_config import LLMConfig
from noleet.llm.embedder import Embedder


@pytest.mark.integration
class TestLLMIntegration:
    """Integration tests for LLM components working together."""

    @pytest.mark.asyncio
    async def test_llm_factory_and_embedder_integration(self, test_settings):
        """Test LLM factory and embedder working together."""
        # Create config
        config = LLMConfig.from_settings(test_settings)

        # Create mock provider and embedder
        with patch('noleet.llm.providers.openai_llm.OpenAILLMProvider') as mock_provider_class, \
             patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:

            # Mock provider
            mock_provider = MagicMock()
            mock_provider.generate_text = AsyncMock(return_value="Mock response")
            mock_provider_class.return_value = mock_provider

            # Mock embedder
            mock_embedder = MagicMock()
            mock_embedder.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
            mock_embedder_class.return_value = mock_embedder

            # Create components through factory
            provider = LLMFactory.create_provider('openai', config)
            embedder = Embedder.create('openai', config)

            # Test integration - both should work together
            text_response = await provider.generate_text("Test prompt")
            embedding = await embedder.generate_embedding("Test text")

            assert text_response == "Mock response"
            assert len(embedding) == 3

    @pytest.mark.asyncio
    async def test_semantic_search_pipeline(self):
        """Test complete semantic search pipeline integration."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            # Mock embeddings for semantic search
            mock_embedder.generate_embeddings = AsyncMock(return_value=[
                [1.0, 0.0, 0.0],  # Query embedding
                [0.9, 0.1, 0.0],  # High similarity
                [0.0, 1.0, 0.0],  # Low similarity
                [0.8, 0.2, 0.0]   # Medium similarity
            ])

            from noleet.intelligence.semantic_matcher import SemanticMatcher
            matcher = SemanticMatcher(config)

            query = "machine learning"
            candidates = [
                "ML algorithms implementation",
                "database design",
                "advanced ML techniques"
            ]

            results = matcher.semantic_search(query, candidates, top_k=2)

            assert len(results) == 2
            # Should return most similar first
            assert "ML algorithms implementation" in [r['text'] for r in results]

    @pytest.mark.asyncio
    async def test_agent_orchestrator_with_mock_llm(self):
        """Test agent orchestrator with mock LLM integration."""
        from noleet.agents.agent_orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()

        # Create mock agent
        mock_agent = MagicMock()
        mock_agent.name = "test_agent"
        mock_agent.capabilities = ["analysis"]

        # Mock successful execution
        from noleet.agents.base.agent_base import AgentResult
        mock_agent.execute = AsyncMock(return_value=AgentResult(
            success=True,
            data={"analysis": "Mock analysis result"},
            metadata={"execution_time": 0.5}
        ))

        orchestrator.register_agent(mock_agent)

        # Create simple workflow
        workflow_def = {
            "name": "test_workflow",
            "steps": [
                {
                    "agent": "test_agent",
                    "task": "analyze",
                    "outputs": ["result"]
                }
            ]
        }

        workflow_id = orchestrator.create_workflow(workflow_def)

        # Execute workflow
        result = await orchestrator.execute_workflow(workflow_id, {"input": "test"})

        assert result["success"] is True
        assert "result" in result["data"]
        assert result["data"]["result"]["analysis"] == "Mock analysis result"

    def test_config_to_llm_integration(self, test_settings):
        """Test configuration properly integrates with LLM components."""
        # Test that settings can create LLM config
        llm_config = LLMConfig.from_settings(test_settings)

        # Test that config can create providers
        provider = LLMFactory.create_provider('mock', llm_config)
        embedder = Embedder.create('mock', llm_config)

        assert provider is not None
        assert embedder is not None

        # Test provider and embedder work with config
        assert hasattr(provider, 'generate_text')
        assert hasattr(embedder, 'generate_embedding')

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across integrated components."""
        config = LLMConfig()  # No API keys, should use mock

        # Create components
        provider = LLMFactory.create_provider('mock', config)
        embedder = Embedder.create('mock', config)

        # Test that they handle errors gracefully
        try:
            # These should work with mock implementations
            text_result = await provider.generate_text("test")
            embedding_result = await embedder.generate_embedding("test")

            assert text_result is not None
            assert embedding_result is not None

        except Exception as e:
            # If they fail, error should be informative
            assert "mock" in str(e).lower() or "not implemented" in str(e).lower()

    def test_component_initialization_integration(self):
        """Test that all components can be initialized together."""
        # This tests that imports work and basic initialization succeeds
        try:
            from noleet.llm.llm_factory import LLMFactory
            from noleet.llm.embedder import Embedder
            from noleet.agents.agent_orchestrator import AgentOrchestrator
            from noleet.intelligence.semantic_matcher import SemanticMatcher
            from noleet.app.core.config import Settings

            # Test basic instantiation
            settings = Settings()
            llm_config = LLMConfig.from_settings(settings)

            factory = LLMFactory()
            embedder = Embedder.create('mock', llm_config)
            orchestrator = AgentOrchestrator()
            matcher = SemanticMatcher(llm_config)

            # All should be created successfully
            assert factory is not None
            assert embedder is not None
            assert orchestrator is not None
            assert matcher is not None

        except ImportError as e:
            pytest.fail(f"Import error: {e}")
        except Exception as e:
            pytest.fail(f"Initialization error: {e}")

    @pytest.mark.asyncio
    async def test_workflow_with_semantic_matching(self):
        """Test complete workflow from query to semantic matching results."""
        # This simulates the full pipeline: query -> semantic search -> results
        config = LLMConfig()

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            # Mock embeddings for a realistic search scenario
            mock_embedder.generate_embeddings = AsyncMock(return_value=[
                [1.0, 0.0, 0.0, 0.0],  # Query: "data structures"
                [0.9, 0.1, 0.0, 0.0],  # "advanced data structures"
                [0.1, 0.9, 0.0, 0.0],  # "web development"
                [0.8, 0.2, 0.0, 0.0],  # "algorithms and data structures"
                [0.0, 0.0, 1.0, 0.0],  # "machine learning"
            ])

            from noleet.intelligence.semantic_matcher import SemanticMatcher
            matcher = SemanticMatcher(config)

            # Simulate user query and available projects
            user_query = "data structures"
            available_projects = [
                "advanced data structures",
                "web development",
                "algorithms and data structures",
                "machine learning",
                "database design"
            ]

            # Get recommendations
            recommendations = matcher.semantic_search(user_query, available_projects, top_k=3)

            # Should return most relevant projects
            assert len(recommendations) == 3
            recommended_titles = [r['text'] for r in recommendations]

            # Most relevant should be first
            assert "advanced data structures" in recommended_titles
            assert "algorithms and data structures" in recommended_titles

            # Less relevant should be lower
            ml_index = next(i for i, r in enumerate(recommendations) if r['text'] == "machine learning")
            web_index = next(i for i, r in enumerate(recommendations) if r['text'] == "web development")
            assert ml_index > web_index  # ML should be less relevant than web dev for "data structures" query
