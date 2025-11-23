"""Community contribution system for peer-powered learning."""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from uuid import uuid4

from noleet.core.models import Project


class ContributionType(Enum):
    """Types of community contributions."""
    PROJECT_IMPLEMENTATION = "project_implementation"  # Complete project solution
    CODE_SNIPPET = "code_snippet"               # Specific algorithm/code example
    LEARNING_INSIGHT = "learning_insight"       # Key learning or insight
    DEBUG_STORY = "debug_story"                 # Debugging experience/challenge
    ALTERNATIVE_APPROACH = "alternative_approach"  # Different solution method
    OPTIMIZATION_TIP = "optimization_tip"       # Performance improvement
    BEST_PRACTICE = "best_practice"             # Coding best practice
    CONCEPT_EXPLANATION = "concept_explanation" # DSA concept clarification


@dataclass
class CommunityContribution:
    """A community contribution with metadata and content."""
    id: str = field(default_factory=lambda: str(uuid4()))
    contribution_type: ContributionType = ContributionType.PROJECT_IMPLEMENTATION
    project_id: str = ""  # Associated NoLeet project
    title: str = ""
    description: str = ""
    content: str = ""  # Main content (code, explanation, etc.)
    author_id: str = "anonymous"  # Could be enhanced with user system
    topics: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Quality and engagement metrics
    upvotes: int = 0
    downvotes: int = 0
    views: int = 0
    helpful_count: int = 0
    quality_score: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1

    # Relationships
    parent_contribution_id: Optional[str] = None  # For follow-ups/improvements
    related_contribution_ids: List[str] = field(default_factory=list)

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['contribution_type'] = self.contribution_type.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommunityContribution':
        """Create from dictionary."""
        # Convert string back to enum
        data['contribution_type'] = ContributionType(data['contribution_type'])
        # Convert ISO strings back to datetime
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

    @property
    def score(self) -> float:
        """Calculate overall contribution score."""
        # Simple scoring algorithm: upvotes - downvotes + helpful_count * 0.5
        return self.upvotes - self.downvotes + (self.helpful_count * 0.5)

    def add_upvote(self) -> None:
        """Add an upvote."""
        self.upvotes += 1
        self._update_quality_score()

    def add_downvote(self) -> None:
        """Add a downvote."""
        self.downvotes += 1
        self._update_quality_score()

    def mark_helpful(self) -> None:
        """Mark as helpful."""
        self.helpful_count += 1
        self._update_quality_score()

    def record_view(self) -> None:
        """Record a view."""
        self.views += 1

    def _update_quality_score(self) -> None:
        """Update the quality score based on engagement."""
        # Quality score considers multiple factors
        engagement_score = (self.upvotes * 2) - (self.downvotes * 1.5) + (self.helpful_count * 1.2)
        recency_bonus = min(1.0, (datetime.now() - self.created_at).days / 30)  # Recent content bonus
        self.quality_score = engagement_score * (1 + recency_bonus * 0.1)


@dataclass
class ContributionSearchQuery:
    """Search query for finding contributions."""
    project_id: Optional[str] = None
    contribution_type: Optional[ContributionType] = None
    topics: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    author_id: Optional[str] = None
    min_score: float = 0.0
    sort_by: str = "quality_score"  # quality_score, created_at, score, views
    sort_order: str = "desc"  # asc, desc
    limit: int = 20
    offset: int = 0


