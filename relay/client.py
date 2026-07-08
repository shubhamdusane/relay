"""Drop-in OpenAI-compatible wrapper that routes + budgets every call.

Design: proxy classes delegate attribute access so any SDK method keeps working.
Only `chat.completions.create` (OpenAI) and `messages.create` (Anthropic) are
intercepted to inject model-override from the router.

Usage:
    from openai import OpenAI
    import relay

    client = relay.wrap_openai(OpenAI(), budget=relay.Budget(daily_usd=5.0))
    resp = client.chat.completions.create(
        messages=[{"role": "user", "content": "Summarize this PR"}]
        # NOTE: no `model=` needed — relay picks the cheapest tier
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from relay.budget import Budget
from relay.router import Router, TaskClass


def _prompt_text_from_messages(messages: list) -> str:
    """Flatten a chat `messages` list to a single string for classification."""
    parts: list[str] = []
    for m in messages:
        content = m.get("content") if isinstance(m, dict) else getattr(m, "content", None)
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for blk in content:
                if isinstance(blk, dict):
                    if "text" in blk:
                        parts.append(str(blk["text"]))
                    elif blk.get("type") == "text" and "text" in blk:
                        parts.append(str(blk["text"]))
    return "\n".join(parts)


def _token_count_from_response(resp: Any) -> tuple[int, int]:
    """Extract (input_tokens, output_tokens) from common SDK response shapes."""
    # OpenAI style: resp.usage.prompt_tokens / completion_tokens
    usage = getattr(resp, "usage", None) or (
        resp.get("usage") if isinstance(resp, dict) else None
    )
    if usage is None:
        return 0, 0

    def _get(obj, *keys):
        for k in keys:
            if isinstance(obj, dict) and k in obj:
                return obj[k]
            v = getattr(obj, k, None)
            if v is not None:
                return v
        return 0

    inp = _get(usage, "prompt_tokens", "input_tokens")
    out = _get(usage, "completion_tokens", "output_tokens")
    return int(inp or 0), int(out or 0)


# ---------- OpenAI wrapper ----------

@dataclass
class _OpenAIChatCompletions:
    _inner: Any
    _router: Router
    _budget: Optional[Budget]
    _dry_run: bool
    _last_decision: dict

    def create(self, *args, **kwargs):
        messages = kwargs.get("messages") or (args[0] if args else [])
        prompt = _prompt_text_from_messages(messages)
        decision = self._router.decide(prompt)
        self._last_decision["value"] = decision

        # Only override model if caller didn't explicitly pin one
        if "model" not in kwargs or kwargs["model"] is None:
            kwargs["model"] = decision.model

        if self._dry_run:
            return {
                "relay_decision": str(decision),
                "routed_model": decision.model,
                "task_class": decision.task_class.value,
            }

        # Budget pre-check (rough: 4 chars ~ 1 token)
        if self._budget is not None:
            self._budget.check(
                model=kwargs["model"],
                input_tokens=max(1, len(prompt) // 4),
                output_tokens_est=256,
            )

        resp = self._inner.create(*args, **kwargs)

        if self._budget is not None:
            inp, out = _token_count_from_response(resp)
            if inp or out:
                self._budget.record(model=kwargs["model"], input_tokens=inp, output_tokens=out)

        return resp

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


@dataclass
class _OpenAIChat:
    _inner: Any
    _router: Router
    _budget: Optional[Budget]
    _dry_run: bool
    _last_decision: dict

    @property
    def completions(self) -> _OpenAIChatCompletions:
        return _OpenAIChatCompletions(
            _inner=self._inner.completions,
            _router=self._router,
            _budget=self._budget,
            _dry_run=self._dry_run,
            _last_decision=self._last_decision,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class RelayClient:
    """Wraps an LLM SDK client with routing + budgeting. See `wrap_openai`."""

    def __init__(
        self,
        inner: Any,
        router: Optional[Router] = None,
        budget: Optional[Budget] = None,
        dry_run: bool = False,
    ) -> None:
        self._inner = inner
        self._router = router or Router()
        self._budget = budget
        self._dry_run = dry_run
        self._last_decision: dict = {}

    @property
    def chat(self) -> _OpenAIChat:
        return _OpenAIChat(
            _inner=self._inner.chat,
            _router=self._router,
            _budget=self._budget,
            _dry_run=self._dry_run,
            _last_decision=self._last_decision,
        )

    @property
    def last_decision(self):
        return self._last_decision.get("value")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def wrap_openai(
    client: Any,
    *,
    router: Optional[Router] = None,
    budget: Optional[Budget] = None,
    dry_run: bool = False,
) -> RelayClient:
    """Wrap an `openai.OpenAI()` instance. Returned client keeps all original methods."""
    return RelayClient(inner=client, router=router, budget=budget, dry_run=dry_run)


# ---------- Anthropic wrapper ----------

@dataclass
class _AnthropicMessages:
    _inner: Any
    _router: Router
    _budget: Optional[Budget]
    _dry_run: bool
    _last_decision: dict

    def create(self, *args, **kwargs):
        messages = kwargs.get("messages") or []
        system = kwargs.get("system", "")
        prompt = (system + "\n" if system else "") + _prompt_text_from_messages(messages)
        decision = self._router.decide(prompt)
        self._last_decision["value"] = decision

        if "model" not in kwargs or kwargs["model"] is None:
            kwargs["model"] = decision.model

        if self._dry_run:
            return {
                "relay_decision": str(decision),
                "routed_model": decision.model,
                "task_class": decision.task_class.value,
            }

        if self._budget is not None:
            self._budget.check(
                model=kwargs["model"],
                input_tokens=max(1, len(prompt) // 4),
                output_tokens_est=256,
            )

        resp = self._inner.create(*args, **kwargs)

        if self._budget is not None:
            inp, out = _token_count_from_response(resp)
            if inp or out:
                self._budget.record(model=kwargs["model"], input_tokens=inp, output_tokens=out)

        return resp

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _AnthropicWrapper:
    def __init__(
        self,
        inner: Any,
        router: Router,
        budget: Optional[Budget],
        dry_run: bool,
    ) -> None:
        self._inner = inner
        self._router = router
        self._budget = budget
        self._dry_run = dry_run
        self._last_decision: dict = {}

    @property
    def messages(self) -> _AnthropicMessages:
        return _AnthropicMessages(
            _inner=self._inner.messages,
            _router=self._router,
            _budget=self._budget,
            _dry_run=self._dry_run,
            _last_decision=self._last_decision,
        )

    @property
    def last_decision(self):
        return self._last_decision.get("value")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def wrap_anthropic(
    client: Any,
    *,
    router: Optional[Router] = None,
    budget: Optional[Budget] = None,
    dry_run: bool = False,
) -> _AnthropicWrapper:
    """Wrap an `anthropic.Anthropic()` instance."""
    return _AnthropicWrapper(
        inner=client,
        router=router or Router(),
        budget=budget,
        dry_run=dry_run,
    )
