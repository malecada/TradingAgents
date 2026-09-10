# Master Thesis Workspace — Crypto Trading Research

Master's thesis: multi-agent LLM trading framework (TradingAgents, crypto-adapted) + systematic quant strategy research. This root dir is NOT a git repo — it holds git worktrees, canonical reports, and data. Docs read as the author's solo work: no "we/our", passive/impersonal voice.

## State (September 10, 2026)

- **Zero validated strategies. The existing research program remains closed.** September9 system audit identifies additional accounting, missing-forecast, causal-data, evidence and execution defects. Failed adoption does not establish that every possible strategy lacks an edge.
- **Active correction checkout: `TradingAgents-audit-fixes/`, branch `feature/terminal-event-accounting` (repaired base preserved on `fix/system-audit-2026-09-09`).** It combines the committed predlab and xsect packages. Original worktrees and raw stores remain preserved for provenance. Use the correction checkout for current engineering; do not resume legacy experiment scripts by rerunning them.
- The registered bounded correction is complete: seven S2/S3 development cells do not graduate; sixteen saved ENet diagnostics materially qualify earlier comparisons. Details: `AUDIT_REPAIRS_2026-09-09.md`, correction result and THESIS_FINDINGS §88. No model refits or holdout evaluation occurred.
- Canonical evidence: `AUDIT_SYSTEM_2026-09-09.md`, `AUDIT_REPAIRS_2026-09-09.md`, `REEVALUATION_LEADS_2026-09-09.md`, **`DATA_RECOVERY_2026-09-10.md`**, and the audit-fixes correction register. The September 9 cycles and three separately registered September 10 recovery/exposure/replay cycles are complete. **Current accounting interpretation: two conditional measured failures and 22 unavailable cases (12 momentum, six carry, four liquidation-fade).** This supersedes September 9's three/21 count: threshold 3.5/24h has unverified LUNA terminal exposure. Recovered H6 SRs 0.159713/0.815672 still fail original gates. Unavailable cases are not confirmed kills. PRX remains a conditional failure with six structurally unavailable outcomes; NLST4 retains qualified T1 IC=0.14236 on 2,718/2,776 scoreable pools and retrospective economic T2 failure. Details: THESIS_FINDINGS §§89–90.
- Market recovery completed: **5,568 authentic hourly observations across 47 symbols**, with original values preserved; all admitted hours were absent from checksum-valid monthly archives but agreed exactly between daily archives and the public API. The 1,264 BNX/ICP identity-quarantined hours remain unavailable. TOMO/RNDR/MATIC successors are separate futures and cannot complete original PRX persistence outcomes. Remaining requirement: exact historical BZRX/LUNA/BNX settlement cashflows, applicable fees/final funding, and contract lifetimes. Public notices establish closure times but not those cashflows. No last-close substitution, ticker rename or shortened sample is valid. Further empirical correction requires a new committed registration; existing holdout spending is preserved.
- Historical settlement follow-up is complete under `audit_settlement_evidence_2026_09_10`: **52 public requests; no exact terminal price admitted for BZRX/LUNA/BNX.** A dated November 2024 notice establishes the 30-minute default before BNX closure; older default rules, fee context and funding valuation are recovered. Public minute candles and estimates do not establish exact terminal cashflows. Old asynchronous export availability remains untested; ordinary income-history retention must not be applied to it. The precise provider request is drafted and unsent. No new financial replay or ledger rows. Details: `SETTLEMENT_EVIDENCE_2026-09-10.md`, THESIS_FINDINGS §91.
- Settlement/funding event accounting is implemented and independently reviewed: **61 synthetic checks plus 173 existing regressions passed**. The separate event API retains signed quantities, explicit event order, fees, funding calendars and original-contract closure. Historical BZRX/LUNA/BNX inputs remain unknown; legacy wrappers and all financial artifacts are preserved. No financial rerun or ledger row was added. The provider request remains unsent: official visitor chat is available, but this session lacks an interactive browser/connector and supplied contact details. Main integration and paper/VPS verification remain pending. Details: `EVENT_ACCOUNTING_2026-09-10.md`, THESIS_FINDINGS §92.
- NLST4 is closed under its recorded economic gates; its old restart instruction is withdrawn. NLST2/3/4 causal-feature/FX results require qualification. OFLOW's original P0 sign bug was corrected before P1 failed. LIQ_FADE_V1 failed P3. Combo-C1 holdout is spent. The deferred LLM cycle and scheduled value-reversal snapshot retain their original registrations; this engineering repair does not initiate them.
- S1 software has local v2 order reconciliation and measurement repairs. **The VPS has not been changed or verified by this repair.** Existing live journals do not prove reconciled fills; old paper gross returns cannot be mixed with v2 net measurement.
- Thesis evidence reconciliation is part of the September9 repair. The positive S1/champion/Bybit claims and superseded log-PnL figures are withdrawn. The supplied assignment does not require positive alpha; a signed assignment attachment remains a submission requirement.

## Directory map

| dir | what | status |
|---|---|---|
| `TradingAgents/` | preserved xsect/LLM worktree (`feature/llm-event-xs`); original dirty files retained | provenance |
| `TradingAgents-predlab/` | preserved predlab source, forecasts and raw data (`research/prediction-lab`) | provenance |
| `TradingAgents-audit-fixes/` | consolidated correction and reevaluation branch (`research/settlement-evidence-2026-09-10`) | active engineering |
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
- `REEVALUATION_LEADS_2026-09-09.md` — preserved 26-case correction; accounting counts are superseded by September 10 lifecycle evidence
- `DATA_RECOVERY_2026-09-10.md` — verified hourly recovery, contract identities and guarded replay; two conditional measured failures, 22 unavailable accounting cases; takes precedence over incompatible earlier counts
- `SETTLEMENT_EVIDENCE_2026-09-10.md` — historical rule/fee/funding follow-up, unresolved exact cashflows and unsent evidence request; no financial rerun
- `EVENT_ACCOUNTING_2026-09-10.md` — synthetic settlement/funding engine validation; historical inputs remain unavailable, no financial rerun
- `AUDIT_GATES_2026-08-25.md` — earlier arithmetic/power audit; “no false kills” is not a zero false-negative probability and is qualified by the September9 audit
- `AUDIT_RESEARCH_PROGRAM_2026-09-02.md` — closure audit of all 63 verdicts; **Jul xsect engines (portfolio/trend/carry_xs) booked Σw·Δlog** — historical verdicts are subject to September 9 corrections and §89 availability qualifications; thin-edge stratum + ranked open leads; forensic in `data/audit_2026-09-02/`
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


<claude-mem-context>
# Memory Context

# [master_thesis] recent context, 2026-09-09 10:03am GMT+2

No previous sessions found.
</claude-mem-context>