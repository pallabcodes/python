"""
Template for creating comparison scripts.

This template demonstrates how to structure a comparison script
for different concurrency approaches.
"""

import time
from typing import Callable, Dict, Any


def compare_approaches(
    approaches: Dict[str, Callable],
    test_data: Any,
    iterations: int = 5
) -> Dict[str, Dict[str, float]]:
    """
    Compare different approaches and return performance metrics.
    
    Args:
        approaches: Dictionary of approach names to functions
        test_data: Test data to use for comparison
        iterations: Number of iterations to run
    
    Returns:
        Dictionary of approach names to performance metrics
    """
    results = {}
    
    for name, func in approaches.items():
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            func(test_data)
            elapsed = time.time() - start_time
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        results[name] = {
            'average': avg_time,
            'min': min_time,
            'max': max_time,
            'times': times
        }
    
    return results


def print_comparison_results(results: Dict[str, Dict[str, float]]):
    """
    Print comparison results in a readable format.
    
    Args:
        results: Results dictionary from compare_approaches
    """
    print("\n" + "=" * 60)
    print("Comparison Results")
    print("=" * 60)
    
    for name, metrics in results.items():
        print(f"\n{name}:")
        print(f"  Average: {metrics['average']:.4f}s")
        print(f"  Min:     {metrics['min']:.4f}s")
        print(f"  Max:     {metrics['max']:.4f}s")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Example usage
    def approach_a(data):
        """Example approach A."""
        time.sleep(0.1)
        return sum(data)
    
    def approach_b(data):
        """Example approach B."""
        time.sleep(0.15)
        return sum(data)
    
    approaches = {
        'Approach A': approach_a,
        'Approach B': approach_b
    }
    
    test_data = list(range(1000))
    results = compare_approaches(approaches, test_data)
    print_comparison_results(results)

