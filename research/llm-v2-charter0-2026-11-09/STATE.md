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
- 2026-11-08 reviewer unavailable (user decision: do not wait for the blind review). Bounds
  diagnostic `scripts/llm_v2c0_bounds.py` → `p0_bounds.json`: under BOTH extreme resolutions of
  the 46 review rows the primary and secondary verdicts are **FAIL**. The recall gate (>= 0.6)
  fails for every class in the best case (hack 0.30, insolvency_halt 0.58, listing 0.50,
  regulatory 0.55, upgrade 0.47); precision also fails for insolvency_halt (0.78) and, in the
  worst case, regulatory (0.68). Anonymization agreement 0.94 PASS; asset link 0.86–1.00;
  repeat flips 2/50.
- Mechanism: not the verbatim-span rule (5 of 52 raw events dropped). The model is
  conservative on title-only GDELT rows: 135 of 400 rows flagged `ambiguous` with no events,
  32 of them carrying 34 truth events. On the 154 human-adjudicated rows recall is 0.26
  (precision 0.67); on the 246 unaudited rows recall is 0.51. gpt-5.4-mini extracted from
  titles where V4-Pro declined.
- **Charter 0 verdict: FAIL (determined without review; E2 not run, no filled sheet).** The
  blind review remains available later to replace bounds by point estimates; it cannot change
  the decision. Family attempts used: 3 of 12 (C1 v1, C1 v2, this E1).
- Routing per charter §5: dossier uses article summaries + numeric cards; no typed-event
  extraction store this cycle. Revival condition (new charter, new data after 2026-09-15):
  full-text articles (CC-NEWS) instead of GDELT titles, and a prompt that returns a
  best-effort event with `ambiguous: true` rather than an empty list.
