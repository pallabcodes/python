"""
Demonstrations of YAML-driven pipeline configuration.

This module provides practical examples of building and running
pipelines using YAML configuration files.
"""

import tempfile
import logging
from pathlib import Path

from .pipeline_builder import build_pipeline_from_yaml
from .config_loader import create_config_manager
from ..pipeline_core.message import create_data_message


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

        # Create input data
        input_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        input_messages = [create_data_message(data) for data in input_data]

        print(f"Input: {input_data}")
        print("Pipeline: Multiply by 3 -> Filter Even -> Print")
        print("Expected: Even numbers from input multiplied by 3")
        print()

        # Run pipeline
        results = runner.run_pipeline(input_messages, timeout=10.0)

        print(f"\nPipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

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
        from .config_loader import load_pipeline_config
        from .pipeline_builder import YamlPipelineBuilder

        config = load_pipeline_config(config_file)
        builder = YamlPipelineBuilder()
        runner = builder.build_pipeline(config)

        # Test data
        input_data = ["short", "medium length text", "this is a very long string for testing"]
        input_messages = [create_data_message(data) for data in input_data]

        print(f"Input: {input_data}")
        print("Pipeline: Add prefix -> Filter length >= 15 -> Print")
        print()

        # Run pipeline
        results = runner.run_pipeline(input_messages, timeout=10.0)

        print(f"\nPipeline completed in {results['execution_time']:.2f}s")
        print(f"Success: {results['success']}")

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


def demo_environment_variables() -> None:
    """Demonstrate environment variable substitution in configs."""
    print("\n=== Environment Variables Demo ===")

    # Set test environment variables
    import os
    os.environ["PIPELINE_WORKERS"] = "4"
    os.environ["PIPELINE_TIMEOUT"] = "30"

    yaml_config = """
name: "env_var_pipeline"
version: "1.0.0"
description: "Pipeline with environment variable substitution"

stages:
  - name: "processor"
    type: "transform"
    module: "pipeline_core.stage_types"
    class_name: "TransformStage"
    parameters:
      workers: ${PIPELINE_WORKERS}

global_settings:
  max_workers: ${PIPELINE_WORKERS}
  timeout: ${PIPELINE_TIMEOUT}
"""

    print("YAML with environment variables:")
    print(yaml_config)

    try:
        # Build pipeline (env vars will be substituted during loading)
        from .config_loader import SecureConfigLoader

        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_config)
            config_file = f.name

        # Load with env var processing
        loader = SecureConfigLoader()
        config = loader.load_config(config_file)

        print(f"\nLoaded config: {config.name}")
        print(f"Global settings: {config.global_settings}")

        # Clean up
        Path(config_file).unlink()

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up env vars
        del os.environ["PIPELINE_WORKERS"]
        del os.environ["PIPELINE_TIMEOUT"]


def run_all_yaml_demos() -> None:
    """Run all YAML pipeline demonstrations."""
    # Configure logging for demos
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Running YAML Pipeline Configuration Demonstrations")
    print("=" * 60)

    try:
        demo_simple_yaml_pipeline()
        demo_file_based_pipeline()
        demo_config_manager()
        demo_environment_variables()

        print("\n" + "=" * 60)
        print("All YAML demonstrations completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    """Run demonstrations when executed directly."""
    run_all_yaml_demos()

