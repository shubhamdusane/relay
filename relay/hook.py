"""Claude Code UserPromptSubmit hook — inject routing decision as systemMessage.

Runs `python -m relay.hook` per prompt. Reads event JSON from stdin, emits
decision JSON to stdout. Silent-fail on any error to avoid blocking the agent.
"""

from __future__ import annotations

import json
import os
import sys

from relay.router import Router, TaskClass


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print("{}")
            return 0
        event = json.loads(raw)
        prompt = event.get("prompt") or event.get("user_prompt") or ""
        if not isinstance(prompt, str) or not prompt.strip():
            print("{}")
            return 0

        router = Router()
        force = os.environ.get("RELAY_FORCE_TIER")
        if force:
            try:
                router.force_tier = TaskClass(force.lower())
            except ValueError:
                pass

        decision = router.decide(prompt)
        report = os.environ.get("RELAY_REPORT") == "1"

        out: dict = {"continue": True}
        if report:
            out["systemMessage"] = (
                f"[relay] task={decision.task_class.value} "
                f"-> {decision.model} ({decision.prompt_chars} chars)"
            )
        print(json.dumps(out))
        return 0
    except Exception:
        # Silent fail: never block agent on hook error
        print("{}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
