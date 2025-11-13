"""
LangChain Technique Decision Guide - When to Use Which Technique.

This guide helps you choose the right LangChain technique based on your requirements.
Based on research papers, open-source repos, and production best practices.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class CostSensitivity(Enum):
    """Cost sensitivity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LatencyRequirement(Enum):
    """Latency requirement levels."""
    LOW = "low"  # Seconds acceptable
    MEDIUM = "medium"  # Sub-second preferred
    HIGH = "high"  # Real-time required
    CRITICAL = "critical"  # Instant required


@dataclass
class TechniqueRecommendation:
    """Recommendation for a technique."""
    technique: str
    confidence: float
    reasoning: str
    alternatives: List[str]
    when_to_use: str
    when_not_to_use: str


class TechniqueDecisionGuide:
    """
    Decision guide for choosing LangChain techniques.
    
    Helps you select the right technique based on:
    - Task complexity
    - Cost sensitivity
    - Latency requirements
    - Quality requirements
    - Available resources
    """
    
    def recommend_technique(
        self,
        task_complexity: TaskComplexity,
        cost_sensitivity: CostSensitivity = CostSensitivity.MEDIUM,
        latency_requirement: LatencyRequirement = LatencyRequirement.MEDIUM,
        needs_verification: bool = False,
        needs_collaboration: bool = False,
        has_budget: bool = True
    ) -> List[TechniqueRecommendation]:
        """
        Recommend techniques based on requirements.
        
        Args:
            task_complexity: Complexity of the task
            cost_sensitivity: How cost-sensitive the application is
            latency_requirement: Latency requirements
            needs_verification: Whether verification is needed
            needs_collaboration: Whether multiple agents needed
            has_budget: Whether there's budget for multiple calls
            
        Returns:
            List of recommendations sorted by confidence
        """
        recommendations = []
        
        # Simple tasks
        if task_complexity == TaskComplexity.SIMPLE:
            recommendations.append(TechniqueRecommendation(
                technique="Basic LLM Chain",
                confidence=0.9,
                reasoning="Simple tasks don't need complex reasoning",
                alternatives=["Prompt Templates", "Output Parsers"],
                when_to_use="Single-step tasks, simple Q&A, text generation",
                when_not_to_use="Multi-step reasoning, complex problem-solving"
            ))
        
        # Moderate complexity
        elif task_complexity == TaskComplexity.MODERATE:
            if needs_verification:
                recommendations.append(TechniqueRecommendation(
                    technique="Reflective Agent",
                    confidence=0.85,
                    reasoning="Moderate complexity with verification needs",
                    alternatives=["Chain-of-Thought", "Self-Consistency"],
                    when_to_use="Tasks requiring verification, code generation",
                    when_not_to_use="When verification not needed, simple tasks"
                ))
            else:
                recommendations.append(TechniqueRecommendation(
                    technique="Chain-of-Thought",
                    confidence=0.8,
                    reasoning="Moderate complexity benefits from step-by-step reasoning",
                    alternatives=["Sequential Chain", "Basic LLM Chain"],
                    when_to_use="Multi-step reasoning, mathematical problems",
                    when_not_to_use="Simple tasks, when speed is critical"
                ))
        
        # Complex tasks
        elif task_complexity == TaskComplexity.COMPLEX:
            if has_budget and not cost_sensitivity == CostSensitivity.CRITICAL:
                if needs_collaboration:
                    recommendations.append(TechniqueRecommendation(
                        technique="Multi-Agent Collaboration",
                        confidence=0.9,
                        reasoning="Complex tasks requiring multiple specialized agents",
                        alternatives=["Tree of Thoughts", "Plan-and-Execute Agent"],
                        when_to_use="Tasks requiring multiple skills, research tasks",
                        when_not_to_use="Single-domain tasks, cost-critical applications"
                    ))
                else:
                    recommendations.append(TechniqueRecommendation(
                        technique="Tree of Thoughts",
                        confidence=0.85,
                        reasoning="Complex tasks benefit from multi-path exploration",
                        alternatives=["Self-Consistency", "Reflective Agent"],
                        when_to_use="Complex problem-solving, exploration needed",
                        when_not_to_use="Simple tasks, cost-critical, time-critical"
                    ))
            else:
                recommendations.append(TechniqueRecommendation(
                    technique="Self-Consistency",
                    confidence=0.8,
                    reasoning="Complex tasks with cost constraints",
                    alternatives=["Chain-of-Thought", "Reflective Agent"],
                    when_to_use="Complex reasoning, need confidence, cost-aware",
                    when_not_to_use="Simple tasks, when single answer sufficient"
                ))
        
        # Very complex tasks
        elif task_complexity == TaskComplexity.VERY_COMPLEX:
            if needs_collaboration:
                recommendations.append(TechniqueRecommendation(
                    technique="Multi-Agent Collaboration + Tree of Thoughts",
                    confidence=0.9,
                    reasoning="Very complex tasks need both exploration and collaboration",
                    alternatives=["AutoGPT Agent", "BabyAGI Task Manager"],
                    when_to_use="Research tasks, complex multi-domain problems",
                    when_not_to_use="Simple tasks, cost-critical, time-critical"
                ))
            elif has_budget:
                recommendations.append(TechniqueRecommendation(
                    technique="AutoGPT Agent",
                    confidence=0.85,
                    reasoning="Very complex tasks benefit from autonomous decomposition",
                    alternatives=["BabyAGI Task Manager", "Tree of Thoughts"],
                    when_to_use="Complex multi-step tasks, autonomous agents",
                    when_not_to_use="Simple tasks, when steps are known"
                ))
            else:
                recommendations.append(TechniqueRecommendation(
                    technique="BabyAGI Task Manager",
                    confidence=0.8,
                    reasoning="Very complex tasks with dynamic task generation",
                    alternatives=["Plan-and-Execute Agent", "Sequential Chain"],
                    when_to_use="Long-running tasks, evolving task queues",
                    when_not_to_use="Simple tasks, fixed workflows"
                ))
        
        # Cost optimization recommendations
        if cost_sensitivity in [CostSensitivity.HIGH, CostSensitivity.CRITICAL]:
            recommendations.append(TechniqueRecommendation(
                technique="Prompt Optimization + Token Optimization",
                confidence=0.95,
                reasoning="Cost-critical applications need optimization",
                alternatives=["Response Compression", "Caching"],
                when_to_use="High-volume systems, cost-sensitive applications",
                when_not_to_use="Low-volume, when quality is more important"
            ))
        
        # Latency optimization recommendations
        if latency_requirement in [LatencyRequirement.HIGH, LatencyRequirement.CRITICAL]:
            recommendations.append(TechniqueRecommendation(
                technique="Streaming Optimizations",
                confidence=0.9,
                reasoning="High latency requirements need streaming",
                alternatives=["Response Compression", "Caching"],
                when_to_use="Real-time applications, user-facing interfaces",
                when_not_to_use="Batch processing, when latency not critical"
            ))
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        
        return recommendations
    
    def get_technique_comparison(self) -> Dict[str, Dict[str, Any]]:
        """
        Get comparison of all techniques.
        
        Returns:
            Dictionary comparing techniques
        """
        return {
            "Basic LLM Chain": {
                "complexity": "Simple",
                "cost": "Low",
                "latency": "Low",
                "quality": "Medium",
                "best_for": "Simple Q&A, text generation"
            },
            "Chain-of-Thought": {
                "complexity": "Moderate",
                "cost": "Medium",
                "latency": "Medium",
                "quality": "High",
                "best_for": "Multi-step reasoning, math problems"
            },
            "Tree of Thoughts": {
                "complexity": "Complex",
                "cost": "High",
                "latency": "High",
                "quality": "Very High",
                "best_for": "Complex problem-solving, exploration"
            },
            "Self-Consistency": {
                "complexity": "Complex",
                "cost": "High",
                "latency": "High",
                "quality": "Very High",
                "best_for": "High-stakes decisions, need confidence"
            },
            "Reflective Agent": {
                "complexity": "Moderate-Complex",
                "cost": "Medium-High",
                "latency": "Medium-High",
                "quality": "Very High",
                "best_for": "Code generation, verification needed"
            },
            "AutoGPT Agent": {
                "complexity": "Very Complex",
                "cost": "Very High",
                "latency": "Very High",
                "quality": "Very High",
                "best_for": "Autonomous agents, complex multi-step tasks"
            },
            "BabyAGI Task Manager": {
                "complexity": "Very Complex",
                "cost": "Very High",
                "latency": "Very High",
                "quality": "Very High",
                "best_for": "Long-running agents, evolving tasks"
            },
            "Multi-Agent Collaboration": {
                "complexity": "Complex-Very Complex",
                "cost": "Very High",
                "latency": "High",
                "quality": "Very High",
                "best_for": "Multi-domain tasks, specialized expertise"
            },
            "Advanced RAG": {
                "complexity": "Moderate-Complex",
                "cost": "Medium",
                "latency": "Medium",
                "quality": "High",
                "best_for": "Document Q&A, knowledge retrieval"
            }
        }
    
    def print_decision_tree(self):
        """Print decision tree for technique selection."""
        print("=" * 70)
        print("LANGCHAIN TECHNIQUE DECISION TREE")
        print("=" * 70)
        print()
        print("1. ASSESS TASK COMPLEXITY:")
        print("   Simple → Basic LLM Chain")
        print("   Moderate → Chain-of-Thought or Reflective Agent")
        print("   Complex → Tree of Thoughts or Self-Consistency")
        print("   Very Complex → AutoGPT or BabyAGI")
        print()
        print("2. ASSESS COST SENSITIVITY:")
        print("   Low → Use any technique")
        print("   Medium → Consider optimization")
        print("   High → Prompt + Token Optimization required")
        print("   Critical → Optimization + Caching required")
        print()
        print("3. ASSESS LATENCY REQUIREMENTS:")
        print("   Low → Any technique")
        print("   Medium → Consider streaming")
        print("   High → Streaming required")
        print("   Critical → Streaming + Caching required")
        print()
        print("4. ASSESS QUALITY REQUIREMENTS:")
        print("   Need verification → Reflective Agent")
        print("   Need confidence → Self-Consistency")
        print("   Need exploration → Tree of Thoughts")
        print("   Need collaboration → Multi-Agent")
        print()
        print("5. ASSESS RESOURCE CONSTRAINTS:")
        print("   Limited budget → Chain-of-Thought or Self-Consistency")
        print("   Unlimited budget → Tree of Thoughts or AutoGPT")
        print("   Need autonomy → AutoGPT or BabyAGI")
        print("   Need specialization → Multi-Agent")
        print()
        print("=" * 70)


