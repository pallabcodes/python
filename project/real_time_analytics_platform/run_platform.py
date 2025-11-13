"""
Main entry point for the Real-Time Analytics Platform.

This script provides different ways to run the platform:
1. Full integration demo (shows all patterns working together)
2. Individual component demos
3. Performance benchmarks
4. Development mode with detailed logging
"""

import asyncio
import sys
import logging
from typing import Optional

from integration_demo import RealTimeAnalyticsDemo
from core.platform import AnalyticsPlatform


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('analytics_platform.log')
        ]
    )


async def run_full_demo(duration: int = 30):
    """Run the complete integration demo."""
    print("🚀 Starting Real-Time Analytics Platform - Full Integration Demo")
    print(f"Duration: {duration} seconds")
    print("-" * 60)

    demo = RealTimeAnalyticsDemo()
    await demo.run_demo(duration)


async def run_platform_only():
    """Run just the core analytics platform."""
    print("🏗️ Starting Core Analytics Platform")
    print("-" * 40)

    platform = AnalyticsPlatform()

    try:
        await platform.start()
        print("✅ Platform started successfully!")
        print("📊 Generating sample events...")

        # Generate some sample events
        for i in range(10):
            event = await platform.ingest_event({
                "event_id": f"sample_{i}",
                "event_type": "custom_event",
                "data": {"sample_data": i, "timestamp": asyncio.get_event_loop().time()},
                "source": "manual_test"
            })
            print(f"📥 Ingested event: {event}")

        # Wait a bit for processing
        await asyncio.sleep(5)

        # Show final stats
        stats = await platform.get_platform_stats()
        print(f"📊 Final Stats: {stats}")

    finally:
        await platform.stop()


async def run_advanced_features_demo(duration: int = 30):
    """Run demo showcasing all advanced features."""
    print("🌐 Starting Advanced Features Demo")
    print(f"Duration: {duration} seconds")
    print("-" * 60)
    
    from core.platform import AnalyticsPlatform
    from ingestion import WebSocketHandler
    from analytics import MLProcessor, MLModelConfig, AdvancedAnalyticsEngine
    from monitoring import DashboardAPI
    import time
    
    platform = AnalyticsPlatform()
    
    try:
        await platform.start()
        print("✅ Platform started with all advanced components")
        
        # Demonstrate WebSocket
        if platform.websocket_handler:
            print("\n📡 WebSocket Handler:")
            print(f"   Active connections: {platform.websocket_handler.get_metrics()['active_connections']}")
            print(f"   Messages sent: {platform.websocket_handler.get_metrics()['total_messages_sent']}")
        
        # Demonstrate Kafka
        if platform.kafka_consumer:
            print("\n📨 Kafka Integration:")
            kafka_metrics = platform.kafka_consumer.get_metrics()
            print(f"   Messages consumed: {kafka_metrics['messages_consumed']}")
            print(f"   Messages processed: {kafka_metrics['messages_processed']}")
        
        # Demonstrate ML Pipeline
        if platform.ml_processor:
            print("\n🤖 ML Processor:")
            ml_metrics = platform.ml_processor.get_metrics()
            print(f"   Total predictions: {ml_metrics['total_predictions']}")
            print(f"   GPU predictions: {ml_metrics['gpu_predictions']}")
            print(f"   CPU predictions: {ml_metrics['cpu_predictions']}")
            print(f"   Avg processing time: {ml_metrics['avg_processing_time']:.3f}s")
            
            # Run sample ML prediction
            sample_input = [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]
            prediction = await platform.ml_processor.predict("default_model", sample_input)
            if prediction:
                print(f"   Sample prediction: {prediction.predictions[0]:.3f}")
        
        # Demonstrate Advanced Analytics
        if platform.advanced_analytics:
            print("\n📊 Advanced Analytics:")
            # Add some sample data points
            current_time = time.time()
            for i in range(20):
                value = 50 + i * 2 + (i % 3) * 5
                platform.advanced_analytics.add_metric_point("sample_metric", current_time - (20-i), value)
            
            # Generate forecast
            forecast = platform.advanced_analytics.generate_forecast("sample_metric", steps=5)
            if forecast:
                print(f"   Forecast generated: {len(forecast.forecast_values)} steps")
                print(f"   Next predicted value: {forecast.forecast_values[0]:.2f}")
            
            # Detect anomalies
            anomaly = platform.advanced_analytics.detect_anomalies(
                "sample_metric", current_time, 100.0
            )
            if anomaly:
                print(f"   Anomaly detected: {anomaly.anomaly_type} (severity: {anomaly.severity})")
        
        # Demonstrate Dashboard
        if platform.dashboard_api:
            print("\n📈 Dashboard API:")
            print(f"   Available at: http://localhost:8081")
            print(f"   Health endpoint: http://localhost:8081/health")
            print(f"   Metrics endpoint: http://localhost:8081/api/v1/metrics")
            print(f"   WebSocket stream: ws://localhost:8081/ws/metrics")
        
        # Demonstrate Container Orchestration
        if platform.kubernetes_orchestrator:
            print("\n☸️  Kubernetes Orchestration:")
            replicas = await platform.kubernetes_orchestrator.get_deployment_replicas()
            print(f"   Current replicas: {replicas}")
        
        # Generate some events to process
        print("\n📥 Generating sample events...")
        for i in range(10):
            from core.platform import AnalyticsEvent
            event = AnalyticsEvent(
                event_id=f"advanced_demo_{i}",
                event_type="system_metrics",
                data={"cpu": 50 + i, "memory": 60 + i, "timestamp": time.time()},
                source="advanced_demo"
            )
            await platform.ingest_event(event)
            await asyncio.sleep(0.1)
        
        # Wait for processing
        print(f"\n⏳ Processing events for {duration} seconds...")
        await asyncio.sleep(duration)
        
        # Show final stats
        stats = await platform.get_platform_stats()
        print("\n📊 Final Platform Stats:")
        print(f"   Events processed: {stats['platform']['events_processed']}")
        print(f"   Avg processing time: {stats['platform']['avg_processing_time']:.3f}s")
        
    finally:
        await platform.stop()
        print("\n✅ Advanced Features Demo Complete!")


