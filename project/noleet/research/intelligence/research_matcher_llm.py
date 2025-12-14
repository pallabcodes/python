"""LLM-powered research paper to project matching."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..matcher import ResearchMatch
from ...core.models import Project, Topic
from ...llm.llm_factory import LLMFactory
from ...llm.llm_config import LLMConfig


@dataclass
class LLMMatchResult:
    """LLM-powered research to project matching result."""
    project_id: str
    paper_title: str
    match_score: float  # 0.0-1.0
    reasoning: str
    relevant_algorithms: List[str]
    application_areas: List[str]
    implementation_suggestions: List[str]
    confidence_score: float  # 0.0-1.0
    match_type: str  # 'direct', 'adaptation', 'inspiration', 'none'


class ResearchMatcherLLM:
    """Uses LLM to intelligently match research papers to coding projects."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize LLM-powered research matcher.

        Args:
            llm_config: LLM configuration
            logger: Optional logger instance
        """
        self._config = llm_config or LLMConfig()
        self._llm_factory = LLMFactory(self._config, logger)
        self._logger = logger or logging.getLogger(__name__)

        # Matching prompts
        self._matching_prompt = self._build_matching_prompt()
        self._detailed_analysis_prompt = self._build_detailed_analysis_prompt()

    def _build_matching_prompt(self) -> str:
        """Build the research-to-project matching prompt."""
        return """You are an expert at connecting academic research to practical coding projects. Analyze how this research paper relates to coding projects.

Research Paper:
Title: {paper_title}
Algorithms: {algorithms}
Topics: {topics}
Applications: {applications}

Coding Project:
Title: {project_title}
Description: {project_description}
Topics: {project_topics}
DSA Concepts: {dsa_concepts}

Analyze the relationship and provide:

1. **Match Score**: 0.0-1.0 indicating how well the research applies to this project
2. **Reasoning**: Detailed explanation of the connection
3. **Relevant Algorithms**: Which paper algorithms are most relevant
4. **Application Areas**: How the research can be applied in this project
5. **Implementation Suggestions**: Specific ways to use the research
6. **Confidence Score**: How confident you are in this matching (0.0-1.0)
7. **Match Type**: "direct" (research directly solves project), "adaptation" (research can be adapted), "inspiration" (research inspires solution), "none" (no meaningful connection)

Consider:
- Algorithmic overlap
- Problem domain similarity
- Complexity improvements possible
- Practical implementation feasibility

Return as JSON with keys: match_score, reasoning, relevant_algorithms, application_areas, implementation_suggestions, confidence_score, match_type"""

    def _build_detailed_analysis_prompt(self) -> str:
        """Build the detailed matching analysis prompt."""
        return """Provide a detailed technical analysis of how this research can enhance this coding project.

Research: {paper_title}
Project: {project_title}

Focus on:
1. **Algorithmic Improvements**: How research algorithms can improve project performance
2. **Implementation Strategies**: Step-by-step integration approaches
3. **Complexity Analysis**: Expected performance gains
4. **Edge Cases**: How research handles edge cases relevant to the project
5. **Code Structure**: How to organize the implementation