def decision_guide_real_world_example() -> None:
    """
    Real-World Scenario: Decision Guide - Choosing the Right Technique.
    
    REAL-WORLD SCENARIO:
    ====================
    You're building an LLM application:
    - Don't know which technique to use
    - Multiple options available
    - Problem: Need guidance on selection
    
    THE PROBLEM WITHOUT DECISION GUIDE:
    ===================================
    - Trial and error → wasted time
    - Wrong technique → poor results
    - Over-engineering → unnecessary costs
    - Under-engineering → poor quality
    - No guidance → confusion
    
    THE SOLUTION:
    =============
    Decision guide enables:
    - Systematic selection → right technique
    - Requirement-based → matches needs
    - Cost-aware → budget-friendly
    - Quality-focused → best results
    - Production-ready → scalable
    
    WHEN TO USE DECISION GUIDE:
    ============================
    ✅ Starting new LLM project
    ✅ Choosing between techniques
    ✅ Optimizing existing system
    ✅ Cost optimization needed
    ✅ Quality improvement needed
    """
    print("=" * 70)
    print("REAL-WORLD SCENARIO: Choosing the Right Technique")
    print("=" * 70)
    print()
    print("SITUATION:")
    print("  - Building an LLM application")
    print("  - Don't know which technique to use")
    print("  - Multiple options available")
    print("  - Problem: Need guidance on selection")
    print()
    print("THE PROBLEM:")
    print("  Without decision guide:")
    print("    ❌ Trial and error → wasted time")
    print("    ❌ Wrong technique → poor results")
    print("    ❌ Over-engineering → unnecessary costs")
    print("    ❌ Under-engineering → poor quality")
    print()
    print("THE SOLUTION:")
    print("  With decision guide:")
    print("    ✅ Systematic selection → right technique")
    print("    ✅ Requirement-based → matches needs")
    print("    ✅ Cost-aware → budget-friendly")
    print("    ✅ Quality-focused → best results")
    print()
    print("=" * 70)
    print()

    guide = TechniqueDecisionGuide()
    
    # Example: Complex task with cost sensitivity
    recommendations = guide.recommend_technique(
        task_complexity=TaskComplexity.COMPLEX,
        cost_sensitivity=CostSensitivity.HIGH,
        latency_requirement=LatencyRequirement.MEDIUM,
        needs_verification=False,
        needs_collaboration=False,
        has_budget=True
    )
    
    print("Example Recommendations:")
    print()
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"{i}. {rec.technique} (Confidence: {rec.confidence:.0%})")
        print(f"   Reasoning: {rec.reasoning}")
        print(f"   When to use: {rec.when_to_use}")
        print()
    
    guide.print_decision_tree()
    
    print()
    print("  ✅ Decision guide enabled systematic technique selection!")
    print()
    print("=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("1. WHEN TO USE DECISION GUIDE:")
    print("   ✅ Starting new LLM project")
    print("   ✅ Choosing between techniques")
    print("   ✅ Optimizing existing system")
    print("   ✅ Cost optimization needed")
    print()
    print("2. WHY IT MATTERS:")
    print("   - Saves time and resources")
    print("   - Ensures right technique selection")
    print("   - Cost-aware recommendations")
    print("   - Quality-focused guidance")
    print("=" * 70)
    print()


if __name__ == "__main__":
    decision_guide_real_world_example()

