"""Multi-agent orchestrator using LangGraph."""

from typing import Dict, List, Any, Optional, Callable
import logging
import asyncio

from ..llm.llm_config import LLMConfig
from .base.agent_base import BaseAgent, AgentResult
from ..manual_intervention.manual_intervention_manager import ManualInterventionManager
from ..manual_intervention.intervention_config import InterventionConfig


class AgentOrchestrator:
    """Orchestrates multiple agents using LangGraph workflows."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        intervention_config: Optional[InterventionConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize agent orchestrator.

        Args:
            llm_config: LLM configuration
            intervention_config: Manual intervention configuration
            logger: Optional logger instance
        """
        self._llm_config = llm_config or LLMConfig()
        self._intervention_config = intervention_config or InterventionConfig()
        self._logger = logger or logging.getLogger(__name__)
        self._agents: Dict[str, BaseAgent] = {}
        self._workflows: Dict[str, Any] = {}
        self._graph = None
        self._intervention_manager = ManualInterventionManager(
            config=self._intervention_config,
            logger=self._logger
        )

        self._initialize()

    def _initialize(self):
        """Initialize orchestrator components."""
        try:
            self._setup_langgraph()
            self._logger.info("Agent orchestrator initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize orchestrator: {e}")

    def _setup_langgraph(self):
        """Setup LangGraph for multi-agent orchestration."""
        try:
            from langgraph import StateGraph
            from typing import TypedDict

            class OrchestratorState(TypedDict):
                current_agent: str
                task_data: Dict[str, Any]
                results: Dict[str, Any]
                next_agent: Optional[str]
                completed_agents: List[str]

            # Create state graph
            self._graph = StateGraph(OrchestratorState)

            # Add nodes for different orchestration steps
            self._graph.add_node("analyze_task", self._analyze_task)
            self._graph.add_node("route_to_agent", self._route_to_agent)
            self._graph.add_node("execute_agent", self._execute_agent)
            self._graph.add_node("collect_results", self._collect_results)

            # Define edges
            self._graph.add_edge("analyze_task", "route_to_agent")
            self._graph.add_edge("route_to_agent", "execute_agent")
            self._graph.add_edge("execute_agent", "collect_results")

            # Set entry point
            self._graph.set_entry_point("analyze_task")

        except ImportError:
            self._logger.warning("LangGraph not available, using simple orchestration")
            self._graph = None

    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the orchestrator.

        Args:
            agent: Agent to register
        """
        self._agents[agent.agent_type] = agent
        self._logger.info(f"Registered agent: {agent.agent_type}")

    def create_workflow(
        self,
        workflow_name: str,
        agent_sequence: List[str],
        task_processor: Optional[Callable] = None,
        workflow_type: str = "sequential"
    ):
        """
        Create a workflow with specific agent sequence.

        Args:
            workflow_name: Name of the workflow
            agent_sequence: Sequence of agent types to execute
            task_processor: Optional task processing function
            workflow_type: Type of workflow (sequential, parallel, conditional)
        """
        workflow = {
            "name": workflow_name,
            "agents": agent_sequence,
            "task_processor": task_processor,
            "workflow_type": workflow_type,
            "created_at": self._get_timestamp()
        }

        self._workflows[workflow_name] = workflow
        self._logger.info(f"Created workflow: {workflow_name} ({workflow_type})")

    def create_recommendation_workflow(self) -> str:
        """
        Create a standard project recommendation workflow.

        Returns:
            Workflow name
        """
        workflow_name = "project_recommendation_workflow"

        self.create_workflow(
            workflow_name=workflow_name,
            agent_sequence=[
                "question_analysis_agent",  # First analyze the user's query
                "project_recommendation_agent",  # Then generate recommendations
                "research_matching_agent"  # Finally suggest research papers
            ],
            task_processor=self._process_recommendation_task,
            workflow_type="sequential"
        )

        return workflow_name

    def create_content_analysis_workflow(self) -> str:
        """
        Create a content analysis workflow.

        Returns:
            Workflow name
        """
        workflow_name = "content_analysis_workflow"

        self.create_workflow(
            workflow_name=workflow_name,
            agent_sequence=[
                "sentiment_analysis_agent",  # Analyze sentiment first
                "question_analysis_agent"   # Then analyze technical aspects
            ],
            task_processor=self._process_content_analysis_task,
            workflow_type="sequential"
        )

        return workflow_name

    def execute_workflow(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
        allow_manual_intervention: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow_name: Name of workflow to execute
            input_data: Input data for the workflow
            allow_manual_intervention: Whether to allow manual intervention

        Returns:
            Workflow execution results
        """
        if workflow_name not in self._workflows:
            return {
                "success": False,
                "error": f"Workflow '{workflow_name}' not found"
            }

        workflow = self._workflows[workflow_name]

        if self._graph:
            # Use LangGraph for complex orchestration
            return self._execute_langgraph_workflow(workflow, input_data, allow_manual_intervention)
        else:
            # Use simple sequential execution
            return self._execute_simple_workflow(workflow, input_data, allow_manual_intervention)

    def _execute_langgraph_workflow(
        self,
        workflow: Dict[str, Any],
        input_data: Dict[str, Any],
        allow_manual_intervention: bool = True
    ) -> Dict[str, Any]:
        """Execute workflow using LangGraph."""
        try:
            # Create a simple state graph for the workflow
            from langgraph import StateGraph, END
            from typing import TypedDict

            class WorkflowState(TypedDict):
                current_step: int
                task_data: Dict[str, Any]
                results: Dict[str, Any]
                completed_agents: List[str]

            def execute_step(state: WorkflowState) -> WorkflowState:
                """Execute current workflow step."""
                step = state["current_step"]
                agents = workflow["agents"]

                if step >= len(agents):
                    return state

                agent_type = agents[step]
                task_data = state["task_data"]

                # Apply task processor if available
                if workflow.get("task_processor"):
                    task_data = workflow["task_processor"](task_data, agent_type, state["results"])

                # Check for manual intervention before executing agent
                if allow_manual_intervention and self._intervention_config.should_intervene_at(agent_type):
                    # For LangGraph, we need to handle this synchronously
                    # The actual async handling will be done at the orchestrator level
                    intervention_result = {
                        "action": "pause_requested",
                        "agent_type": agent_type,
                        "task_data": task_data,
                        "workflow_name": workflow.get("name", "unknown_workflow"),
                        "current_state": state
                    }

                    # Return paused state - orchestrator will handle the async pause
                    return {
                        "current_step": step,
                        "task_data": task_data,
                        "results": state["results"],
                        "completed_agents": state["completed_agents"],
                        "intervention_request": intervention_result,
                        "status": "intervention_requested"
                    }

                # Execute agent
                result = self.execute_direct(agent_type, task_data)

                # Update state
                new_results = state["results"].copy()
                new_results[agent_type] = result.data if result.success else {"error": result.message}

                new_completed = state["completed_agents"].copy()
                new_completed.append(agent_type)

                # Prepare next task data
                next_task_data = task_data.copy()
                if result.success and result.data:
                    next_task_data.update(result.data)

                return {
                    "current_step": step + 1,
                    "task_data": next_task_data,
                    "results": new_results,
                    "completed_agents": new_completed
                }

            def should_continue(state: WorkflowState) -> str:
                """Determine if workflow should continue."""
                return "execute_step" if state["current_step"] < len(workflow["agents"]) else END

            # Create and configure graph
            workflow_graph = StateGraph(WorkflowState)
            workflow_graph.add_node("execute_step", execute_step)
            workflow_graph.add_conditional_edges(
                "execute_step",
                should_continue,
                {"execute_step": "execute_step", END: END}
            )
            workflow_graph.set_entry_point("execute_step")

            # Execute workflow
            initial_state = {
                "current_step": 0,
                "task_data": input_data,
                "results": {},
                "completed_agents": []
            }

            final_state = workflow_graph.invoke(initial_state)

            # Check if intervention was requested
            if final_state.get("status") == "intervention_requested":
                intervention_req = final_state["intervention_request"]
                # Perform the actual async pause operation
                import asyncio
                if asyncio.iscoroutinefunction(self._check_manual_intervention):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        intervention_result = loop.run_until_complete(
                            self._check_manual_intervention(
                                intervention_req["workflow_name"],
                                intervention_req["agent_type"],
                                intervention_req["task_data"],
                                intervention_req["current_state"]
                            )
                        )

                        if intervention_result["action"] == "paused":
                            return {
                                "success": True,
                                "results": final_state["results"],
                                "completed_agents": final_state["completed_agents"],
                                "status": "waiting_for_manual_input",
                                "intervention_session": intervention_result["session_id"],
                                "paused_at_agent": intervention_req["agent_type"]
                            }
                    finally:
                        loop.close()

            return {
                "success": True,
                "results": final_state["results"],
                "completed_agents": final_state["completed_agents"],
                "workflow_steps": len(workflow["agents"])
            }

        except Exception as e:
            self._logger.error(f"LangGraph workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _check_manual_intervention(
        self,
        workflow_id: str,
        agent_type: str,
        task_data: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if manual intervention is needed and handle pause."""
        try:
            context_data = {
                "workflow_id": workflow_id,
                "current_step": current_state.get("current_step", 0),
                "completed_agents": current_state.get("completed_agents", []),
                "previous_results": current_state.get("results", {})
            }

            intervention_data = {
                "agent_type": agent_type,
                "task_data": task_data,
                "available_projects": task_data.get("available_projects", []),
                "analysis_results": task_data.get("analysis_results", {})
            }

            intervention_result = await self._intervention_manager.pause_for_manual_intervention(
                workflow_id=workflow_id,
                agent_type=agent_type,
                context_data=context_data,
                intervention_data=intervention_data
            )

            return intervention_result

        except Exception as e:
            self._logger.error(f"Manual intervention check failed: {e}")
            return {"action": "continue", "reason": "intervention_check_failed"}

    def _execute_simple_workflow(
        self,
        workflow: Dict[str, Any],
        input_data: Dict[str, Any],
        allow_manual_intervention: bool = True
    ) -> Dict[str, Any]:
        """Execute workflow using simple sequential execution."""
        results = {}
        completed_agents = []

        task_data = input_data

        for agent_type in workflow["agents"]:
            if agent_type not in self._agents:
                self._logger.warning(f"Agent '{agent_type}' not found, skipping")
                continue

            agent = self._agents[agent_type]

            try:
                self._logger.info(f"Executing agent: {agent_type}")

                # Apply task processor if available
                if workflow.get("task_processor"):
                    task_data = workflow["task_processor"](task_data, agent_type)

                # Check for manual intervention before executing agent
                if allow_manual_intervention and self._intervention_config.should_intervene_at(agent_type):
                    # For simple workflow, we need to handle this synchronously
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if not loop.is_running():
                            # We can pause for manual intervention
                            intervention_result = loop.run_until_complete(
                                self._check_manual_intervention(
                                    workflow.get("name", "unknown_workflow"),
                                    agent_type,
                                    task_data,
                                    {
                                        "current_step": len(completed_agents),
                                        "completed_agents": completed_agents,
                                        "results": results
                                    }
                                )
                            )

                            if intervention_result["action"] == "paused":
                                return {
                                    "success": True,
                                    "results": results,
                                    "completed_agents": completed_agents,
                                    "status": "waiting_for_manual_input",
                                    "intervention_session": intervention_result["session_id"],
                                    "paused_at_agent": agent_type
                                }
                    except RuntimeError:
                        # No event loop available, skip manual intervention
                        pass

                # Execute agent
                result = agent.execute(task_data)

                if result.success:
                    results[agent_type] = result.data
                    completed_agents.append(agent_type)

                    # Update task data for next agent
                    task_data.update(result.data)
                else:
                    self._logger.error(f"Agent '{agent_type}' failed: {result.message}")
                    return {
                        "success": False,
                        "error": f"Agent '{agent_type}' failed: {result.message}",
                        "partial_results": results,
                        "completed_agents": completed_agents
                    }

            except Exception as e:
                self._logger.error(f"Error executing agent '{agent_type}': {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "partial_results": results,
                    "completed_agents": completed_agents
                }

        return {
            "success": True,
            "results": results,
            "completed_agents": completed_agents
        }

    def execute_direct(
        self,
        agent_type: str,
        input_data: Dict[str, Any]
    ) -> AgentResult:
        """
        Execute a specific agent directly.

        Args:
            agent_type: Type of agent to execute
            input_data: Input data for the agent

        Returns:
            Agent execution result
        """
        if agent_type not in self._agents:
            return AgentResult(
                success=False,
                message=f"Agent '{agent_type}' not found",
                errors=[f"Available agents: {list(self._agents.keys())}"]
            )

        agent = self._agents[agent_type]

        try:
            return agent.execute(input_data)
        except Exception as e:
            self._logger.error(f"Direct agent execution failed: {e}")
            return AgentResult(
                success=False,
                message=str(e),
                errors=[str(e)]
            )

    async def execute_async(
        self,
        agent_type: str,
        input_data: Dict[str, Any]
    ) -> AgentResult:
        """
        Execute agent asynchronously.

        Args:
            agent_type: Type of agent to execute
            input_data: Input data for the agent

        Returns:
            Agent execution result
        """
        # For now, just call sync version
        # Can be enhanced with actual async execution
        return self.execute_direct(agent_type, input_data)

    def get_available_agents(self) -> List[str]:
        """Get list of available agent types."""
        return list(self._agents.keys())

    def get_available_workflows(self) -> List[str]:
        """Get list of available workflow names."""
        return list(self._workflows.keys())

    def _process_recommendation_task(
        self,
        task_data: Dict[str, Any],
        agent_type: str,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process task data for recommendation workflow."""
        enhanced_data = task_data.copy()

        if agent_type == "project_recommendation_agent":
            # Use results from question analysis if available
            if "question_analysis_agent" in previous_results:
                analysis_result = previous_results["question_analysis_agent"]
                if "topics" in analysis_result:
                    enhanced_data["topics"] = [
                        t for t in analysis_result["topics"]["extracted_topics"]
                    ]

        elif agent_type == "research_matching_agent":
            # Use recommendations from project recommendation agent
            if "project_recommendation_agent" in previous_results:
                rec_result = previous_results["project_recommendation_agent"]
                if "recommendations" in rec_result and rec_result["recommendations"]:
                    # Use the first recommended project for research matching
                    top_project = rec_result["recommendations"][0]
                    enhanced_data["project_id"] = top_project["project_id"]
                    enhanced_data["topics"] = [
                        t.lower().replace(" ", "_")
                        for t in top_project["primary_topics"]
                    ]

        return enhanced_data

    def _process_content_analysis_task(
        self,
        task_data: Dict[str, Any],
        agent_type: str,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process task data for content analysis workflow."""
        # For now, pass through the data unchanged
        # Could be enhanced to use results from previous agents
        return task_data.copy()

    def execute_recommendation_workflow(
        self,
        user_query: str,
        user_id: Optional[str] = None,
        topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute the standard recommendation workflow.

        Args:
            user_query: User's query
            user_id: User identifier
            topics: Selected topics

        Returns:
            Workflow results
        """
        workflow_name = "project_recommendation_workflow"
        if workflow_name not in self._workflows:
            self.create_recommendation_workflow()

        input_data = {
            "query": user_query,
            "user_id": user_id,
            "topics": topics or [],
            "max_recommendations": 3
        }

        return self.execute_workflow(workflow_name, input_data)

    def execute_content_analysis_workflow(
        self,
        content: str,
        content_type: str = "question",
        source: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Execute the content analysis workflow.

        Args:
            content: Content to analyze
            content_type: Type of content
            source: Content source

        Returns:
            Analysis results
        """
        workflow_name = "content_analysis_workflow"
        if workflow_name not in self._workflows:
            self.create_content_analysis_workflow()

        input_data = {
            "content": content,
            "content_type": content_type,
            "source": source
        }

        return self.execute_workflow(workflow_name, input_data)

    def resume_workflow(self, session_id: str) -> Dict[str, Any]:
        """
        Resume a workflow that is waiting for manual intervention.

        Args:
            session_id: Intervention session ID

        Returns:
            Resume result
        """
        try:
            # Check if manual input is available
            resume_result = self._intervention_manager.check_for_resume(session_id)

            if not resume_result["can_resume"]:
                return {
                    "success": False,
                    "error": resume_result.get("reason", "Cannot resume workflow")
                }

            # Get session data to reconstruct workflow state
            session_data = self._intervention_manager.get_session_status(session_id)
            if not session_data:
                return {"success": False, "error": "Session not found"}

            # Reconstruct workflow execution from the paused point
            workflow_name = session_data.get("workflow_id", "unknown")
            paused_agent = session_data.get("agent_type", "")

            if workflow_name not in self._workflows:
                return {"success": False, "error": f"Workflow '{workflow_name}' not found"}

            workflow = self._workflows[workflow_name]

            # Find the paused agent in the workflow
            try:
                paused_index = workflow["agents"].index(paused_agent)
            except ValueError:
                return {"success": False, "error": f"Agent '{paused_agent}' not found in workflow"}

            # Continue workflow execution from the next agent
            results = session_data.get("results", {})
            completed_agents = session_data.get("completed_agents", [])
            task_data = session_data.get("task_data", {})

            # Add manual data to task_data
            if resume_result.get("manual_data"):
                task_data.update(resume_result["manual_data"])

            # Continue executing remaining agents
            for i in range(paused_index + 1, len(workflow["agents"])):
                agent_type = workflow["agents"][i]

                # Apply task processor if available
                if workflow.get("task_processor"):
                    task_data = workflow["task_processor"](task_data, agent_type, results)

                # Execute agent
                result = self.execute_direct(agent_type, task_data)

                # Store result
                results[agent_type] = result.data if result.success else {"error": result.message}
                completed_agents.append(agent_type)

                # Update task data for next agent
                if result.success and result.data:
                    task_data.update(result.data)

            return {
                "success": True,
                "results": results,
                "completed_agents": completed_agents,
                "resumed_from": paused_agent,
                "manual_data_applied": bool(resume_result.get("manual_data"))
            }

        except Exception as e:
            self._logger.error(f"Workflow resume failed: {e}")
            return {"success": False, "error": str(e)}

    def get_paused_workflows(self) -> Dict[str, Any]:
        """
        Get information about workflows waiting for manual intervention.

        Returns:
            Dictionary with paused workflow information
        """
        active_sessions = self._intervention_manager.get_active_sessions()

        paused_workflows = {}
        for session_id, session_data in active_sessions.items():
            workflow_id = session_data.get("workflow_id", "unknown")
            if workflow_id not in paused_workflows:
                paused_workflows[workflow_id] = []

            paused_workflows[workflow_id].append({
                "session_id": session_id,
                "agent_type": session_data.get("agent_type", ""),
                "paused_at": session_data.get("created_at", ""),
                "export_path": session_data.get("export_path", "")
            })

        return {
            "total_paused": len(active_sessions),
            "workflows": paused_workflows
        }

    def cancel_manual_intervention(self, session_id: str) -> bool:
        """
        Cancel a manual intervention session.

        Args:
            session_id: Session ID to cancel

        Returns:
            True if cancelled successfully
        """
        return self._intervention_manager.cancel_session(session_id)

    def get_intervention_statistics(self) -> Dict[str, Any]:
        """Get statistics about manual interventions."""
        return self._intervention_manager.get_statistics()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

