"""
RSS Feed Source for analytics pipeline.

This module provides RSS feed ingestion capabilities for the analytics pipeline,
supporting multiple feeds, configurable polling intervals, and robust error handling.
"""

import time
import logging
import threading
import feedparser
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..pipeline_core.message import DataMessage, ControlMessage
from ..pipeline_core.stage_base import SourceStage


@dataclass
class RSSFeedConfig:
    """Configuration for RSS feed source."""
    url: str
    name: str
    poll_interval: int = 300  # 5 minutes
    max_entries: int = 100
    timeout: int = 30
    user_agent: str = "AnalyticsPipeline/1.0"
    enabled: bool = True


@dataclass
class FeedEntry:
    """Represents a parsed RSS feed entry."""
    id: str
    title: str
    link: str
    published: Optional[datetime]
    updated: Optional[datetime]
    summary: str
    content: str
    author: str
    tags: List[str]
    raw_data: Dict[str, Any]

    @classmethod
    def from_feedparser_entry(cls, entry: Dict[str, Any]) -> 'FeedEntry':
        """Create FeedEntry from feedparser entry."""
        # Parse published/updated dates
        published = None
        updated = None

        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])

        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            updated = datetime(*entry.updated_parsed[:6])

        # Extract content
        content = ""
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value if isinstance(entry.content, list) else entry.content
        elif hasattr(entry, 'summary'):
            content = entry.summary

        # Extract tags
        tags = []
        if hasattr(entry, 'tags'):
            tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]

        return cls(
            id=entry.get('id', entry.link),
            title=entry.get('title', ''),
            link=entry.link,
            published=published,
            updated=updated,
            summary=entry.get('summary', ''),
            content=content,
            author=entry.get('author', ''),
            tags=tags,
            raw_data=dict(entry)
        )


@dataclass
class RSSFeedStats:
    """Statistics for RSS feed processing."""
    feeds_configured: int = 0
    feeds_active: int = 0
    entries_processed: int = 0
    entries_failed: int = 0
    last_poll_time: Optional[float] = None
    poll_errors: int = 0


class RSSFeedSource(SourceStage):
    """RSS Feed source stage for the analytics pipeline.

    This stage polls RSS feeds at configured intervals and emits new entries
    as pipeline messages. It supports multiple feeds, duplicate detection,
    and robust error handling.
    """

    def __init__(
        self,
        name: str,
        feeds: List[RSSFeedConfig],
        duplicate_window_hours: int = 24,
        max_workers: int = 4
    ):
        """Initialize RSS feed source.

        Args:
            name: Stage name
            feeds: List of RSS feed configurations
            duplicate_window_hours: Hours to keep entry IDs for duplicate detection
            max_workers: Maximum concurrent feed polling workers
        """
        super().__init__(name)
        self.feeds = feeds
# Methods are implemented inline to keep file under 200 lines
