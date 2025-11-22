"""Integrate research papers into projects."""

import logging
from typing import List, Optional

from noleet.core.models import Project, ResearchReference
from noleet.research.paper_parser import ResearchPaper
from noleet.research.matcher import ResearchMatcher


class ResearchIntegrator:
    """Integrates research papers into projects."""
    
    def __init__(self) -> None:
        """Initialize integrator."""
        self._matcher = ResearchMatcher()
        self._logger = logging.getLogger(__name__)
    
    def integrate_papers_into_project(
        self,
        project: Project,
        papers: List[ResearchPaper],
        custom_modifications: Optional[str] = None
    ) -> Project:
        """
        Integrate matching research papers into a project.
        
        Args:
            project: Project to enhance
            papers: Available research papers
            custom_modifications: Custom modifications description
            
        Returns:
            Enhanced project with research references
        """
        matching_papers = self._matcher.find_matching_papers(papers, project)
        
        if not matching_papers:
            self._logger.warning(
                f"No matching papers found for project {project.id}",
                extra={"project_id": project.id}
            )
            return project
        
        research_refs = []
        
        for paper in matching_papers[:3]:
            ref = self._create_research_reference(paper, custom_modifications)
            research_refs.append(ref)
        
        project.research_references.extend(research_refs)
        
        self._logger.info(
            f"Integrated {len(research_refs)} papers into project {project.id}",
            extra={
                "project_id": project.id,
                "paper_count": len(research_refs)
            }
        )
        
        return project
    
    def _create_research_reference(
        self,
        paper: ResearchPaper,
        custom_modifications: Optional[str] = None
    ) -> ResearchReference:
        """
        Create research reference from paper.
        
        Args:
            paper: Research paper
            custom_modifications: Custom modifications description
            
        Returns:
            Research reference
        """
        algorithms = [algo.name for algo in paper.algorithms]
        
        modifications = custom_modifications or paper.custom_modifications
        
        return ResearchReference(
            title=paper.title,
            authors=paper.authors,
            url=paper.url,
            github_repo=paper.github_repo,
            description=paper.abstract[:500] if paper.abstract else "",
            algorithms=algorithms,
            custom_modifications=modifications
        )
    
    def suggest_algorithm_modifications(
        self,
        paper: ResearchPaper,
        project: Project
    ) -> str:
        """
        Suggest custom modifications for algorithms based on project needs.
        
        Args:
            paper: Research paper
            project: Target project
            
        Returns:
            Suggested modifications description
        """
        modifications: List[str] = []
        
        project_topics = project.primary_topics | project.required_topics
        paper_topics = paper.topics
        
        if project_topics and not paper_topics.issuperset(project_topics):
            missing_topics = project_topics - paper_topics
            modifications.append(
                f"Extend algorithms to incorporate: {', '.join(t.value for t in missing_topics)}"
            )
        
        if project.difficulty == "advanced":
            modifications.append(
                "Optimize for production scale with memory and performance improvements"
            )
        
        if paper.algorithms:
            modifications.append(
                f"Combine {len(paper.algorithms)} algorithms from paper with project requirements"
            )
        
        return "; ".join(modifications) if modifications else ""

