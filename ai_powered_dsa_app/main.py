#!/usr/bin/env python3
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
        print("\n📝 Basic Generation:")
        response = await ai.generate("Explain the concept of recursion in programming")
        print(f"Response: {response.content[:200]}...")

        # Example 2: Code generation with quality requirements
        print("\n💻 Code Generation:")
        code_response = await ai.generate(
            "Write a Python function to check if a string is a palindrome",
            quality_requirement="high"
        )
        print(f"Code:\n{code_response.content}")

        # Example 3: Get framework status
        print("\n📊 Framework Status:")
        status = await ai.get_status()
        provider_count = len(status['providers'])
        print(f"Providers available: {provider_count}")

        print("\n✅ Application completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
