"""Base scraper interface and common functionality."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging


@dataclass
class QuestionMetadata:
    """Metadata for a collected DSA question."""
    
    source: str
    source_id: str
    title: str
    content: str
    url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    difficulty: Optional[str] = None
    company_tags: List[str] = field(default_factory=list)
    collected_at: datetime = field(default_factory=datetime.utcnow)
    raw_data: Dict[str, Any] = field(default_factory=dict)


class BaseScraper(ABC):
    """Base class for all scrapers."""
    
    def __init__(self, source_name: str) -> None:
        """
        Initialize scraper.
        
        Args:
            source_name: Name of the source being scraped
        """
        self._source_name = source_name
        self._logger = logging.getLogger(f"{__name__}.{source_name}")
    
    @abstractmethod
    def scrape(self, **kwargs) -> List[QuestionMetadata]:
        """
        Scrape questions from the source.
        
        Args:
            **kwargs: Source-specific parameters
            
        Returns:
            List of collected questions
        """
        pass
    
    def _log_collection(self, count: int) -> None:
        """Log collection results."""
        self._logger.info(
            f"Collected {count} questions from {self._source_name}",
            extra={
                "source": self._source_name,
                "count": count,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _create_question(
        self,
        source_id: str,
        title: str,
        content: str,
        url: Optional[str] = None,
        tags: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
        company_tags: Optional[List[str]] = None,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> QuestionMetadata:
        """Create a question metadata object."""
        return QuestionMetadata(
            source=self._source_name,
            source_id=source_id,
            title=title,
            content=content,
            url=url,
            tags=tags or [],
            difficulty=difficulty,
            company_tags=company_tags or [],
            raw_data=raw_data or {}
        )

