# Accounting reevaluation wrapper verification

`scripts/audit_reevaluate_accounting_2026_09_09.py` implements the committed 12/6/6 momentum/carry/liq-fade slate. Registration preceded source execution; no empirical outcome was generated during implementation.

The wrapper consumes the original daily manifest and required hourly symbol/membership files through `RunContext.track/read_market`. Market observations are filtered strictly before April1,2025, with complete output calendars and UTC-normalized endpoints. It calls the audited library weekly, daily-carry and hourly engines. Legacy script mains, stale local momentum fast PnL, fetchers and fitters are not called.

Every registered cell is passed to `RunContext.finish`, including missing-source, probe-blocked, primary-accounting-blocked and incomplete-inference cells. Four return streams are attempted for each measurable cell: valid simple PnL at original fees, zero transaction fees, double transaction fees and deliberately invalid log PnL. Funding/rf retain their registered meanings; zero transaction fees does not remove them. Original saved measurements and differences are preserved alongside corrected metrics. Original DSR denominators74/87/100 are verified against original result metadata, and current150 is read from the new gate. No selection or validation flag is generated.

An original SR or original-denominator DSR failure can skip the remaining costly gates. A current150-only failure cannot. A missing momentum benchmark is reported separately: real cells still receive all measurable returns and forensics; an original primary failure remains conclusive, while any survivor's required paired gates remain unavailable. Benchmark absence never becomes a benchmark-free pass.

Liq-fade recomputes P0/P1/P2 on development data. P1 retains the existential rule: a definitely observed hit survives missing observations from another symbol; a day with no hit and missing required inputs remains unknown. P2 passes when any fully scoreable cell's compounded forward simple return exceeds25bp. The original summed forward statistic is retained separately. End-of-window censoring and missing interior windows have separate counts. Missing interior observations do not become zero or disappear from coverage. The shared default_rng48 advances through the original grid order; skipped cells draw the identical shifts/redraws without building placebo PnL, preserving later cells' streams.

## Tests

The new feature initially failed collection because the runner did not yet exist (`verification/accounting-red.log`). Additional targeted red regressions were retained for mixed UTC/date endpoint handling, existential probe missingness, and benchmark-only data failure. An early P1 fixture itself mixed naive/aware date endpoints and was corrected; its setup failure is retained transparently in `accounting-probe-red.log`. No historical outcome was used as a test fixture.

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -m pytest -p no:cacheprovider tests/predlab/test_audit_reevaluate_accounting.py tests/predlab/test_audit_reeval_common.py tests/test_xsect_portfolio.py tests/test_xsect_carry_xs.py tests/xsect/test_liq_fade_pnl.py -q -k 'not parity_with_sep2_forensic_simple_numbers'
```

Final targeted outcome: **63 passed in12.43s**, retained in `verification/accounting-targeted-green.log`. The 23 wrapper cases cover fixed grids/counts, hand-derived weekly wealth, missing held marks/funding, hourly compounding, forensic replays, original/current-DSR early stopping, all-cell preservation, shared RNG state, loader filtering, immutable original DSR metadata, UTC fences, P1/P2 missingness and required benchmark handling. `git diff --check` passed before handoff.

Remaining limitations are empirical input completeness, historical DSR model assumptions, the original funding exclusion for liq-fade, and historical holdout spending. Missing source/probe measurement is an unavailable result, not evidence of an absent edge. All source must be committed and independent review completed before invoking any `--execute` family.
