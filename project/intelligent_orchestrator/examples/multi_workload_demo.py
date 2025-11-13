"""Multiple workloads demonstration."""

from intelligent_orchestrator.core.orchestrator_factory import OrchestratorFactory
from intelligent_orchestrator.core.orchestrator_logger import setup_logger


def main():
    """Run multi-workload demo."""
    logger = setup_logger(__name__)
    orchestrator = OrchestratorFactory.create(logger=logger)
    
    workloads = [
        {
            "code": "def cpu_task(n): return sum(i*i for i in range(n))",
            "description": "CPU-intensive computation"
        },
        {
            "code": """
import requests
def fetch_data(urls):
    return [requests.get(url) for url in urls]
""",
            "description": "I/O-bound HTTP requests"
        },
        {
            "code": """
import asyncio
async def async_task():
    await asyncio.sleep(1)
    return "done"
""",
            "description": "Async I/O workload"
        }
    ]
    
    print("Optimizing multiple workloads...\n")
    results = []
    for i, workload in enumerate(workloads, 1):
        print(f"Workload {i}: {workload['description']}")
        result = orchestrator.optimize_workload(workload)
        strategy = result.get('selection', {}).get('selected_strategy', 'unknown')
        print(f"  Selected Strategy: {strategy}\n")
        results.append(result)
    
    print(f"\nOptimized {len(results)} workloads successfully")


if __name__ == "__main__":
    main()

