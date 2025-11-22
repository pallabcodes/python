"""Match research papers to projects based on topics and algorithms."""

import logging
from typing import List, Set

from noleet.core.models import Project, Topic
from noleet.research.paper_parser import ResearchPaper


class ResearchMatcher:
    """Matches research papers to projects."""
    
    def __init__(self) -> None:
        """Initialize matcher."""
        self._logger = logging.getLogger(__name__)
    
    def find_matching_papers(
        self,
        papers: List[ResearchPaper],
        project: Project
    ) -> List[ResearchPaper]:
        """
        Find research papers that match a project.
        
        Args:
            papers: List of available papers
            project: Project to match papers for
            
        Returns:
            List of matching papers sorted by relevance
        """
        matches: List[tuple[ResearchPaper, float]] = []
        
        project_topics = project.primary_topics | project.required_topics
        
        for paper in papers:
            score = self._calculate_match_score(paper, project, project_topics)
            if score > 0:
                matches.append((paper, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        
        self._logger.info(
            f"Found {len(matches)} matching papers for project {project.id}",
            extra={
                "project_id": project.id,
                "match_count": len(matches),
                "project_topics": [t.value for t in project_topics]
            }
        )
        
        return [paper for paper, _ in matches]
    
    def _calculate_match_score(
        self,
        paper: ResearchPaper,
        project: Project,
        project_topics: Set[Topic]
    ) -> float:
        """
        Calculate match score between paper and project.
        
        Args:
            paper: Research paper
            project: Project
            project_topics: Topics required/primary for project
            
        Returns:
            Match score (0.0 to 1.0)
        """
        if not project_topics:
            return 0.0
        
        topic_overlap = len(paper.topics.intersection(project_topics))
        topic_score = topic_overlap / len(project_topics) if project_topics else 0.0
        
        algorithm_score = 0.0
        if paper.algorithms:
            algorithm_score = min(len(paper.algorithms) / 5.0, 1.0)
        
        technique_score = 0.0
        if paper.techniques:
            technique_score = min(len(paper.techniques) / 3.0, 1.0)
        
        total_score = (topic_score * 0.5) + (algorithm_score * 0.3) + (technique_score * 0.2)
        
        return total_score
    
    def suggest_paper_combinations(
        self,
        papers: List[ResearchPaper],
        project: Project
    ) -> List[List[ResearchPaper]]:
        """
        Suggest combinations of papers that together match a project.
        
        Args:
            papers: List of available papers
            project: Project to match for
            
        Returns:
            List of paper combinations, each combination is a list of papers
        """
        matching_papers = self.find_matching_papers(papers, project)
        
        if len(matching_papers) < 2:
            return [[p] for p in matching_papers]
        
        combinations: List[List[ResearchPaper]] = []
        
        project_topics = project.primary_topics | project.required_topics
        
        for i, paper1 in enumerate(matching_papers[:5]):
            for paper2 in matching_papers[i+1:5]:
                combined_topics = paper1.topics | paper2.topics
                if combined_topics.issuperset(project_topics):
                    combinations.append([paper1, paper2])
        
        self._logger.info(
            f"Found {len(combinations)} paper combinations for project {project.id}",
            extra={
                "project_id": project.id,
                "combination_count": len(combinations)
            }
        )
        
        return combinations[:10]

