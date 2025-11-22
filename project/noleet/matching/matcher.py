"""Project matching engine that finds projects based on topic combinations."""

from typing import List, Set
import logging

from noleet.core.models import Project, Topic


class ProjectMatcher:
    """Matches projects based on selected DSA topics."""
    
    def __init__(self) -> None:
        """Initialize project matcher."""
        self._logger = logging.getLogger(__name__)
    
    def find_matching_projects(
        self,
        projects: List[Project],
        selected_topics: Set[Topic],
        min_match_score: float = 30.0
    ) -> List[Project]:
        """
        Find projects that match selected topics.
        
        Args:
            projects: List of all available projects
            selected_topics: Set of topics user selected
            min_match_score: Minimum match score threshold
            
        Returns:
            List of matching projects sorted by match score
        """
        if not selected_topics:
            self._logger.warning("No topics selected, returning empty list")
            return []
        
        matching_projects: List[tuple[Project, float]] = []
        
        for project in projects:
            if not project.matches_topics(selected_topics):
                continue
            
            score = project.get_match_score(selected_topics)
            if score >= min_match_score:
                matching_projects.append((project, score))
        
        matching_projects.sort(key=lambda x: x[1], reverse=True)
        
        self._logger.info(
            f"Found {len(matching_projects)} projects matching topics {selected_topics}",
            extra={
                "selected_topics": [t.value for t in selected_topics],
                "match_count": len(matching_projects),
                "min_score": min_match_score
            }
        )
        
        return [project for project, _ in matching_projects]
    
    def get_topic_combinations(self, projects: List[Project]) -> List[Set[Topic]]:
        """
        Extract unique topic combinations from projects.
        
        Args:
            projects: List of all projects
            
        Returns:
            List of unique topic combinations
        """
        combinations: Set[frozenset[Topic]] = set()
        
        for project in projects:
            coverage = project.get_topic_coverage()
            primary_topics = {
                topic for topic, percentage in coverage.items() 
                if percentage >= 20.0
            }
            if primary_topics:
                combinations.add(frozenset(primary_topics))
        
        return [set(combo) for combo in combinations]

