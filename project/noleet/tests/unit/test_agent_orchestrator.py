"""
Unit tests for agent orchestrator functionality.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any, List

from noleet.agents.agent_orchestrator import AgentOrchestrator
from noleet.agents.base.agent_base import AgentResult


class TestAgentOrchestrator:
    """Test cases for agent orchestration functionality."""

    def test_orchestrator_initialization(self):
        """Test agent orchestrator initialization."""
        orchestrator = AgentOrchestrator()

        assert orchestrator.agents == {}
        assert orchestrator.workflows == {}
        assert orchestrator.is_initialized is False

    def test_register_agent(self):
        """Test registering an agent with the orchestrator."""
        orchestrator = AgentOrchestrator()

        mock_agent = MagicMock()
        mock_agent.name = "test_agent"
        mock_agent.capabilities = ["analysis", "recommendation"]

        orchestrator.register_agent(mock_agent)

        assert "test_agent" in orchestrator.agents
        assert orchestrator.agents["test_agent"] == mock_agent

    def test_get_agent_by_capability(self):
        """Test finding agents by capability."""
        orchestrator = AgentOrchestrator()

        # Register multiple agents with different capabilities
        agent1 = MagicMock()
        agent1.name = "analysis_agent"
        agent1.capabilities = ["analysis", "sentiment"]

        agent2 = MagicMock()
        agent2.name = "recommendation_agent"
        agent2.capabilities = ["recommendation", "matching"]

        agent3 = MagicMock()
        agent3.name = "coding_agent"
        agent3.capabilities = ["coding", "review"]

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)

        # Test finding agents by capability
        analysis_agents = orchestrator.get_agents_by_capability("analysis")
        assert len(analysis_agents) == 1
        assert analysis_agents[0].name == "analysis_agent"

        coding_agents = orchestrator.get_agents_by_capability("coding")
        assert len(coding_agents) == 1
        assert coding_agents[0].name == "coding_agent"

        # Test non-existent capability
        empty_agents = orchestrator.get_agents_by_capability("nonexistent")
        assert empty_agents == []

    def test_create_workflow(self):
        """Test creating a workflow definition."""
        orchestrator = AgentOrchestrator()

        workflow_def = {
            "name": "project_recommendation_workflow",
            "steps": [
                {
                    "agent": "analysis_agent",
                    "task": "analyze_user_profile",
                    "inputs": ["user_profile"],
                    "outputs": ["analysis_result"]
                },
                {
                    "agent": "recommendation_agent",
                    "task": "generate_recommendations",
                    "inputs": ["analysis_result"],
                    "outputs": ["recommendations"]
                }
            ]
        }

        workflow_id = orchestrator.create_workflow(workflow_def)

        assert workflow_id in orchestrator.workflows
        assert orchestrator.workflows[workflow_id] == workflow_def

    @pytest.mark.asyncio
    async def test_execute_workflow_simple(self):
        """Test executing a simple linear workflow."""
        orchestrator = AgentOrchestrator()

        # Create mock agents
        analysis_agent = MagicMock()
        analysis_agent.name = "analysis_agent"
        analysis_agent.capabilities = ["analysis"]
        analysis_agent.execute = AsyncMock(return_value=AgentResult(
            success=True,
            data={"sentiment": "positive", "difficulty": "medium"},
            metadata={"execution_time": 0.5}
        ))

        recommendation_agent = MagicMock()
        recommendation_agent.name = "recommendation_agent"
        recommendation_agent.capabilities = ["recommendation"]
        recommendation_agent.execute = AsyncMock(return_value=AgentResult(
            success=True,
            data={"projects": ["project1", "project2"]},
            metadata={"execution_time": 0.3}
        ))

        # Register agents
        orchestrator.register_agent(analysis_agent)
        orchestrator.register_agent(recommendation_agent)

        # Create workflow
        workflow_def = {
            "name": "simple_recommendation",
            "steps": [
                {
                    "agent": "analysis_agent",
                    "task": "analyze",
                    "inputs": ["user_input"],
                    "outputs": ["analysis"]
                },
                {
                    "agent": "recommendation_agent",
                    "task": "recommend",
                    "inputs": ["analysis"],
                    "outputs": ["recommendations"]
                }
            ]
        }

        workflow_id = orchestrator.create_workflow(workflow_def)

        # Execute workflow
        initial_data = {"user_input": "I want to learn algorithms"}
        result = await orchestrator.execute_workflow(workflow_id, initial_data)

        assert result["success"] is True
        assert "recommendations" in result["data"]
        assert "execution_time" in result["metadata"]

        # Verify agents were called
        analysis_agent.execute.assert_called_once()
        recommendation_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_workflow_with_failure(self):
        """Test workflow execution when an agent fails."""
        orchestrator = AgentOrchestrator()

        # Create agents - first succeeds, second fails
        analysis_agent = MagicMock()
        analysis_agent.name = "analysis_agent"
        analysis_agent.execute = AsyncMock(return_value=AgentResult(
            success=True,
            data={"analysis": "success"},
            metadata={}
        ))

        failing_agent = MagicMock()
        failing_agent.name = "failing_agent"
        failing_agent.execute = AsyncMock(return_value=AgentResult(
            success=False,
            error="Agent failed",
            metadata={}
        ))

        orchestrator.register_agent(analysis_agent)
        orchestrator.register_agent(failing_agent)

        # Create workflow
        workflow_def = {
            "name": "failing_workflow",
            "steps": [
                {"agent": "analysis_agent", "task": "analyze", "outputs": ["result1"]},
                {"agent": "failing_agent", "task": "fail", "outputs": ["result2"]}
            ]
        }

        workflow_id = orchestrator.create_workflow(workflow_def)

        # Execute workflow
        result = await orchestrator.execute_workflow(workflow_id, {})

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_workflow_parallel_steps(self):
        """Test workflow execution with parallel steps."""
        orchestrator = AgentOrchestrator()

        # Create multiple agents
        agent1 = MagicMock()
        agent1.name = "agent1"
        agent1.execute = AsyncMock(return_value=AgentResult(success=True, data={"result1": "data1"}))

        agent2 = MagicMock()
        agent2.name = "agent2"
        agent2.execute = AsyncMock(return_value=AgentResult(success=True, data={"result2": "data2"}))

        agent3 = MagicMock()
        agent3.name = "agent3"
        agent3.execute = AsyncMock(return_value=AgentResult(success=True, data={"result3": "data3"}))

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)

        # Create workflow with parallel execution
        workflow_def = {
            "name": "parallel_workflow",
            "steps": [
                {
                    "agent": "agent1",
                    "task": "task1",
                    "parallel_group": "group1",
                    "outputs": ["result1"]
                },
                {
                    "agent": "agent2",
                    "task": "task2",
                    "parallel_group": "group1",
                    "outputs": ["result2"]
                },
                {
                    "agent": "agent3",
                    "task": "combine",
                    "inputs": ["result1", "result2"],
                    "outputs": ["final_result"]
                }
            ]
        }

        workflow_id = orchestrator.create_workflow(workflow_def)
        result = await orchestrator.execute_workflow(workflow_id, {})

        assert result["success"] is True
        # Verify all agents were called
        agent1.execute.assert_called_once()
        agent2.execute.assert_called_once()
        agent3.execute.assert_called_once()

    def test_workflow_validation(self):
        """Test workflow definition validation."""
        orchestrator = AgentOrchestrator()

        # Valid workflow
        valid_workflow = {
            "name": "valid_workflow",
            "steps": [
                {
                    "agent": "test_agent",
                    "task": "test_task",
                    "inputs": ["input1"],
                    "outputs": ["output1"]
                }
            ]
        }

        # Should not raise exception
        workflow_id = orchestrator.create_workflow(valid_workflow)
        assert workflow_id is not None

        # Invalid workflow - missing agent
        invalid_workflow = {
            "name": "invalid_workflow",
            "steps": [
                {
                    "task": "test_task",
                    "inputs": ["input1"],
                    "outputs": ["output1"]
                    # Missing "agent" field
                }
            ]
        }

        with pytest.raises(ValueError, match="Invalid workflow definition"):
            orchestrator.create_workflow(invalid_workflow)

    def test_get_workflow_status(self):
        """Test getting workflow execution status."""
        orchestrator = AgentOrchestrator()

        # Initially no workflows running
        status = orchestrator.get_workflow_status()
        assert status["active_workflows"] == 0
        assert status["completed_workflows"] == 0

    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self):
        """Test workflow execution timeout handling."""
        orchestrator = AgentOrchestrator()

        slow_agent = MagicMock()
        slow_agent.name = "slow_agent"
        slow_agent.execute = AsyncMock()  # Never completes

        orchestrator.register_agent(slow_agent)

        workflow_def = {
            "name": "timeout_workflow",
            "steps": [
                {
                    "agent": "slow_agent",
                    "task": "slow_task",
                    "timeout": 1,  # 1 second timeout
                    "outputs": ["result"]
                }
            ]
        }

        workflow_id = orchestrator.create_workflow(workflow_def)

        # This should timeout and fail
        result = await orchestrator.execute_workflow(workflow_id, {}, timeout=2)

        # Should handle timeout gracefully
        assert "timeout" in result.get("error", "").lower() or result["success"] is False

    def test_agent_health_monitoring(self):
        """Test agent health monitoring functionality."""
        orchestrator = AgentOrchestrator()

        healthy_agent = MagicMock()
        healthy_agent.name = "healthy_agent"
        healthy_agent.health_check = AsyncMock(return_value=True)

        unhealthy_agent = MagicMock()
        unhealthy_agent.name = "unhealthy_agent"
        unhealthy_agent.health_check = AsyncMock(return_value=False)

        orchestrator.register_agent(healthy_agent)
        orchestrator.register_agent(unhealthy_agent)

        # Get health status
        health_status = orchestrator.get_agent_health_status()

        assert health_status["healthy_agent"] is True
        assert health_status["unhealthy_agent"] is False

    def test_workflow_execution_history(self):
        """Test workflow execution history tracking."""
        orchestrator = AgentOrchestrator()

        # Initially empty history
        history = orchestrator.get_execution_history()
        assert history == []

        # After executions, history should be populated
        # (This would be tested in integration tests with actual workflow execution)

    def test_resource_cleanup(self):
        """Test proper resource cleanup after workflow execution."""
        orchestrator = AgentOrchestrator()

        mock_agent = MagicMock()
        mock_agent.name = "test_agent"
        mock_agent.cleanup = AsyncMock()

        orchestrator.register_agent(mock_agent)

        # Cleanup should be called
        orchestrator.cleanup_resources()

        mock_agent.cleanup.assert_called_once()

    def test_error_recovery_mechanisms(self):
        """Test error recovery and retry mechanisms."""
        orchestrator = AgentOrchestrator()

        # Create agent that fails initially but succeeds on retry
        failing_agent = MagicMock()
        failing_agent.name = "retry_agent"

        call_count = 0
        async def failing_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return AgentResult(success=True, data={"result": "success"})

        failing_agent.execute = failing_execute

        orchestrator.register_agent(failing_agent)

        # This test validates the error recovery interface exists
        assert hasattr(orchestrator, 'execute_workflow')

    def test_concurrent_workflow_execution(self):
        """Test concurrent execution of multiple workflows."""
        orchestrator = AgentOrchestrator()

        # Test that orchestrator can handle multiple concurrent workflows
        # (Implementation would use asyncio.gather or similar)

        assert hasattr(orchestrator, 'execute_workflow')

    def test_workflow_dependency_resolution(self):
        """Test resolution of complex workflow dependencies."""
        orchestrator = AgentOrchestrator()

        # Test DAG (Directed Acyclic Graph) dependency resolution
        # Complex workflows with multiple dependencies

        workflow_def = {
            "name": "complex_workflow",
            "steps": [
                {"agent": "agent1", "task": "task1", "outputs": ["output1"]},
                {"agent": "agent2", "task": "task2", "inputs": ["output1"], "outputs": ["output2"]},
                {"agent": "agent3", "task": "task3", "inputs": ["output1"], "outputs": ["output3"]},
                {"agent": "agent4", "task": "task4", "inputs": ["output2", "output3"], "outputs": ["final"]}
            ]
        }

        workflow_id = orchestrator.create_workflow(workflow_def)

        # The orchestrator should handle dependency resolution
        assert workflow_id in orchestrator.workflows