async def run_performance_test():
    """Run performance benchmarking."""
    print("⚡ Running Performance Tests")
    print("-" * 30)

    import time
    from analytics.analytics_engine import AnalyticsEngine, statistical_analysis

    engine = AnalyticsEngine()

    # Test different workloads
    test_data = [
        ("light", {"values": list(range(100))}, 50),
        ("medium", {"values": list(range(1000))}, 20),
        ("heavy", {"values": list(range(10000))}, 5)
    ]

    for workload, data, iterations in test_data:
        print(f"\\n🧪 Testing {workload} workload ({iterations} iterations)")

        start_time = time.time()

        # Run batch analytics
        tasks = [(statistical_analysis, data, f"perf_test_{i}") for i in range(iterations)]
        results = await engine.execute_batch(tasks)

        elapsed = time.time() - start_time

        successful = sum(1 for r in results if not isinstance(r, Exception))
        print(f"{elapsed:.2f}s")
    await engine.shutdown()


def show_menu():
    """Show the main menu."""
    print("\\n🎯 Real-Time Analytics Platform")
    print("=" * 40)
    print("Choose how to run the platform:")
    print()
    print("1. 🚀 Full Integration Demo (Recommended)")
    print("   - Shows ALL concurrency patterns working together")
    print("   - Real-time data ingestion, processing, analytics")
    print("   - Actor-based monitoring and alerting")
    print("   - Comprehensive performance metrics")
    print()
    print("2. 🌐 Advanced Features Demo (NEW!)")
    print("   - WebSocket real-time streaming")
    print("   - Kafka distributed messaging")
    print("   - ML pipeline with GPU acceleration")
    print("   - Dashboard API with live metrics")
    print("   - Container orchestration (K8s/Docker)")
    print("   - Advanced analytics (forecasting, anomaly detection)")
    print()
    print("3. 🏗️ Core Platform Only")
    print("   - Basic analytics platform functionality")
    print("   - Manual event ingestion testing")
    print()
    print("4. ⚡ Performance Tests")
    print("   - Benchmark different workload types")
    print("   - Measure throughput and latency")
    print()
    print("5. 📚 Show Architecture Overview")
    print("   - Detailed explanation of components")
    print("   - Concurrency pattern integration")
    print()
    print("6. 🔧 Development Mode")
    print("   - Detailed logging and debugging")
    print("   - Component isolation testing")
    print()


