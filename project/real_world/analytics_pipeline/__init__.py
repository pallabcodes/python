"""
Real-Time Web Analytics Pipeline

A production-grade real-time analytics pipeline that ingests data from RSS feeds,
public APIs, and log files, processes it through multi-stage pipelines, and stores
results with comprehensive monitoring.

This project demonstrates:
- Concurrent multi-source data ingestion (50+ sources)
- Real-time stream processing with windowing analytics
- Adaptive resource management and autoscaling
- Multi-backend storage with connection pooling
- Comprehensive monitoring and alerting
- Circuit breakers and fault tolerance

All data sources are free (no payment required):
- RSS feeds (TechCrunch, BBC News, Hacker News)
- Public APIs (NewsAPI free tier, OpenWeatherMap free tier, JSONPlaceholder)
- Log files (web server logs, application logs)

Perfect for Google SDE-3 level: Demonstrates web-scale data processing similar
to Google's internal systems while using all 8 completed mini-projects.
"""

__version__ = "1.0.0"
__author__ = "Python Concurrency Learning Project"
__description__ = "Real-time web analytics pipeline demonstrating production-grade concurrency patterns"
