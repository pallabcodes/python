"""
LangGraph - Complex Workflow Orchestration.

Demonstrates:
- State graphs
- Node definitions
- Edge routing
- Conditional logic
- Production-grade patterns
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable, TypedDict
from dataclasses import dataclass, field
from enum import Enum

# LangGraph imports (with fallbacks)
try:
    from langgraph.graph import StateGraph
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    class StateGraph:
        def __init__(self): pass
        def add_node(self, name: str, func): pass
        def add_edge(self, source: str, target: str): pass
        def add_conditional_edges(self, source: str, condition_func: Callable): pass
        def compile(self): return None

logger = logging.getLogger(__name__)


class NodeState(Enum):
    """Node execution state."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GraphState(TypedDict):
    """State passed between graph nodes."""
    messages: List[Dict[str, Any]]
    current_step: str
    results: Dict[str, Any]
    errors: List[str]
    metadata: Dict[str, Any]


@dataclass
class NodeResult:
    """Result of node execution."""
    success: bool
    output: Any
    execution_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowOrchestrator:
    """
    Workflow orchestrator using LangGraph.
    
    Features:
    - State graph construction
    - Node and edge management
    - Conditional routing
    - Error handling
    - Execution tracking
    """
    
    def __init__(self, workflow_name: str):
        self.workflow_name = workflow_name
        self.graph: Optional[StateGraph] = None
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, List[str]] = {}
        self.conditional_routes: Dict[str, Callable] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self._logger = logging.getLogger(f"{__name__}.{workflow_name}")
    
    def add_node(self, name: str, node_func: Callable) -> None:
        """
        Add a node to the graph.
        
        Args:
            name: Node name
            node_func: Node function that processes state
        """
        self.nodes[name] = node_func
        self._logger.info(f"Added node: {name}")
    
    def add_edge(self, source: str, target: str) -> None:
        """
        Add an edge between nodes.
        
        Args:
            source: Source node name
            target: Target node name
        """
        if source not in self.edges:
            self.edges[source] = []
        self.edges[source].append(target)
        self._logger.info(f"Added edge: {source} -> {target}")
    
    def add_conditional_route(
        self,
        source: str,
        route_func: Callable[[GraphState], str]
    ) -> None:
        """
        Add conditional routing from a node.
        
        Args:
            source: Source node name
            route_func: Function that returns next node name based on state
        """
        self.conditional_routes[source] = route_func
        self._logger.info(f"Added conditional route from: {source}")
    
    def build_graph(self) -> None:
        """Build the workflow graph."""
        if not HAS_LANGGRAPH:
            self._logger.warning("LangGraph not available, using fallback")
            return
        
        try:
            self.graph = StateGraph()
            
            # Add all nodes
            for name, func in self.nodes.items():
                self.graph.add_node(name, func)
            
            # Add edges
            for source, targets in self.edges.items():
                for target in targets:
                    self.graph.add_edge(source, target)
            
            # Add conditional routes
            for source, route_func in self.conditional_routes.items():
                self.graph.add_conditional_edges(source, route_func)
            
            # Compile graph
            self.graph = self.graph.compile()
            self._logger.info(f"Graph built with {len(self.nodes)} nodes")
        except Exception as e:
            self._logger.error(f"Failed to build graph: {e}", exc_info=True)
            self.graph = None
    
    async def execute(
        self,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the workflow graph.
        
        Args:
            initial_state: Initial state for the graph
            
        Returns:
            Final state after execution
        """
        if not self.graph:
            self.build_graph()
        
        if not self.graph:
            return {
                "success": False,
                "error": "Graph not available",
                "execution_history": self.execution_history
            }
        
        start_time = time.time()
        state = initial_state or {
            "messages": [],
            "current_step": "start",
            "results": {},
            "errors": [],
            "metadata": {}
        }
        
        try:
            # Execute graph
            if HAS_LANGGRAPH:
                final_state = await self.graph.ainvoke(state)
            else:
                # Fallback execution
                final_state = await self._fallback_execute(state)
            
            execution_time = time.time() - start_time
            
            self.execution_history.append({
                "timestamp": time.time(),
                "execution_time": execution_time,
                "final_state": final_state
            })
            
            return {
                "success": True,
                "final_state": final_state,
                "execution_time": execution_time,
                "execution_history": self.execution_history
            }
            
        except Exception as e:
            self._logger.error(f"Graph execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "execution_history": self.execution_history
            }
    
    async def _fallback_execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback execution when LangGraph is not available."""
        # Find entry point (first node without incoming edges or explicit start)
        entry_points = []
        all_targets = set()
        for targets in self.edges.values():
            all_targets.update(targets)
        
        # Nodes that are not targets of any edge are entry points
        for node_name in self.nodes.keys():
            if node_name not in all_targets:
                entry_points.append(node_name)
        
        # Start from first entry point or first node
        current = entry_points[0] if entry_points else (list(self.nodes.keys())[0] if self.nodes else None)
        
        visited = set()
        max_iterations = 100
        iteration = 0
        
        while current and current in self.nodes and iteration < max_iterations:
            if current in visited:
                self._logger.warning(f"Cycle detected at node {current}, stopping")
                break
            
            visited.add(current)
            iteration += 1
            node_func = self.nodes[current]
            state["current_step"] = current
            
            try:
                if asyncio.iscoroutinefunction(node_func):
                    result = await node_func(state)
                else:
                    result = await asyncio.to_thread(node_func, state)
                
                if isinstance(result, dict):
                    state.update(result)
                else:
                    state["results"][current] = result
                
                # Determine next node
                if current in self.conditional_routes:
                    current = self.conditional_routes[current](state)
                elif current in self.edges and self.edges[current]:
                    current = self.edges[current][0]
                else:
                    current = None
                    
            except Exception as e:
                state["errors"].append(f"Node {current} failed: {e}")
                self._logger.error(f"Node {current} failed: {e}")
                break
        
        if iteration >= max_iterations:
            state["errors"].append("Maximum iterations reached")
            self._logger.warning("Maximum iterations reached in fallback execution")
        
        return state
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "workflow_name": self.workflow_name,
            "total_executions": len(self.execution_history),
            "nodes": list(self.nodes.keys()),
            "edges": self.edges,
            "has_conditional_routes": len(self.conditional_routes) > 0
        }