Return detailed technical analysis."""

    def match_paper_to_project_llm(
        self,
        paper_title: str,
        paper_algorithms: List[str],
        paper_topics: List[str],
        paper_applications: List[str],
        project: Project
    ) -> LLMMatchResult:
        """
        Match a research paper to a project using LLM analysis.

        Args:
            paper_title: Title of the research paper
            paper_algorithms: List of algorithms from the paper
            paper_topics: Research topics
            paper_applications: Application areas
            project: Project to match against

        Returns:
            LLM-powered matching result
        """
        try:
            # Prepare project information
            project_topics = [topic.value for topic in project.topics]
            dsa_concepts = []
            for task in project.tasks:
                for involvement in task.dsa_involvements:
                    dsa_concepts.append(involvement.topic.value)

            # Format matching prompt
            prompt = self._matching_prompt.format(
                paper_title=paper_title,
                algorithms=", ".join(paper_algorithms) if paper_algorithms else "General algorithmic research",
                topics=", ".join(paper_topics) if paper_topics else "Computer science research",
                applications=", ".join(paper_applications) if paper_applications else "Algorithmic applications",
                project_title=project.title,
                project_description=project.description,
                project_topics=", ".join(project_topics),
                dsa_concepts=", ".join(set(dsa_concepts)) if dsa_concepts else "General DSA concepts"
            )

            # Get LLM matching analysis
            llm = self._llm_factory.create_llm()
            response = llm.generate(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent matching
                max_tokens=800
            )

            # Parse matching result
            match_data = self._parse_matching_response(response)

            return LLMMatchResult(
                project_id=project.id,
                paper_title=paper_title,
                match_score=float(match_data.get("match_score", 0.0)),
                reasoning=match_data.get("reasoning", "LLM matching analysis"),
                relevant_algorithms=match_data.get("relevant_algorithms", []),
                application_areas=match_data.get("application_areas", []),
                implementation_suggestions=match_data.get("implementation_suggestions", []),
                confidence_score=float(match_data.get("confidence_score", 0.5)),
                match_type=match_data.get("match_type", "none")
            )

        except Exception as e:
            self._logger.error(f"Failed to match paper {paper_title} to project {project.title}: {e}")
            return self._fallback_matching(project.id, paper_title)

    def _parse_matching_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM matching response."""
        try:
            import json

            # Try to extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return json.loads(response)

        except (json.JSONDecodeError, ValueError) as e:
            self._logger.warning(f"Failed to parse matching response: {e}")
            return self._get_default_matching_structure()

    def _get_default_matching_structure(self) -> Dict[str, Any]:
        """Get default matching structure when parsing fails."""
        return {
            "match_score": 0.0,
            "reasoning": "Failed to analyze match",
            "relevant_algorithms": [],
            "application_areas": [],
            "implementation_suggestions": [],
            "confidence_score": 0.0,
            "match_type": "none"
        }

    def _fallback_matching(self, project_id: str, paper_title: str) -> LLMMatchResult:
        """Provide fallback matching when LLM fails."""
        return LLMMatchResult(
            project_id=project_id,
            paper_title=paper_title,
            match_score=0.0,
            reasoning="Fallback matching due to analysis failure",
            relevant_algorithms=[],
            application_areas=[],
            implementation_suggestions=[],
            confidence_score=0.0,
            match_type="none"
        )

    def batch_match_papers_to_projects(
        self,
        papers: List[Dict[str, Any]],
        projects: List[Project],
        min_score_threshold: float = 0.3
    ) -> List[LLMMatchResult]:
        """
        Match multiple papers to multiple projects.

        Args:
            papers: List of paper dictionaries
            projects: List of projects
            min_score_threshold: Minimum score to include in results

        Returns:
            List of matching results above threshold
        """
        results = []

        for paper in papers:
            for project in projects:
                match_result = self.match_paper_to_project_llm(
                    paper_title=paper["title"],
                    paper_algorithms=paper.get("algorithms", []),
                    paper_topics=paper.get("topics", []),
                    paper_applications=paper.get("applications", []),
                    project=project
                )

                # Only include results above threshold
                if match_result.match_score >= min_score_threshold:
                    results.append(match_result)

        # Sort by match score (highest first)
        results.sort(key=lambda x: x.match_score, reverse=True)

        self._logger.info(f"Found {len(results)} paper-project matches above threshold {min_score_threshold}")
        return results

    def get_detailed_match_analysis(
        self,
        paper_title: str,
        project: Project
    ) -> Dict[str, Any]:
        """
        Get detailed analysis of how a paper can enhance a project.

        Args:
            paper_title: Research paper title
            project: Project to analyze

        Returns:
            Detailed technical analysis
        """
        try:
            prompt = self._detailed_analysis_prompt.format(
                paper_title=paper_title,
                project_title=project.title
            )

            llm = self._llm_factory.create_llm()
            response = llm.generate(
                prompt=prompt,
                temperature=0.2,  # Slightly higher for detailed analysis
                max_tokens=1200
            )

            return {
                "paper_title": paper_title,
                "project_title": project.title,
                "detailed_analysis": response,
                "analysis_type": "llm_detailed"
            }

        except Exception as e:
            self._logger.error(f"Failed to get detailed analysis for {paper_title} -> {project.title}: {e}")
            return {
                "paper_title": paper_title,
                "project_title": project.title,
                "detailed_analysis": "Analysis failed",
                "analysis_type": "error"
            }

    def rank_matches_by_relevance(
        self,
        matches: List[LLMMatchResult],
        criteria: Optional[Dict[str, float]] = None
    ) -> List[LLMMatchResult]:
        """
        Rank matches by multiple relevance criteria.

        Args:
            matches: List of match results
            criteria: Weighting criteria (default: balanced)

        Returns:
            Ranked list of matches
        """
        if not matches:
            return []

        # Default criteria weights
        criteria = criteria or {
            "match_score": 0.4,
            "confidence_score": 0.3,
            "relevance_count": 0.2,  # Based on number of relevant algorithms
            "application_count": 0.1,  # Based on application areas
        }

        def calculate_weighted_score(match: LLMMatchResult) -> float:
            relevance_count = len(match.relevant_algorithms)
            application_count = len(match.application_areas)

            return (
                match.match_score * criteria["match_score"] +
                match.confidence_score * criteria["confidence_score"] +
                min(relevance_count / 5.0, 1.0) * criteria["relevance_count"] +  # Cap at 5 algorithms
                min(application_count / 3.0, 1.0) * criteria["application_count"]   # Cap at 3 applications
            )

        # Sort by weighted score
        ranked_matches = sorted(matches, key=calculate_weighted_score, reverse=True)

        return ranked_matches

    def filter_matches_by_topic_overlap(
        self,
        matches: List[LLMMatchResult],
        project_topics: List[Topic],
        min_overlap: int = 1
    ) -> List[LLMMatchResult]:
        """
        Filter matches based on topic overlap.

        Args:
            matches: List of match results
            project_topics: Project's DSA topics
            min_overlap: Minimum topic overlap required

        Returns:
            Filtered matches
        """
        filtered_matches = []

        project_topic_names = {topic.value for topic in project_topics}

        for match in matches:
            # Simple topic overlap check (could be enhanced with LLM)
            match_topics = set()
            # Extract topics from reasoning and suggestions
            reasoning_lower = match.reasoning.lower()
            for topic in project_topic_names:
                if topic.replace("_", " ") in reasoning_lower:
                    match_topics.add(topic)

            if len(match_topics) >= min_overlap:
                filtered_matches.append(match)

        return filtered_matches
