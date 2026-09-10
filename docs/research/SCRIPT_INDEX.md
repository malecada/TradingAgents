# Script and source navigation

This map identifies roles and side effects, not an execution allowlist. Inspect
the actual registration and source before any empirical use. Historical mains
may refit models, fetch data or overwrite outputs even when their name sounds
like an audit or report. Preserve dated runners as provenance.

## Preparation entry points

| Entry point | Intended scope |
|---|---|
| `.venv/bin/python -B scripts/verify_offline.py` | Reviewed offline engineering and saved-checker suite; add `--collect-only` for collection. See [testing contract](../TESTING.md). |
| `.venv/bin/python -m tradingagents.research check --root . --registration <committed-json> --experiment <id> --source <full-HEAD>` | Admission metadata/source/history only; no empirical inputs opened or run started. See [schema/API](README.md). |
| `.venv/bin/python -m tradingagents.research examples` | Temporary synthetic Git fixtures demonstrate the lifecycle; no market-data experiment. |

Use the verified runtime/retention/Codex configuration commands documented by
their own `--help` and the preparation receipt. Configuration and test commands
do not grant permission for research, network/account access or production use.

## Research and measurement source families

| Location/pattern | Role and boundary |
|---|---|
| `tradingagents/research/` | New run admission, ownership and retained receipts. No strategy logic; source and synthetic checks must be verified independently. |
| `scripts/audit_*2026_09_09.py`, `scripts/audit_*2026_09_10.py` | Separately registered fixed corrections, reevaluations and diagnostics. Completed cycles are closed to repeats; read saved artifacts first. |
| `scripts/audit_reeval_common.py` | Existing dated-run admission/manifest pattern. A reference for new helpers, not permission to bypass a new charter. |
| `scripts/capture_dated_carry_2026_09_10.py` | Completed one-attempt public depth measurement; source-pinned and exclusive outputs. Do not rerun to find better quotes. |
| `scripts/carry_feasibility_math_2026_09_10.py` | Pure Decimal accounting for the frozen conditional carry model. No capture or historical backtest by itself. |
| `scripts/report_dated_carry_2026_09_10.py` | Retained-evidence report generator with exclusive output files. Even reporting is not necessarily write-free. |
| `scripts/predlab_*.py`, `tradingagents/predlab/` | Forecasting, statistical research and legacy experiment phases; some scripts fetch, fit, open holdouts or run execution loops. Resolve the exact function/entry point. |
| `scripts/*_xs_*.py`, `scripts/liq_*.py`, `scripts/carry_*.py`, `tradingagents/xsect/` | Cross-sectional strategy, universe and cost experiments. Read matching gates, date boundaries and qualified outcome first. |
| `scripts/combo_c1_*`, `scripts/exec_pf_*`, `scripts/holdout/` | Closed combination/execution work and holdout entry points. Their availability does not unspend the history. |
| `scripts/baseline_strategy*.py`, `scripts/factor_baselines.py`, `scripts/backtest*.py`, `scripts/walkforward*.py` | Legacy strategy and model evaluation. Can write result stores and have instrument/funding qualifications. Default engineering tests must not invoke them on retained data. |
| `scripts/fetch_*`, `scripts/backfill_*`, `scripts/recover_*`, `scripts/predlab_*fetch*.py` | External collection or recovery. Use provenance and declared attempt/source bounds; filenames do not imply fee-free or credential-free behavior. |
| `scripts/llm_*`, `tradingagents/agents/`, `graph/`, `llm_clients/` | LLM decision/feature pipelines, potentially with paid provider calls and training-cutoff leakage. Not required by the current offline preparation. |
| `scripts/predlab_capture_funding.py`, `scripts/predlab_s1_paper.py`, `scripts/predlab_journal_backup.py` | Prospective capture, paper bookkeeping and journal retention; governed by separate admission and rollout documents. No scheduler or paper run is started here. |
| `tradingagents/execution/`, `tradingagents/monitor/` | Account/order adapters and monitoring. Distinguish simulated measurement from exchange side effects and deployed version. |
| `tests/`, `docs/*/verification/` | Engineering and independent saved-evidence checks. Historical tests are not all automatically safe; use the reviewed inventory. |

Find a concrete source with `rg --files scripts tradingagents tests` and targeted
`rg` queries from this checkout. Avoid recursive searches through sibling raw
stores or virtual environments. Do not reorganize dated scripts solely to make
this table tidier; preserve pinned paths and add new interfaces narrowly.