# ============================================================================
# REAL-WORLD EXAMPLE
# ============================================================================

async def langgraph_real_world_example() -> None:
    """
    Real-World Scenario: LangGraph - Content Approval Workflow.
    
    REAL-WORLD SCENARIO:
    ====================
    You're building a content approval workflow:
    - Process content submissions
    - Validate content quality
    - Route based on content type
    - Get approval for sensitive content
    - Problem: Need structured, conditional workflow
    
    THE PROBLEM WITHOUT LANGGRAPH:
    ==============================
    - Manual workflow → error-prone
    - No state management → lost context
    - No conditional routing → inflexible
    - Complex code → hard to maintain
    - No visibility → can't track progress
    
    THE SOLUTION:
    =============
    LangGraph enables:
    - Structured workflows → reliable processing
    - State management → preserve context
    - Conditional routing → flexible workflows
    - Clear structure → maintainable code
    - Execution tracking → full visibility
    
    WHEN TO USE LANGGRAPH:
    ======================
    ✅ Multi-step workflows
    ✅ Conditional processing
    ✅ State management needed
    ✅ Complex business logic
    ✅ Production workflow systems
    """
    print("=" * 70)
    print("REAL-WORLD SCENARIO: Content Approval Workflow")
    print("=" * 70)
    print()
    print("SITUATION:")
    print("  - Content approval workflow")
    print("  - Process content submissions")
    print("  - Validate content quality")
    print("  - Route based on content type")
    print("  - Get approval for sensitive content")
    print("  - Problem: Need structured, conditional workflow")
    print()
    print("THE PROBLEM:")
    print("  Without LangGraph:")
    print("    ❌ Manual workflow → error-prone")
    print("    ❌ No state management → lost context")
    print("    ❌ No conditional routing → inflexible")
    print("    ❌ Complex code → hard to maintain")
    print("    ❌ No visibility → can't track progress")
    print()
    print("THE SOLUTION:")
    print("  With LangGraph:")
    print("    ✅ Structured workflows → reliable processing")
    print("    ✅ State management → preserve context")
    print("    ✅ Conditional routing → flexible workflows")
    print("    ✅ Clear structure → maintainable code")
    print("    ✅ Execution tracking → full visibility")
    print()
    print("=" * 70)
    print()
    
    # Define node functions
    async def validate_content(state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content quality."""
        content = state.get("content", "")
        state["results"]["validation"] = {
            "valid": len(content) > 10,
            "quality_score": 0.85 if len(content) > 50 else 0.6
        }
        state["messages"].append("Content validated")
        return state
    
    async def classify_content(state: Dict[str, Any]) -> Dict[str, Any]:
        """Classify content type."""
        content = state.get("content", "")
        content_type = "sensitive" if "confidential" in content.lower() else "normal"
        state["results"]["classification"] = {"type": content_type}
        state["messages"].append(f"Content classified as: {content_type}")
        return state
    
    async def route_decision(state: Dict[str, Any]) -> str:
        """Conditional routing based on content type."""
        classification = state.get("results", {}).get("classification", {})
        content_type = classification.get("type", "normal")
        return "approve_sensitive" if content_type == "sensitive" else "approve_normal"
    
    async def approve_sensitive(state: Dict[str, Any]) -> Dict[str, Any]:
        """Approve sensitive content (requires human review)."""
        state["results"]["approval"] = {"status": "pending_review", "requires_human": True}
        state["messages"].append("Sensitive content requires human approval")
        return state
    
    async def approve_normal(state: Dict[str, Any]) -> Dict[str, Any]:
        """Approve normal content automatically."""
        state["results"]["approval"] = {"status": "approved", "requires_human": False}
        state["messages"].append("Normal content approved automatically")
        return state
    
    async def publish_content(state: Dict[str, Any]) -> Dict[str, Any]:
        """Publish approved content."""
        approval = state.get("results", {}).get("approval", {})
        if approval.get("status") == "approved":
            state["results"]["publication"] = {"status": "published", "timestamp": time.time()}
            state["messages"].append("Content published successfully")
        return state
    
    # Build workflow
    orchestrator = WorkflowOrchestrator("content_approval_workflow")
    
    # Add nodes
    orchestrator.add_node("validate", validate_content)
    orchestrator.add_node("classify", classify_content)
    orchestrator.add_node("approve_sensitive", approve_sensitive)
    orchestrator.add_node("approve_normal", approve_normal)
    orchestrator.add_node("publish", publish_content)
    
    # Add edges
    orchestrator.add_edge("validate", "classify")
    orchestrator.add_edge("approve_sensitive", "publish")
    orchestrator.add_edge("approve_normal", "publish")
    
    # Add conditional routing
    orchestrator.add_conditional_route("classify", route_decision)
    
    # Execute workflow
    print("Executing workflow with normal content...")
    result1 = await orchestrator.execute({
        "content": "This is a normal blog post about Python programming.",
        "messages": [],
        "current_step": "start",
        "results": {},
        "errors": [],
        "metadata": {}
    })
    
    print(f"\nWorkflow Result: {result1['success']}")
    print(f"Execution Time: {result1.get('execution_time', 0):.3f}s")
    print(f"Messages: {result1.get('final_state', {}).get('messages', [])}")
    print(f"Final Results: {result1.get('final_state', {}).get('results', {})}")
    
    print("\n" + "-" * 70)
    print("Executing workflow with sensitive content...")
    result2 = await orchestrator.execute({
        "content": "This is confidential information about our company strategy.",
        "messages": [],
        "current_step": "start",
        "results": {},
        "errors": [],
        "metadata": {}
    })
    
    print(f"\nWorkflow Result: {result2['success']}")
    print(f"Execution Time: {result2.get('execution_time', 0):.3f}s")
    print(f"Messages: {result2.get('final_state', {}).get('messages', [])}")
    print(f"Final Results: {result2.get('final_state', {}).get('results', {})}")
    
    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS:")
    print("=" * 70)
    print("  ✅ LangGraph provides structured workflow orchestration")
    print("  ✅ State management preserves context across nodes")
    print("  ✅ Conditional routing enables flexible workflows")
    print("  ✅ Clear structure makes code maintainable")
    print("  ✅ Execution tracking provides full visibility")
    print()
    print("Use LangGraph when:")
    print("  - Building multi-step workflows")
    print("  - Need conditional processing")
    print("  - State management is critical")
    print("  - Complex business logic")
    print("  - Production workflow systems")
    print("=" * 70)

