"""
Data Source Factory for analytics pipeline.

This module provides factory functions and utilities for creating
and configuring various data sources for the analytics pipeline.
"""

from typing import List, Dict, Any, Optional
from .rss_feed_source import RSSFeedSource, RSSFeedConfig
from .api_client_source import APIClientSource, APIEndpointConfig, APIAuthType
from .log_file_source import LogFileSource, LogFileConfig


def create_rss_feed_source(
    name: str,
    feed_urls: List[str],
    feed_names: Optional[List[str]] = None,
    poll_interval: int = 300,
    **kwargs
) -> RSSFeedSource:
    """Create RSS feed source with multiple feeds.

    Args:
        name: Source stage name
        feed_urls: List of RSS feed URLs
        feed_names: Optional list of feed names (defaults to URL-based names)
        poll_interval: Polling interval in seconds
        **kwargs: Additional RSSFeedSource parameters

    Returns:
        Configured RSSFeedSource
    """
    if feed_names is None:
        feed_names = [f"feed_{i+1}" for i in range(len(feed_urls))]

    feeds = []
    for url, feed_name in zip(feed_urls, feed_names):
        feed_config = RSSFeedConfig(
            url=url,
            name=feed_name,
            poll_interval=poll_interval
        )
        feeds.append(feed_config)

    return RSSFeedSource(name=name, feeds=feeds, **kwargs)


def create_newsapi_source(
    name: str,
    api_key: str,
    poll_interval: int = 600,  # 10 minutes
    **kwargs
) -> APIClientSource:
    """Create NewsAPI source for news articles.

    Args:
        name: Source stage name
        api_key: NewsAPI key
        poll_interval: Polling interval in seconds
        **kwargs: Additional APIClientSource parameters

    Returns:
        Configured APIClientSource for NewsAPI
    """
    endpoints = [
        {
            "name": "top_headlines",
            "url": "https://newsapi.org/v2/top-headlines",
            "method": "GET",
            "params": {"country": "us", "pageSize": 20},
            "auth_type": "api_key"
        }
    ]
    
    return APIClientSource(
        name="newsapi",
        base_url="https://newsapi.org/v2",
        endpoints=endpoints,
        auth_config={"api_key": api_key},
        **kwargs
    )
