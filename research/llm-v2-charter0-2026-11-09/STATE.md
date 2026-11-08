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
- 2026-11-08 E1 `llm-v2c0-p0-label-20261109` COMPLETE at a1b41f7 (claim/complete receipts in
  `research_runs/`). Blind sheet rendered to `review/deepseek-review-sheet.md`.
- Status: AWAITING BLIND REVIEW. Reviewer fills every `VERDICT:` and `SAME (...)` line in the
  sheet (allowed verdicts in the header), commits the filled sheet, and must not open
  `research_runs/llm-v2c0-p0-label-20261109/outputs/` or `data/llm_event_xs/` before that
  commit. Then: `PYTHONPATH=. .venv/bin/python scripts/llm_v2c0_register.py e2`, commit
  `gates_e2.json`, push, and `PYTHONPATH=. .venv/bin/python scripts/llm_v2c0_p0.py score`.
