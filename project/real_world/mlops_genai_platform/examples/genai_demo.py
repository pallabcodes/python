#!/usr/bin/env python3
"""
Gen AI capabilities demonstration for MLOps + Gen AI Platform.

This script demonstrates advanced Gen AI features including:
- LLM text generation with multiple providers
- RAG system for knowledge retrieval
- AI agent with tool calling
- Multi-modal content processing
- Fine-tuning pipeline setup
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.platform import MLOpsPlatform


async def llm_demo():
    """Demonstrate LLM capabilities."""
    print("\n🤖 LLM Demo")
    print("-" * 30)

    try:
        # Generate text with basic LLM
        response = await platform.generate_text(
            "Explain the concept of machine learning in simple terms."
        )
        print(f"✅ LLM Response: {response[:200]}...")

        # Generate with RAG context (if available)
        context_docs = [
            "Machine learning is a subset of artificial intelligence",
            "ML algorithms learn patterns from data without explicit programming",
            "Supervised learning uses labeled training data"
        ]

        rag_response = await platform.generate_text(
            "What is machine learning?",
            context=context_docs
        )
        print(f"✅ RAG Response: {rag_response[:200]}...")

        # Get usage statistics
        usage_stats = platform._genai_components["llm_manager"].get_usage_stats()
        print(f"✅ Usage Stats: {usage_stats['total_calls']} calls, {usage_stats['total_tokens']} tokens")

    except Exception as e:
        print(f"❌ LLM demo failed: {e}")


async def rag_demo():
    """Demonstrate RAG system capabilities."""
    print("\n📚 RAG Demo")
    print("-" * 30)

    try:
        # Add documents to knowledge base
        documents = [
            "Machine learning is a method of data analysis that automates analytical model building.",
            "Deep learning uses neural networks with multiple layers to process data.",
            "Natural language processing enables computers to understand human language.",
            "Computer vision allows machines to interpret and understand visual information.",
            "Reinforcement learning trains agents through trial and error with rewards."
        ]

        doc_ids = []
        for i, doc in enumerate(documents):
            ids = await platform._genai_components["rag_system"].add_document(
                content=doc,
                metadata={"category": "ai_concepts", "index": i},
                source=f"demo_doc_{i}"
            )
            doc_ids.extend(ids)

        print(f"✅ Added {len(doc_ids)} document chunks to knowledge base")

        # Search for relevant information
        results = await platform.search_knowledge(
            "What is deep learning?",
            top_k=3
        )
        print(f"✅ Found {len(results)} relevant results")
        for result in results[:2]:
            print(f"  Score: {result['score']:.3f} - {result['content'][:100]}...")

        # Get RAG stats
        stats = platform._genai_components["rag_system"].get_stats()
        print(f"✅ RAG Stats: {stats}")

    except Exception as e:
        print(f"❌ RAG demo failed: {e}")


async def agent_demo():
    """Demonstrate AI agent capabilities."""
    print("\n🎭 AI Agent Demo")
    print("-" * 35)

    try:
        # Create a reasoning agent
        from genai.ai_agent_framework import AgentConfig

        agent_config = AgentConfig(
            name="ml_expert",
            role="Machine Learning Specialist",
            goal="Help users understand and apply ML concepts",
            personality="helpful and educational"
        )

        agent = await platform.create_agent(
            agent_type="reasoning",
            config=agent_config,
            tools=["web_search", "calculator", "read_file"]
        )

        print(f"✅ Created agent: {agent.config.name} with {len(agent.available_tools)} tools")

        # Execute a task
        task = "Explain the difference between supervised and unsupervised learning, and give a practical example of each."

        result = await platform._genai_components["agent_framework"].execute_task(
            "ml_expert",
            task,
            timeout=30
        )

        print(f"✅ Agent task completed: {result.success}")
        print(f"  Iterations: {result.iterations_used}")
        print(f"  Execution time: {result.execution_time:.2f}s")
        print(f"  Response: {result.final_answer[:200]}...")

        # Get agent status
        status = platform._genai_components["agent_framework"].get_agent_status()
        print(f"✅ Agent status: {list(status.keys())}")

    except Exception as e:
        print(f"❌ Agent demo failed: {e}")


async def multimodal_demo():
    """Demonstrate multi-modal processing capabilities."""
    print("\n🎨 Multi-modal Demo")
    print("-" * 35)

    try:
        # Process text content
        text_result = await platform.process_multimodal(
            content="Machine learning is transforming industries worldwide.",
            content_type="text",
            analysis_types=["sentiment", "entities"]
        )
        print(f"✅ Text analysis: {text_result}")

        # Process code content
        code_content = """
