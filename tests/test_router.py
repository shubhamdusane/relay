import pytest

from relay.router import (
    DEFAULT_TIERS,
    Router,
    TaskClass,
    classify_task,
)


def test_classify_simple_short():
    assert classify_task("tl;dr: what is HTTP?") == TaskClass.SIMPLE


def test_classify_simple_extract():
    assert classify_task("extract the email addresses from this text") == TaskClass.SIMPLE


def test_classify_standard_code():
    assert classify_task("implement a binary search in python") == TaskClass.STANDARD


def test_classify_complex_keyword():
    t = classify_task("design a system for multi-region active-active replication")
    assert t == TaskClass.COMPLEX


def test_classify_complex_long_context():
    big = "context " * 3000
    assert classify_task(big) == TaskClass.COMPLEX


def test_classify_length_heuristic_mid():
    text = "some neutral text " * 60
    assert classify_task(text) == TaskClass.STANDARD


def test_classify_length_heuristic_short_fallback():
    text = "neutral filler " * 5
    assert classify_task(text) == TaskClass.SIMPLE


def test_classify_rejects_non_str():
    with pytest.raises(TypeError):
        classify_task(123)  # type: ignore[arg-type]


def test_router_decide_returns_model():
    r = Router()
    d = r.decide("classify the sentiment of: great product")
    assert d.model in DEFAULT_TIERS[d.task_class].models


def test_router_force_tier():
    r = Router(force_tier=TaskClass.COMPLEX)
    d = r.decide("hi")
    assert d.task_class == TaskClass.COMPLEX
    assert d.reason == "forced"


def test_router_fallback_chain():
    r = Router()
    chain = r.fallback_chain(TaskClass.SIMPLE)
    assert chain == DEFAULT_TIERS[TaskClass.SIMPLE].models
    assert len(chain) >= 2


def test_router_set_tier_override():
    r = Router()
    r.set_tier(TaskClass.SIMPLE, ("my-custom-model",))
    d = r.decide("classify spam")
    assert d.model == "my-custom-model"


def test_router_set_tier_rejects_empty():
    r = Router()
    with pytest.raises(ValueError):
        r.set_tier(TaskClass.SIMPLE, ())


def test_default_tiers_nondeg():
    for t, tier in DEFAULT_TIERS.items():
        assert tier.name == t
        assert len(tier.models) >= 1


def test_decision_str():
    r = Router()
    d = r.decide("summarize this")
    s = str(d)
    assert "[relay]" in s and d.model in s
