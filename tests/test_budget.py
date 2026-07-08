import json

import pytest

from relay.budget import Budget, BudgetExceeded


def test_budget_no_cap_allows(tmp_path):
    b = Budget(log_path=str(tmp_path / "spend.jsonl"))
    b.check("gpt-4o", 1_000_000, 1_000_000)


def test_budget_daily_cap_blocks(tmp_path):
    b = Budget(daily_usd=0.10, log_path=str(tmp_path / "spend.jsonl"))
    with pytest.raises(BudgetExceeded) as ei:
        b.check("gpt-4o", 1_000_000, 1_000_000)
    assert "daily" in str(ei.value)


def test_budget_monthly_cap_blocks(tmp_path):
    b = Budget(monthly_usd=1.00, log_path=str(tmp_path / "spend.jsonl"))
    with pytest.raises(BudgetExceeded) as ei:
        b.check("claude-opus-4", 1_000_000, 1_000_000)
    assert "monthly" in str(ei.value)


def test_budget_record_writes_jsonl(tmp_path):
    p = tmp_path / "spend.jsonl"
    b = Budget(log_path=str(p))
    spent = b.record("gpt-4o-mini", 1000, 500)
    assert spent > 0
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["model"] == "gpt-4o-mini"
    assert rec["input_tokens"] == 1000
    assert rec["output_tokens"] == 500
    assert "ts" in rec and rec["ts"].endswith("Z")


def test_budget_total_sums_records(tmp_path):
    p = tmp_path / "spend.jsonl"
    b = Budget(log_path=str(p))
    b.record("gpt-4o-mini", 1000, 500)
    b.record("gpt-4o-mini", 2000, 1000)
    total = b.total()
    assert total > 0


def test_budget_key_isolation(tmp_path):
    p = tmp_path / "spend.jsonl"
    a = Budget(log_path=str(p), key="team-a")
    c = Budget(log_path=str(p), key="team-b")
    a.record("gpt-4o", 1000, 500)
    c.record("gpt-4o", 1000, 500)
    assert a.total() == c.total()
    b_only = Budget(log_path=str(p), key="team-a")
    assert b_only.total() > 0


def test_budget_today_accumulates(tmp_path):
    p = tmp_path / "spend.jsonl"
    b = Budget(log_path=str(p))
    b.record("gpt-4o-mini", 1000, 500)
    b.record("gpt-4o-mini", 1000, 500)
    assert b.today() > 0


def test_budget_handles_missing_file(tmp_path):
    b = Budget(log_path=str(tmp_path / "nope.jsonl"))
    assert b.today() == 0.0
    assert b.month() == 0.0
    assert b.total() == 0.0


def test_budget_cap_enforces_after_record(tmp_path):
    p = tmp_path / "spend.jsonl"
    b = Budget(daily_usd=0.001, log_path=str(p))
    b.check("gpt-4o-mini", 1000, 1000)
    b.record("gpt-4o-mini", 1000, 1000)
    with pytest.raises(BudgetExceeded):
        b.check("gpt-4o-mini", 1000, 1000)
