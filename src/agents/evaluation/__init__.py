"""
Evaluation System Package
Provides evaluation metrics, feedback collection, and improvement suggestions
for self-improving models.
"""

from src.agents.evaluation.metrics import (
    EvaluationMetrics,
    EvaluationService
)
from src.agents.evaluation.optimizer import (
    ImprovementSuggestion,
    Optimizer
)

__all__ = [
    "EvaluationMetrics",
    "EvaluationService",
    "ImprovementSuggestion",
    "Optimizer"
]
