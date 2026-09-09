# TradingAgents — consolidated audit corrections

The repaired base branch `fix/system-audit-2026-09-09` combines committed research/prediction-lab and feature/llm-event-xs source. Original worktrees and local modifications are preserved. This is the correction/integration checkout; monitoring/main and the VPS are not updated by its existence.

## Current status

Zero validated strategies. The confirmed September 9 accounting, missing-data, causal-data, provenance, execution and manuscript defects have been repaired and reviewed locally; 779 offline tests passed. The registered bounded correction completed seven S2/S3 development cells and sixteen saved ENet diagnostics, with no strategy graduation. See docs/audit/AUDIT_REPAIRS_2026-09-09.md and THESIS_FINDINGS §88. Historical results remain subject to their explicit corrections and qualifications. NLST4 is closed; value_rev and llm_c3p_conf retain their existing prospective dates. No family is reopened by software repairs.

## Active reevaluation

Current branch: `research/audit-reevaluation-2026-09-09`. The user authorized reevaluating materially affected leads after repairs. Gate `audit_reevaluation_2026_09_09` freezes26 primary cases across momentum, carry, liquidation fade, PRX and NLST4. Use only the new wrappers and immutable output namespace; no legacy main calls, forecast-model retraining, new signals, holdout cohorts or deployment. Details: docs/superpowers/specs/2026-09-09-lead-reevaluation.md and corresponding plan. S2/S3 and the16 ENet diagnostics were already corrected and are not repeated.

## Required research discipline

- Root AGENTS.md and canonical audits govern; RESEARCH_LOOP_GUIDE.md supplies the house process.
- Simple returns only for arithmetic position PnL. Log returns are legitimate signal/forecast targets only.
- Any empirical correction needs a committed charter and new gates.json key before execution, retaining old grids, windows and criteria. Preserve original artifacts and append supersession records.
- Sealed or spent windows cannot be silently reused as new out-of-sample evidence. No LLM evaluation before its training cutoff.
- New negative/positive evidence must be linked in THESIS_FINDINGS.md with source, data, gate and result provenance. No strategy is validated unless its full registered process passes.
- Do not read credentials, private key files, .env files, or key directories. Do not run live orders or VPS/systemd mutations in this correction task.
- Search the specific source directory; exclude .venv and node_modules.

## Layout and environment

Both tradingagents/predlab and tradingagents/xsect are present. scripts/predlab_*.py hold historical workflows; data/predlab/gates.json and data/rebuild/gates.json retain registrations. THESIS_FINDINGS.md contains the canonical combined history. docs/audit and docs/superpowers hold the remediation register and plan.

Use Python 3.13.13. The existing sibling predlab environment can run offline tests from this checkout with PYTHONPATH set to this checkout. New result output must stay in a new correction directory; original market stores are read-only inputs. Push reviewed correction branch changes for backup. The original thesis repository must be pushed after manuscript changes.
