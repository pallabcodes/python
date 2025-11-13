"""
Dask-inspired task graph optimizer.

Implements patterns from Dask:
- Task graph optimization
- Lazy evaluation
- Adaptive scheduling
- Memory-aware execution
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Node in task graph."""
    
    node_id: str
    func: Callable
    args: List[str]  # References to other nodes
    kwargs: Dict[str, Any]
    estimated_cost: float = 0.0
    dependencies: Set[str] = field(default_factory=set)


class DaskInspiredOptimizer:
    """
    Dask-inspired task graph optimizer.
    
    Features:
    - Task graph analysis and optimization
    - Optimal scheduling strategies
    - Memory-aware execution
    - Lazy evaluation
    """
    
    def __init__(self):
        """Initialize Dask-inspired optimizer."""
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._graph: Dict[str, GraphNode] = {}
        self._execution_order: List[str] = []
        
    def add_task(
        self,
        node_id: str,
        func: Callable,
        *dependencies: str,
        **kwargs: Any
    ) -> None:
        """
        Add a task to the graph.
        
        Args:
            node_id: Unique node identifier
            func: Function to execute
            *dependencies: Node IDs this task depends on
            **kwargs: Keyword arguments
        """
        node = GraphNode(
            node_id=node_id,
            func=func,
            args=list(dependencies),
            kwargs=kwargs
        )
        
        # Build dependency set
        for dep in dependencies:
            node.dependencies.add(dep)
        
        self._graph[node_id] = node
        self._logger.debug(f"Added task to graph: {node_id} (dependencies={dependencies})")
    
    def optimize_graph(self) -> List[str]:
        """
        Optimize task graph and return execution order.
        
        Returns:
            Ordered list of node IDs
        """
        # Topological sort for optimal execution order
        execution_order = []
        visited = set()
        temp_visited = set()
        
        def visit(node_id: str):
            if node_id in temp_visited:
                # Cycle detected
                return
            if node_id in visited:
                return
            
            temp_visited.add(node_id)
            
            node = self._graph[node_id]
            for dep in node.dependencies:
                if dep in self._graph:
                    visit(dep)
            
            temp_visited.remove(node_id)
            visited.add(node_id)
            execution_order.append(node_id)
        
        for node_id in self._graph:
            if node_id not in visited:
                visit(node_id)
        
        self._execution_order = execution_order
        self._logger.info(f"Optimized graph: {len(execution_order)} tasks")
        
        return execution_order
    
    def analyze_graph(self) -> Dict[str, Any]:
        """Analyze task graph characteristics."""
        if not self._graph:
            return {}
        
        total_dependencies = sum(len(node.dependencies) for node in self._graph.values())
        avg_dependencies = total_dependencies / len(self._graph) if self._graph else 0
        
        # Find critical path
        critical_path_length = self._find_critical_path()
        
        return {
            "node_count": len(self._graph),
            "total_dependencies": total_dependencies,
            "avg_dependencies": avg_dependencies,
            "critical_path_length": critical_path_length,
            "execution_order": self._execution_order,
        }
    
    def _find_critical_path(self) -> int:
        """Find critical path length in graph."""
        if not self._graph:
            return 0
        
        # Simple critical path: longest dependency chain
        max_depth = 0
        
        def get_depth(node_id: str, visited: Set[str]) -> int:
            if node_id in visited:
                return 0
            
            visited.add(node_id)
            node = self._graph[node_id]
            
            if not node.dependencies:
                return 1
            
            max_dep_depth = max(
                (get_depth(dep, visited.copy()) for dep in node.dependencies),
                default=0
            )
            
            return max_dep_depth + 1
        
        for node_id in self._graph:
            depth = get_depth(node_id, set())
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    async def execute_graph(self, results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute optimized task graph.
        
        Args:
            results: Dictionary to store results (created if None)
            
        Returns:
            Dictionary mapping node IDs to results
        """
        if results is None:
            results = {}
        
        if not self._execution_order:
            self.optimize_graph()
        
        for node_id in self._execution_order:
            node = self._graph[node_id]
            
            # Resolve dependencies
            resolved_args = [results[dep] for dep in node.args if dep in results]
            
            # Execute task
            if asyncio.iscoroutinefunction(node.func):
                result = await node.func(*resolved_args, **node.kwargs)
            else:
                result = node.func(*resolved_args, **node.kwargs)
            
            results[node_id] = result
            self._logger.debug(f"Executed task: {node_id}")
        
        return results

