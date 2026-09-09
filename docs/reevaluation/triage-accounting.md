# Accounting lead triage — September 9, 2026

This read-only triage preceded the committed lead reevaluation charter. Existing gates, ledgers, findings, source, prior audit reports and file inventories were inspected. No new market outcome was computed during triage. S2/S3 had already received the bounded September 9 correction and are excluded here.

## Accepted bounded accounting slate

| Family | Frozen grid | Reason for reevaluation | Preserved inputs and audited path |
| --- | --- | --- | --- |
| XS momentum | 12: L7/14/28 × skip0/1 × K10/20; original EW top100 benchmark; 10bp per side | Weekly fixed contracts differ from the old daily constant-mix path. The direction is unsigned, so false rejection is possible. The September 2 simple-only audit found best SR .692 against .8, but DSR .163; proximity to one threshold is not evidence of a full gate reversal. | `TradingAgents/data/xsect/klines/` (799 files at inventory), original `xs_mom/dev_results.json` and rebuild gate/ledger. `portfolio.fast_weekly_portfolio` is repaired; `scripts/xs_mom_dev.py::_fast_portfolio` remains stale and must not be called. |
| XS carry | 6: L1/7/30 × leg .1/.2; original monthly top50; 10bp, signed funding, 4.5% full-capital charge | Completeness check. Missing maintenance costs flattered the old daily-target book, so a rescued absolute economic rejection is less plausible. The September 2 simple-only best was .923 against1.0 and DSR .279, with the placebo passing. | Original 799 daily klines and 799 funding files; `carry_xs.run_ls_portfolio`. Original runner loaders read full stores before clipping and must not be used. |
| Liquidation fade i1 | 6: threshold2.5/3.5 × H6/24/48; original universe, .1 weight, cap1, 10bp, 4.5% rf; funding excluded | Hourly summation, actual maintenance turnover and daily capital accounting materially change the measurement. Original i1 was not a simple SR rejection: its strongest cell had SR1.305 and good placebos but failed cumulative DSR. | Original hourly store (393 files present at inventory), `liq_fade_symbols.txt`, monthly membership and daily BTC reference. Require every original symbol's file, leaving gaps explicit. `liq_fade.run_hourly_portfolio` is the audited API. |

All three families retain January1,2021–March31,2025 decisions and prior-only warmup. Weekly momentum/carry first accrue January5 under the original first-Monday decision. Liq-fade includes March31 at23:00UTC. Input Parquet must be filtered before DataFrame materialization. File counts establish presence, not historical completeness or settlement validity.

Original `n_trials_at_eval` values were verified in the saved family result JSON: **momentum74, carry87, liq-fade100**. The new registration separately freezes current accounting DSR at **150 =126 existing distinct rebuild strategy identities +24 new accounting cells**. Forecast rows are not mixed into this namespace. The original per-series DSR recipe is retained as a policy comparator, not a measured effective-independent-trial count.

Compute every real cell and all declared zero-fee/double-fee/log-convention diagnostics first. If original SR or original-denominator DSR fails, the original conjunction fails and expensive remaining gates may be recorded as `not_run_primary_gate_failed`. Current150-DSR failure alone must not suppress an original-policy gate survivor. No winning configuration is selected.

## Deferred families

- Wide trend: all6 N10/20 × vt.2/.3/.4 cells are technically reproducible, but added maintenance costs remove favorable accounting. The September 2 SR.916 cell still had placebo around.22 and DSR.274; exposure rather than timing remained the binding concern.
- Classic V2/factor floor: doubled fees and side-blind funding could penalize shorts and change permanent halt dates. The original18 model-free factor cells on BTC/ETH, November7,2021–March31,2025, are a defensible later correction requiring no fit. Their wrapper still uses sqrt252 for aggregate metrics, and original cost/sizing/stop assumptions need explicit registration. Replacing assumed funding with realized funding is a separate measurement change. Existing ML prediction directories do not themselves establish post-purge provenance.
- Predlab S1/OPT2: daily maintenance costs mostly worsen economics. Original OPT2 retained24 cells, best LS development SR.111, best LO.577 below its BTC-relative threshold, and negative validation cells. Empty-signal omission is unsigned but requires demonstrated exposure before a broad rerun is justified.
- O4/PP2 overlays: duplicate base fees are a real conservative defect. A future fixed development-only base/overlay attribution is defensible, but the underlying champion is invalidated; the old full-stage selection chain is not a valid new search.
- Bybit liq-fade: if separately included later, rerun its single fixed primary/control pair before placebos. Original P3 separation .417 missed .75 and primary SR.808 missed1.0. This venue was not added to the present slate.
- The standalone cash-and-carry audit uses its own sleeve accounting. The V2 side-blind short-funding defect does not automatically apply to it.

## Compute and holdout limits

Actual daily grids are small relative to inference. Momentum's full battery has6000 placebo books; carry has6000 across its two families. Each represents roughly9million daily accounting steps. Liq-fade's full battery is roughly223million hourly steps plus trigger/weight construction. Grid work is expected to take minutes, daily placebo batteries tens of minutes to hours, and hourly batteries hours or longer; these were workload estimates, not measured empirical timings. Registered early stopping can avoid most inference work without deleting cells.

Combo-C1 spent April1,2025–July1,2026 for momentum, carry, value and liq-fade. Classic factor/carry and predlab holdout/validation periods are also spent. A corrected historical gate reversal would not restore a virgin holdout or validate a strategy. The current slate is a separately committed measurement correction, with no holdout, new model, threshold, signal, venue, or post-result cell selection.
