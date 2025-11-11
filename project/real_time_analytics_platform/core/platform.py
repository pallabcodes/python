"""
Main Analytics Platform - Integrates ALL Our Concurrency Patterns.

This demonstrates how to combine:
- AsyncIO for real-time ingestion
- Reactive streams for event processing
- Multiprocessing for heavy analytics
- Actor model for monitoring
- Distributed coordination
- Hybrid adaptive execution
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

# Import our concurrency patterns (with fallbacks)
try:
    from advanced_hybrid_concurrency import (
        AdaptiveExecutor, ConcurrencyConfig, ReactiveStream,
        ActorSystem, AlertActor, DistributedLock
    )
    from hybrid_concurrency import AsyncioThreadingHybrid
    HAS_ADVANCED_PATTERNS = True
except ImportError:
    HAS_ADVANCED_PATTERNS = False
    # Create fallback classes
    class AdaptiveExecutor:
        def __init__(self, config=None): pass
        async def initialize(self): pass
        async def execute(self, func, *args, **kwargs): return await func(*args, **kwargs)
        async def get_stats(self): return {"adaptation_count": 0}
        async def cleanup(self): pass

    class ConcurrencyConfig:
        def __init__(self, adaptive_enabled=False, max_threads=4, max_processes=2, cpu_high_threshold=80.0):
            self.adaptive_enabled = adaptive_enabled
            self.max_threads = max_threads
            self.max_processes = max_processes
            self.cpu_high_threshold = cpu_high_threshold

    class ReactiveStream:
        def __init__(self, name="stream"): self.name = name
        async def emit(self, data, metadata=None): return True
        def subscribe(self, func): return self
        async def start(self): pass
        async def stop(self): pass

    class ActorSystem:
        def __init__(self): pass
        async def start(self): pass
        async def stop(self): pass
        async def send_message(self, target, message): return True
        def get_system_metrics(self): return {"total_actors": 0, "running_actors": 0, "total_messages_processed": 0, "success_rate": 1.0}

    class AlertActor: pass
    class DistributedLock:
        def __init__(self, name, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass

    class AsyncioThreadingHybrid:
        def __init__(self, max_workers=4): pass
        async def start(self): pass
        async def stop(self): pass
        async def run_cpu_task(self, func, *args): return func(*args)

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsEvent:
    """Represents an analytics event."""
    event_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"
    priority: int = 1


@dataclass
class AnalyticsResult:
    """Result of analytics processing."""
    event_id: str
    results: Dict[str, Any]
    processing_time: float
    alerts_triggered: List[str] = field(default_factory=list)


class AnalyticsPlatform:
    """
    Real-Time Analytics Platform demonstrating ALL concurrency patterns.

    Architecture:
    - AsyncIO ingestion layer for real-time data intake
    - Reactive streams for event processing pipeline
    - Multiprocessing analytics for heavy computations
    - Actor-based monitoring and alerting
    - Distributed coordination for scaling
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.running = False

        # Core concurrency components
        self.adaptive_executor = AdaptiveExecutor(self.config.concurrency)
        self.hybrid_processor = AsyncioThreadingHybrid(max_workers=4)
        self.event_system = EventSystem()

        # Analytics pipeline components
        self.ingestion_stream = ReactiveStream()
        self.processing_stream = ReactiveStream()
        self.analytics_stream = ReactiveStream()

        # Actor system for monitoring
        self.actor_system = ActorSystem()
        self.alert_actor = None

        # Distributed coordination
        self.distributed_lock = DistributedLock("analytics_platform")

        # Statistics
        self.stats = {
            "events_processed": 0,
            "alerts_triggered": 0,
            "processing_time_avg": 0.0,
            "uptime_seconds": 0
        }

    def _load_config(self, config_path: Optional[str] = None) -> 'PlatformConfig':
        """Load platform configuration."""
        # Default configuration
        return PlatformConfig(
            concurrency=ConcurrencyConfig(
                adaptive_enabled=True,
                max_threads=8,
                max_processes=4,
                cpu_high_threshold=80.0
            ),
            ingestion_port=8080,
            enable_distributed=True,
            alert_thresholds={
                "error_rate": 0.05,
                "latency_p95": 1.0,
                "throughput_drop": 0.5
            }
        )

    async def start(self):
        """Start the analytics platform."""
        if self.running:
            return

        logger.info("Starting Real-Time Analytics Platform...")

        # Initialize all components
        await self.adaptive_executor.initialize()
        await self.hybrid_processor.start()

        # Setup reactive processing pipeline
        self._setup_processing_pipeline()

        # Start actor system and monitoring (if available)
        if HAS_ADVANCED_PATTERNS:
            await self.actor_system.start()
            self.alert_actor = await self.actor_system.spawn(AlertActor, "analytics_alerts")
        else:
            self.alert_actor = None

        # Start ingestion API
        ingestion_task = asyncio.create_task(self._start_ingestion_api())

        # Start monitoring loop
        monitoring_task = asyncio.create_task(self._monitoring_loop())

        self.running = True
        self.start_time = time.time()

        logger.info("✅ Analytics Platform started successfully!")
        logger.info("🚀 Ready to process real-time analytics events")

        # Wait for components (in real implementation, this would run indefinitely)
        await asyncio.sleep(1)

    async def stop(self):
        """Stop the analytics platform."""
        if not self.running:
            return

        logger.info("Stopping Analytics Platform...")

        self.running = False

        await self.adaptive_executor.cleanup()
        await self.hybrid_processor.stop()
        if HAS_ADVANCED_PATTERNS:
            await self.actor_system.stop()

        self.stats["uptime_seconds"] = time.time() - self.start_time

        logger.info("✅ Analytics Platform stopped")

    def _setup_processing_pipeline(self):
        """Setup the reactive processing pipeline."""
        # Ingestion → Validation → Processing → Analytics → Storage

        def validate_event(event: AnalyticsEvent) -> Optional[AnalyticsEvent]:
            """Validate incoming events."""
            if not event.data or not isinstance(event.data, dict):
                logger.warning(f"Invalid event data: {event.event_id}")
                return None
            return event

        def enrich_event(event: AnalyticsEvent) -> AnalyticsEvent:
            """Enrich event with metadata."""
            event.data["processed_at"] = time.time()
            event.data["platform_version"] = "1.0.0"
            return event

        def route_by_priority(event: AnalyticsEvent) -> Optional[AnalyticsEvent]:
            """Route high-priority events for immediate processing."""
            if event.priority >= 3:
                # High priority - process immediately
                asyncio.create_task(self._process_high_priority_event(event))
                return None  # Don't continue in normal pipeline
            return event

        # Setup pipeline transformations
        async def process_event(event):
            # Apply transformations sequentially
            validated = validate_event(event)
            if validated is None:
                return

            enriched = enrich_event(validated)
            routed = route_by_priority(enriched)
            if routed is not None:
                await self._process_normal_event(routed)

        async def handle_ingestion(event):
            await self.processing_stream.emit(event)
            await process_event(event)

        self.ingestion_stream.subscribe(lambda e: asyncio.create_task(handle_ingestion(e)))

    async def _process_high_priority_event(self, event: AnalyticsEvent):
        """Process high-priority events immediately."""
        logger.info(f"🚨 Processing high-priority event: {event.event_id}")

        # Use adaptive executor for immediate processing
        result = await self.adaptive_executor.execute(
            self._run_analytics, event, priority="high"
        )

        # Send alert if anomalies detected
        if result.get("anomaly_detected", False) and HAS_ADVANCED_PATTERNS and self.alert_actor:
            await self.actor_system.send_message(
                self.alert_actor.actor_id,
                Message(
                    message_type="anomaly_alert",
                    payload={
                        "event_id": event.event_id,
                        "anomaly_score": result["anomaly_score"],
                        "severity": "high"
                    }
                )
            )

    def _process_normal_event(self, event: AnalyticsEvent):
        """Process normal-priority events."""
        logger.debug(f"Processing normal event: {event.event_id}")

        # Add to analytics stream for batch processing
        self.analytics_stream.emit(event)

    async def _run_analytics(self, event: AnalyticsEvent, priority: str = "normal") -> Dict[str, Any]:
        """Run analytics on event data."""
        start_time = time.time()

        # Simulate different types of analytics based on event type
        if event.event_type == "user_action":
            # Light analytics - use threading
            result = await self.hybrid_processor.run_cpu_task(
                self._user_behavior_analytics, event.data
            )
        elif event.event_type == "system_metrics":
            # Heavy analytics - use adaptive executor
            result = await self.adaptive_executor.execute(
                self._system_performance_analytics, event.data
            )
        else:
            # Default analytics
            result = await self.adaptive_executor.execute(
                self._general_analytics, event.data
            )

        processing_time = time.time() - start_time

        # Update statistics
        self.stats["events_processed"] += 1
        self.stats["processing_time_avg"] = (
            (self.stats["processing_time_avg"] * (self.stats["events_processed"] - 1)) +
            processing_time
        ) / self.stats["events_processed"]

        return {
            "event_id": event.event_id,
            "analytics": result,
            "processing_time": processing_time,
            "priority": priority
        }

    def _user_behavior_analytics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Lightweight user behavior analytics."""
        # Simulate user segmentation, engagement scoring, etc.
        time.sleep(0.01)  # Simulate processing
        return {
            "user_segment": "premium" if data.get("revenue", 0) > 100 else "standard",
            "engagement_score": min(100, data.get("actions", 0) * 10),
            "anomaly_detected": data.get("actions", 0) > 50
        }

    def _system_performance_analytics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Heavy system performance analytics."""
        # Simulate complex performance analysis, anomaly detection, etc.
        import math
        time.sleep(0.05)  # Simulate heavy computation

        cpu_usage = data.get("cpu_percent", 50)
        memory_usage = data.get("memory_percent", 50)

        # Calculate performance score
        performance_score = 100 - (cpu_usage * 0.7 + memory_usage * 0.3)

        return {
            "performance_score": performance_score,
            "bottleneck_detected": cpu_usage > 85 or memory_usage > 90,
            "optimization_suggestions": [
                "Consider scaling CPU" if cpu_usage > 80 else None,
                "Consider scaling memory" if memory_usage > 85 else None
            ]
        }

    def _general_analytics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """General-purpose analytics."""
        # Basic statistical analysis
        if "values" in data:
            values = data["values"]
            if isinstance(values, list) and values:
                import statistics
                return {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "anomaly_detected": any(v > 100 for v in values)  # Simple anomaly detection
                }

        return {"analysis": "general", "insights": len(str(data))}

    async def ingest_event(self, event: AnalyticsEvent) -> str:
        """Ingest an analytics event into the platform."""
        if not self.running:
            raise RuntimeError("Platform not started")

        # Emit to ingestion stream
        self.ingestion_stream.emit(event)

        logger.info(f"📥 Ingested event: {event.event_id} ({event.event_type})")
        return event.event_id

    async def get_platform_stats(self) -> Dict[str, Any]:
        """Get comprehensive platform statistics."""
        executor_stats = await self.adaptive_executor.get_stats()

        return {
            "platform": {
                "running": self.running,
                "uptime_seconds": time.time() - getattr(self, 'start_time', time.time()),
                "events_processed": self.stats["events_processed"],
                "alerts_triggered": self.stats["alerts_triggered"],
                "avg_processing_time": self.stats["processing_time_avg"]
            },
            "executor": executor_stats,
            "concurrency": {
                "adaptive_enabled": self.config.concurrency.adaptive_enabled,
                "current_load": "unknown"  # Would integrate with monitoring
            }
        }

    async def _start_ingestion_api(self):
        """Start the ingestion API (simplified for demo)."""
        logger.info("Ingestion API would start on port 8080")
        # In real implementation, would start FastAPI server

    async def _monitoring_loop(self):
        """Continuous monitoring loop."""
        while self.running:
            try:
                # Check for anomalies and system health
                stats = await self.get_platform_stats()

                # Trigger alerts if needed
                if (stats["platform"]["avg_processing_time"] > 2.0 and  # High latency
                    HAS_ADVANCED_PATTERNS and self.alert_actor):
                    await self.actor_system.send_message(
                        self.alert_actor.actor_id,
                        Message(
                            message_type="latency_alert",
                            payload={
                                "avg_latency": stats["platform"]["avg_processing_time"],
                                "threshold": 2.0
                            }
                        )
                    )

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)


# Simplified Message class for actor communication
@dataclass
class Message:
    """Message for actor communication."""
    message_type: str
    payload: Dict[str, Any]
    sender: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class PlatformConfig:
    """Platform configuration."""
    concurrency: ConcurrencyConfig
    ingestion_port: int = 8080
    enable_distributed: bool = False
    alert_thresholds: Dict[str, float] = None

    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "error_rate": 0.05,
                "latency_p95": 1.0,
                "throughput_drop": 0.5
            }


class EventSystem:
    """Simple event system for demonstration."""
    def __init__(self):
        self.listeners: Dict[str, List[callable]] = {}

    def subscribe(self, event_type: str, callback: callable):
        """Subscribe to event type."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    async def publish(self, event_type: str, data: Any):
        """Publish event to subscribers."""
        if event_type in self.listeners:
            tasks = []
            for callback in self.listeners[event_type]:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(data))
                else:
                    tasks.append(asyncio.get_event_loop().run_in_executor(None, callback, data))
            await asyncio.gather(*tasks, return_exceptions=True)


