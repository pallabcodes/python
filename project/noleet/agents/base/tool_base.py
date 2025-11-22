"""Base tool classes for agent system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseTool(ABC):
    """Base class for agent tools."""

    def __init__(self, name: str, description: str):
        """
        Initialize tool.

        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
        self._logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool.

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        pass

    def validate_params(self, **kwargs) -> bool:
        """
        Validate tool parameters.

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if parameters are valid
        """
        return True

    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool parameter schema.

        Returns:
            JSON schema for tool parameters
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def to_langchain_tool(self) -> Optional[Any]:
        """Convert to LangChain tool format."""
        try:
            from langchain.tools import Tool
            return Tool(
                name=self.name,
                description=self.description,
                func=self.execute
            )
        except ImportError:
            return None


class ProjectSearchTool(BaseTool):
    """Tool for searching projects by topics."""

    def __init__(self, project_repository):
        """
        Initialize project search tool.

        Args:
            project_repository: Repository for accessing projects
        """
        super().__init__(
            "project_search",
            "Search for projects that match specific DSA topics"
        )
        self._repository = project_repository

    def execute(self, topics: list[str], **kwargs) -> Dict[str, Any]:
        """
        Search for projects by topics.

        Args:
            topics: List of topic names to search for

        Returns:
            Search results
        """
        try:
            from ...matching.matcher import ProjectMatcher
            from ...core.models import Topic

            projects = self._repository.load_projects()
            matcher = ProjectMatcher()

            # Convert topic names to Topic enums
            selected_topics = set()
            for topic_name in topics:
                try:
                    topic = Topic(topic_name.lower().replace(" ", "_"))
                    selected_topics.add(topic)
                except ValueError:
                    self._logger.warning(f"Unknown topic: {topic_name}")

            matching_projects = matcher.find_matching_projects(
                projects,
                selected_topics
            )

            results = []
            for project in matching_projects[:5]:  # Limit results
                results.append({
                    "id": project.id,
                    "title": project.title,
                    "description": project.short_description,
                    "difficulty": project.difficulty,
                    "topics": [t.value for t in project.primary_topics]
                })

            return {
                "success": True,
                "results": results,
                "count": len(results)
            }

        except Exception as e:
            self._logger.error(f"Project search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of DSA topics to search for"
                }
            },
            "required": ["topics"]
        }


class DataCollectionTool(BaseTool):
    """Tool for collecting data from sources."""

    def __init__(self, data_coordinator):
        """
        Initialize data collection tool.

        Args:
            data_coordinator: Coordinator for data gathering
        """
        super().__init__(
            "data_collection",
            "Collect DSA questions from various online sources"
        )
        self._coordinator = data_coordinator

    def execute(self, max_results: int = 50, **kwargs) -> Dict[str, Any]:
        """
        Collect data from sources.

        Args:
            max_results: Maximum results per source

        Returns:
            Collection results
        """
        try:
            categorized = self._coordinator.gather_all_sources(max_results)

            summary = {}
            for topic, questions in categorized.items():
                summary[topic.value] = len(questions)

            return {
                "success": True,
                "total_questions": sum(summary.values()),
                "topics_covered": len(summary),
                "topic_breakdown": summary
            }

        except Exception as e:
            self._logger.error(f"Data collection failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results per source",
                    "default": 50
                }
            }
        }


class ResearchSearchTool(BaseTool):
    """Tool for searching research papers."""

    def __init__(self, research_papers):
        """
        Initialize research search tool.

        Args:
            research_papers: List of available research papers
        """
        super().__init__(
            "research_search",
            "Search for research papers related to algorithms and data structures"
        )
        self._papers = research_papers

    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search for research papers.

        Args:
            query: Search query

        Returns:
            Search results
        """
        try:
            # Simple text-based search (can be enhanced with embeddings)
            results = []
            query_lower = query.lower()

            for paper in self._papers:
                if (query_lower in paper.title.lower() or
                    query_lower in paper.abstract.lower() or
                    any(query_lower in algo.lower() for algo in paper.algorithms)):
                    results.append({
                        "title": paper.title,
                        "authors": paper.authors,
                        "abstract": paper.abstract[:200] + "...",
                        "algorithms": paper.algorithms,
                        "url": paper.url
                    })

            return {
                "success": True,
                "results": results[:5],  # Limit results
                "count": len(results)
            }

        except Exception as e:
            self._logger.error(f"Research search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for research papers"
                }
            },
            "required": ["query"]
        }

