"""`relay` CLI — inspect routing decisions, estimate cost, benchmark, manage budget."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from relay.budget import Budget
from relay.pricing import MODEL_PRICING, estimate_cost
from relay.router import DEFAULT_TIERS, Router, TaskClass


def _cmd_route(args: argparse.Namespace) -> int:
    text = args.text
    if text == "-":
        text = sys.stdin.read()
    router = Router()
    if args.force:
        router.force_tier = TaskClass(args.force)
    decision = router.decide(text)
    out = {
        "task_class": decision.task_class.value,
        "model": decision.model,
        "reason": decision.reason,
        "prompt_chars": decision.prompt_chars,
        "fallback_chain": list(router.fallback_chain(decision.task_class)),
    }
    print(json.dumps(out, indent=2))
    return 0


def _cmd_price(args: argparse.Namespace) -> int:
    q = estimate_cost(args.model, args.input_tokens, args.output_tokens)
    print(str(q))
    return 0


def _cmd_bench(args: argparse.Namespace) -> int:
    text = args.text
    if text == "-":
        text = sys.stdin.read()
    router = Router()
    dec = router.decide(text)

    input_tok = max(1, len(text) // 4)
    output_tok = args.output_tokens

    # Compare every tier's primary model
    print(f"Prompt: {len(text)} chars (~{input_tok} tokens), routed -> {dec.model}\n")
    print(f"{'model':<24} {'tier':<10} {'input$':>10} {'output$':>10} {'total$':>10}")
    print("-" * 68)
    rows: list[tuple[str, str, float]] = []
    for task, tier in DEFAULT_TIERS.items():
        for m in tier.models:
            q = estimate_cost(m, input_tok, output_tok)
            marker = " <- routed" if m == dec.model else ""
            print(
                f"{m:<24} {task.value:<10} "
                f"${q.input_usd:>9.6f} ${q.output_usd:>9.6f} ${q.total_usd:>9.6f}{marker}"
            )
            rows.append((m, task.value, q.total_usd))

    cheapest = min(rows, key=lambda r: r[2])
    most_expensive = max(rows, key=lambda r: r[2])
    saved_pct = (
        (most_expensive[2] - cheapest[2]) / most_expensive[2] * 100.0
        if most_expensive[2] > 0
        else 0.0
    )
    print()
    print(f"cheapest:        {cheapest[0]} (${cheapest[2]:.6f})")
    print(f"most_expensive:  {most_expensive[0]} (${most_expensive[2]:.6f})")
    print(f"max_saving_pct:  {saved_pct:.1f}%")
    return 0


def _cmd_budget(args: argparse.Namespace) -> int:
    b = Budget(
        daily_usd=args.daily,
        monthly_usd=args.monthly,
        log_path=args.log_path,
        key=args.key,
    )
    print(f"key:       {b.key}")
    print(f"log_path:  {b.log_path}")
    print(f"today:     ${b.today():.6f}" + (f" / ${args.daily:.2f}" if args.daily else ""))
    print(f"month:     ${b.month():.6f}" + (f" / ${args.monthly:.2f}" if args.monthly else ""))
    print(f"all_time:  ${b.total():.6f}")
    return 0


def _cmd_models(args: argparse.Namespace) -> int:
    rows = []
    for m, (inp, out) in sorted(MODEL_PRICING.items(), key=lambda kv: kv[1][0] + kv[1][1]):
        rows.append((m, inp, out))
    print(f"{'model':<24} {'input $/Mtok':>14} {'output $/Mtok':>14}")
    print("-" * 56)
    for m, inp, out in rows:
        print(f"{m:<24} {inp:>14.4f} {out:>14.4f}")
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    hook_snippet = {
        "hooks": {
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {"type": "command", "command": "python -m relay.hook"}
                    ]
                }
            ]
        }
    }
    print("# Claude Code integration — add this to ~/.claude/settings.json")
    print(json.dumps(hook_snippet, indent=2))
    print()
    print("# Env vars:")
    print("#   RELAY_REPORT=1        # print routing decision as systemMessage")
    print("#   RELAY_FORCE_TIER=...  # force simple|standard|complex")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="relay", description="Cost-optimizing LLM router")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("route", help="Show routing decision for a prompt")
    pr.add_argument("text", help="Prompt text, or '-' to read from stdin")
    pr.add_argument("--force", choices=["simple", "standard", "complex"])
    pr.set_defaults(func=_cmd_route)

    pp = sub.add_parser("price", help="Estimate cost for a model call")
    pp.add_argument("model")
    pp.add_argument("input_tokens", type=int)
    pp.add_argument("output_tokens", type=int)
    pp.set_defaults(func=_cmd_price)

    pb = sub.add_parser("bench", help="Compare cost across all tiers")
    pb.add_argument("text", help="Prompt text, or '-' to read from stdin")
    pb.add_argument("--output-tokens", type=int, default=512)
    pb.set_defaults(func=_cmd_bench)

    pbg = sub.add_parser("budget", help="Show current spend")
    pbg.add_argument("--daily", type=float, default=None)
    pbg.add_argument("--monthly", type=float, default=None)
    pbg.add_argument("--log-path", default="relay_spend.jsonl")
    pbg.add_argument("--key", default="default")
    pbg.set_defaults(func=_cmd_budget)

    pm = sub.add_parser("models", help="List all known models + pricing")
    pm.set_defaults(func=_cmd_models)

    pi = sub.add_parser("install", help="Print Claude Code hook snippet")
    pi.set_defaults(func=_cmd_install)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
