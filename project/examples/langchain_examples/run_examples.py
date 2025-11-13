"""
LangChain Examples Runner - Demonstrates All Features.

This script demonstrates all LangChain examples following production standards.
"""

import asyncio
import logging
import sys
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_core_concepts():
    """Demonstrate core LangChain concepts."""
    print("\n" + "="*60)
    print("CORE CONCEPTS DEMO")
    print("="*60)
    
    try:
        from core_concepts import OpenAIProvider, LLMService, PromptManager
        
        # Create provider
        provider = OpenAIProvider(model_name="gpt-3.5-turbo")
        print("✅ Created OpenAI provider")
        
        # Create service
        service = LLMService(provider)
        print("✅ Created LLM service")
        
        # Register template
        service.prompt_manager.register_template(
            "greeting",
            "Say hello to {name}",
            ["name"]
        )
        print("✅ Registered prompt template")
        
        # Generate response
        result = await service.generate_with_template(
            "greeting",
            name="Python Developer"
        )
        print(f"✅ Generated response: {result.get('content', 'Mock response')[:50]}...")
        
    except Exception as e:
        logger.error(f"Error in core concepts demo: {e}")


async def demo_chains():
    """Demonstrate LangChain chains."""
    print("\n" + "="*60)
    print("CHAINS DEMO")
    print("="*60)
    
    try:
        from chains import SimpleLLMChainWrapper, ChainOrchestrator
        
        # Create chain wrapper
        chain = SimpleLLMChainWrapper("demo_chain")
        print("✅ Created chain wrapper")
        
        # Create orchestrator
        orchestrator = ChainOrchestrator()
        orchestrator.register_chain("demo", chain)
        print("✅ Registered chain")
        
        # Execute chain
        result = await orchestrator.execute_chain("demo", {"input": "test"})
        print(f"✅ Chain executed: {result.steps_executed} steps")
        
    except Exception as e:
        logger.error(f"Error in chains demo: {e}")


async def demo_agents():
    """Demonstrate LangChain agents."""
    print("\n" + "="*60)
    print("AGENTS DEMO")
    print("="*60)
    
    try:
        from agents import ReActAgentWrapper, AgentOrchestrator
        
        # Create agent
        agent = ReActAgentWrapper("demo_agent")
        print("✅ Created ReAct agent")
        
        # Create orchestrator
        orchestrator = AgentOrchestrator()
        orchestrator.register_agent("demo", agent)
        print("✅ Registered agent")
        
        # Execute agent
        result = await orchestrator.execute_agent("demo", "What is Python?")
        print(f"✅ Agent executed: {len(result.output)} chars")
        
    except Exception as e:
        logger.error(f"Error in agents demo: {e}")


async def demo_memory():
    """Demonstrate LangChain memory."""
    print("\n" + "="*60)
    print("MEMORY DEMO")
    print("="*60)
    
    try:
        from memory import ConversationBufferMemoryWrapper, MemoryManager
        
        # Create memory
        memory = ConversationBufferMemoryWrapper("demo_memory")
        print("✅ Created memory")
        
        # Save context
        memory.save_context({"input": "Hello"}, {"output": "Hi there!"})
        print("✅ Saved conversation context")
        
        # Load memory
        variables = memory.load_memory_variables({})
        print(f"✅ Loaded memory: {len(variables.get('history', ''))} chars")
        
        # Get stats
        stats = memory.get_stats()
        print(f"✅ Memory stats: {stats['total_messages']} messages")
        
    except Exception as e:
        logger.error(f"Error in memory demo: {e}")


