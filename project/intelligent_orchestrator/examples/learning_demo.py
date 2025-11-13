"""Learning system demonstration."""

from intelligent_orchestrator.intelligence.learning_system.learning_system import LearningSystem
from intelligent_orchestrator.core.orchestrator_logger import setup_logger


def main():
    """Run learning system demo."""
    logger = setup_logger(__name__)
    learning_system = LearningSystem(logger=logger)
    
    optimization_results = [
        {
            "workload_type": "cpu_bound",
            "strategy": "multiprocessing",
            "performance": {"throughput": 1000, "latency": 0.1},
            "timestamp": "2024-01-01T00:00:00"
        },
        {
            "workload_type": "io_bound",
            "strategy": "asyncio",
            "performance": {"throughput": 5000, "latency": 0.05},
            "timestamp": "2024-01-01T00:01:00"
        },
        {
            "workload_type": "cpu_bound",
            "strategy": "multiprocessing",
            "performance": {"throughput": 1200, "latency": 0.09},
            "timestamp": "2024-01-01T00:02:00"
        }
    ]
    
    print("Learning from optimization results...\n")
    for i, result in enumerate(optimization_results, 1):
        print(f"Processing result {i}...")
        insights = learning_system.learn_from_results(result)
        if insights:
            print(f"  Patterns: {insights.get('patterns', {})}")
            print(f"  Feedback: {insights.get('feedback', {})}\n")
    
    print("Learning system demonstration completed")


if __name__ == "__main__":
    main()

