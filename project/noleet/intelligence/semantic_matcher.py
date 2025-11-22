"""Semantic matching using embeddings instead of keyword matching."""

import logging
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
import json

from ..core.models import Project, Topic
from ..llm.embedder import TextEmbedder
from ..llm.llm_config import LLMConfig


class SemanticMatcher:
    """Semantic matching for projects using embeddings."""

    def __init__(
        self,
        embedder: Optional[TextEmbedder] = None,
        llm_config: Optional[LLMConfig] = None,
        cache_dir: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize semantic matcher.

        Args:
            embedder: Text embedder instance
            llm_config: LLM configuration
            cache_dir: Directory to cache embeddings
            logger: Optional logger instance
        """
        self._embedder = embedder or TextEmbedder(llm_config)
        self._config = llm_config or LLMConfig()
        self._cache_dir = cache_dir or Path.home() / ".noleet" / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logger or logging.getLogger(__name__)

        # Cache for project embeddings
        self._project_embeddings: Dict[str, List[List[float]]] = {}
        self._project_texts: Dict[str, List[str]] = {}

        self._load_cache()

    def find_matching_projects(
        self,
        projects: List[Project],
        query_topics: Set[Topic],
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[Project, float]]:
        """
        Find projects that semantically match the query topics.

        Args:
            projects: List of projects to search
            query_topics: Set of topics to match against
            top_k: Maximum number of results to return
            min_score: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of (project, score) tuples, sorted by score descending
        """
        if not query_topics:
            return []

        # Create query text from topics
        query_text = self._topics_to_query(query_topics)
        self._logger.info(f"Searching for projects matching: {query_text}")

        # Get query embedding
        try:
            query_embedding = self._embedder.embed_query(query_text)
        except Exception as e:
            self._logger.error(f"Failed to embed query: {e}")
            return []

        matches = []

        for project in projects:
            # Get project embeddings
            project_texts, project_embeddings = self._get_project_embeddings(project)

            if not project_embeddings:
                continue

            # Calculate similarity scores
            similarities = self._embedder.find_similar(
                query_text,
                project_texts,
                top_k=len(project_texts)
            )

            # Take the highest similarity score for this project
            if similarities:
                best_match = max(similarities, key=lambda x: x[1])
                score = best_match[1]

                # Boost score if project actually contains the topics
                topic_boost = self._calculate_topic_boost(project, query_topics)
                final_score = min(1.0, score + topic_boost)

                if final_score >= min_score:
                    matches.append((project, final_score))

        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)

        self._logger.info(
            f"Found {len(matches)} matching projects "
            f"(showing top {min(top_k, len(matches))})"
        )

        return matches[:top_k]

    def _topics_to_query(self, topics: Set[Topic]) -> str:
        """Convert topics to a natural language query."""
        topic_names = [t.value.replace("_", " ").title() for t in topics]

        if len(topic_names) == 1:
            return f"projects involving {topic_names[0]}"
        elif len(topic_names) == 2:
            return f"projects involving {topic_names[0]} and {topic_names[1]}"
        else:
            return f"projects involving {', '.join(topic_names[:-1])}, and {topic_names[-1]}"

    def _get_project_embeddings(self, project: Project) -> Tuple[List[str], List[List[float]]]:
        """
        Get or create embeddings for a project.

        Args:
            project: Project to embed

        Returns:
            Tuple of (texts, embeddings)
        """
        if project.id in self._project_embeddings:
            return (
                self._project_texts[project.id],
                self._project_embeddings[project.id]
            )

        # Create texts to embed
        texts = self._create_project_texts(project)

        try:
            embeddings = self._embedder.embed_texts(texts)
        except Exception as e:
            self._logger.error(f"Failed to embed project {project.id}: {e}")
            return [], []

        # Cache the embeddings
        self._project_texts[project.id] = texts
        self._project_embeddings[project.id] = embeddings

        # Save to cache
        self._save_project_cache(project.id)

        return texts, embeddings

    def _create_project_texts(self, project: Project) -> List[str]:
        """
        Create searchable texts from project data.

        Args:
            project: Project to create texts for

        Returns:
            List of text chunks for embedding
        """
        texts = []

        # Main project description
        main_text = f"""
        {project.title}. {project.description}.
        Difficulty: {project.difficulty}.
        Topics: {', '.join(t.value.replace('_', ' ') for t in project.primary_topics)}.
        """

        if project.tags:
            main_text += f" Tags: {', '.join(project.tags)}."

        texts.append(main_text.strip())

        # Task descriptions
        for task in project.tasks:
            task_text = f"""
            Task: {task.title}. {task.description}.
            DSA involvement: {', '.join(f'{inv.topic.value}: {inv.percentage}%' for inv in task.dsa_involvements)}.
            """

            if task.subtasks:
                subtasks_desc = []
                for subtask in task.subtasks:
                    sub_desc = f"{subtask.title}: {subtask.description}"
                    if subtask.dsa_involvements:
                        sub_desc += f" ({', '.join(f'{inv.topic.value}: {inv.percentage}%' for inv in subtask.dsa_involvements)})"
                    subtasks_desc.append(sub_desc)
                task_text += f" Subtasks: {'; '.join(subtasks_desc)}."

            texts.append(task_text.strip())

        return texts

    def _calculate_topic_boost(self, project: Project, query_topics: Set[Topic]) -> float:
        """
        Calculate boost score based on topic overlap.

        Args:
            project: Project to check
            query_topics: Query topics

        Returns:
            Boost score (0.0 to 0.3)
        """
        project_topics = project.primary_topics | project.required_topics
        overlap = len(project_topics.intersection(query_topics))

        if overlap == len(query_topics):
            return 0.3  # Full overlap
        elif overlap > 0:
            return 0.1  # Partial overlap
        else:
            return 0.0  # No overlap

    def _load_cache(self):
        """Load cached embeddings from disk."""
        cache_file = self._cache_dir / "embeddings_cache.json"

        if not cache_file.exists():
            return

        try:
            with open(cache_file, "r") as f:
                data = json.load(f)

            self._project_texts = data.get("texts", {})
            self._project_embeddings = data.get("embeddings", {})

            self._logger.info(f"Loaded embeddings cache for {len(self._project_texts)} projects")

        except Exception as e:
            self._logger.error(f"Failed to load embeddings cache: {e}")

    def _save_project_cache(self, project_id: str):
        """Save project embeddings to cache."""
        cache_file = self._cache_dir / "embeddings_cache.json"

        try:
            data = {
                "texts": self._project_texts,
                "embeddings": self._project_embeddings
            }

            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self._logger.error(f"Failed to save embeddings cache: {e}")

    def clear_cache(self):
        """Clear all cached embeddings."""
        self._project_embeddings.clear()
        self._project_texts.clear()

        cache_file = self._cache_dir / "embeddings_cache.json"
        if cache_file.exists():
            cache_file.unlink()

        self._logger.info("Embeddings cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_projects": len(self._project_texts),
            "total_embeddings": sum(len(emb) for emb in self._project_embeddings.values())
        }

    def is_available(self) -> bool:
        """Check if semantic matcher is available."""
        return self._embedder.is_available()

