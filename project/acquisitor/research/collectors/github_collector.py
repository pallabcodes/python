"""GitHub data collector for research insights."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from github3 import GitHub
from github3.exceptions import GitHubException

from app.core.config import settings
from app.core.exceptions import ExternalAPIError
from app.models.research_data import ResearchData
from .base_collector import BaseCollector


class GitHubCollector(BaseCollector):
    """Collect research data from GitHub."""

    def __init__(self, company_id: int):
        """Initialize GitHub collector."""
        super().__init__("github", company_id)
        self.github_client = None
        self.requests_per_minute = 5000  # GitHub allows 5000 requests per hour

    async def initialize_client(self):
        """Initialize GitHub API client."""
        try:
            self.github_client = GitHub(token=settings.GITHUB_TOKEN)
            self.logger.info("GitHub client initialized")
        except Exception as e:
            raise ExternalAPIError("github", f"Failed to initialize GitHub client: {e}")

    async def close_client(self):
        """Close GitHub client."""
        # GitHub3 doesn't require explicit closing
        self.github_client = None

    async def collect_data(self) -> List[ResearchData]:
        """Collect research data from GitHub."""
        if not self.github_client:
            raise ExternalAPIError("github", "GitHub client not initialized")

        research_data = []
        collected_count = 0

        # Get company info for search terms
        company_keywords = await self._get_company_keywords()
        search_terms = self._build_search_terms(company_keywords)

        for search_term in search_terms:
            if collected_count >= self.max_items_per_collection:
                break

            try:
                self.logger.info(f"Searching GitHub for: {search_term}")

                # Search issues
                issues = self.github_client.search_issues(
                    search_term,
                    sort="updated",
                    order="desc",
                    per_page=min(50, self.max_items_per_collection - collected_count)
                )

                for issue in issues:
                    if collected_count >= self.max_items_per_collection:
                        break

                    # Process issue
                    issue_data = await self._process_issue(issue)
                    if issue_data:
                        research_data.append(issue_data)
                        collected_count += 1

                    # Process comments if issue has them
                    if issue.comments_count > 0:
                        comment_count = 0
                        for comment in issue.comments():
                            if comment_count >= self.max_comments_per_item:
                                break

                            comment_data = await self._process_comment(comment, issue)
                            if comment_data:
                                research_data.append(comment_data)
                                collected_count += 1
                                comment_count += 1

            except GitHubException as e:
                self.logger.warning(f"Error searching GitHub for '{search_term}': {e}")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error in GitHub collection: {e}")
                continue

        self.logger.info(f"Collected {len(research_data)} items from GitHub")
        return research_data

    async def _get_company_keywords(self) -> List[str]:
        """Get company-related keywords for searching."""
        # TODO: This should come from company model
        # For now, return generic terms
        return ["productivity", "tool", "workflow", "collaboration", "management"]

    def _build_search_terms(self, keywords: List[str]) -> List[str]:
        """Build search terms from keywords."""
        search_terms = []

        # Issues and discussions
        issue_qualifiers = [
            "is:issue",
            "is:open",
            "label:bug",
            "label:enhancement",
            "label:feature-request",
            "label:help-wanted"
        ]

        for keyword in keywords[:5]:  # Limit keywords
            for qualifier in issue_qualifiers:
                search_terms.append(f"{keyword} {qualifier}")

        # Repository topics
        for keyword in keywords[:3]:
            search_terms.append(f"topic:{keyword}")

        return search_terms[:10]  # Limit to avoid rate limits

    async def _process_issue(self, issue) -> Optional[ResearchData]:
        """Process a GitHub issue into ResearchData."""
        try:
            # Skip if issue is too old (more than 2 years)
            issue_date = issue.created_at
            if isinstance(issue_date, str):
                issue_date = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))

            if issue_date < datetime.now() - timedelta(days=730):
                return None

            # Clean content
            title = self._clean_text(issue.title or "")
            body = self._clean_text(issue.body or "")
            content = f"{title}\n\n{body}" if body else title

            if len(content) < 50:  # Skip very short issues
                return None

            # Extract labels
            labels = [label.name for label in issue.labels()] if hasattr(issue, 'labels') else []

            # Calculate relevance
            keywords = await self._get_company_keywords()
            relevance_score = self._calculate_relevance_score(content, keywords)

            return self.create_research_data(
                content_type="issue",
                title=title,
                content=content,
                source_url=issue.html_url,
                source_title=f"{issue.repository.full_name}",
                source_author=issue.user.login if issue.user else None,
                source_date=issue_date,
                comments_count=issue.comments_count,
                views=0,  # GitHub doesn't expose view counts easily
                relevance_score=relevance_score,
                tags=labels,
                language="en",  # GitHub is primarily English
            )

        except Exception as e:
            self.logger.warning(f"Error processing issue {issue.number}: {e}")
            return None

    async def _process_comment(self, comment, issue) -> Optional[ResearchData]:
        """Process a GitHub comment into ResearchData."""
        try:
            # Skip if comment is too old
            comment_date = comment.created_at
            if isinstance(comment_date, str):
                comment_date = datetime.fromisoformat(comment_date.replace('Z', '+00:00'))

            if comment_date < datetime.now() - timedelta(days=730):
                return None

            content = self._clean_text(comment.body or "")
            if len(content) < 30:  # Skip very short comments
                return None

            # Calculate relevance
            keywords = await self._get_company_keywords()
            relevance_score = self._calculate_relevance_score(content, keywords)

            return self.create_research_data(
                content_type="comment",
                title=f"Comment on: {issue.title[:50]}...",
                content=content,
                source_url=comment.html_url,
                source_title=f"{issue.repository.full_name}",
                source_author=comment.user.login if comment.user else None,
                source_date=comment_date,
                relevance_score=relevance_score,
                language="en",
            )

        except Exception as e:
            self.logger.warning(f"Error processing comment: {e}")
            return None
