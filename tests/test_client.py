from types import SimpleNamespace

import pytest

from relay import Budget, wrap_anthropic, wrap_openai
from relay.router import Router, TaskClass


class _OpenAICompletions:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50),
        )


class _OpenAIChat:
    def __init__(self):
        self.completions = _OpenAICompletions()


class _MockOpenAI:
    def __init__(self):
        self.chat = _OpenAIChat()
        self.some_other_attr = "preserved"


def test_wrap_openai_routes_simple():
    inner = _MockOpenAI()
    c = wrap_openai(inner)
    c.chat.completions.create(messages=[{"role": "user", "content": "classify spam"}])
    assert inner.chat.completions.last_kwargs["model"] in (
        "gpt-4o-mini",
        "claude-haiku-4",
        "gemini-2.5-flash",
    )
    assert c.last_decision.task_class == TaskClass.SIMPLE


def test_wrap_openai_respects_explicit_model():
    inner = _MockOpenAI()
    c = wrap_openai(inner)
    c.chat.completions.create(
        model="gpt-4o-pinned",
        messages=[{"role": "user", "content": "classify spam"}],
    )
    assert inner.chat.completions.last_kwargs["model"] == "gpt-4o-pinned"


def test_wrap_openai_dry_run_skips_call():
    inner = _MockOpenAI()
    c = wrap_openai(inner, dry_run=True)
    out = c.chat.completions.create(messages=[{"role": "user", "content": "hi"}])
    assert isinstance(out, dict)
    assert "routed_model" in out
    assert inner.chat.completions.last_kwargs is None


def test_wrap_openai_preserves_attrs():
    inner = _MockOpenAI()
    c = wrap_openai(inner)
    assert c.some_other_attr == "preserved"


def test_wrap_openai_budget_records(tmp_path):
    inner = _MockOpenAI()
    b = Budget(log_path=str(tmp_path / "s.jsonl"))
    c = wrap_openai(inner, budget=b)
    c.chat.completions.create(messages=[{"role": "user", "content": "extract names"}])
    assert b.total() > 0


def test_wrap_openai_budget_blocks(tmp_path):
    inner = _MockOpenAI()
    b = Budget(daily_usd=0.0000001, log_path=str(tmp_path / "s.jsonl"))
    c = wrap_openai(inner, budget=b)
    with pytest.raises(Exception):
        c.chat.completions.create(
            messages=[{"role": "user", "content": "implement a full compiler"}]
        )


def test_wrap_openai_force_router():
    inner = _MockOpenAI()
    r = Router(force_tier=TaskClass.COMPLEX)
    c = wrap_openai(inner, router=r)
    c.chat.completions.create(messages=[{"role": "user", "content": "hello"}])
    assert c.last_decision.task_class == TaskClass.COMPLEX


class _AnthropicMessages:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(
            content=[SimpleNamespace(text="ok")],
            usage=SimpleNamespace(input_tokens=80, output_tokens=40),
        )


class _MockAnthropic:
    def __init__(self):
        self.messages = _AnthropicMessages()


def test_wrap_anthropic_routes():
    inner = _MockAnthropic()
    c = wrap_anthropic(inner)
    c.messages.create(
        system="you are a helpful assistant",
        messages=[{"role": "user", "content": "classify: 'yes' or 'no'"}],
    )
    assert inner.messages.last_kwargs["model"] is not None


def test_wrap_anthropic_dry_run():
    inner = _MockAnthropic()
    c = wrap_anthropic(inner, dry_run=True)
    out = c.messages.create(messages=[{"role": "user", "content": "summarize"}])
    assert "routed_model" in out
    assert inner.messages.last_kwargs is None


def test_wrap_anthropic_budget(tmp_path):
    inner = _MockAnthropic()
    b = Budget(log_path=str(tmp_path / "s.jsonl"))
    c = wrap_anthropic(inner, budget=b)
    c.messages.create(messages=[{"role": "user", "content": "label this"}])
    assert b.total() > 0
