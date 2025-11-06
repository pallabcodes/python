"""
Data Sources for Analytics Pipeline.

This module provides various data source implementations for ingesting
data from RSS feeds, REST APIs, log files, and other sources into
the analytics pipeline.
"""

from .rss_feed_source import RSSFeedSource, RSSFeedConfig, FeedEntry, RSSFeedStats
from .api_client_source import APIClientSource, APIEndpointConfig, APIAuthType, APIResponse, APIClientStats
from .log_file_source import LogFileSource, LogFileConfig, LogEntry, LogFileStats
from .source_factory import (
    create_rss_feed_source,
    create_newsapi_source,
    create_log_file_source,
    create_web_analytics_source,
    create_demo_sources
)

__all__ = [
    # RSS Feed Source
    'RSSFeedSource', 'RSSFeedConfig', 'FeedEntry', 'RSSFeedStats',

    # API Client Source
    'APIClientSource', 'APIEndpointConfig', 'APIAuthType', 'APIResponse', 'APIClientStats',

    # Log File Source
    'LogFileSource', 'LogFileConfig', 'LogEntry', 'LogFileStats',

    # Factory Functions
    'create_rss_feed_source', 'create_newsapi_source', 'create_log_file_source',
    'create_web_analytics_source', 'create_demo_sources'
]