def train_model(data, labels):
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier()
    model.fit(data, labels)
    return model
"""
        code_result = await platform.process_multimodal(
            content=code_content,
            content_type="code",
            analysis_types=["language", "complexity"]
        )
        print(f"✅ Code analysis: {code_result}")

        # Get processor stats
        stats = platform._genai_components["multimodal_processor"].get_stats()
        print(f"✅ Multi-modal stats: {stats}")

    except Exception as e:
        print(f"❌ Multi-modal demo failed: {e}")


async def finetuning_demo():
    """Demonstrate fine-tuning pipeline setup."""
    print("\n🎯 Fine-tuning Demo")
    print("-" * 35)

    try:
        # Setup fine-tuning configuration
        from genai.finetuning_pipeline import FineTuningConfig

        ft_config = FineTuningConfig(
            base_model="microsoft/DialoGPT-small",
            use_lora=True,
            lora_r=8,
            lora_alpha=16,
            num_train_epochs=1,
            per_device_train_batch_size=2,
            max_steps=10  # Very small for demo
        )

        # Create fine-tuning job (without actual execution for demo)
        job_id = await platform._genai_components["finetuning_pipeline"].create_finetuning_job(
            name="demo_finetune",
            config=ft_config,
            dataset_config={"type": "demo", "samples": 100}
        )

        print(f"✅ Created fine-tuning job: {job_id}")
        print(f"  Model: {ft_config.base_model}")
        print(f"  LoRA: {ft_config.use_lora} (r={ft_config.lora_r})")
        print(f"  Max steps: {ft_config.max_steps}")

        # Show job status
        status = platform._genai_components["finetuning_pipeline"].get_training_status(job_id)
        print(f"✅ Job status: {status['status']}")

    except Exception as e:
        print(f"❌ Fine-tuning demo failed: {e}")


async def platform_genai_status():
    """Show Gen AI platform status."""
    print("\n📊 Gen AI Platform Status")
    print("-" * 40)

    status = platform.get_status()
    print(f"Status: {status.status}")
    print(f"Components loaded: {len(status.components)}")

    # Gen AI specific components
    genai_components = [k for k in status.components.keys() if k.startswith("genai_")]
    print(f"Gen AI components: {len(genai_components)}")
    for comp in genai_components:
        print(f"  {comp}: {status.components[comp]}")

    print(f"\nTotal uptime: {status.uptime_seconds:.1f} seconds")


async def main():
    """Main demo function."""
    print("🚀 MLOps + Gen AI Platform - Gen AI Demo")
    print("=" * 60)

    global platform
    platform = MLOpsPlatform()

    try:
        # Initialize platform
        print("🔧 Initializing platform with Gen AI components...")
        await platform.initialize()
        print("✅ Platform ready with full Gen AI capabilities!")

        # Run Gen AI demos
        await llm_demo()
        await rag_demo()
        await agent_demo()
        await multimodal_demo()
        await finetuning_demo()
        await platform_genai_status()

        print("\n🎉 Gen AI demonstrations completed!")
        print("\n💡 Key capabilities demonstrated:")
        print("  • Multi-provider LLM management")
        print("  • RAG knowledge retrieval")
        print("  • AI agent reasoning and tool use")
        print("  • Multi-modal content processing")
        print("  • Fine-tuning pipeline setup")
        print("\n🚀 Ready for production Gen AI applications!")

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
