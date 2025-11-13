"""Basic optimization demonstration."""

from intelligent_orchestrator.core.orchestrator_factory import OrchestratorFactory


def main():
    """Run basic optimization demo."""
    orchestrator = OrchestratorFactory.create()
    workload = {
        "code": """
def process_data(items):
    results = []
    for item in items:
        result = expensive_computation(item)
        results.append(result)
    return results
""",
        "description": "CPU-intensive data processing workload"
    }
    result = orchestrator.optimize_workload(workload)
    print("Optimization Result:")
    print(f"Selected Strategy: {result.get('selection', {}).get('selected_strategy', 'unknown')}")
    if result.get("explanation"):
        print(f"Explanation: {result['explanation'].get('explanation', 'N/A')}")


if __name__ == "__main__":
    main()

