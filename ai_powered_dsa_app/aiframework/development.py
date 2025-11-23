"""
Development Utilities and Tools

Provides everything you need for AI development:
- Quick setup and configuration
- Development vs production mode helpers
- Mock providers for testing
- Performance profiling tools
- Debugging utilities
- Example implementations
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from contextlib import asynccontextmanager

from .core import AIFramework
from .config import Mode, FrameworkConfig

class DevelopmentEnvironment:
    """
    Development environment manager.

    Provides:
    - Easy setup for development
    - Mock providers for unlimited testing
    - Performance profiling
    - Debugging tools
    - Example usage patterns
    """

    def __init__(self, project_name: str = "my_ai_project"):
        self.project_name = project_name
        self.logger = logging.getLogger("DevEnvironment")

        # Setup development configuration
        self.config = FrameworkConfig(mode=Mode.DEVELOPMENT)
        self.framework: Optional[AIFramework] = None

    async def setup(self) -> AIFramework:
        """Setup the development environment."""
        print(f"🚀 Setting up AI Framework for {self.project_name}")
        print("=" * 50)

        # Create framework instance
        self.framework = AIFramework(
            mode="development",
            config=self.config,
            enable_batching=True,
            enable_intervention=False,  # Disable for faster development
            log_level="INFO"
        )

        # Initialize
        await self.framework.__aenter__()

        # Show status
        status = await self.framework.get_status()
        print("✅ Development environment ready!")
        print(f"   📊 Providers: {status['providers']['total_available']}")
        print(f"   🧠 Multi-provider routing: {'Enabled' if status['providers']['multi_provider_enabled'] else 'Disabled'}")
        print(f"   📦 Batching: {'Enabled' if status['batching']['enabled'] else 'Disabled'}")
        print(f"   🎭 Intervention: {'Enabled' if status['intervention']['enabled'] else 'Disabled'}")

        return self.framework

    async def quick_test(self) -> Dict[str, Any]:
        """Run quick functionality tests."""
        print("\n🧪 Running Quick Tests")
        print("=" * 25)

        if not self.framework:
            await self.setup()

        results = {}

        # Test 1: Basic generation
        try:
            response = await self.framework.generate("Explain what AI is in one sentence.")
            results["basic_generation"] = {
                "status": "✅ PASSED",
                "response_length": len(response.content),
                "latency": round(response.latency, 2),
                "provider": response.provider_used
            }
            print(f"✅ Basic generation: {response.latency:.2f}s")
        except Exception as e:
            results["basic_generation"] = {"status": "❌ FAILED", "error": str(e)}
            print(f"❌ Basic generation failed: {e}")

        # Test 2: Quality levels
        try:
            responses = {}
            for quality in ["basic", "standard", "high"]:
                response = await self.framework.generate(
                    "Write a function to calculate factorial",
                    quality_requirement=quality
                )
                responses[quality] = {
                    "length": len(response.content),
                    "latency": round(response.latency, 2)
                }

            results["quality_levels"] = {"status": "✅ PASSED", "responses": responses}
            print(f"✅ Quality levels: {len(responses)} levels tested")
        except Exception as e:
            results["quality_levels"] = {"status": "❌ FAILED", "error": str(e)}
            print(f"❌ Quality levels failed: {e}")

        # Test 3: Batching (if enabled)
        try:
            status = await self.framework.get_status()
            if status["batching"]["enabled"]:
                # Simulate multiple requests
                tasks = []
                for i in range(3):
                    task = self.framework.generate(f"Test request {i+1}")
                    tasks.append(task)

                start_time = time.time()
                batch_responses = await asyncio.gather(*tasks)
                batch_time = time.time() - start_time

                results["batching"] = {
                    "status": "✅ PASSED",
                    "requests": len(batch_responses),
                    "total_time": round(batch_time, 2),
                    "avg_latency": round(sum(r.latency for r in batch_responses) / len(batch_responses), 2)
                }
                print(f"✅ Batching: {len(batch_responses)} requests in {batch_time:.2f}s")
        except Exception as e:
            results["batching"] = {"status": "❌ FAILED", "error": str(e)}
            print(f"❌ Batching failed: {e}")

        return results

    async def performance_profile(self, requests: List[str] = None) -> Dict[str, Any]:
        """Profile performance across different scenarios."""
        if not self.framework:
            await self.setup()

        # Default test requests
        if requests is None:
            requests = [
                "Explain quantum computing",
                "Write a Python function to reverse a string",
                "What are the benefits of microservices architecture?",
                "Create a simple REST API design",
                "Explain database normalization"
            ]

        print(f"\n📊 Performance Profiling ({len(requests)} requests)")
        print("=" * 45)

        results = []
        start_time = time.time()

        for i, prompt in enumerate(requests, 1):
            request_start = time.time()

            try:
                response = await self.framework.generate(prompt)

                result = {
                    "request_id": i,
                    "prompt_length": len(prompt),
                    "response_length": len(response.content),
                    "latency": round(response.latency, 3),
                    "provider": response.provider_used,
                    "cost": response.cost,
                    "quality_score": response.quality_score,
                    "batch_efficiency": response.batch_efficiency
                }
                results.append(result)

                print("2d")

            except Exception as e:
                results.append({
                    "request_id": i,
                    "error": str(e),
                    "latency": round(time.time() - request_start, 3)
                })
                print("2d")

        total_time = time.time() - start_time

        # Calculate aggregates
        successful_results = [r for r in results if "error" not in r]
        if successful_results:
            avg_latency = sum(r["latency"] for r in successful_results) / len(successful_results)
            total_cost = sum(r["cost"] for r in successful_results)
            avg_quality = sum(r["quality_score"] for r in successful_results) / len(successful_results)

            summary = {
                "total_requests": len(requests),
                "successful_requests": len(successful_results),
                "success_rate": round(len(successful_results) / len(requests) * 100, 1),
                "total_time": round(total_time, 2),
                "avg_latency": round(avg_latency, 3),
                "total_cost": round(total_cost, 4),
                "avg_quality": round(avg_quality, 3),
                "throughput": round(len(successful_results) / total_time, 2)
            }
        else:
            summary = {"error": "No successful requests"}

        print("\n📈 Summary:")
        print(f"   Success Rate: {summary.get('success_rate', 0)}%")
        print(f"   Average Latency: {summary.get('avg_latency', 0):.3f}s")
        print(f"   Total Cost: ${summary.get('total_cost', 0):.4f}")
        print(f"   Throughput: {summary.get('throughput', 0):.2f} req/s")

        return {
            "summary": summary,
            "detailed_results": results
        }

    async def create_project_template(self, project_path: str = None) -> str:
        """Create a project template with AI Framework integration."""
        if project_path is None:
            project_path = f"./{self.project_name}"

        project_dir = Path(project_path)
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create main application file
        main_py = project_dir / "main.py"
        main_py.write_text(self._get_main_template())

        # Create configuration file
        config_py = project_dir / "config.py"
        config_py.write_text(self._get_config_template())

        # Create requirements file
        requirements_txt = project_dir / "requirements.txt"
        requirements_txt.write_text(self._get_requirements_template())

        # Create README
        readme_md = project_dir / "README.md"
        readme_md.write_text(self._get_readme_template())

        print(f"✅ Project template created at: {project_dir.absolute()}")

        return str(project_dir)

    def _get_main_template(self) -> str:
        """Get the main application template."""
        return '''#!/usr/bin/env python3
"""
AI-Powered Application using AI Framework

