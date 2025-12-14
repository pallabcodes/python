"""Twitter/X data collector for research insights."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import tweepy
from tweepy.errors import TweepyException

from app.core.config import settings
from app.core.exceptions import ExternalAPIError
from app.models.research_data import ResearchData
from .base_collector import BaseCollector


class TwitterCollector(BaseCollector):
    """Collect research data from Twitter/X."""

    def __init__(self, company_id: int):
        """Initialize Twitter collector."""
        super().__init__("twitter", company_id)
        self.twitter_client = None
        self.requests_per_minute = 300  # Twitter API v2 limit

    async def initialize_client(self):
        """Initialize Twitter API client."""
        try:
            self.twitter_client = tweepy.Client(
                bearer_token=settings.TWITTER_BEARER_TOKEN,
                consumer_key=settings.TWITTER_API_KEY,
                consumer_secret=settings.TWITTER_API_SECRET,
                access_token=settings.TWITTER_ACCESS_TOKEN,
                access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )
            self.logger.info("Twitter client initialized")
        except Exception as e:
            raise ExternalAPIError("twitter", f"Failed to initialize Twitter client: {e}")

    async def close_client(self):
        """Close Twitter client."""
        # Tweepy doesn't require explicit closing
        self.twitter_client = None

    async def collect_data(self) -> List[ResearchData]:
        """Collect research data from Twitter."""
        if not self.twitter_client:
            raise ExternalAPIError("twitter", "Twitter client not initialized")

        research_data = []
        collected_count = 0

        # Get company info for search terms
        company_keywords = await self._get_company_keywords()

        # Build search queries
        search_queries = self._build_search_queries(company_keywords)

        for query in search_queries:
            if collected_count >= self.max_items_per_collection:
                break

            try:
                self.logger.info(f"Searching Twitter for: {query}")

                # Search recent tweets (last 7 days due to API limitations)
                tweets = self.twitter_client.search_recent_tweets(
                    query=query,
                    max_results=min(100, self.max_items_per_collection - collected_count),
                    tweet_fields=[
                        'created_at', 'public_metrics', 'author_id',
                        'context_annotations', 'entities', 'lang'
                    ],
                    user_fields=['username', 'name', 'verified'],
                    expansions=['author_id']
                )

                if tweets.data:
                    for tweet in tweets.data:
                        if collected_count >= self.max_items_per_collection:
                            break

                        # Process tweet
                        tweet_data = await self._process_tweet(tweet)
                        if tweet_data:
                            research_data.append(tweet_data)
                            collected_count += 1

                        # Note: Twitter API v2 doesn't provide replies in search results
                        # For replies, we'd need to use different endpoints

            except TweepyException as e:
                self.logger.warning(f"Error searching Twitter for '{query}': {e}")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error in Twitter collection: {e}")
                continue

        self.logger.info(f"Collected {len(research_data)} items from Twitter")
        return research_data

    async def _get_company_keywords(self) -> List[str]:
        """Get company-related keywords for searching."""
        # TODO: This should come from company model
        return ["productivity", "SaaS", "workflow", "tool", "app"]

    def _build_search_queries(self, keywords: List[str]) -> List[str]:
        """Build Twitter search queries from keywords."""
        queries = []

        # Basic keyword searches
        for keyword in keywords[:3]:  # Limit keywords
            queries.append(f'"{keyword}"')

        # Pain point indicators
        pain_indicators = ["problem", "issue", "frustrated", "annoying", "difficult", "broken"]
        for keyword in keywords[:2]:
            for indicator in pain_indicators[:2]:  # Limit combinations
                queries.append(f'"{keyword}" {indicator}')

        # Feature requests
        feature_indicators = ["need", "want", "wish", "should have", "feature request"]
        for keyword in keywords[:2]:
            for indicator in feature_indicators[:2]:
                queries.append(f'"{keyword}" {indicator}')

        # Filter for English and exclude retweets
        filtered_queries = []
        for query in queries:
            filtered_queries.append(f"{query} lang:en -is:retweet")

        return filtered_queries[:8]  # Limit to avoid rate limits

    async def _process_tweet(self, tweet) -> Optional[ResearchData]:
        """Process a Twitter tweet into ResearchData."""
        try:
            # Skip if tweet is too old (more than 7 days - API limitation)
            tweet_date = tweet.created_at
            if isinstance(tweet_date, str):
                tweet_date = datetime.fromisoformat(tweet_date.replace('Z', '+00:00'))

            if tweet_date < datetime.now() - timedelta(days=7):
                return None

            # Clean content
            content = self._clean_text(tweet.text)
            if len(content) < 20:  # Skip very short tweets
                return None

            # Skip tweets that are just URLs or mentions
            if len(content.replace('@', '').replace('#', '').replace('http', '').strip()) < 10:
                return None

            # Calculate relevance
            keywords = await self._get_company_keywords()
            relevance_score = self._calculate_relevance_score(content, keywords)

            # Extract metrics
            metrics = tweet.public_metrics
            likes = metrics.get('like_count', 0)
            retweets = metrics.get('retweet_count', 0)
            replies = metrics.get('reply_count', 0)

            # Extract hashtags and mentions
            hashtags = []
            mentions = []
            if hasattr(tweet, 'entities') and tweet.entities:
                if 'hashtags' in tweet.entities:
                    hashtags = [tag['tag'] for tag in tweet.entities['hashtags']]
                if 'mentions' in tweet.entities:
                    mentions = [mention['username'] for mention in tweet.entities['mentions']]

            # Get author info if available
            author_name = None
            if hasattr(tweet, 'author') and tweet.author:
                author_name = tweet.author.username

            return self.create_research_data(
                content_type="tweet",
                title=f"Tweet by @{author_name}" if author_name else "Tweet",
                content=content,
                source_url=f"https://twitter.com/i/web/status/{tweet.id}",
                source_title="Twitter",
                source_author=f"@{author_name}" if author_name else None,
                source_date=tweet_date,
                upvotes=likes,
                comments_count=replies,
                shares=retweets,
                relevance_score=relevance_score,
                tags=hashtags,
                language=tweet.lang or "en",
            )

        except Exception as e:
            self.logger.warning(f"Error processing tweet {tweet.id}: {e}")
            return None
