# TradingAgents — consolidated audit corrections

The repaired base branch `fix/system-audit-2026-09-09` combines committed research/prediction-lab and feature/llm-event-xs source. Original worktrees and local modifications are preserved. This is the correction/integration checkout; monitoring/main and the VPS are not updated by its existence.

## Current status

Current engineering branch: `fix/prospective-funding-capture-2026-09-10`. Public funding capture and optional paired paper admission are implemented on source `7d2a0ae9ef4ad707774360d2f67af40258a7d2e3`; 584 integrated Python tests passed. Raw event timestamps and exact Unicode identities are preserved. The prospective one-second comparison-label policy is separate from the unchanged legacy loader; missing cadence/quotes/state produces WAIT before either paper append. See `docs/funding-capture/FUNDING_CAPTURE_2026-09-10.md` and Section 94. The prepared archive has not been uploaded or deployed; no paper accumulation, financial replay or ledger append occurred.

Previous operational integration: `fix/operational-integration-2026-09-10`. Main at `ed5e22f` is merged locally with repaired source; the existing main worktree and VPS remain unchanged. The v2 monitor/backup compatibility repair is complete: saved base and overlay net measurements, explicit unavailable intervals and reconciliation, 20-base-return warmup, legacy diagnostics without invalidated S1 references, and append-only backups of both paper journal versions. Verification: 489 integrated Python tests and 25 frontend tests passed; frontend build/lint and synthetic browser checks passed. See `docs/operations/OPERATIONAL_INTEGRATION_2026-09-10.md` and Section 93.

The read-only VPS audit found legacy paper/live code at `558ffe7`, main monitor at `ed5e22f`, no v2 journals and no `xsect/funding` store. Monitor/Caddy/cron run; quant/hybrid timers are inactive. Actual account positions, full scheduler commands and dependency versions were not inspected. No deployment or account action occurred. Use the manual rollout document; generic deployment enables unrelated timers. Funding coverage must precede any corrected paper accumulation, and a broken v2 chain cannot silently restart.

The user deferred missing BZRX/LUNA/BNX settlement evidence and ended the support route. The research request was not sent; a contact address was entered before visitor security verification. No further provider contact is pending. Current accounting evidence remains **two conditional measured failures and 22 unavailable cases**. Event accounting remains a separate API, with its 61 synthetic tests and prior 173 regressions preserved; legacy bar wrappers and financial results remain unchanged. No financial replay or ledger row was added by operational integration.

Zero validated strategies. The confirmed September 9 accounting, missing-data, causal-data, provenance, execution and manuscript defects have been repaired and reviewed locally; 779 offline tests passed. The registered bounded correction completed seven S2/S3 development cells and sixteen saved ENet diagnostics, with no strategy graduation. See docs/audit/AUDIT_REPAIRS_2026-09-09.md and THESIS_FINDINGS §88. Historical results remain subject to their explicit corrections and qualifications. NLST4 is closed; value_rev and llm_c3p_conf retain their existing prospective dates. No family is reopened by software repairs.

## Completed reevaluation

Preserved branch: `research/audit-reevaluation-2026-09-09`. The user-authorized `audit_reevaluation_2026_09_09` cycle completed all 26 fixed cases on source `49fb9e4`. Its original three-failure/21-unavailable accounting interpretation is superseded by Section 90's two/22 count. PRX fails its conditional comparison with six unavailable selected-pair outcomes, and NLST4 passes descriptive ranking but fails economics. No strategy was validated or promoted. See docs/reevaluation/REEVALUATION_LEADS_2026-09-09.md, the immutable results and THESIS_FINDINGS §§89–90. S2/S3 and the 16 ENet diagnostics were not repeated.

Do not convert unavailable measurements into negative verdicts or rerun these output directories. Settlement events and internal hourly coverage must be recovered under explicit provenance before a separately registered correction. Original samples, criteria and spent holdouts remain preserved. The stronger NLST4 IC is a retrospective ranking association; no online entry policy was tested.

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
