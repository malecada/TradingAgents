# Master Thesis Workspace — Crypto Trading Research

Master's thesis: multi-agent LLM trading framework (TradingAgents, crypto-adapted) + systematic quant strategy research. This root dir is NOT a git repo — it holds git worktrees, canonical reports, and data. Docs read as the author's solo work: no "we/our", passive/impersonal voice.

## State (September 9, 2026)

- **Zero validated strategies. The existing research program remains closed.** September9 system audit identifies additional accounting, missing-forecast, causal-data, evidence and execution defects. Failed adoption does not establish that every possible strategy lacks an edge.
- **Active correction checkout: `TradingAgents-audit-fixes/`, branch `fix/system-audit-2026-09-09`.** It combines the committed predlab and xsect packages. Original worktrees and raw stores remain preserved for provenance. Use the correction checkout for current engineering; do not resume legacy experiment scripts by rerunning them.
- Canonical correction records: `AUDIT_SYSTEM_2026-09-09.md`, `TradingAgents-audit-fixes/docs/audit/corrections.jsonl`, and `TradingAgents-audit-fixes/docs/superpowers/plans/2026-09-09-audit-corrections.md`. The only authorized empirical repair is the separately committed `audit_correction_2026_09_09` development-only charter. No new strategy search or unspent holdout use is authorized by these repairs.
- NLST4 is closed under its recorded economic gates; its old restart instruction is withdrawn. NLST2/3/4 causal-feature/FX results require qualification. OFLOW's original P0 sign bug was corrected before P1 failed. LIQ_FADE_V1 failed P3. Combo-C1 holdout is spent. The deferred LLM cycle and scheduled value-reversal snapshot retain their original registrations; this engineering repair does not initiate them.
- S1 software has local v2 order reconciliation and measurement repairs. **The VPS has not been changed or verified by this repair.** Existing live journals do not prove reconciled fills; old paper gross returns cannot be mixed with v2 net measurement.
- Thesis evidence reconciliation is part of the September9 repair. The positive S1/champion/Bybit claims and superseded log-PnL figures are withdrawn. The supplied assignment does not require positive alpha; a signed assignment attachment remains a submission requirement.

## Directory map

| dir | what | status |
|---|---|---|
| `TradingAgents/` | preserved xsect/LLM worktree (`feature/llm-event-xs`); original dirty files retained | provenance |
| `TradingAgents-predlab/` | preserved predlab source, forecasts and raw data (`research/prediction-lab`) | provenance |
| `TradingAgents-audit-fixes/` | consolidated audited correction branch (`fix/system-audit-2026-09-09`) | active engineering |
| `TradingAgents-monitor-nav/` | monitoring dashboard worktree (`main`), deployed to VPS | live |
| `thesis-latex/` | manuscript; private remote `malecada/master-thesis-latex` = only off-laptop copy — **push each session** | live |
| `Krypto-v0/` | supervisor's reference implementation — neutral tone, no criticism; .venv deleted (rebuild: `uv sync`) | reference |
| `crypto-quant-agents/` | de-forked supervisor-facing repo; NOT the live-bot deploy source | reference |
| `News_fulltext/` | 378K-article news corpus (reusable) | data |
| `archive/` | superseded pre-audit docs — **numbers in there are void, never cite** | archive |
| `keys/`, `apis/`, `hf_token.txt` | secrets — do not read, print, or commit | secrets |

Deleted worktrees (Sep-1 cleanup): exp-e1..e4, sentiment, metalabel, research — branches preserved in `TradingAgents/.git` (incl. `archive/research-jun16-wip`).

## Canonical root docs

- `AUDIT_BACKTEST_2026-07-07.md` — same-bar execution + unpurged labels; **voids all pre-Jul-7 strategy Sharpes** (V5 MIX 3.25→+0.36, 8-coin 3.97→+0.145)
- `AUDIT_BACKTEST_2026-08-24.md` — predlab engine booked log returns as PnL; **voids predlab Phase O/P + Bybit** (champion +1.892→−0.371)
- `AUDIT_SYSTEM_2026-09-09.md` — system audit; corrections and historical claim qualifications take precedence
- `AUDIT_GATES_2026-08-25.md` — earlier arithmetic/power audit; “no false kills” is not a zero false-negative probability and is qualified by the September9 audit
- `AUDIT_RESEARCH_PROGRAM_2026-09-02.md` — closure audit of all 63 verdicts; **Jul xsect engines (portfolio/trend/carry_xs) booked Σw·Δlog** — verdicts stand, §43/§45/§46 narratives need addenda; thin-edge stratum + ranked open leads; forensic in `data/audit_2026-09-02/`
- `AUDIT_2026-06-12.md`, `DECISION_REVIEW_2026-07-08.md`, `SUPERVISOR_REPORT_2026-07-28.md`
- `RESEARCH_LOOP_GUIDE.md` — house methodology: charter → pre-registration → tier ladder → sealed holdout → forensics

## Hard rules

1. **Never book log returns as PnL** — shorts gain fake +½σ²/day edge. Convention-swap kill-test is mandatory forensics.
2. **No backtest without pre-registered charter + gates.json key**, committed before results exist. Never edit gate criteria post-result.
3. **Pre-Jul-7 Sharpes and pre-Aug-24 predlab numbers are void.** Historical V2 figures also require the September9 funding/fee/turnover qualifications; they do not validate the revised implementation.
4. LLM-in-the-loop backtests must start after the LLM's training cutoff (memory look-ahead).
5. Verify negative results forensically: power probes, kill-tests, honest denominators.
6. Production VPS: don't run systemd edits over ssh from here (classifier blocks) — surface commands for manual execution.

## Environment

- Per-worktree venvs: `uv sync --all-extras --python 3.13.13`; tests: `python -m pytest tests/`
- Search hygiene: always exclude `.venv/` (≈200K+ files per worktree). Grep/glob from the specific worktree, not from this root.
