# llm-v2-charter0-2026-11-09 — state

- Charter: `docs/superpowers/specs/2026-11-09-llm-v2-charter0-extraction-charter.md`
- Parent plan: `docs/superpowers/specs/2026-11-08-multiagent-v2-analysis-and-plan.md` (Phase 0)
- Branch: `research/llm-v2-charter0-2026-11-09` (devbox checkout `master_thesis/TradingAgents`)
- Model: `deepseek/deepseek-v4-pro` via OpenRouter chat completions, provider Baidu fp8,
  reasoning effort medium, temperature 0, C1 v2 prompt, strict JSON schema.
- Key: `OPENROUTER_API_KEY` from `~/.secrets/openrouter.env` (never committed).
- Status: see the bottom of this file.

## Log
- 2026-11-08 smoke test on invented headlines: 5 calls, USD 0.0046, model/provider echoed as
  pinned (`smoke/smoke-20261108.txt`).
