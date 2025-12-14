"""
Agent-specific metrics collection for monitoring agent operations.
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Optional


class AgentMetricsCollector:
    """Collects metrics specific to agent operations."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        # Agent request metrics
        self.agent_requests_total = Counter(
            'noleet_agent_requests_total',
            'Total agent requests',
            ['agent_name', 'agent_type', 'request_type'],
            registry=registry
        )

        self.agent_request_duration_seconds = Histogram(
            'noleet_agent_request_duration_seconds',
            'Agent request duration in seconds',
            ['agent_name', 'agent_type', 'request_type'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0],
            registry=registry
        )

        self.agent_completions_total = Counter(
            'noleet_agent_completions_total',
            'Total agent request completions',
            ['agent_name', 'agent_type', 'outcome'],
            registry=registry
        )

        self.agent_errors_total = Counter(
            'noleet_agent_errors_total',
            'Total agent errors',
            ['agent_name', 'agent_type', 'error_type'],
            registry=registry
        )

        # Agent-specific operation metrics
        self.sentiment_analysis_requests = Counter(
            'noleet_sentiment_analysis_requests_total',
            'Total sentiment analysis requests',
            ['model', 'text_length'],
            registry=registry
        )

        self.question_analysis_requests = Counter(
            'noleet_question_analysis_requests_total',
            'Total question analysis requests',
            ['difficulty_level', 'topic'],
            registry=registry
        )

        self.recommendation_generation_requests = Counter(
            'noleet_recommendation_generation_requests_total',
            'Total recommendation generation requests',
            ['algorithm', 'user_type'],
            registry=registry
        )

        self.research_matching_requests = Counter(
            'noleet_research_matching_requests_total',
            'Total research matching requests',
            ['paper_count', 'project_count'],
            registry=registry
        )

        # Agent performance metrics
        self.agent_memory_usage_bytes = Gauge(
            'noleet_agent_memory_usage_bytes',
            'Agent memory usage in bytes',
            ['agent_name'],
            registry=registry
        )

        self.agent_active_requests = Gauge(
            'noleet_agent_active_requests',
            'Number of active agent requests',
            ['agent_name'],
            registry=registry
        )

        self.agent_success_rate = Gauge(
            'noleet_agent_success_rate',
            'Agent success rate (0-1)',
            ['agent_name'],
            registry=registry
        )

        # Orchestrator metrics
        self.orchestrator_workflows_total = Counter(
            'noleet_orchestrator_workflows_total',
            'Total orchestrator workflows',
            ['workflow_type', 'status'],
            registry=registry
        )

        self.orchestrator_workflow_duration_seconds = Histogram(
            'noleet_orchestrator_workflow_duration_seconds',
            'Orchestrator workflow duration in seconds',
            ['workflow_type'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
            registry=registry
        )

    def record_agent_request_start(self, agent_name: str, agent_type: str,
                                 request_type: str = 'unknown'):
        """Record the start of an agent request."""
        self.agent_requests_total.labels(
            agent_name=agent_name,
            agent_type=agent_type,
            request_type=request_type
        ).inc()

        self.agent_active_requests.labels(agent_name=agent_name).inc()

    def record_agent_request_complete(self, agent_name: str, agent_type: str,
                                    request_type: str, duration: float,
                                    outcome: str = 'success'):
        """Record the completion of an agent request."""
        self.agent_active_requests.labels(agent_name=agent_name).dec()

        self.agent_request_duration_seconds.labels(
            agent_name=agent_name,
            agent_type=agent_type,
            request_type=request_type
        ).observe(duration)

        self.agent_completions_total.labels(
            agent_name=agent_name,
            agent_type=agent_type,
            outcome=outcome
        ).inc()

    def record_agent_error(self, agent_name: str, agent_type: str,
                         error_type: str = 'unknown'):
        """Record an agent error."""
        self.agent_errors_total.labels(
            agent_name=agent_name,
            agent_type=agent_type,
            error_type=error_type
        ).inc()

        self.agent_active_requests.labels(agent_name=agent_name).dec()

    def record_sentiment_analysis(self, model: str, text_length: int):
        """Record sentiment analysis request."""
        # Bucket text length
        if text_length <= 100:
            length_bucket = '0-100'
        elif text_length <= 500:
            length_bucket = '100-500'
        elif text_length <= 1000:
            length_bucket = '500-1000'
        else:
            length_bucket = '1000+'

        self.sentiment_analysis_requests.labels(
            model=model,
            text_length=length_bucket
        ).inc()

    def record_question_analysis(self, difficulty_level: str, topic: str):
        """Record question analysis request."""
        self.question_analysis_requests.labels(
            difficulty_level=difficulty_level,
            topic=topic
        ).inc()

    def record_recommendation_generation(self, algorithm: str, user_type: str = 'unknown'):
        """Record recommendation generation request."""
        self.recommendation_generation_requests.labels(
            algorithm=algorithm,
            user_type=user_type
        ).inc()

    def record_research_matching(self, paper_count: int, project_count: int):
        """Record research matching request."""
        # Bucket counts
        paper_bucket = self._bucket_count(paper_count)
        project_bucket = self._bucket_count(project_count)

        self.research_matching_requests.labels(
            paper_count=paper_bucket,
            project_count=project_bucket
        ).inc()

    def _bucket_count(self, count: int) -> str:
        """Bucket count values for metrics."""
        if count <= 5:
            return f"{count}"
        elif count <= 10:
            return "6-10"
        elif count <= 25:
            return "11-25"
        elif count <= 50:
            return "26-50"
        else:
            return "50+"

    def update_agent_stats(self, agent_name: str, memory_usage: int,
                         success_rate: float):
        """Update agent statistics."""
        self.agent_memory_usage_bytes.labels(agent_name=agent_name).set(memory_usage)
        self.agent_success_rate.labels(agent_name=agent_name).set(success_rate)

    def record_orchestrator_workflow_start(self, workflow_type: str):
        """Record orchestrator workflow start."""
        # This could be enhanced with workflow ID tracking
        pass

    def record_orchestrator_workflow_complete(self, workflow_type: str,
                                            duration: float, status: str = 'success'):
        """Record orchestrator workflow completion."""
        self.orchestrator_workflows_total.labels(
            workflow_type=workflow_type,
            status=status
        ).inc()

        self.orchestrator_workflow_duration_seconds.labels(
            workflow_type=workflow_type
        ).observe(duration)
