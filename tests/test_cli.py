import io
import json
from contextlib import redirect_stdout

from relay.cli import main


def _run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(argv)
    return rc, buf.getvalue()


def test_cli_route_simple():
    rc, out = _run(["route", "classify this email as spam"])
    assert rc == 0
    payload = json.loads(out)
    assert payload["task_class"] == "simple"


def test_cli_route_force():
    rc, out = _run(["route", "short", "--force", "complex"])
    assert rc == 0
    payload = json.loads(out)
    assert payload["task_class"] == "complex"


def test_cli_price():
    rc, out = _run(["price", "gpt-4o-mini", "1000", "500"])
    assert rc == 0
    assert "gpt-4o-mini" in out and "total" in out


def test_cli_bench():
    rc, out = _run(["bench", "classify this"])
    assert rc == 0
    assert "cheapest" in out and "max_saving_pct" in out


def test_cli_models():
    rc, out = _run(["models"])
    assert rc == 0
    assert "gpt-4o-mini" in out and "claude-opus-4" in out


def test_cli_install():
    rc, out = _run(["install"])
    assert rc == 0
    assert "UserPromptSubmit" in out and "relay.hook" in out


def test_cli_budget_empty(tmp_path):
    p = tmp_path / "s.jsonl"
    rc, out = _run(["budget", "--log-path", str(p)])
    assert rc == 0
    assert "today" in out and "month" in out
