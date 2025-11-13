"""Strategy selection demonstration."""

from intelligent_orchestrator.intelligence.strategy_selector_llm.strategy_selector_llm import StrategySelectorLLM
from intelligent_orchestrator.core.orchestrator_logger import setup_logger


def main():
    """Run strategy selection demo."""
    logger = setup_logger(__name__)
    selector = StrategySelectorLLM(logger=logger)
    
    analysis = {
        "bound_type": "io_bound",
        "has_async": True,
        "io_operations": True
    }
    
    strategies = ["threading", "asyncio", "multiprocessing", "hybrid"]
    
    print("Selecting optimal strategy with LLM...")
    selection = selector.select(analysis, strategies)
    
    print("\nSelection Results:")
    print(f"Selected Strategy: {selection.get('selected_strategy', 'unknown')}")
    print(f"Reasoning: {selection.get('reasoning', 'N/A')}")
    print(f"Confidence: {selection.get('confidence', 0.0)}")
    if selection.get('tradeoffs'):
        print(f"Trade-offs Analyzed: {len(selection['tradeoffs'])}")
    if selection.get('prediction'):
        print(f"Prediction: {selection['prediction']}")


if __name__ == "__main__":
    main()

