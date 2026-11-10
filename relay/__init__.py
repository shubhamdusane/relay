"""relay — cost-optimizing LLM router.

Route every call to the cheapest model that can handle the task.
Drop-in OpenAI-compatible wrapper. Deterministic keyword and length rules; no model call.
"""

from relay.budget import Budget, BudgetExceeded
from relay.client import RelayClient, wrap_anthropic, wrap_openai
from relay.pricing import MODEL_PRICING, estimate_cost
from relay.router import (
    DEFAULT_TIERS,
    RouteDecision,
    Router,
    TaskClass,
    Tier,
    classify_task,
)

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
