"""relay — cost-optimizing LLM router.

Route every call to the cheapest model that can handle the task.
Drop-in OpenAI-compatible wrapper. Deterministic rules + optional ML classifier.
"""

from relay.router import (
    Router,
    RouteDecision,
    Tier,
    TaskClass,
    DEFAULT_TIERS,
    classify_task,
)
from relay.pricing import MODEL_PRICING, estimate_cost
from relay.budget import Budget, BudgetExceeded
from relay.client import wrap_openai, wrap_anthropic, RelayClient

__version__ = "0.1.0"
__all__ = [
    "Router",
    "RouteDecision",
    "Tier",
    "TaskClass",
    "DEFAULT_TIERS",
    "classify_task",
    "MODEL_PRICING",
    "estimate_cost",
    "Budget",
    "BudgetExceeded",
    "wrap_openai",
    "wrap_anthropic",
    "RelayClient",
]