class CommunityContributionSystem:
    """Manages community contributions and peer learning content."""

    def __init__(self, data_dir: Path):
        """
        Initialize the community contribution system.

        Args:
            data_dir: Directory for storing community data
        """
        self._data_dir = data_dir
        self._contributions_dir = data_dir / "community" / "contributions"
        self._contributions_dir.mkdir(parents=True, exist_ok=True)

        self._contributions: Dict[str, CommunityContribution] = {}
        self._logger = logging.getLogger(__name__)

        # Load existing contributions
        asyncio.create_task(self._load_contributions())

    async def _load_contributions(self) -> None:
        """Load existing contributions from disk."""
        try:
            for file_path in self._contributions_dir.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    contribution = CommunityContribution.from_dict(data)
                    self._contributions[contribution.id] = contribution

            self._logger.info(f"Loaded {len(self._contributions)} community contributions")

        except Exception as e:
            self._logger.error(f"Error loading contributions: {e}")

    async def save_contribution(self, contribution: CommunityContribution) -> None:
        """
        Save a contribution to disk.

        Args:
            contribution: The contribution to save
        """
        try:
            contribution.updated_at = datetime.now()
            file_path = self._contributions_dir / f"{contribution.id}.json"

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(contribution.to_dict(), f, indent=2, ensure_ascii=False)

            self._contributions[contribution.id] = contribution
            self._logger.info(f"Saved contribution {contribution.id}: {contribution.title}")

        except Exception as e:
            self._logger.error(f"Error saving contribution {contribution.id}: {e}")
            raise

    async def create_contribution(
        self,
        contribution_type: ContributionType,
        project_id: str,
        title: str,
        description: str,
        content: str,
        author_id: str = "anonymous",
        topics: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CommunityContribution:
        """
        Create a new community contribution.

        Args:
            contribution_type: Type of contribution
            project_id: Associated project ID
            title: Contribution title
            description: Brief description
            content: Main content
            author_id: Author identifier
            topics: Related DSA topics
            tags: Additional tags
            metadata: Additional metadata

        Returns:
            The created contribution
        """
        contribution = CommunityContribution(
            contribution_type=contribution_type,
            project_id=project_id,
            title=title,
            description=description,
            content=content,
            author_id=author_id,
            topics=topics or [],
            tags=tags or [],
            metadata=metadata or {}
        )

        await self.save_contribution(contribution)
        return contribution

    async def search_contributions(
        self,
        query: ContributionSearchQuery
    ) -> List[CommunityContribution]:
        """
        Search for contributions based on query parameters.

        Args:
            query: Search query parameters

        Returns:
            List of matching contributions
        """
        # Filter contributions
        filtered = []

        for contribution in self._contributions.values():
            # Apply filters
            if query.project_id and contribution.project_id != query.project_id:
                continue
            if query.contribution_type and contribution.contribution_type != query.contribution_type:
                continue
            if query.author_id and contribution.author_id != query.author_id:
                continue
            if contribution.quality_score < query.min_score:
                continue

            # Check topic/tag matches
            if query.topics:
                if not any(topic in contribution.topics for topic in query.topics):
                    continue
            if query.tags:
                if not any(tag in contribution.tags for tag in query.tags):
                    continue

            filtered.append(contribution)

        # Sort results
        reverse = query.sort_order == "desc"
        if query.sort_by == "quality_score":
            filtered.sort(key=lambda c: c.quality_score, reverse=reverse)
        elif query.sort_by == "created_at":
            filtered.sort(key=lambda c: c.created_at, reverse=reverse)
        elif query.sort_by == "score":
            filtered.sort(key=lambda c: c.score, reverse=reverse)
        elif query.sort_by == "views":
            filtered.sort(key=lambda c: c.views, reverse=reverse)

        # Apply pagination
        start_idx = query.offset
        end_idx = start_idx + query.limit
        return filtered[start_idx:end_idx]

    async def get_contribution(self, contribution_id: str) -> Optional[CommunityContribution]:
        """
        Get a specific contribution by ID.

        Args:
            contribution_id: The contribution ID

        Returns:
            The contribution if found, None otherwise
        """
        contribution = self._contributions.get(contribution_id)
        if contribution:
            contribution.record_view()
            await self.save_contribution(contribution)
        return contribution

    async def update_contribution(
        self,
        contribution_id: str,
        updates: Dict[str, Any]
    ) -> Optional[CommunityContribution]:
        """
        Update a contribution.

        Args:
            contribution_id: The contribution to update
            updates: Fields to update

        Returns:
            Updated contribution if found, None otherwise
        """
        contribution = self._contributions.get(contribution_id)
        if not contribution:
            return None

        # Update allowed fields
        allowed_fields = {
            'title', 'description', 'content', 'topics', 'tags', 'metadata'
        }

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(contribution, field, value)

        contribution.version += 1
        await self.save_contribution(contribution)
        return contribution

    async def vote_contribution(
        self,
        contribution_id: str,
        vote_type: str  # 'upvote', 'downvote', 'helpful'
    ) -> bool:
        """
        Vote on a contribution.

        Args:
            contribution_id: The contribution to vote on
            vote_type: Type of vote

        Returns:
            True if vote was recorded, False if contribution not found
        """
        contribution = self._contributions.get(contribution_id)
        if not contribution:
            return False

        if vote_type == "upvote":
            contribution.add_upvote()
        elif vote_type == "downvote":
            contribution.add_downvote()
        elif vote_type == "helpful":
            contribution.mark_helpful()

        await self.save_contribution(contribution)
        return True

    async def get_project_contributions(
        self,
        project_id: str,
        contribution_type: Optional[ContributionType] = None,
        limit: int = 10
    ) -> List[CommunityContribution]:
        """
        Get contributions for a specific project.

        Args:
            project_id: The project ID
            contribution_type: Optional type filter
            limit: Maximum number of contributions to return

        Returns:
            List of contributions for the project
        """
        query = ContributionSearchQuery(
            project_id=project_id,
            contribution_type=contribution_type,
            limit=limit,
            sort_by="quality_score"
        )
        return await self.search_contributions(query)

    async def get_related_contributions(
        self,
        contribution_id: str,
        limit: int = 5
    ) -> List[CommunityContribution]:
        """
        Get contributions related to a specific contribution.

        Args:
            contribution_id: The base contribution ID
            limit: Maximum number of related contributions

        Returns:
            List of related contributions
        """
        base_contribution = self._contributions.get(contribution_id)
        if not base_contribution:
            return []

        # Find contributions with similar topics or same project
        related = []
        for contribution in self._contributions.values():
            if contribution.id == contribution_id:
                continue

            # Same project or shared topics
            if (contribution.project_id == base_contribution.project_id or
                set(contribution.topics) & set(base_contribution.topics)):
                related.append(contribution)

        # Sort by relevance and quality
        related.sort(key=lambda c: (len(set(c.topics) & set(base_contribution.topics)), c.quality_score), reverse=True)

        return related[:limit]

    async def get_popular_contributions(
        self,
        topics: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[CommunityContribution]:
        """
        Get popular contributions, optionally filtered by topics.

        Args:
            topics: Optional topic filter
            limit: Maximum number of contributions

        Returns:
            List of popular contributions
        """
        query = ContributionSearchQuery(
            topics=topics or [],
            sort_by="score",
            limit=limit,
            min_score=1.0  # Only show contributions with positive engagement
        )
        return await self.search_contributions(query)

    def get_stats(self) -> Dict[str, Any]:
        """Get community contribution statistics."""
        total_contributions = len(self._contributions)
        total_views = sum(c.views for c in self._contributions.values())
        total_upvotes = sum(c.upvotes for c in self._contributions.values())
        total_helpful = sum(c.helpful_count for c in self._contributions.values())

        # Contributions by type
        type_counts = {}
        for contribution in self._contributions.values():
            type_name = contribution.contribution_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # Top topics
        topic_counts = {}
        for contribution in self._contributions.values():
            for topic in contribution.topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_contributions": total_contributions,
            "total_views": total_views,
            "total_upvotes": total_upvotes,
            "total_helpful_marks": total_helpful,
            "contributions_by_type": type_counts,
            "top_topics": top_topics,
            "average_quality_score": sum(c.quality_score for c in self._contributions.values()) / max(total_contributions, 1)
        }
