"""Model pricing table — USD per 1M tokens (input, output).

Updated 2026-04. Intentionally conservative; providers tend to cut prices over time.
If a model is missing, `estimate_cost` falls back to `default`.
"""

from __future__ import annotations

from dataclasses import dataclass

# (input_price_per_M, output_price_per_M) in USD.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "o1": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
    # Anthropic
    "claude-opus-4": (15.00, 75.00),
    "claude-sonnet-4": (3.00, 15.00),
    "claude-haiku-4": (0.25, 1.25),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-haiku": (0.25, 1.25),
    # Google
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
    "gemini-1.5-flash": (0.075, 0.30),
    # Open / local (electricity + amortized hardware, rough)
    "llama-3.1-70b": (0.35, 0.40),
    "llama-3.1-8b": (0.05, 0.08),
    "mistral-large": (2.00, 6.00),
    "mixtral-8x7b": (0.24, 0.24),
    # Default fallback for unknown models
    "default": (1.00, 3.00),
}


@dataclass(frozen=True)
class CostQuote:
    model: str
    input_tokens: int
    output_tokens: int
    input_usd: float
    output_usd: float

    @property
    def total_usd(self) -> float:
        return self.input_usd + self.output_usd

    def __str__(self) -> str:
        return (
            f"{self.model} | in={self.input_tokens}tok ${self.input_usd:.6f} | "
            f"out={self.output_tokens}tok ${self.output_usd:.6f} | "
            f"total=${self.total_usd:.6f}"
        )


def estimate_cost(model: str, input_tokens: int, output_tokens: int = 0) -> CostQuote:
    """Return CostQuote for a model call. Unknown models fall back to `default` pricing."""
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts cannot be negative")
    in_rate, out_rate = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    return CostQuote(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_usd=in_rate * input_tokens / 1_000_000,
        output_usd=out_rate * output_tokens / 1_000_000,
    )


def cheapest(models: list[str]) -> str:
    """Return model with lowest blended (input+output) price."""
    if not models:
        raise ValueError("models list is empty")
    scored = []
    for m in models:
        in_rate, out_rate = MODEL_PRICING.get(m, MODEL_PRICING["default"])
        scored.append((in_rate + out_rate, m))
    scored.sort()
    return scored[0][1]
