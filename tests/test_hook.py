import io
import json
import os
import sys
from contextlib import redirect_stdout
from typing import Optional

from relay.hook import main as hook_main


def _run_hook(event: dict, env: Optional[dict] = None) -> dict:
    old_env = {k: os.environ.get(k) for k in ("RELAY_REPORT", "RELAY_FORCE_TIER")}
    old_stdin = sys.stdin
    try:
        for k, v in (env or {}).items():
            os.environ[k] = v
        sys.stdin = io.StringIO(json.dumps(event))
        out_buf = io.StringIO()
        with redirect_stdout(out_buf):
            rc = hook_main()
        assert rc == 0
        return json.loads(out_buf.getvalue() or "{}")
    finally:
        sys.stdin = old_stdin
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_hook_empty_input():
    out = _run_hook({})
    assert out == {}


def test_hook_basic_continue():
    out = _run_hook({"prompt": "classify this email as spam"})
    assert out.get("continue") is True


def test_hook_report_adds_systemmessage():
    out = _run_hook(
        {"prompt": "implement binary search"},
        env={"RELAY_REPORT": "1"},
    )
    assert "systemMessage" in out
    assert "[relay]" in out["systemMessage"]


def test_hook_force_tier():
    out = _run_hook(
        {"prompt": "hi"},
        env={"RELAY_REPORT": "1", "RELAY_FORCE_TIER": "complex"},
    )
    assert "complex" in out["systemMessage"]


def test_hook_silent_fail_on_bad_json():
    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO("{not json")
        out_buf = io.StringIO()
        with redirect_stdout(out_buf):
            rc = hook_main()
        assert rc == 0
        assert out_buf.getvalue().strip() == "{}"
    finally:
        sys.stdin = old_stdin