def show_architecture():
    """Show detailed architecture overview."""
    print("\\n🏗️ REAL-TIME ANALYTICS PLATFORM ARCHITECTURE")
    print("=" * 55)

    print("\\n🎯 MISSION:")
    print("Demonstrate the most comprehensive integration of Python concurrency patterns")
    print("in a production-ready, real-world analytics platform.")
    print()

    print("📊 DATA FLOW ARCHITECTURE:")
    print("1. 📥 Ingestion Layer (AsyncIO)")
    print("   • REST API server with concurrent request handling")
    print("   • Rate limiting and circuit breakers")
    print("   • WebSocket streams for real-time data (NEW!)")
    print("   • Kafka consumer for distributed ingestion (NEW!)")
    print()

    print("2. 🌊 Processing Layer (Reactive Streams)")
    print("   • Event validation and filtering")
    print("   • Backpressure handling for load management")
    print("   • Real-time event transformation")
    print("   • Stream processing pipelines")
    print()

    print("3. 🧠 Analytics Layer (Multiprocessing)")
    print("   • CPU-intensive statistical analysis")
    print("   • ML model inference with GPU acceleration (NEW!)")
    print("   • Advanced anomaly detection algorithms (NEW!)")
    print("   • Time series forecasting (NEW!)")
    print("   • Predictive analytics and trend analysis (NEW!)")
    print()

    print("4. 👁️ Monitoring Layer (Actor Model)")
    print("   • Fault-tolerant alerting system")
    print("   • Supervisor hierarchies for resilience")
    print("   • Real-time health monitoring")
    print("   • Dashboard API with live metrics (NEW!)")
    print("   • WebSocket streaming for real-time updates (NEW!)")
    print("   • Historical metrics queries (NEW!)")
    print()

    print("5. 🎛️ Coordination Layer (Hybrid Patterns)")
    print("   • Adaptive workload routing")
    print("   • Distributed synchronization")
    print("   • Configuration-driven execution")
    print("   • Kubernetes container orchestration (NEW!)")
    print("   • Docker Swarm integration (NEW!)")
    print("   • Auto-scaling based on metrics (NEW!)")
    print()

    print("🚀 CONCURRENCY PATTERNS INTEGRATION:")
    print("• AsyncIO: Handles 1000s of concurrent connections")
    print("• Reactive Streams: Processes events without blocking")
    print("• Multiprocessing: Scales analytics to multiple CPU cores")
    print("• Actor Model: Provides fault-tolerant monitoring")
    print("• Hybrid Execution: Automatically routes workloads optimally")
    print("• Distributed Systems: Coordinates across multiple nodes")
    print()

    print("💼 REAL-WORLD APPLICATIONS:")
    print("• E-commerce: Real-time purchase analytics & recommendations")
    print("• IoT: Sensor data processing & predictive maintenance")
    print("• Financial: Ultra-low latency trading analytics")
    print("• Social Media: Real-time sentiment analysis")
    print("• Infrastructure: System monitoring & anomaly detection")
    print()

    print("🎉 RESULT: Production-grade analytics at any scale!")


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Command line mode
        command = sys.argv[1].lower()

        if command == "demo":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            await run_full_demo(duration)
        elif command == "advanced":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            await run_advanced_features_demo(duration)
        elif command == "platform":
            await run_platform_only()
        elif command == "perf":
            await run_performance_test()
        elif command == "dev":
            setup_logging("DEBUG")
            await run_full_demo(15)
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run_platform.py [demo|platform|perf|dev] [duration]")
    else:
        # Interactive menu mode
        while True:
            show_menu()
            try:
                choice = input("Enter your choice (1-6): ").strip()

                if choice == "1":
                    duration = input("Demo duration in seconds (default 30): ").strip()
                    duration = int(duration) if duration.isdigit() else 30
                    await run_full_demo(duration)
                    break

                elif choice == "2":
                    duration = input("Demo duration in seconds (default 30): ").strip()
                    duration = int(duration) if duration.isdigit() else 30
                    await run_advanced_features_demo(duration)
                    break

                elif choice == "3":
                    await run_platform_only()
                    break

                elif choice == "4":
                    await run_performance_test()
                    break

                elif choice == "5":
                    show_architecture()
                    input("\\nPress Enter to continue...")
                    continue

                elif choice == "6":
                    setup_logging("DEBUG")
                    print("🔧 Development mode enabled")
                    await run_full_demo(15)
                    break

                else:
                    print("❌ Invalid choice. Please select 1-6.")
                    continue

            except KeyboardInterrupt:
                print("\\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break


if __name__ == "__main__":
    # Setup default logging
    setup_logging("INFO")

    # Run the platform
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 Platform shutdown complete!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
