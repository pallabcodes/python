"""Research orchestrator for coordinating data collection."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResearchCollectionError
from app.db.session import get_db
from app.models.company import Company
from app.models.research_data import ResearchData
from app.services.company_service import CompanyService
from .collectors import (
    RedditCollector,
    GitHubCollector,
    MediumCollector,
    TwitterCollector,
)


class ResearchOrchestrator:
    """Orchestrates research data collection across multiple sources."""

    def __init__(self):
        """Initialize research orchestrator."""
        self.logger = logging.getLogger(__name__)
        self.collectors = {
            'reddit': RedditCollector,
            'github': GitHubCollector,
            'medium': MediumCollector,
            'twitter': TwitterCollector,
        }

    async def collect_company_research(self, company_id: int, sources: Optional[List[str]] = None) -> Dict[str, int]:
        """Collect research data for a company from specified sources.

        Args:
            company_id: ID of the company to research
            sources: List of sources to collect from (default: all available)

        Returns:
            Dict mapping source names to number of items collected
        """
        if sources is None:
            sources = list(self.collectors.keys())

        self.logger.info(f"Starting research collection for company {company_id} from sources: {sources}")

        # Update company research status
        async for db in get_db():
            company_service = CompanyService(db)
            company = await company_service.get_company(company_id)
            if not company:
                raise ResearchCollectionError("research", f"Company {company_id} not found")

            company.research_status = "in_progress"
            await db.commit()

        collection_results = {}

        try:
            # Collect from each source concurrently
            tasks = []
            for source in sources:
                if source in self.collectors:
                    task = self._collect_from_source(company_id, source)
                    tasks.append(task)

            # Wait for all collections to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for source, result in zip(sources, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Collection failed for {source}: {result}")
                    collection_results[source] = 0
                else:
                    collection_results[source] = result

            # Update company with results
            await self._update_company_research_status(company_id, collection_results)

            total_collected = sum(collection_results.values())
            self.logger.info(f"Research collection completed. Total items: {total_collected}")

            return collection_results

        except Exception as e:
            self.logger.error(f"Research collection failed: {e}")
            await self._update_company_research_status(company_id, {}, error=str(e))
            raise ResearchCollectionError("research", f"Collection orchestration failed: {e}")

    async def _collect_from_source(self, company_id: int, source: str) -> int:
        """Collect data from a specific source."""
        try:
            collector_class = self.collectors[source]
            async with collector_class(company_id) as collector:
                research_data = await collector.collect_data()

                # Save collected data
                saved_count = await self._save_research_data(research_data)

                self.logger.info(f"Collected {saved_count} items from {source}")
                return saved_count

        except Exception as e:
            self.logger.error(f"Failed to collect from {source}: {e}")
            raise

    async def _save_research_data(self, research_data: List[ResearchData]) -> int:
        """Save research data to database."""
        if not research_data:
            return 0

        async for db in get_db():
            try:
                db.add_all(research_data)
                await db.commit()

                # Refresh to get IDs
                for item in research_data:
                    await db.refresh(item)

                return len(research_data)

            except Exception as e:
                await db.rollback()
                self.logger.error(f"Failed to save research data: {e}")
                raise ResearchCollectionError("research", f"Database save failed: {e}")

    async def _update_company_research_status(
        self,
        company_id: int,
        collection_results: Dict[str, int],
        error: Optional[str] = None
    ):
        """Update company research status and metadata."""
        async for db in get_db():
            try:
                company_service = CompanyService(db)
                company = await company_service.get_company(company_id)
                if not company:
                    return

                # Update status
                if error:
                    company.research_status = "failed"
                else:
                    company.research_status = "completed"

                company.last_researched = datetime.utcnow()

                # Update research sources
                current_sources = company.research_sources or []
                for source in collection_results.keys():
                    if source not in current_sources:
                        current_sources.append(source)
                company.research_sources = current_sources

                # Update pain points count (placeholder - will be updated by analysis)
                # company.pain_points_count = await self._count_pain_points(company_id)

                await db.commit()

            except Exception as e:
                self.logger.error(f"Failed to update company research status: {e}")

    async def get_collection_status(self, company_id: int) -> Dict[str, any]:
        """Get current research collection status for a company."""
        async for db in get_db():
            company_service = CompanyService(db)
            company = await company_service.get_company(company_id)

            if not company:
                return {"error": "Company not found"}

            return {
                "company_id": company_id,
                "research_status": company.research_status,
                "last_researched": company.last_researched,
                "research_sources": company.research_sources or [],
                "pain_points_count": company.pain_points_count,
                "product_ideas_count": company.product_ideas_count,
            }

    async def get_available_sources(self) -> List[str]:
        """Get list of available research sources."""
        return list(self.collectors.keys())

    async def validate_source_config(self, source: str) -> Dict[str, bool]:
        """Validate configuration for a research source."""
        # Check if required API keys/credentials are configured
        config_status = {}

        if source == "reddit":
            from app.core.config import settings
            config_status["client_id"] = bool(settings.REDDIT_CLIENT_ID)
            config_status["client_secret"] = bool(settings.REDDIT_CLIENT_SECRET)
            config_status["configured"] = all(config_status.values())

        elif source == "github":
            from app.core.config import settings
            config_status["token"] = bool(settings.GITHUB_TOKEN)
            config_status["configured"] = config_status["token"]

        elif source == "twitter":
            from app.core.config import settings
            config_status["bearer_token"] = bool(settings.TWITTER_BEARER_TOKEN)
            config_status["api_key"] = bool(settings.TWITTER_API_KEY)
            config_status["configured"] = all(config_status.values())

        elif source == "medium":
            # Medium doesn't require API keys for basic scraping
            config_status["configured"] = True

        else:
            config_status["configured"] = False

        return config_status
