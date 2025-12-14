"""Reddit data collector for research insights."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import praw
from praw.models import Submission, Comment
from prawcore.exceptions import PrawcoreException

from app.core.config import settings
from app.core.exceptions import ExternalAPIError
from app.models.research_data import ResearchData
from .base_collector import BaseCollector


class RedditCollector(BaseCollector):
    """Collect research data from Reddit."""

    def __init__(self, company_id: int):
        """Initialize Reddit collector."""
        super().__init__("reddit", company_id)
        self.reddit_client = None
        self.subreddits = [
            "SaaS", "ProductManagement", "Entrepreneur", "startups",
            "ProductHunt", "SideProject", "indiehackers", "smallbusiness",
            "technology", "business", "marketing", "growth"
        ]

    async def initialize_client(self):
        """Initialize Reddit API client."""
        try:
            self.reddit_client = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
            )
            self.logger.info("Reddit client initialized")
        except Exception as e:
            raise ExternalAPIError("reddit", f"Failed to initialize Reddit client: {e}")

    async def close_client(self):
        """Close Reddit client."""
        # PRAW doesn't require explicit closing
        self.reddit_client = None

    async def collect_data(self) -> List[ResearchData]:
        """Collect research data from Reddit."""
        if not self.reddit_client:
            raise ExternalAPIError("reddit", "Reddit client not initialized")

        research_data = []
        collected_count = 0

        # Get company info for search terms
        company_keywords = await self._get_company_keywords()

        for subreddit_name in self.subreddits:
            if collected_count >= self.max_items_per_collection:
                break

            try:
                subreddit = self.reddit_client.subreddit(subreddit_name)
                self.logger.info(f"Collecting from r/{subreddit_name}")

                # Search for company mentions and related discussions
                search_queries = self._build_search_queries(company_keywords)

                for query in search_queries:
                    if collected_count >= self.max_items_per_collection:
                        break

                    try:
                        # Search submissions
                        submissions = subreddit.search(
                            query,
                            sort="relevance",
                            time_filter="year",  # Last year
                            limit=min(50, self.max_items_per_collection - collected_count)
                        )

                        for submission in submissions:
                            if collected_count >= self.max_items_per_collection:
                                break

                            # Collect submission
                            submission_data = await self._process_submission(submission)
                            if submission_data:
                                research_data.append(submission_data)
                                collected_count += 1

                            # Collect top comments
                            comment_count = 0
                            submission.comments.replace_more(limit=0)  # Remove "load more comments"
                            for comment in submission.comments[:self.max_comments_per_item]:
                                if comment_count >= self.max_comments_per_item:
                                    break

                                comment_data = await self._process_comment(comment, submission)
                                if comment_data:
                                    research_data.append(comment_data)
                                    collected_count += 1
                                    comment_count += 1

                        # Add small delay between queries to avoid rate limits
                        await asyncio.sleep(1)

                    except PrawcoreException as e:
                        self.logger.warning(f"Error searching r/{subreddit_name} with '{query}': {e}")
                        continue

            except PrawcoreException as e:
                self.logger.error(f"Error accessing r/{subreddit_name}: {e}")
                continue

        self.logger.info(f"Collected {len(research_data)} items from Reddit")
        return research_data

    async def _get_company_keywords(self) -> List[str]:
        """Get company-related keywords for searching."""
        # TODO: This should come from company model
        # For now, return generic terms
        return ["productivity", "tool", "software", "app", "platform", "workflow"]

    def _build_search_queries(self, keywords: List[str]) -> List[str]:
        """Build search queries from keywords."""
        queries = []

        # Individual keywords
        queries.extend(keywords)

        # Common pain point terms
        pain_terms = ["problem", "issue", "frustrated", "annoying", "difficult", "complicated"]
        for keyword in keywords[:3]:  # Limit to top keywords
            for pain_term in pain_terms:
                queries.append(f'"{keyword}" {pain_term}')

        # Feature request terms
        feature_terms = ["feature", "missing", "need", "want", "wish", "should have"]
        for keyword in keywords[:3]:
            for feature_term in feature_terms:
                queries.append(f'"{keyword}" {feature_term}')

        return queries[:10]  # Limit queries to avoid rate limits

    async def _process_submission(self, submission: Submission) -> Optional[ResearchData]:
        """Process a Reddit submission into ResearchData."""
        try:
            # Skip if post is too old (more than 2 years)
            post_date = datetime.fromtimestamp(submission.created_utc)
            if post_date < datetime.now() - timedelta(days=730):
                return None

            # Clean and prepare content
            content = self._clean_text(submission.selftext or submission.title)
            if len(content) < 50:  # Skip very short posts
                return None

            # Calculate relevance (placeholder logic)
            keywords = await self._get_company_keywords()
            relevance_score = self._calculate_relevance_score(content, keywords)

            return self.create_research_data(
                content_type="post",
                title=submission.title,
                content=content,
                source_url=f"https://reddit.com{submission.permalink}",
                source_title=f"r/{submission.subreddit.display_name}",
                source_author=submission.author.name if submission.author else None,
                source_date=post_date,
                upvotes=submission.score,
                comments_count=submission.num_comments,
                relevance_score=relevance_score,
            )

        except Exception as e:
            self.logger.warning(f"Error processing submission {submission.id}: {e}")
            return None

    async def _process_comment(self, comment: Comment, submission: Submission) -> Optional[ResearchData]:
        """Process a Reddit comment into ResearchData."""
        try:
            # Skip if comment is too old or short
            comment_date = datetime.fromtimestamp(comment.created_utc)
            if comment_date < datetime.now() - timedelta(days=730):
                return None

            content = self._clean_text(comment.body)
            if len(content) < 30:  # Skip very short comments
                return None

            # Calculate relevance
            keywords = await self._get_company_keywords()
            relevance_score = self._calculate_relevance_score(content, keywords)

            return self.create_research_data(
                content_type="comment",
                title=f"Comment on: {submission.title[:50]}...",
                content=content,
                source_url=f"https://reddit.com{submission.permalink}{comment.id}",
                source_title=f"r/{submission.subreddit.display_name}",
                source_author=comment.author.name if comment.author else None,
                source_date=comment_date,
                upvotes=comment.score,
                relevance_score=relevance_score,
            )

        except Exception as e:
            self.logger.warning(f"Error processing comment {comment.id}: {e}")
            return None