This application demonstrates how to integrate the AI Framework
into your projects for intelligent, cost-effective AI operations.
"""

import asyncio
import logging
from aiframework import AIFramework

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    """Main application entry point."""

    # Initialize AI Framework
    async with AIFramework(mode="development") as ai:
        print("🤖 AI Framework initialized!")

        # Example 1: Basic text generation
        print("\\n📝 Basic Generation:")
        response = await ai.generate("Explain the concept of recursion in programming")
        print(f"Response: {response.content[:200]}...")

        # Example 2: Code generation with quality requirements
        print("\\n💻 Code Generation:")
        code_response = await ai.generate(
            "Write a Python function to check if a string is a palindrome",
            quality_requirement="high"
        )
        print(f"Code:\\n{code_response.content}")

        # Example 3: Get framework status
        print("\\n📊 Framework Status:")
        status = await ai.get_status()
        print(f"Providers available: {status['providers']['total_available']}")

        print("\\n✅ Application completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
'''

    def _get_config_template(self) -> str:
        """Get the configuration template."""
        return '''"""
Application Configuration

Configure your AI Framework settings here.
"""

from aiframework import FrameworkConfig, Mode

# Development configuration
def get_development_config() -> FrameworkConfig:
    """Get configuration for development environment."""
    return FrameworkConfig(
        mode=Mode.DEVELOPMENT
        # Add custom settings here
    )

# Production configuration
def get_production_config() -> FrameworkConfig:
    """Get configuration for production environment."""
    return FrameworkConfig(
        mode=Mode.PRODUCTION
        # Add production settings here
    )

# Get appropriate configuration based on environment
def get_config():
    """Get configuration based on current environment."""
    import os
    if os.getenv("ENVIRONMENT") == "production":
        return get_production_config()
    else:
        return get_development_config()
'''

    def _get_requirements_template(self) -> str:
        """Get the requirements template."""
        return '''# AI Framework Requirements
aiframework>=1.0.0

# Optional: Add your application-specific dependencies here
# requests>=2.28.0
# fastapi>=0.100.0
# uvicorn>=0.23.0
'''

    def _get_readme_template(self) -> str:
        """Get the README template."""
        return f'''# {self.project_name}

AI-powered application built with AI Framework.

## Features

- 🤖 Intelligent text generation
- 💰 Cost-optimized AI operations
- ⚡ High-performance batching
- 🎯 Quality-controlled responses
- 🔧 Easy development setup

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```

## Development

This project uses the AI Framework for intelligent AI operations:

- **Development Mode**: Unlimited free testing with mock providers
- **Production Mode**: Optimized cost and performance with real APIs
- **Automatic Batching**: Efficient API usage through intelligent batching
- **Quality Control**: Manual intervention for premium results

## Configuration

Edit `config.py` to customize your AI Framework settings.

## Learn More

- [AI Framework Documentation](https://github.com/yourusername/aiframework)
- [API Reference](https://aiframework.readthedocs.io/)
'''

    async def show_examples(self):
        """Show practical usage examples."""
        print("\n📚 AI Framework Usage Examples")
        print("=" * 35)

        if not self.framework:
            await self.setup()

        examples = [
            {
                "title": "Basic Text Generation",
                "code": '''
response = await ai.generate("Explain machine learning in simple terms")
print(response.content)
''',
                "description": "Simple text generation with automatic provider selection"
            },
            {
                "title": "Quality-Controlled Generation",
                "code": '''
response = await ai.generate(
    "Design a REST API for a task management system",
    quality_requirement="high"
)
''',
                "description": "Specify quality requirements for better results"
            },
            {
                "title": "Code Generation",
                "code": '''
code = await ai.generate(
    "Write a Python function to merge two sorted lists",
    quality_requirement="premium"
)
print(code.content)
''',
                "description": "Generate code with high quality standards"
            },
            {
                "title": "Batch Processing",
                "code": '''
# Framework automatically batches requests for efficiency
tasks = [
    ai.generate("Explain algorithm complexity"),
    ai.generate("What is Big O notation?"),
    ai.generate("Give examples of sorting algorithms")
]

responses = await asyncio.gather(*tasks)
''',
                "description": "Efficient batch processing of multiple requests"
            }
        ]

        for example in examples:
            print(f"\n🔹 {example['title']}")
            print(f"   {example['description']}")
            print(f"   Code: {example['code'].strip()}")

            # Execute example
            try:
                if "Basic Text Generation" in example["title"]:
                    response = await self.framework.generate("Explain machine learning briefly")
                    print(f"   Result: {response.content[:100]}...")
                elif "Quality-Controlled Generation" in example["title"]:
                    response = await self.framework.generate(
                        "Design a simple REST API endpoint",
                        quality_requirement="standard"
                    )
                    print(f"   Result: Generated {len(response.content)} chars in {response.latency:.2f}s")
                print("   ✅ Example executed successfully")
            except Exception as e:
                print(f"   ❌ Example failed: {e}")

    async def cleanup(self):
        """Cleanup development environment."""
        if self.framework:
            await self.framework.shutdown()
            print("🧹 Development environment cleaned up")

@asynccontextmanager
async def dev_environment(project_name: str = "my_ai_project"):
    """Context manager for development environment."""
    dev = DevelopmentEnvironment(project_name)
    try:
        yield await dev.setup()
    finally:
        await dev.cleanup()

# Convenience functions for quick development
async def quick_ai(prompt: str, quality: str = "standard") -> str:
    """Quick AI generation for development."""
    async with dev_environment() as ai:
        response = await ai.generate(prompt, quality_requirement=quality)
        return response.content

def create_project(name: str, path: str = None):
    """Create a new AI project template."""
    dev = DevelopmentEnvironment(name)
    return asyncio.run(dev.create_project_template(path))
