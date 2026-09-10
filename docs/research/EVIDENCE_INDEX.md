# Evidence and supersession index

This is a navigation and interpretation layer. Original report/source bytes,
gate objects, ledgers and snapshots are retained. A historical file can contain
an invalidated claim; its presence is not current evidence of profitability.

## Current interpretation routes

| Question or older claim | Applicable evidence and qualification |
|---|---|
| Any current strategy validation claim | [Current state](STATE.md): zero validated strategies. [Findings](../../THESIS_FINDINGS.md) Sections 88–98 reconcile September 9–10 evidence. |
| Same-bar execution, label leakage and early positive strategy Sharpes | July 7 root audit voids pre-July-7 numbers; August 24 root audit voids earlier predlab log-PnL results. Root audit identities are in the artifact catalogue. [September 9 system audit](../audit/AUDIT_SYSTEM_2026-09-09.md) and [repair report](../audit/AUDIT_REPAIRS_2026-09-09.md) supply the tracked correction route. |
| `CHAMPION_SYSTEM.md` headline +1.89 Sharpe/+409% and earlier S1/Bybit claims | **Withdrawn.** [Historical champion document](../CHAMPION_SYSTEM.md) is retained as history, not a setup recommendation. Read [correction register](../audit/corrections.jsonl), the system audit and Findings §88 before citing it. Source documents pinned by previous runs are not edited to implement this notice. |
| September 9 accounting “three failures / 21 unavailable” | Superseded by [data recovery](../data-recovery/DATA_RECOVERY_2026-09-10.md): **two conditional measured failures / 22 unavailable**. The original [reevaluation](../reevaluation/REEVALUATION_LEADS_2026-09-09.md) remains preserved. |
| Historical BZRX/LUNA/BNX settlement estimates or modern generic rules | [Settlement evidence](../settlement-evidence/SETTLEMENT_EVIDENCE_2026-09-10.md) did not recover exact terminal cashflows. [Explicit deferral](../settlement-evidence/DEFERRED_2026-09-10.md) remains active. Unknown outcomes are not confirmed kills. |
| Event accounting implementation | [Event-accounting review](../event-accounting/EVENT_ACCOUNTING_2026-09-10.md): synthetic implementation evidence; missing historical settlement inputs remain missing. |
| Repaired software versus current VPS operation | [Operational integration](../operations/OPERATIONAL_INTEGRATION_2026-09-10.md) and [funding capture](../funding-capture/FUNDING_CAPTURE_2026-09-10.md). Local v2 repairs do not establish deployed reconciliation or corrected net paper performance. |
| Corrected positive factor development statistics | [Factor correction](../factor-correction/FACTOR_CORRECTION_2026-09-10.md), then [forecast/risk diagnostics](../diagnostics-2026-09-10/RESULTS.md) and [risk-policy interpretation](../risk-policy-2026-09-10/INTERPRETATION.md). Proxy prices, assumed funding, halted sleeves and spent history qualify the result. |
| Volume forecast improvements | [Diagnostics](../diagnostics-2026-09-10/RESULTS.md): conditional comparisons, not a validated model class or profitable execution strategy. |
| Latest dated BTC/ETH carry | [Interpretation](../carry-feasibility-2026-09-10/INTERPRETATION.md): all 432 modeled terminal outcomes negative at one frozen three-snapshot capture. Fee/account/spot freshness/path-margin qualifications remain. No automatic refresh; no general timeless impossibility claim. |
| Old generic research workflow or “champion” language | [Retained house process](../audit/workspace-RESEARCH_LOOP_GUIDE.md) is methodology history; use the [new phase prompt](../PROMPT_STRATEGY_RESEARCH_PHASE_2026-09-10.md) and current governance for any new authorized program. |

## Registries and scope

`data/predlab/gates.json`, `data/rebuild/gates.json` and separately named
`data/llm_event_xs`, `data/llm_pair_xs`, `data/llm_rank_xs` gate/ledger pairs
retain different program histories. The new [run lifecycle](README.md) does
not rewrite those objects or reinterpret a spent window as untouched.

The append-only [correction register](../audit/corrections.jsonl) links
supersessions; it does not erase original financial rows. Quote and diagnostic
forensic ledgers stay separate from financial experiments. Current counts must
be checked against exact files before a new claim.

## Root workspace documents

The original author workspace keeps canonical `AUDIT_*.md`, recovery,
settlement, operational and process documents one directory above this checkout.
Their filenames, hashes and physical locations appear as `external_inputs` in
[artifact_catalog.json](artifact_catalog.json). They remain outside this Git
checkout. Tracked counterparts above provide portable routes to the current
September 9–10 evidence. Where counterparts differ, the three assessed recovery,
reevaluation and settlement reports differ only in local versus relative link
targets; no report bytes were altered by preparation.

Hashes establish identity, not an external backup. Historical root documents
without tracked counterparts are unavailable in a clean clone unless separately
restored. Detailed pre-preparation instruction copies were saved locally under
the workspace's `.readiness-backups/`; they are not an independent backup or a
replacement for authoritative result artifacts.
