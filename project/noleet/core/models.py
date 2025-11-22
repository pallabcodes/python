"""Core data models for NoLeet platform."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum


class Topic(str, Enum):
    """DSA topics available in the platform."""
    
    DYNAMIC_PROGRAMMING = "dynamic_programming"
    SLIDING_WINDOW = "sliding_window"
    MERGE_INTERVALS = "merge_intervals"
    TWO_POINTERS = "two_pointers"
    BINARY_SEARCH = "binary_search"
    GRAPH_TRAVERSAL = "graph_traversal"
    TREE_TRAVERSAL = "tree_traversal"
    BACKTRACKING = "backtracking"
    GREEDY = "greedy"
    UNION_FIND = "union_find"
    TRIE = "trie"
    HEAP = "heap"
    HASH_TABLE = "hash_table"
    LINKED_LIST = "linked_list"
    STACK = "stack"
    QUEUE = "queue"
    BIT_MANIPULATION = "bit_manipulation"
    SORTING = "sorting"
    STRING_MATCHING = "string_matching"


@dataclass
class DSAInvolvement:
    """Represents DSA concept involvement in a task."""
    
    topic: Topic
    percentage: float
    
    def __post_init__(self) -> None:
        """Validate percentage is between 0 and 100."""
        if not 0.0 <= self.percentage <= 100.0:
            raise ValueError(f"Percentage must be between 0 and 100, got {self.percentage}")


@dataclass
class Subtask:
    """A subtask within a task."""
    
    id: str
    title: str
    description: str
    dsa_involvements: List[DSAInvolvement] = field(default_factory=list)
    order: int = 0
    
    def get_total_dsa_percentage(self) -> float:
        """Calculate total DSA involvement percentage."""
        return sum(inv.percentage for inv in self.dsa_involvements)


@dataclass
class Task:
    """A task within a project."""
    
    id: str
    title: str
    description: str
    subtasks: List[Subtask] = field(default_factory=list)
    dsa_involvements: List[DSAInvolvement] = field(default_factory=list)
    order: int = 0
    
    def get_total_dsa_percentage(self) -> float:
        """Calculate total DSA involvement percentage."""
        task_percentage = sum(inv.percentage for inv in self.dsa_involvements)
        subtask_percentage = sum(
            subtask.get_total_dsa_percentage() 
            for subtask in self.subtasks
        )
        return max(task_percentage, subtask_percentage)
    
    def get_primary_topics(self) -> List[Topic]:
        """Get topics with highest involvement."""
        all_involvements = self.dsa_involvements.copy()
        for subtask in self.subtasks:
            all_involvements.extend(subtask.dsa_involvements)
        
        if not all_involvements:
            return []
        
        sorted_topics = sorted(
            all_involvements,
            key=lambda inv: inv.percentage,
            reverse=True
        )
        return [inv.topic for inv in sorted_topics[:3]]


@dataclass
class ResearchReference:
    """Reference to research paper or open-source implementation."""
    
    title: str
    authors: List[str]
    url: Optional[str] = None
    github_repo: Optional[str] = None
    description: str = ""
    algorithms: List[str] = field(default_factory=list)
    custom_modifications: str = ""


@dataclass
class Project:
    """A project that teaches DSA through building."""
    
    id: str
    title: str
    description: str
    short_description: str
    tasks: List[Task] = field(default_factory=list)
    required_topics: Set[Topic] = field(default_factory=set)
    primary_topics: Set[Topic] = field(default_factory=set)
    difficulty: str = "intermediate"
    estimated_hours: int = 0
    research_references: List[ResearchReference] = field(default_factory=list)
    github_template: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def get_topic_coverage(self) -> Dict[Topic, float]:
        """Calculate coverage percentage for each topic."""
        coverage: Dict[Topic, float] = {}
        
        for task in self.tasks:
            for involvement in task.dsa_involvements:
                coverage[involvement.topic] = (
                    coverage.get(involvement.topic, 0.0) + involvement.percentage
                )
            for subtask in task.subtasks:
                for involvement in subtask.dsa_involvements:
                    coverage[involvement.topic] = (
                        coverage.get(involvement.topic, 0.0) + involvement.percentage
                    )
        
        total = sum(coverage.values())
        if total > 0:
            return {topic: (percentage / total) * 100 for topic, percentage in coverage.items()}
        return coverage
    
    def matches_topics(self, selected_topics: Set[Topic]) -> bool:
        """Check if project matches selected topics."""
        project_topics = self.get_topic_coverage().keys()
        return bool(selected_topics.intersection(project_topics))
    
    def get_match_score(self, selected_topics: Set[Topic]) -> float:
        """Calculate match score based on selected topics."""
        coverage = self.get_topic_coverage()
        if not coverage:
            return 0.0
        
        matching_topics = selected_topics.intersection(coverage.keys())
        if not matching_topics:
            return 0.0
        
        total_score = sum(coverage[topic] for topic in matching_topics)
        return total_score / len(selected_topics) if selected_topics else 0.0

