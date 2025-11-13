"""Explainability demonstration."""

from intelligent_orchestrator.intelligence.explainability.decision_explainer import DecisionExplainer
from intelligent_orchestrator.intelligence.explainability.report_generator import ReportGenerator
from intelligent_orchestrator.intelligence.explainability.qa_system import QASystem
from intelligent_orchestrator.core.orchestrator_logger import setup_logger


def main():
    """Run explainability demo."""
    logger = setup_logger(__name__)
    
    decision = {
        "selected_strategy": "asyncio",
        "reasoning": "Workload is I/O-bound with async operations",
        "confidence": 0.85,
        "context": {
            "bound_type": "io_bound",
            "has_async": True
        }
    }
    
    print("=== Decision Explanation ===\n")
    explainer = DecisionExplainer(logger=logger)
    explanation = explainer.explain(decision)
    print(f"Explanation: {explanation.get('explanation', 'N/A')}\n")
    
    print("=== Optimization Report ===\n")
    report_gen = ReportGenerator(logger=logger)
    optimization_data = {
        "decision": decision,
        "results": {"performance": {"throughput": 5000}},
        "workload": {"type": "io_bound"}
    }
    report = report_gen.generate(optimization_data)
    print(f"Report Summary: {report.get('summary', 'N/A')}\n")
    
    print("=== Q&A System ===\n")
    qa = QASystem(logger=logger)
    answer = qa.answer(
        "Why was asyncio selected over threading?",
        decision
    )
    print(f"Q: Why was asyncio selected over threading?")
    print(f"A: {answer.get('answer', 'N/A')}")


if __name__ == "__main__":
    main()

