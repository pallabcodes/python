"""
Queue management utilities for ProducerConsumerQueue.

This module provides utility functions for managing and monitoring
producer-consumer queues.
"""

import logging
from typing import Any, Dict

from .queue_core import ProducerConsumerQueue


def get_queue_stats(queue: ProducerConsumerQueue) -> Dict[str, Any]:
    """Get comprehensive queue statistics.

    Args:
        queue: Queue to get statistics for.

    Returns:
        Dictionary with detailed queue statistics.
    """
    queue_stats = queue.queue.get_stats()

    # Basic stats
    stats = {
        "queue_name": queue.name,
        "queue_size": queue_stats["size"],
        "maxsize": queue_stats["maxsize"],
        "producer_count": len(queue.producers),
        "consumer_count": len(queue.consumers),
        "active_producers": sum(1 for p in queue.producers if p.is_alive()),
        "active_consumers": sum(1 for c in queue.consumers if c.is_alive()),
    }

    if queue.shutdown_event:
        stats["shutdown_signaled"] = queue.shutdown_event.is_set()
    else:
        stats["shutdown_signaled"] = False

    # Detailed producer stats
    producer_stats = []
    for producer in queue.producers:
        producer_stats.append({
            "name": producer.name,
            "alive": producer.is_alive(),
            "items_produced": producer.items_produced,
            "errors": producer.errors_encountered
        })
    stats["producers"] = producer_stats

    # Detailed consumer stats
    consumer_stats = []
    for consumer in queue.consumers:
        consumer_stats.append({
            "name": consumer.name,
            "alive": consumer.is_alive(),
            "items_processed": consumer.items_processed,
            "errors": consumer.errors_encountered,
            "shutdown_received": consumer.shutdown_received
        })
    stats["consumers"] = consumer_stats

    # Performance metrics
    total_produced = sum(p["items_produced"] for p in producer_stats)
    total_processed = sum(c["items_processed"] for c in consumer_stats)
    total_errors = sum(p["errors"] + c["errors"] for p in producer_stats for c in consumer_stats)

    stats.update({
        "total_items_produced": total_produced,
        "total_items_processed": total_processed,
        "total_errors": total_errors,
        "items_in_flight": total_produced - total_processed,
        "processing_efficiency": total_processed / max(total_produced, 1),
    })

    return stats


def log_queue_stats(queue: ProducerConsumerQueue, level: int = logging.INFO) -> None:
    """Log current queue statistics.

    Args:
        queue: Queue to log statistics for.
        level: Logging level to use.
    """
    stats = get_queue_stats(queue)
    logger = logging.getLogger(__name__)

    logger.log(
        level,
        f"Queue '{stats['queue_name']}' stats: "
        f"size={stats['queue_size']}, "
        f"produced={stats['total_items_produced']}, "
        f"processed={stats['total_items_processed']}, "
        f"errors={stats['total_errors']}",
        extra=stats
    )


def check_queue_health(queue: ProducerConsumerQueue) -> Dict[str, Any]:
    """Check queue health and identify potential issues.

    Args:
        queue: Queue to check health for.

    Returns:
        Health check results with warnings and recommendations.
    """
    stats = get_queue_stats(queue)
    issues = []
    recommendations = []

    # Check for thread health
    dead_producers = [p for p in stats["producers"] if not p["alive"]]
    dead_consumers = [c for c in stats["consumers"] if not c["alive"]]

    if dead_producers:
        issues.append(f"{len(dead_producers)} producer threads are dead")
        recommendations.append("Check producer threads for exceptions")

    if dead_consumers:
        issues.append(f"{len(dead_consumers)} consumer threads are dead")
        recommendations.append("Check consumer threads for exceptions")

    # Check for errors
    if stats["total_errors"] > 0:
        issues.append(f"{stats['total_errors']} errors encountered")
        recommendations.append("Review error logs for failure patterns")

    # Check for backpressure
    if stats.get("bounded", False) and stats["queue_size"] == stats["maxsize"]:
        issues.append("Queue is at maximum capacity")
        recommendations.append("Consider increasing queue size or consumer throughput")

    # Check for processing lag
    if stats["items_in_flight"] > stats["maxsize"] * 2:
        issues.append(f"High items in flight: {stats['items_in_flight']}")
        recommendations.append("Increase consumer count or reduce producer rate")

    return {
        "healthy": len(issues) == 0,
        "issues": issues,
        "recommendations": recommendations,
        "stats": stats
    }

