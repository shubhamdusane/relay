# Relay

A small, rule-based LLM router and budget guard for Python. Relay looks at a prompt, assigns it to a
cost tier (simple / standard / complex), picks a model from that tier, and can enforce hard daily and
monthly spend caps before a call is made.

**Status: early alpha (v0.1.0).** Routing and budget logic are unit-tested; the SDK wrappers have only
been tested against mocks, not live provider APIs. See [Status & limitations](#status--limitations).

## What it does

- **Rule-based task classifier** (`relay.classify_task`): regex keywords plus prompt length decide
  between `SIMPLE`, `STANDARD` and `COMPLEX`. Deterministic, no extra model call, no network.
- **Tier to model mapping** (`relay.Router`, `relay.DEFAULT_TIERS`): each tier is an ordered list of
  models. You can override tiers, force a tier, or pass your own classifier callable.
- **Budget gate** (`relay.Budget`): daily and monthly USD caps, tracked in an append-only JSONL file.
  `check()` raises `BudgetExceeded` before a call; `record()` logs spend after it.
- **SDK wrappers** (`relay.wrap_openai`, `relay.wrap_anthropic`): proxy an existing client; when you do
  not pass `model=`, Relay fills it in from the router and applies the budget check.
- **CLI** (`relay route | bench | price | models | budget | install`) and a Claude Code
  `UserPromptSubmit` hook (`python -m relay.hook`) that reports the routing decision.
- **Pricing table** (`relay.MODEL_PRICING`): hard-coded list prices (USD per 1M tokens) used for
  estimates. These go stale; check provider pricing pages.

## Install

```bash
pip install git+https://github.com/shubhamdusane/relay.git
```

Not published on PyPI (the name `relay-llm` on PyPI belongs to a different project). CI tests
Python 3.10 to 3.12. Provider SDKs (`openai`, `anthropic`) are optional and only needed if you use
the wrappers.

From source:

```bash
git clone https://github.com/shubhamdusane/relay.git
cd relay
pip install -e ".[dev]"
pytest
```

## Quick start

```python
import relay
from openai import OpenAI

client = relay.wrap_openai(OpenAI(), budget=relay.Budget(daily_usd=5.0, monthly_usd=100.0))

# No model= given, so Relay picks one from the classified tier.
resp = client.chat.completions.create(
    messages=[{"role": "user", "content": "Classify this email as spam or not: ..."}]
)
print(client.last_decision)  # [relay] simple -> gpt-4o-mini (rule-match)
```

If you pass `model=` yourself, Relay does not override it (it still applies the budget check).
`dry_run=True` on a wrapper returns the routing decision instead of calling the provider.

## Cost estimates: how to reproduce

Relay does not ship a traffic benchmark and makes no claim about percentage savings on your
workload; savings depend entirely on your prompt mix and on which models you would otherwise use.
What it can do is show, for one prompt, what each tier would cost at the list prices in
`relay/pricing.py`. Reproduce with:

```bash
relay bench "Summarize this article about climate change in three bullet points." --output-tokens 256
```

Real output from this repo at v0.1.0 (input tokens are estimated as chars / 4; output tokens are the
value you pass; prices come from the hard-coded table, not live):

```
Prompt: 67 chars (~16 tokens), routed -> gpt-4o-mini

model                    tier           input$    output$     total$
--------------------------------------------------------------------
gpt-4o-mini              simple     $ 0.000002 $ 0.000154 $ 0.000156 <- routed
claude-haiku-4           simple     $ 0.000004 $ 0.000320 $ 0.000324
gemini-2.5-flash         simple     $ 0.000001 $ 0.000077 $ 0.000078
gpt-4o                   standard   $ 0.000040 $ 0.002560 $ 0.002600
claude-sonnet-4          standard   $ 0.000048 $ 0.003840 $ 0.003888
gemini-2.5-pro           standard   $ 0.000020 $ 0.002560 $ 0.002580
claude-opus-4            complex    $ 0.000240 $ 0.019200 $ 0.019440
o1                       complex    $ 0.000240 $ 0.015360 $ 0.015600
gpt-4o                   complex    $ 0.000040 $ 0.002560 $ 0.002600

cheapest:        gemini-2.5-flash ($0.000078)
most_expensive:  claude-opus-4 ($0.019440)
max_saving_pct:  99.6%
```

`max_saving_pct` is the gap between the cheapest and priciest model in the table for that one
prompt. It is a price-list ratio, not a measured saving, and says nothing about output quality.
Relay has not been evaluated for answer quality or routing accuracy.

## How classification works

`classify_task` in `relay/router.py`, in this order:

1. Prompt length of 12,000 chars or more: `COMPLEX`.
2. Keyword regex for complex work (prove, derive, audit, research, "design a system", ...): `COMPLEX`.
3. Keyword regex for standard work (write code, implement, debug, json schema, analyze, ...): `STANDARD`.
4. Keyword regex for simple work (classify, extract, summarize, define, yes or no, ...): `SIMPLE`.
5. Fallback by length: under 400 chars `SIMPLE`, under 3,000 `STANDARD`, otherwise `COMPLEX`.

It is a heuristic. For example, a short prompt containing "audit" goes to the most expensive tier.
Replace it with your own function via `Router(classifier=my_fn)`.

Default tiers (the first model is used; the rest are exposed as a fallback chain):

| Tier | Models |
|------|--------|
| simple | gpt-4o-mini, claude-haiku-4, gemini-2.5-flash |
| standard | gpt-4o, claude-sonnet-4, gemini-2.5-pro |
| complex | claude-opus-4, o1, gpt-4o |

## Budget gate

```python
budget = relay.Budget(daily_usd=10.0, monthly_usd=200.0, log_path="relay_spend.jsonl", key="team-a")
budget.check(
    "gpt-4o", input_tokens=1200, output_tokens_est=256
)  # raises BudgetExceeded if over a cap
budget.record("gpt-4o", input_tokens=1180, output_tokens=240)  # appends a JSONL record
```

Spend is computed from token counts reported in the provider response and the hard-coded price
table. It is an estimate, not your invoice.

## Claude Code hook

`relay install` prints a settings snippet that registers `python -m relay.hook` as a
`UserPromptSubmit` hook. It only reports the routing decision (set `RELAY_REPORT=1`); it does not
change which model Claude Code uses.

## Status & limitations

- Alpha, not used in production. 55 unit tests, all offline. No test calls a live provider API, so
  the wrappers are verified only against mock clients.
- No benchmark of routing accuracy, answer quality, latency or real-world savings exists in this
  repo. Any such numbers seen elsewhere are not backed by this code.
- The classifier is keyword and length based. It will misroute prompts, and nothing here measures
  how often.
- The router can pick a model from a different provider than the client you wrapped (for example a
  `gpt-*` model on an Anthropic client). Pin `model=` or supply tiers that match your provider.
- `Router.fallback_chain()` exposes fallback models, but the wrappers do not retry on failure.
- Streaming and async calls are not specially handled; token accounting needs a `usage` field on
  the response.
- Budget tracking is a local JSONL file: single machine, not a distributed or tamper-proof limit.
- Pricing is a static table (last edited 2026-04) and will drift from real provider prices.
- The classifier makes no model call by design, so its overhead is small, but latency is not
  benchmarked here.

## Project layout

```
relay/
  router.py    # classifier, tiers, Router
  budget.py    # Budget, BudgetExceeded
  pricing.py   # MODEL_PRICING, estimate_cost
  client.py    # wrap_openai, wrap_anthropic, RelayClient
  cli.py       # `relay` command
  hook.py      # Claude Code hook
tests/         # 55 tests
examples/quickstart.py
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
```

## License

MIT. See [LICENSE](LICENSE).
