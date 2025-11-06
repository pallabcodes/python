#!/usr/bin/env python3
"""
Basic usage examples for the MLOps + Gen AI Platform.

This script demonstrates core platform functionality including:
- Platform initialization
- MLOps experiment tracking
- Feature store operations
- Model registry usage
- Basic monitoring
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.platform import MLOpsPlatform


async def mlops_demo():
    """Demonstrate MLOps capabilities."""
    print("\n🔬 MLOps Demo")
    print("-" * 30)

    # Create experiment
    from mlops.experiment_tracker import ExperimentConfig
    experiment_config = ExperimentConfig(
        name="sentiment_analysis_experiment",
        description="Training sentiment analysis model",
        tags={"type": "nlp", "task": "sentiment"}
    )
    experiment_id = await platform._mlops_components["experiment_tracker"].create_experiment(experiment_config)
    print(f"✅ Created experiment: {experiment_id}")

    # Start experiment run
    run_id = await platform._mlops_components["experiment_tracker"].start_run(
        "sentiment_analysis_experiment",
        run_name="bert_base_run"
    )
    print(f"✅ Started run: {run_id}")

    # Log hyperparameters
    await platform._mlops_components["experiment_tracker"].log_hyperparameters(
        run_id,
        {
            "learning_rate": 2e-5,
            "batch_size": 16,
            "epochs": 3,
            "model": "bert-base-uncased"
        }
    )
    print("✅ Logged hyperparameters")

    # Create feature in feature store
    feature_version = await platform._mlops_components["feature_store"].create_feature(
        name="text_length",
        feature_type="numerical",
        data_type="int",
        description="Length of input text in characters"
    )
    print(f"✅ Created feature: text_length v{feature_version}")

    # Store feature values
    sample_texts = {
        "text_001": 45,
        "text_002": 123,
        "text_003": 78,
        "text_004": 234,
        "text_005": 67
    }
    stored_count = await platform._mlops_components["feature_store"].store_feature_values(
        "text_length", sample_texts
    )
    print(f"✅ Stored {stored_count} feature values")

    # Retrieve features
    retrieved = await platform._mlops_components["feature_store"].get_feature_values(
        ["text_length"], ["text_001", "text_002", "text_003"]
    )
    print(f"✅ Retrieved features: {retrieved}")

    # Register model
    from datetime import datetime
    from mlops.model_registry import ModelMetadata

    metadata = ModelMetadata(
        name="sentiment_classifier",
        version="1.0.0",
        description="BERT-based sentiment classification model",
        model_type="text_classification",
        framework="transformers",
        hyperparameters={
            "model_name": "bert-base-uncased",
            "num_labels": 3,
            "max_length": 512
        },
        metrics={
            "accuracy": 0.92,
            "f1_score": 0.91,
            "precision": 0.93
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
        status="staging"
    )

    # Create a dummy model file for demo
    import os
    os.makedirs("models", exist_ok=True)
    with open("models/sentiment_classifier_v1.pkl", "w") as f:
        f.write("dummy model data")  # In real usage, this would be actual model

    model_version = await platform._mlops_components["model_registry"].register_model(
        name="sentiment_classifier",
        model_artifact="models/sentiment_classifier_v1.pkl",
        metadata=metadata
    )
    print(f"✅ Registered model: sentiment_classifier v{model_version}")

    # End experiment run
    await platform._mlops_components["experiment_tracker"].end_run(run_id)
    print("✅ Ended experiment run")


async def monitoring_demo():
    """Demonstrate monitoring capabilities."""
    print("\n📊 Monitoring Demo")
    print("-" * 30)

    # Configure alert
    from mlops.model_monitor import AlertConfig

    alert = AlertConfig(
        metric_name="accuracy",
        threshold=0.85,
        condition="below",
        severity="warning"
    )

    await platform._mlops_components["model_monitor"].configure_alert(
        "sentiment_classifier", alert
    )
    print("✅ Configured accuracy alert")

    # Record some metrics
    from mlops.model_monitor import ModelMetrics
    from datetime import datetime

    metrics = ModelMetrics(
        timestamp=datetime.now(),
        accuracy=0.89,
        precision=0.87,
        recall=0.91,
        f1_score=0.89,
        latency_ms=45.2,
        throughput=125.8
    )

    await platform._mlops_components["model_monitor"].record_metrics(
        "sentiment_classifier", metrics
    )
    print("✅ Recorded model metrics")

    # Get performance summary
    performance = await platform._mlops_components["model_monitor"].get_model_performance(
        "sentiment_classifier", hours=24
    )
    print(f"✅ Performance summary: {performance}")


async def platform_status_demo():
    """Show platform status and capabilities."""
    print("\n📈 Platform Status")
    print("-" * 30)

    status = platform.get_status()
    print(f"Status: {status.status}")
    print(f"Version: {status.version}")
    print(f"Environment: {status.environment}")
    print(f"Uptime: {status.uptime_seconds:.1f} seconds" if status.uptime_seconds else "Uptime: N/A")

    print("\nComponent Status:")
    for component, comp_status in status.components.items():
        print(f"  {component}: {comp_status}")

    # List models
    models = await platform._mlops_components["model_registry"].list_models()
    print(f"\n📋 Registered Models: {len(models)}")
    for model in models[:3]:  # Show first 3
        print(f"  {model['name']} v{model['latest_version']} - {model['status']}")

    # List features
    features = await platform._mlops_components["feature_store"].list_features()
    print(f"\n🔍 Feature Store: {len(features)} features")
    for feature in features[:3]:  # Show first 3
        print(f"  {feature['name']} ({feature['type']}) - {feature['count']} values")


async def main():
    """Main demo function."""
    print("🚀 MLOps + Gen AI Platform - Basic Usage Demo")
    print("=" * 60)

    global platform
    platform = MLOpsPlatform()

    try:
        # Initialize platform
        print("🔧 Initializing platform...")
        await platform.initialize()
        print("✅ Platform ready!")

        # Run demos
        await mlops_demo()
        await monitoring_demo()
        await platform_status_demo()

        print("\n🎉 Demo completed successfully!")
        print("\n💡 Next steps:")
        print("  • Explore Gen AI features (coming in Phase 2)")
        print("  • Deploy to production (Phase 3)")
        print("  • Integrate with your analytics pipeline")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if 'platform' in globals():
            await platform.shutdown()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
