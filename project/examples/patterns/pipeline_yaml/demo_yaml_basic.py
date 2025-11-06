"""
Basic YAML pipeline demonstrations.

This module contains fundamental demonstrations of YAML-driven
pipeline configuration and basic functionality.
"""

import tempfile
import logging
from pathlib import Path

from .pipeline_builder import build_pipeline_from_yaml


def demo_simple_yaml_pipeline() -> None:
    """Demonstrate a simple pipeline from YAML configuration."""
    print("=== Simple YAML Pipeline Demo ===")

    # YAML configuration as string
    yaml_config = """
name: "simple_processing_pipeline"
version: "1.0.0"
description: "A simple data processing pipeline"

stages:
  - name: "data_multiplier"
    type: "transform"
    module: "pipeline_core.stage_types"
    class_name: "TransformStage"
    parameters:
      factor: 3

  - name: "even_filter"
    type: "filter"
    module: "pipeline_core.stage_types"
    class_name: "FilterStage"
    parameters: {}

  - name: "result_printer"
    type: "sink"
    module: "pipeline_core.stage_types"
    class_name: "SinkStage"
    parameters: {}

queues:
  - name: "stage0-stage1"
    type: "memory"
    maxsize: 100

  - name: "stage1-stage2"
    type: "memory"
    maxsize: 100

global_settings:
  max_workers: 2
"""

    print("YAML Configuration:")
    print(yaml_config)
    print("\nBuilding pipeline from YAML...")

    try:
        # Build pipeline from YAML
        runner = build_pipeline_from_yaml(yaml_config)

        # Create input data (this would need to be implemented)
        # For demo purposes, we'll show the structure
        print("Pipeline built successfully!")
        print(f"Stages: {[s.name for s in runner._stages]}")
        print("Note: Actual execution would require custom stage implementations")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()


def demo_file_based_pipeline() -> None:
    """Demonstrate loading pipeline from configuration file."""
    print("\n=== File-Based Pipeline Demo ===")

    # Create temporary config file
    config_content = """
name: "file_based_pipeline"
version: "1.0.0"
description: "Pipeline loaded from configuration file"

stages:
  - name: "string_converter"
    type: "transform"
    module: "pipeline_core.stage_types"
    class_name: "TransformStage"
    parameters:
      prefix: "Processed: "

  - name: "length_filter"
    type: "filter"
    module: "pipeline_core.stage_types"
    class_name: "FilterStage"
    parameters:
      min_length: 15

  - name: "console_output"
    type: "sink"
    module: "pipeline_core.stage_types"
    class_name: "SinkStage"
    parameters: {}

global_settings:
  max_workers: 3
"""

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name

        print(f"Created config file: {config_file}")
        print("Config content:")
        print(config_content)

        # Load and build pipeline from file
        from .config_loader_core import load_pipeline_config
        from .pipeline_builder import YamlPipelineBuilder

        config = load_pipeline_config(config_file)
        builder = YamlPipelineBuilder()
        runner = builder.build_pipeline(config)

        print(f"Pipeline built successfully with {len(runner._stages)} stages")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        try:
            Path(config_file).unlink()
        except:
            pass


def demo_config_manager() -> None:
    """Demonstrate configuration manager usage."""
    print("\n=== Configuration Manager Demo ===")

    # Create temporary config directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple config files
        configs = {
            "data_processing.yaml": """
name: "data_processing"
version: "1.0.0"
stages:
  - name: "validator"
    type: "filter"
    module: "pipeline_core.stage_types"
    class_name: "FilterStage"
    parameters: {}
  - name: "processor"
    type: "transform"
    module: "pipeline_core.stage_types"
    class_name: "TransformStage"
    parameters: {}
""",
            "reporting.yaml": """
name: "reporting"
version: "1.0.0"
stages:
  - name: "aggregator"
    type: "transform"
    module: "pipeline_core.stage_types"
    class_name: "TransformStage"
    parameters: {}
  - name: "reporter"
    type: "sink"
    module: "pipeline_core.stage_types"
    class_name: "SinkStage"
    parameters: {}
"""
        }

        # Write config files
        for filename, content in configs.items():
            config_path = Path(temp_dir) / filename
            config_path.write_text(content)

        print(f"Created config files in: {temp_dir}")
        for filename in configs.keys():
            print(f"  - {filename}")

        # Create config manager
        from .config_loader_core import create_config_manager
        manager = create_config_manager([temp_dir])

        # List available configs
        available = manager.list_configs()
        print(f"\nAvailable configurations: {available}")

        # Load specific config
        try:
            config = manager.load_config("data_processing")
            print(f"\nLoaded config: {config.name}")
            print(f"Stages: {[s.name for s in config.stages]}")

            # Build pipeline
            from .pipeline_builder import YamlPipelineBuilder
            builder = YamlPipelineBuilder()
            runner = builder.build_pipeline(config)

            print(f"Pipeline built successfully with {len(runner._stages)} stages")

        except Exception as e:
            print(f"Failed to load config: {e}")


def run_basic_yaml_demos() -> None:
    """Run all basic YAML pipeline demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running Basic YAML Pipeline Demonstrations")
    print("=" * 40)

    try:
        demo_simple_yaml_pipeline()
        demo_file_based_pipeline()
        demo_config_manager()

        print("\n" + "=" * 40)
        print("Basic YAML demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run basic demonstrations when executed directly."""
    run_basic_yaml_demos()

