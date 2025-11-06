"""
Monitoring and statistics for ProducerConsumerQueue.

This module provides monitoring capabilities and statistics
collection for the producer-consumer queue system.
"""

import logging
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .queue_coordinator import ProducerConsumerQueue


class QueueMonitor:
    """Monitor for ProducerConsumerQueue statistics and health.

    This class provides comprehensive monitoring of queue performance,
    thread health, and system statistics for observability and debugging.

    Attributes:
        _queue: The queue being monitored.
        _logger: Logger for monitoring events.
    """

    def __init__(self, queue: "ProducerConsumerQueue", logger: logging.Logger = None):
        """Initialize queue monitor.

        Args:
            queue: ProducerConsumerQueue to monitor.
            logger: Logger instance (defaults to module logger).
        """
        self._queue = queue
        self._logger = logger or logging.getLogger(__name__)

    def get_stats(self) -> Dict[str, Any]:
        """Get current queue statistics.

        Returns:
            Dictionary with comprehensive queue statistics.
        """
        queue_stats = self._queue.queue.get_stats()

        # Basic stats
        stats = {
            "queue_name": self._queue.name,
            "queue_size": queue_stats["size"],
            "maxsize": queue_stats["maxsize"],
            "bounded": queue_stats["bounded"],
            "producer_count": len(self._queue.producers),
            "consumer_count": len(self._queue.consumers),
        }

        # Thread health
        stats.update({
            "active_producers": sum(1 for p in self._queue.producers if p.is_alive()),
            "active_consumers": sum(1 for c in self._queue.consumers if c.is_alive()),
            "shutdown_signaled": False,  # Would need access to internal state
        })

        # Detailed producer stats
        producer_stats = []
        for producer in self._queue.producers:
            producer_stats.append({
                "name": producer.name,
                "alive": producer.is_alive(),
                "items_produced": producer.items_produced,
                "errors": producer.errors_encountered
            })
        stats["producers"] = producer_stats

        # Detailed consumer stats
        consumer_stats = []
        for consumer in self._queue.consumers:
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

    def log_stats(self, level: int = logging.INFO) -> None:
        """Log current statistics.

        Args:
            level: Logging level to use.
        """
        stats = self.get_stats()

        self._logger.log(
            level,
            f"Queue '{stats['queue_name']}' stats: "
            f"size={stats['queue_size']}, "
            f"produced={stats['total_items_produced']}, "
            f"processed={stats['total_items_processed']}, "
            f"errors={stats['total_errors']}",
            extra=stats
        )

    def check_health(self) -> Dict[str, Any]:
        """Check queue health and identify potential issues.

        Returns:
            Health check results with warnings and recommendations.
        """
        stats = self.get_stats()
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
        if stats["bounded"] and stats["queue_size"] == stats["maxsize"]:
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


def create_monitor(queue: "ProducerConsumerQueue") -> QueueMonitor:
    """Create a monitor for the given queue.

    Args:
        queue: Queue to monitor.

    Returns:
        QueueMonitor instance.
    """
    return QueueMonitor(queue)

