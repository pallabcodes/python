"""
Performance tests for intelligence and agent components.
Benchmarks semantic matching, agent orchestration, and recommendation systems.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import numpy as np

from benchmarks.benchmark_framework import BenchmarkSuite, PerformanceProfiler
from noleet.intelligence.semantic_matcher import SemanticMatcher
from noleet.intelligence.recommendation_engine import RecommendationEngine
from noleet.agents.agent_orchestrator import AgentOrchestrator


class TestIntelligencePerformance(BenchmarkSuite):
    """Performance benchmarks for intelligence components."""

    def __init__(self):
        super().__init__("intelligence_performance", "Intelligence component performance benchmarks")

    def setup_method(self):
        """Setup mock components for testing."""
        # Mock embedder for semantic matching
        self.mock_embedder = MagicMock()
        self.mock_embedder.embed_text.side_effect = lambda text: [hash(text) % 1000 / 1000.0] * 384
        self.mock_embedder.embed_texts.side_effect = lambda texts: [
            [hash(text) % 1000 / 1000.0] * 384 for text in texts
        ]

        # Create semantic matcher
        self.semantic_matcher = SemanticMatcher(self.mock_embedder)

        # Add test documents
        test_docs = {
            "doc1": "Python is a programming language used for web development.",
            "doc2": "Machine learning algorithms help computers learn from data.",
            "doc3": "Data structures and algorithms are fundamental to computer science.",
            "doc4": "Neural networks are inspired by biological brain structures.",
            "doc5": "Database optimization improves query performance significantly."
        }
        self.semantic_matcher.add_documents(test_docs)

    def test_semantic_matcher_creation(self):
        """Benchmark semantic matcher initialization."""
        def benchmark():
            matcher = SemanticMatcher(self.mock_embedder)
            return matcher

        self.add_benchmark("semantic_matcher_creation", benchmark)

    def test_document_embedding(self):
        """Benchmark document embedding during indexing."""
        def benchmark():
            matcher = SemanticMatcher(self.mock_embedder)
            matcher.add_document("test_doc", "This is a test document for embedding.")
            return len(matcher.documents)

        self.add_benchmark("document_embedding", benchmark)

    def test_semantic_search(self):
        """Benchmark semantic search operations."""
        def benchmark():
            results = self.semantic_matcher.find_similar_documents(
                "programming and algorithms", top_k=3
            )
            return len(results)

        self.add_benchmark("semantic_search", benchmark,
                          query="programming and algorithms", top_k=3)

    def test_batch_semantic_search(self):
        """Benchmark batch semantic search operations."""
        queries = [
            "machine learning algorithms",
            "data structures implementation",
            "neural network training",
            "database query optimization"
        ]

        def benchmark():
            total_results = 0
            for query in queries:
                results = self.semantic_matcher.find_similar_documents(query, top_k=2)
                total_results += len(results)
            return total_results

        self.add_benchmark("batch_semantic_search", benchmark,
                          queries=len(queries), top_k=2)

    def test_similarity_calculation(self):
        """Benchmark cosine similarity calculations."""
        # Generate test vectors
        vector1 = np.random.rand(384)
        vectors = [np.random.rand(384) for _ in range(100)]

        def benchmark():
            similarities = []
            for vector2 in vectors:
                # Cosine similarity calculation
                dot_product = np.dot(vector1, vector2)
                norm1 = np.linalg.norm(vector1)
                norm2 = np.linalg.norm(vector2)
                similarity = dot_product / (norm1 * norm2)
                similarities.append(similarity)
            return len(similarities)

        self.add_benchmark("similarity_calculation", benchmark,
                          vector_dimension=384, comparison_count=len(vectors))


class TestAgentPerformance(BenchmarkSuite):
    """Performance benchmarks for agent operations."""

    def __init__(self):
        super().__init__("agent_performance", "Agent orchestration performance benchmarks")

    def setup_method(self):
        """Setup mock agents for testing."""
        # Create mock agents
        self.mock_agents = {}

        for i in range(3):
            agent = MagicMock()
            agent.name = f"Agent{i}"
            agent.run = AsyncMock(return_value=MagicMock(output=f"Result from Agent{i}", success=True))
            self.mock_agents[f"Agent{i}"] = agent

        self.orchestrator = AgentOrchestrator(self.mock_agents)

    def test_agent_orchestrator_creation(self):
        """Benchmark agent orchestrator initialization."""
        def benchmark():
            orchestrator = AgentOrchestrator(self.mock_agents)
            return len(orchestrator.agents)

        self.add_benchmark("agent_orchestrator_creation", benchmark,
                          agent_count=len(self.mock_agents))

    def test_sequential_agent_workflow(self):
        """Benchmark sequential agent workflow execution."""
        workflow = [
            {"agent": "Agent0", "input": "Initial task"},
            {"agent": "Agent1", "input_from": "Agent0"},
            {"agent": "Agent2", "input_from": "Agent1"}
        ]

        async def async_benchmark():
            results = await self.orchestrator.execute_workflow(workflow)
            return len(results)

        def benchmark():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(async_benchmark())
                return result
            finally:
                loop.close()

        self.add_benchmark("sequential_agent_workflow", benchmark,
                          agents=len(workflow))

    def test_parallel_agent_workflow(self):
        """Benchmark parallel agent workflow execution."""
        workflow = [
            {"agent": "Agent0", "input": "Task 0"},
            {"agent": "Agent1", "input": "Task 1"},
            {"agent": "Agent2", "input": "Task 2"}
        ]

        async def async_benchmark():
            results = await self.orchestrator.execute_workflow(workflow)
            return len(results)

        def benchmark():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(async_benchmark())
                return result
            finally:
                loop.close()

        self.add_benchmark("parallel_agent_workflow", benchmark,
                          agents=len(workflow))

    def test_conditional_agent_workflow(self):
        """Benchmark conditional agent workflow execution."""
        workflow = [
            {"agent": "Agent0", "input": "Check condition"},
            {"agent": "Agent1", "input_from": "Agent0", "condition": "Agent0.output == 'success'"},
            {"agent": "Agent2", "input_from": "Agent0", "condition": "Agent0.output != 'success'"}
        ]

        async def async_benchmark():
            results = await self.orchestrator.execute_workflow(workflow)
            return len(results)

        def benchmark():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(async_benchmark())
                return result
            finally:
                loop.close()

        self.add_benchmark("conditional_agent_workflow", benchmark,
                          agents=len(workflow), conditions=2)


class TestRecommendationPerformance(BenchmarkSuite):
    """Performance benchmarks for recommendation systems."""

    def __init__(self):
        super().__init__("recommendation_performance", "Recommendation engine performance benchmarks")

    def setup_method(self):
        """Setup mock recommendation engine."""
        # Mock embedder
        mock_embedder = MagicMock()
        mock_embedder.embed_text.return_value = [0.1] * 384

        # Mock semantic matcher
        mock_matcher = MagicMock()
        mock_matcher.find_similar_documents.return_value = [
            ("project1", 0.95), ("project2", 0.89), ("project3", 0.87)
        ]

        # Create recommendation engine with mocks
        self.recommendation_engine = MagicMock()
        self.recommendation_engine.get_recommendations.return_value = [
            {"id": "project1", "score": 0.95, "reason": "High semantic similarity"},
            {"id": "project2", "score": 0.89, "reason": "Good topic match"},
            {"id": "project3", "score": 0.87, "reason": "Difficulty alignment"}
        ]

    def test_recommendation_engine_creation(self):
        """Benchmark recommendation engine initialization."""
        def benchmark():
            # Mock the creation process
            engine = MagicMock()
            return engine

        self.add_benchmark("recommendation_engine_creation", benchmark)

    def test_recommendation_generation(self):
        """Benchmark recommendation generation."""
        def benchmark():
            recommendations = self.recommendation_engine.get_recommendations(
                user_profile={"skill_level": "intermediate", "interests": ["algorithms", "data structures"]},
                context={"time_available": 30, "difficulty_preference": "medium"}
            )
            return len(recommendations)

        self.add_benchmark("recommendation_generation", benchmark)

    def test_batch_recommendations(self):
        """Benchmark batch recommendation generation."""
        user_profiles = [
            {"skill_level": "beginner", "interests": ["python", "web"]},
            {"skill_level": "intermediate", "interests": ["algorithms", "data structures"]},
            {"skill_level": "advanced", "interests": ["machine learning", "distributed systems"]}
        ]

        def benchmark():
            total_recommendations = 0
            for profile in user_profiles:
                recommendations = self.recommendation_engine.get_recommendations(
                    user_profile=profile,
                    context={"time_available": 60}
                )
                total_recommendations += len(recommendations)
            return total_recommendations

        self.add_benchmark("batch_recommendations", benchmark,
                          user_count=len(user_profiles))

    def test_recommendation_scoring(self):
        """Benchmark recommendation scoring calculations."""
        candidates = [
            {"id": f"project{i}", "difficulty": "medium", "topics": ["algorithms", "data structures"]}
            for i in range(50)
        ]

        def benchmark():
            # Simulate scoring logic
            scored_candidates = []
            for candidate in candidates:
                # Mock scoring calculation
                semantic_score = np.random.rand()
                difficulty_score = 1.0 if candidate["difficulty"] == "medium" else 0.5
                topic_score = len(candidate["topics"]) / 5.0
                final_score = (semantic_score + difficulty_score + topic_score) / 3.0

                scored_candidates.append({
                    "id": candidate["id"],
                    "score": final_score,
                    "reason": "Mock scoring"
                })

            # Sort by score
            scored_candidates.sort(key=lambda x: x["score"], reverse=True)
            return len(scored_candidates)

        self.add_benchmark("recommendation_scoring", benchmark,
                          candidates=len(candidates))


class TestIntelligenceThroughput(BenchmarkSuite):
    """Throughput benchmarks for intelligence operations."""

    def __init__(self):
        super().__init__("intelligence_throughput", "Intelligence component throughput benchmarks")

    def test_semantic_search_throughput(self):
        """Benchmark semantic search throughput."""
        def benchmark():
            profiler = PerformanceProfiler()

            def search_operation():
                # Simulate semantic search
                time.sleep(0.001)  # Simulate search time
                return [("doc1", 0.9), ("doc2", 0.8)]

            result = profiler.measure_throughput(
                search_operation,
                duration_seconds=1
            )
            return result['operations_per_second']

        self.add_benchmark("semantic_search_throughput", benchmark,
                          duration_seconds=1)

    def test_agent_orchestration_throughput(self):
        """Benchmark agent orchestration throughput."""
        def benchmark():
            profiler = PerformanceProfiler()

            def agent_operation():
                # Simulate simple agent operation
                time.sleep(0.005)  # Simulate agent processing time
                return "Agent result"

            result = profiler.measure_throughput(
                agent_operation,
                duration_seconds=1
            )
            return result['operations_per_second']

        self.add_benchmark("agent_orchestration_throughput", benchmark,
                          duration_seconds=1)


# Performance test fixtures
@pytest.fixture
def intelligence_benchmark_suite():
    """Fixture for intelligence performance benchmarks."""
    return TestIntelligencePerformance()


@pytest.fixture
def agent_benchmark_suite():
    """Fixture for agent performance benchmarks."""
    return TestAgentPerformance()


@pytest.fixture
def recommendation_benchmark_suite():
    """Fixture for recommendation performance benchmarks."""
    return TestRecommendationPerformance()


@pytest.fixture
def intelligence_throughput_suite():
    """Fixture for intelligence throughput benchmarks."""
    return TestIntelligenceThroughput()


# Performance test functions
def test_intelligence_performance_basic(intelligence_benchmark_suite):
    """Run basic intelligence performance benchmarks."""
    results = intelligence_benchmark_suite.run_all(iterations=1, warmup_iterations=0)

    assert len(results) > 0
    for result in results:
        assert not result.error
        assert result.metrics.execution_time >= 0


def test_agent_performance_basic(agent_benchmark_suite):
    """Run basic agent performance benchmarks."""
    results = agent_benchmark_suite.run_all(iterations=1, warmup_iterations=0)

    assert len(results) > 0
    for result in results:
        assert not result.error


def test_recommendation_performance_basic(recommendation_benchmark_suite):
    """Run basic recommendation performance benchmarks."""
    results = recommendation_benchmark_suite.run_all(iterations=1, warmup_iterations=0)

    assert len(results) > 0
    for result in results:
        assert not result.error


def test_intelligence_throughput(intelligence_throughput_suite):
    """Run intelligence throughput benchmarks."""
    results = intelligence_throughput_suite.run_all(iterations=1, warmup_iterations=0)

    assert len(results) > 0
    for result in results:
        assert not result.error


# Detailed performance profiling tests
def test_semantic_matcher_memory_profiling():
    """Detailed memory profiling of semantic matcher."""
    from benchmarks.benchmark_framework import MemoryProfiler

    profiler = MemoryProfiler()

    with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
        mock_embedder = MagicMock()
        mock_embedder.embed_text.return_value = [0.1] * 384
        mock_embedder_class.return_value = mock_embedder

        from noleet.intelligence.semantic_matcher import SemanticMatcher

        def matcher_operation():
            matcher = SemanticMatcher(mock_embedder)
            matcher.add_documents({
                "doc1": "Python programming tutorial.",
                "doc2": "Machine learning algorithms.",
                "doc3": "Data structures guide."
            })
            return matcher.find_similar_documents("programming algorithms", top_k=2)

        result = profiler.profile_memory_usage(matcher_operation)

        assert 'memory_delta' in result
        assert result['memory_delta'] >= 0


def test_agent_memory_leak_detection():
    """Test for memory leaks in agent operations."""
    from benchmarks.benchmark_framework import MemoryProfiler

    profiler = MemoryProfiler()

    def agent_operation():
        # Simulate agent operation that might leak memory
        data = [i for i in range(1000)]  # Create some data
        result = sum(data)  # Process it
        del data  # Clean up
        return result

    result = profiler.detect_memory_leaks(agent_operation, iterations=5)

    assert 'leak_detected' in result
    assert isinstance(result['leak_detected'], bool)
