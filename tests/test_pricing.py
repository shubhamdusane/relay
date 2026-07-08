import pytest

from relay.pricing import MODEL_PRICING, cheapest, estimate_cost


def test_pricing_has_default():
    assert "default" in MODEL_PRICING


def test_known_models_present():
    for m in ("gpt-4o-mini", "claude-opus-4", "gemini-2.5-flash"):
        assert m in MODEL_PRICING


def test_all_prices_nonneg():
    for m, (i, o) in MODEL_PRICING.items():
        assert i >= 0 and o >= 0, m


def test_estimate_cost_basic():
    q = estimate_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert abs(q.input_usd - 0.15) < 1e-9
    assert abs(q.output_usd - 0.60) < 1e-9
    assert abs(q.total_usd - 0.75) < 1e-9


def test_estimate_cost_unknown_uses_default():
    q = estimate_cost("made-up-model-xyz", 1_000_000, 0)
    assert q.input_usd == 1.00


def test_estimate_cost_rejects_negative():
    with pytest.raises(ValueError):
        estimate_cost("gpt-4o", -1, 0)


def test_str_format():
    q = estimate_cost("gpt-4o", 100, 50)
    s = str(q)
    assert "gpt-4o" in s and "total" in s


def test_cheapest_picks_lowest_blend():
    assert cheapest(["gpt-4o", "gpt-4o-mini", "gemini-2.5-flash"]) == "gemini-2.5-flash"


def test_cheapest_empty_raises():
    with pytest.raises(ValueError):
        cheapest([])
