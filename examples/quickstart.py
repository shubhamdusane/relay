"""5-line relay demo. Router + budget dry-run, no API key needed."""

from __future__ import annotations

import relay


def main() -> None:
    router = relay.Router()
    prompts = [
        "classify this email as spam or not: 'you won a prize'",
        "write a python function to parse JWT and validate expiry",
        "Design a multi-region active-active Postgres architecture with "
        "audit logs and zero-downtime failover. Analyze tradeoffs step by step.",
    ]
    print(f"{'prompt (truncated)':<60} {'class':<10} {'model':<22} {'est$':>10}")
    print("-" * 105)
    for p in prompts:
        d = router.decide(p)
        q = relay.estimate_cost(d.model, len(p) // 4, 256)
        premium = relay.estimate_cost("claude-opus-4", len(p) // 4, 256)
        saved_pct = (
            (premium.total_usd - q.total_usd) / premium.total_usd * 100 if premium.total_usd else 0
        )
        print(
            f"{p[:58]:<60} {d.task_class.value:<10} {d.model:<22} ${q.total_usd:.6f}  "
            f"(vs opus: -{saved_pct:.0f}%)"
        )


if __name__ == "__main__":
    main()
