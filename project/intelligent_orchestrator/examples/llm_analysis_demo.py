"""LLM analysis demonstration."""

from intelligent_orchestrator.intelligence.workload_analyzer_llm.workload_analyzer_llm import WorkloadAnalyzerLLM
from intelligent_orchestrator.core.orchestrator_logger import setup_logger


def main():
    """Run LLM analysis demo."""
    logger = setup_logger(__name__)
    analyzer = WorkloadAnalyzerLLM(logger=logger)
    
    workload = {
        "code": """
import asyncio
import aiohttp

async def fetch_urls(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        results = await asyncio.gather(*tasks)
    return results
""",
        "description": "I/O-bound async URL fetching workload"
    }
    
    print("Analyzing workload with LLM...")
    analysis = analyzer.analyze(workload)
    
    print("\nAnalysis Results:")
    print(f"Bound Type: {analysis.get('bound_type', 'unknown')}")
    print(f"Confidence: {analysis.get('confidence', 0.0)}")
    if analysis.get('code_analysis'):
        print(f"Code Analysis: {analysis['code_analysis']}")
    if analysis.get('nlp_analysis'):
        print(f"NLP Analysis: {analysis['nlp_analysis']}")


if __name__ == "__main__":
    main()

