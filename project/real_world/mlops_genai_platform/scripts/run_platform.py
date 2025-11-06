#!/usr/bin/env python3
"""
Script to run the MLOps + Gen AI Platform.

This script demonstrates the platform initialization and basic functionality.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.platform import MLOpsPlatform


async def demo_mlops_features():
    """Demonstrate MLOps features."""
    print("🚀 Demonstrating MLOps Features...")

    # Create experiment
    experiment_id = await platform._mlops_components["experiment_tracker"].create_experiment(
        experiment_config={
            "name": "demo_experiment",
            "description": "Demo experiment for platform showcase",
            "tags": {"demo": "true", "type": "classification"}
        }
    )
    print(f"✅ Created experiment: {experiment_id}")

    # Create feature in feature store
    feature_version = await platform._mlops_components["feature_store"].create_feature(
        name="demo_feature",
        feature_type="numerical",
        data_type="float",
        description="Demo feature for platform showcase"
    )
    print(f"✅ Created feature: demo_feature v{feature_version}")

    # Store some sample feature values
    sample_values = {f"user_{i}": float(i) * 0.1 for i in range(10)}
    stored_count = await platform._mlops_components["feature_store"].store_feature_values(
        "demo_feature", sample_values
    )
    print(f"✅ Stored {stored_count} feature values")

    # Register a demo model
    from datetime import datetime
    from mlops.model_registry import ModelMetadata

    metadata = ModelMetadata(
        name="demo_model",
        version="1.0.0",
        description="Demo model for platform showcase",
        model_type="classification",
        framework="pytorch",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    model_version = await platform._mlops_components["model_registry"].register_model(
        name="demo_model",
        model_artifact="demo_model.pkl",  # Would be actual model file
        metadata=metadata
    )
    print(f"✅ Registered model: demo_model v{model_version}")

    print("🎉 MLOps demonstration complete!")


async def main():
    """Main function to run the platform."""
    print("🤖 MLOps + Gen AI Platform")
    print("=" * 50)

    global platform
    platform = MLOpsPlatform()

    try:
        # Initialize platform
        print("🔧 Initializing platform...")
        await platform.initialize()
        print("✅ Platform initialized successfully!")

        # Get platform status
        status = platform.get_status()
        print(f"📊 Platform Status: {status.status}")
        print(f"📦 Components: {len(status.components)} loaded")

        # Demo MLOps features
        await demo_mlops_features()

        # Keep platform running for interactive use
        print("\n🎯 Platform is running! Press Ctrl+C to exit.")
        print("💡 You can now interact with the platform programmatically")

        # In a real application, you might start a web server here
        # For now, just keep it running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested...")
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.exception("Platform error")
        return 1
    finally:
        if 'platform' in globals():
            await platform.shutdown()
            print("👋 Platform shutdown complete!")

    return 0


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run the platform
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
