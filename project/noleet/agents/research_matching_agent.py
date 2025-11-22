"""Research matching agent for intelligent paper-to-project matching."""

import logging
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

from .base.agent_base import BaseAgent, AgentResult
from ..core.models import Project, Topic
from ..research.paper_parser import ResearchPaper
from ..research.matcher import ResearchMatcher
from ..research.integrator import ResearchIntegrator
from ..storage.repository import ProjectRepository
from ..llm.llm_config import LLMConfig


class ResearchMatchingAgent(BaseAgent):
    """Agent for intelligent research paper to project matching."""

    def __init__(
        self,
        research_papers: Optional[List[ResearchPaper]] = None,
        project_repository: Optional[ProjectRepository] = None,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize research matching agent.

        Args:
            research_papers: List of available research papers
            project_repository: Repository for accessing projects
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        super().__init__("research_matching", llm_config, logger)

        self._research_papers = research_papers or []
        self._project_repo = project_repository or ProjectRepository()
        self._matcher = ResearchMatcher(logger)
        self._integrator = ResearchIntegrator()

        # Cache for loaded projects
        self._projects_cache: Optional[List[Project]] = None
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = 600  # 10 minutes

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Match research papers to projects based on input criteria.

        Args:
            input_data: Input data containing project info or paper criteria

        Returns:
            Matching results
        """
        try:
            project_id = input_data.get("project_id")
            project_query = input_data.get("project_query", "")
            topics = input_data.get("topics", [])
            max_matches = input_data.get("max_matches", 5)
            include_combinations = input_data.get("include_combinations", True)

            if not project_id and not project_query and not topics:
                return AgentResult(
                    success=False,
                    message="No project or criteria provided for research matching",
                    errors=["Missing project_id, project_query, or topics"]
                )

            # Get target project(s)
            target_projects = self._get_target_projects(project_id, project_query, topics)

            if not target_projects:
                return AgentResult(
                    success=False,
                    message="No matching projects found",
                    errors=["Could not identify target projects"]
                )

            # Load research papers
            papers = self._load_research_papers()

            if not papers:
                return AgentResult(
                    success=False,
                    message="No research papers available for matching",
                    errors=["Empty research paper collection"]
                )

            all_matches = []
            all_combinations = []

            # Match papers to each target project
            for project in target_projects[:3]:  # Limit to top 3 projects
                project_matches = self._match_papers_to_project(
                    project, papers, max_matches
                )
                all_matches.extend(project_matches)

                if include_combinations:
                    combinations = self._matcher.suggest_paper_combinations(
                        papers, project
                    )
                    all_combinations.extend([
                        {
                            "project_id": project.id,
                            "project_title": project.title,
                            "papers": [{"title": p.title, "url": p.url} for p in combo]
                        }
                        for combo in combinations[:2]  # Limit combinations per project
                    ])

            # Remove duplicates and sort by relevance
            unique_matches = self._deduplicate_matches(all_matches)

            # Generate reasoning
            reasoning = self._generate_matching_reasoning(
                target_projects, unique_matches, all_combinations
            )

            result_data = {
                "matches": unique_matches,
                "combinations": all_combinations,
                "target_projects": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "topics": [t.value for t in p.primary_topics]
                    }
                    for p in target_projects
                ],
                "reasoning": reasoning,
                "total_matches": len(unique_matches),
                "total_combinations": len(all_combinations)
            }

            # Add to memory
            self._add_to_memory(
                f"Matched research papers for {len(target_projects)} projects",
                f"Found {len(unique_matches)} matches, {len(all_combinations)} combinations",
                {"project_count": len(target_projects), "match_count": len(unique_matches)}
            )

            self._logger.info(
                f"Successfully matched {len(unique_matches)} papers for {len(target_projects)} projects"
            )

            return AgentResult(
                success=True,
                data=result_data,
                message=f"Found {len(unique_matches)} research paper matches"
            )

        except Exception as e:
            self._logger.error(f"Research matching failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                message="Research matching failed",
                errors=[str(e)]
            )

    def _get_target_projects(
        self,
        project_id: Optional[str],
        project_query: str,
        topics: List[str]
    ) -> List[Project]:
        """Get target projects based on input criteria."""
        projects = self._load_projects()

        if project_id:
            # Specific project requested
            matching_projects = [p for p in projects if p.id == project_id]
            return matching_projects

        if project_query:
            # Search by query
            query_lower = project_query.lower()
            matching_projects = [
                p for p in projects
                if query_lower in p.title.lower() or
                   query_lower in p.description.lower()
            ]
            return matching_projects[:5]  # Limit results

        if topics:
            # Search by topics
            topic_enums = self._parse_topics(topics)
            matching_projects = []

            for project in projects:
                project_topics = project.primary_topics | project.required_topics
                if any(topic in project_topics for topic in topic_enums):
                    matching_projects.append(project)

            return matching_projects[:5]

        return []

    def _parse_topics(self, topic_strings: List[str]) -> List[Topic]:
        """Parse topic strings into Topic enums."""
        topics = []

        for topic_str in topic_strings:
            normalized = topic_str.lower().replace(" ", "_").replace("-", "_")

            try:
                topic = Topic(normalized)
                topics.append(topic)
            except ValueError:
                continue

        return topics

    def _load_projects(self) -> List[Project]:
        """Load projects with caching."""
        import time

        current_time = time.time()

        if (self._projects_cache is None or
            self._cache_timestamp is None or
            current_time - self._cache_timestamp > self._cache_ttl):

            self._projects_cache = self._project_repo.load_projects()
            self._cache_timestamp = current_time

        return self._projects_cache or []

    def _load_research_papers(self) -> List[ResearchPaper]:
        """Load research papers."""
        # For now, return cached papers. In a full implementation,
        # this would load from a research paper repository
        return self._research_papers

    def _match_papers_to_project(
        self,
        project: Project,
        papers: List[ResearchPaper],
        max_matches: int
    ) -> List[Dict[str, Any]]:
        """Match papers to a specific project."""
        matches = self._matcher.find_matching_papers(papers, project)

        formatted_matches = []
        for paper, score in matches[:max_matches]:
            formatted_matches.append({
                "project_id": project.id,
                "project_title": project.title,
                "paper_title": paper.title,
                "paper_authors": paper.authors,
                "paper_url": paper.url,
                "match_score": score,
                "matching_topics": list(paper.topics.intersection(
                    project.primary_topics | project.required_topics
                )),
                "algorithms": paper.algorithms,
                "techniques": paper.techniques
            })

        return formatted_matches

    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate matches and sort by score."""
        seen = set()
        unique_matches = []

        for match in matches:
            key = (match["project_id"], match["paper_title"])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)

        # Sort by match score descending
        unique_matches.sort(key=lambda x: x["match_score"], reverse=True)

        return unique_matches

    def _generate_matching_reasoning(
        self,
        projects: List[Project],
        matches: List[Dict[str, Any]],
        combinations: List[Dict[str, Any]]
    ) -> str:
        """Generate reasoning for the matching results."""
        if not matches:
            return "No suitable research papers found for the given projects."

        if self.is_available():
            return self._llm_matching_reasoning(projects, matches, combinations)
        else:
            return self._fallback_matching_reasoning(projects, matches, combinations)

    def _llm_matching_reasoning(
        self,
        projects: List[Project],
        matches: List[Dict[str, Any]],
        combinations: List[Dict[str, Any]]
    ) -> str:
        """Generate reasoning using LLM."""
        prompt = f"""
        Analyze these research paper to project matches and explain why they were chosen.

        Projects:
        {self._format_projects_for_prompt(projects)}

        Top Matches:
        {self._format_matches_for_prompt(matches[:5])}

        Paper Combinations:
        {len(combinations)} combinations suggested

        Explain:
        1. Why these specific papers match the projects
        2. What algorithms/techniques from the papers are relevant
        3. Why the combinations are valuable
        4. How this research enhances the project implementation

        Keep response under 400 words.
        """

        try:
            llm = self._llm_factory.create_llm()
            response = llm.generate(prompt)
            return response.strip()
        except Exception as e:
            self._logger.warning(f"LLM reasoning generation failed: {e}")
            return self._fallback_matching_reasoning(projects, matches, combinations)

    def _fallback_matching_reasoning(
        self,
        projects: List[Project],
        matches: List[Dict[str, Any]],
        combinations: List[Dict[str, Any]]
    ) -> str:
        """Generate fallback reasoning without LLM."""
        reasoning_parts = [
            f"I matched {len(matches)} research papers to {len(projects)} projects based on topic alignment and algorithmic relevance."
        ]

        if matches:
            top_match = matches[0]
            reasoning_parts.append(
                f"The top match '{top_match['paper_title']}' (score: {top_match['match_score']:.2f}) "
                f"provides relevant algorithms for {top_match['project_title']}."
            )

        if combinations:
            reasoning_parts.append(
                f"I also identified {len(combinations)} paper combinations that together "
                "cover multiple aspects of the projects."
            )

        reasoning_parts.append(
            "These research papers will help you implement more sophisticated algorithms "
            "and learn cutting-edge techniques beyond basic textbook approaches."
        )

        return ' '.join(reasoning_parts)

    def _format_projects_for_prompt(self, projects: List[Project]) -> str:
        """Format projects for LLM prompt."""
        formatted = []

        for project in projects[:3]:
            formatted.append(f"""
            - {project.title}: {project.primary_topics}
              Focus: {project.description[:100]}...
            """)

        return '\n'.join(formatted)

    def _format_matches_for_prompt(self, matches: List[Dict[str, Any]]) -> str:
        """Format matches for LLM prompt."""
        formatted = []

        for match in matches:
            formatted.append(f"""
            - {match['paper_title']} → {match['project_title']}
              Score: {match['match_score']:.2f}
              Matching topics: {match['matching_topics']}
              Algorithms: {match['algorithms'][:3]}
            """)

        return '\n'.join(formatted)

    def add_research_paper(self, paper: ResearchPaper):
        """Add a research paper to the collection."""
        if paper not in self._research_papers:
            self._research_papers.append(paper)
            self._logger.info(f"Added research paper: {paper.title}")

    def integrate_paper_into_project(
        self,
        project_id: str,
        paper_title: str,
        custom_modifications: Optional[str] = None
    ) -> bool:
        """
        Integrate a specific paper into a project.

        Args:
            project_id: Project identifier
            paper_title: Research paper title
            custom_modifications: Custom modifications description

        Returns:
            True if integration successful
        """
        try:
            projects = self._load_projects()
            papers = self._load_research_papers()

            project = next((p for p in projects if p.id == project_id), None)
            paper = next((p for p in papers if p.title == paper_title), None)

            if not project or not paper:
                self._logger.error(f"Project or paper not found: {project_id}, {paper_title}")
                return False

            enhanced_project = self._integrator.integrate_papers_into_project(
                project, [paper], custom_modifications
            )

            # Update the cached project
            if self._projects_cache:
                for i, p in enumerate(self._projects_cache):
                    if p.id == project_id:
                        self._projects_cache[i] = enhanced_project
                        break

            self._logger.info(f"Integrated paper '{paper_title}' into project '{project_id}'")
            return True

        except Exception as e:
            self._logger.error(f"Paper integration failed: {e}")
            return False

    def get_matching_stats(self) -> Dict[str, Any]:
        """Get matching system statistics."""
        return {
            "total_projects": len(self._load_projects()),
            "total_research_papers": len(self._research_papers),
            "matcher_available": True,
            "integrator_available": True,
            "cache_status": {
                "projects_cached": self._projects_cache is not None,
                "cache_age_seconds": (
                    None if self._cache_timestamp is None
                    else __import__("time").time() - self._cache_timestamp
                )
            }
        }

