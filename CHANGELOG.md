# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-08

### Added
- Initial release of relay-llm
- Cost-optimizing LLM router with drop-in OpenAI-compatible client
- Rule-based deterministic task classifier (<1ms, no ML call)
- Three-tier routing: SIMPLE, STANDARD, COMPLEX
- Multi-provider fallback chains (OpenAI, Anthropic, Gemini)
- Hard budget caps (daily, monthly, per-key)
- JSONL spend logging
- `relay.route` CLI command — inspect routing decisions
- `relay.bench` CLI command — side-by-side tier cost comparison
- `relay.budget` CLI command — inspect spend
- Claude Code hook integration
- Thread-safe Budget with internal lock
- Comprehensive test suite (55+ tests)
- `py.typed` marker for PEP 561
