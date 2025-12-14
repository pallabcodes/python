"""Base collector class for research data collection."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.exceptions import ExternalAPIError, ResearchCollectionError
from app.models.research_data import ResearchData


class BaseCollector(ABC):
    """Abstract base class for research data collectors."""

    def __init__(self, source_name: str, company_id: int):
        """Initialize collector with source and company context."""
        self.source_name = source_name
        self.company_id = company_id
        self.logger = logging.getLogger(f"{__name__}.{source_name}")
        self.client = None

        # Rate limiting
        self.requests_per_minute = 60
        self.last_request_time = None
        self.request_interval = 60.0 / self.requests_per_minute

        # Collection limits
        self.max_items_per_collection = settings.MAX_POSTS_PER_SOURCE
        self.max_comments_per_item = settings.MAX_COMMENTS_PER_POST

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_client()

    @abstractmethod
    async def initialize_client(self):
        """Initialize the HTTP client or API client."""
        pass

    @abstractmethod
    async def close_client(self):
        """Close the HTTP client or API client."""
        pass

    @abstractmethod
    async def collect_data(self) -> List[ResearchData]:
        """Collect research data from the source."""
        pass

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.BACKOFF_FACTOR, min=1, max=60),
        retry=retry_if_exception_type((httpx.HTTPError, ExternalAPIError)),
    )
    async def make_request(self, url: str, method: str = "GET", **kwargs) -> httpx.Response:
        """Make HTTP request with rate limiting and retry logic."""
        await self._rate_limit()

        try:
            if not self.client:
                raise ResearchCollectionError(self.source_name, "Client not initialized")

            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error for {url}: {e}")
            raise ExternalAPIError(self.source_name, f"HTTP error: {e}")
        except Exception as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise ResearchCollectionError(self.source_name, f"Request failed: {e}")

    async def _rate_limit(self):
        """Implement rate limiting."""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.request_interval:
                await asyncio.sleep(self.request_interval - elapsed)

        self.last_request_time = datetime.now()

    def create_research_data(
        self,
        content_type: str,
        title: Optional[str] = None,
        content: str = "",
        source_url: str = "",
        source_title: Optional[str] = None,
        source_author: Optional[str] = None,
        source_date: Optional[datetime] = None,
        **metadata
    ) -> ResearchData:
        """Create a ResearchData object with standardized fields."""
        return ResearchData(
            company_id=self.company_id,
            source_type=self.source_name,
            source_url=source_url,
            source_title=source_title,
            source_author=source_author,
            source_date=source_date,
            content_type=content_type,
            title=title,
            content=content,
            **metadata
        )

    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except Exception:
            return url

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""

        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove common artifacts
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        return text

    def _calculate_relevance_score(self, content: str, keywords: List[str]) -> float:
        """Calculate relevance score based on keyword matches."""
        if not content or not keywords:
            return 0.0

        content_lower = content.lower()
        matches = sum(1 for keyword in keywords if keyword.lower() in content_lower)

        # Simple scoring: percentage of keywords found
        return min(matches / len(keywords), 1.0) if keywords else 0.0
