"""Task classifier + tier router.

Routes each request to the cheapest model capable of handling the task.
Classification is rule-based (deterministic, <1ms, no ML call). Users can
override with a callable classifier for custom tiers.

Tiers (default):
  - SIMPLE  : short Q&A, classification, extraction, summarization    -> cheap
  - STANDARD: multi-step reasoning, code gen, structured output       -> mid
  - COMPLEX : long context, research, nuanced code review, math proof -> premium
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class TaskClass(str, Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"


@dataclass(frozen=True)
class Tier:
    """A routing tier: an ordered list of models tried in order (first = preferred)."""

    name: TaskClass
    models: tuple[str, ...]
    provider: str = "openai"  # default provider; per-model override in client

    def primary(self) -> str:
        return self.models[0]


DEFAULT_TIERS: dict[TaskClass, Tier] = {
    TaskClass.SIMPLE: Tier(
        name=TaskClass.SIMPLE,
        models=("gpt-4o-mini", "claude-haiku-4", "gemini-2.5-flash"),
    ),
    TaskClass.STANDARD: Tier(
        name=TaskClass.STANDARD,
        models=("gpt-4o", "claude-sonnet-4", "gemini-2.5-pro"),
    ),
    TaskClass.COMPLEX: Tier(
        name=TaskClass.COMPLEX,
        models=("claude-opus-4", "o1", "gpt-4o"),
    ),
}


@dataclass
class RouteDecision:
    task_class: TaskClass
    tier: Tier
    model: str
    reason: str
    prompt_chars: int

    def __str__(self) -> str:
        return f"[relay] {self.task_class.value} -> {self.model} ({self.reason})"


# ---------- rule-based classifier ----------

_COMPLEX_KEYWORDS = re.compile(
    r"\b(prove|theorem|derive|analyze.{0,20}architecture|design\s+a\s+system|"
    r"research|literature\s+review|audit|reason\s+step\s+by\s+step|plan\s+a\s+multi|"
    r"refactor\s+the\s+entire|review.{0,30}codebase|explain.{0,30}trade.?offs)\b",
    re.IGNORECASE,
)

_STANDARD_KEYWORDS = re.compile(
    r"\b(write\s+code|implement|refactor|debug|generate\s+tests|explain\s+this\s+code|"
    r"design\s+a\s+function|json\s+schema|structured\s+output|tool\s+call|"
    r"translate\s+the\s+following|analyze)\b",
    re.IGNORECASE,
)

_SIMPLE_KEYWORDS = re.compile(
    r"\b(classify|label|extract|summari[sz]e|what\s+is|define|tl;dr|"
    r"yes\s+or\s+no|pick\s+one|reply\s+with|sentiment)\b",
    re.IGNORECASE,
)


def classify_task(prompt: str, *, complex_char_threshold: int = 12_000) -> TaskClass:
    """Deterministic task classifier. Run order: COMPLEX > STANDARD > SIMPLE.

    Long prompts (>= complex_char_threshold) always escalate to COMPLEX because
    context-heavy work usually benefits from premium reasoning.
    """
    if not isinstance(prompt, str):
        raise TypeError("prompt must be str")
    if len(prompt) >= complex_char_threshold:
        return TaskClass.COMPLEX
    if _COMPLEX_KEYWORDS.search(prompt):
        return TaskClass.COMPLEX
    if _STANDARD_KEYWORDS.search(prompt):
        return TaskClass.STANDARD
    if _SIMPLE_KEYWORDS.search(prompt):
        return TaskClass.SIMPLE
    # Heuristic fallback by length
    if len(prompt) < 400:
        return TaskClass.SIMPLE
    if len(prompt) < 3_000:
        return TaskClass.STANDARD
    return TaskClass.COMPLEX


# ---------- router ----------

Classifier = Callable[[str], TaskClass]


@dataclass
class Router:
    """Picks a tier + model for each prompt. Allows custom classifier + tier override."""

    tiers: dict[TaskClass, Tier] = field(default_factory=lambda: dict(DEFAULT_TIERS))
    classifier: Classifier = classify_task
    force_tier: Optional[TaskClass] = None

    def decide(self, prompt: str) -> RouteDecision:
        task = self.force_tier if self.force_tier else self.classifier(prompt)
        tier = self.tiers[task]
        model = tier.primary()
        reason = "forced" if self.force_tier else "rule-match"
        return RouteDecision(
            task_class=task,
            tier=tier,
            model=model,
            reason=reason,
            prompt_chars=len(prompt),
        )

    def fallback_chain(self, task: TaskClass) -> tuple[str, ...]:
        """Ordered list of models to try if primary fails."""
        return self.tiers[task].models

    def set_tier(self, task: TaskClass, models: tuple[str, ...]) -> None:
        """Override a tier's model list."""
        if not models:
            raise ValueError("tier model list cannot be empty")
        self.tiers[task] = Tier(name=task, models=tuple(models))