async def demo_production():
    """Demonstrate production patterns."""
    print("\n" + "="*60)
    print("PRODUCTION PATTERNS DEMO")
    print("="*60)
    
    try:
        from production import ProductionLLMWrapper, ExponentialBackoffRetry, RetryConfig
        from advanced_patterns import (
            AdaptiveCircuitBreaker,
            SemanticCache,
            TokenBucketRateLimiter,
            DistributedTracer
        )
        
        # Create mock LLM factory
        def llm_factory():
            class MockLLM:
                async def generate(self, prompt: str):
                    await asyncio.sleep(0.01)
                    return f"Response to: {prompt[:30]}"
            return MockLLM()
        
        # Create production wrapper with all advanced features
        wrapper = ProductionLLMWrapper(
            llm_factory=llm_factory,
            cache_size=100,
            enable_semantic_cache=True,
            enable_circuit_breaker=True,
            enable_tracing=True,
            enable_deduplication=True,
            rate_limit_per_second=10.0
        )
        print("✅ Created enterprise-grade production wrapper")
        
        # Generate with all patterns
        result = await wrapper.generate("What is Python?")
        print(f"✅ Generated: cached={result.get('cached', False)}, latency={result.get('latency', 0):.3f}s")
        
        # Generate again (should hit cache)
        result2 = await wrapper.generate("What is Python?")
        print(f"✅ Second request: cached={result2.get('cached', False)} (semantic cache)")
        
        # Show comprehensive metrics
        metrics = await wrapper.get_metrics()
        print(f"\n📊 Production Metrics:")
        print(f"   Total requests: {metrics['total_requests']}")
        print(f"   Success rate: {metrics['success_rate']:.2%}")
        print(f"   Cache hit rate: {metrics.get('cache_hit_rate', 0):.2%}")
        print(f"   Semantic cache hits: {metrics.get('semantic_cache_hits', 0)}")
        print(f"   Deduplicated requests: {metrics.get('deduplicated_requests', 0)}")
        if 'latency_percentiles' in metrics:
            print(f"   P95 latency: {metrics['latency_percentiles'].get('p95', 0):.3f}s")
        if 'circuit_breaker' in metrics:
            print(f"   Circuit breaker state: {metrics['circuit_breaker']['state']}")
        
    except Exception as e:
        logger.error(f"Error in production demo: {e}", exc_info=True)


async def demo_advanced_patterns():
    """Demonstrate advanced patterns."""
    print("\n" + "="*60)
    print("ADVANCED PATTERNS DEMO")
    print("="*60)
    
    try:
        from advanced_patterns import (
            AdaptiveCircuitBreaker,
            CircuitBreakerConfig,
            SemanticCache,
            TokenBucketRateLimiter,
            RequestDeduplicator,
            DistributedTracer,
            IntelligentBatcher
        )
        
        # Circuit Breaker
        print("\n🔌 Circuit Breaker:")
        cb_config = CircuitBreakerConfig(
            failure_threshold=3,
            adaptive_threshold=True
        )
        circuit_breaker = AdaptiveCircuitBreaker("demo_circuit", cb_config)
        print("✅ Created adaptive circuit breaker")
        
        # Semantic Cache
        print("\n🧠 Semantic Cache:")
        semantic_cache = SemanticCache(max_size=100, similarity_threshold=0.9)
        semantic_cache.put("What is Python?", "Python is a programming language")
        result = semantic_cache.get("What is Python programming?")
        print(f"✅ Semantic cache: found similar result = {result is not None}")
        
        # Rate Limiter
        print("\n⏱️  Rate Limiter:")
        rate_limiter = TokenBucketRateLimiter(rate=10.0, capacity=20.0)
        acquired = await rate_limiter.acquire("test_key")
        print(f"✅ Rate limiter: acquired={acquired}")
        
        # Distributed Tracer
        print("\n📡 Distributed Tracer:")
        tracer = DistributedTracer("demo_service")
        trace_id = tracer.start_trace("demo_operation")
        span_id = tracer.start_span(trace_id, "demo_span")
        await asyncio.sleep(0.01)
        tracer.end_span(trace_id, span_id)
        trace_summary = tracer.end_trace(trace_id)
        print(f"✅ Trace completed: duration={trace_summary.get('duration', 0):.3f}s")
        
        print("\n✅ All advanced patterns demonstrated!")
        
    except Exception as e:
        logger.error(f"Error in advanced patterns demo: {e}", exc_info=True)


async def run_all_demos():
    """Run all demonstrations."""
    print("\n" + "="*60)
    print("LANGCHAIN EXAMPLES - COMPREHENSIVE DEMO")
    print("="*60)
    
    demos = [
        ("Core Concepts", demo_core_concepts),
        ("Chains", demo_chains),
        ("Agents", demo_agents),
        ("Memory", demo_memory),
        ("Advanced Patterns", demo_advanced_patterns),
        ("Production", demo_production)
    ]
    
    for name, demo_func in demos:
        try:
            await demo_func()
            await asyncio.sleep(0.5)  # Brief pause between demos
        except Exception as e:
            logger.error(f"Error in {name} demo: {e}")
    
    print("\n" + "="*60)
    print("✅ ALL DEMOS COMPLETE")
    print("="*60)


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "core":
            await demo_core_concepts()
        elif command == "chains":
            await demo_chains()
        elif command == "agents":
            await demo_agents()
        elif command == "memory":
            await demo_memory()
        elif command == "production":
            await demo_production()
        elif command == "advanced":
            await demo_advanced_patterns()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run_examples.py [core|chains|agents|memory|advanced|production|all]")
    else:
        await run_all_demos()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

