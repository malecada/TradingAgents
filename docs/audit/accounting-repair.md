# Executable accounting correction — 2026-09-09

Only synthetic fixtures and offline tests were executed for this change. Historical strategy data/results, gates, holdouts and trial ledgers were not rewritten. Source repairs do not establish a strategy verdict.

## Contract and affected source

`tradingagents/accounting.py` implements `pretrade-nav-v1`. A target is sized from pretrade NAV. The difference from marked signed notionals determines one-way turnover and fees. Fees reduce cash once; unchanged contracts then earn simple price PnL and signed funding. The public `accounting_step` returns marked notionals, pretrade and postfee weights, NAV, gross/net returns, fees, carry, turnover and name attribution. An absent target retains contracts; an explicit zero target closes them. Nonpositive NAV, missing held returns and supplied missing held funding fail explicitly. Only `funding=None` declares zero funding.

The pp/opt engines share this contract. Daily targets pay actual drift-maintenance fees; opt cadence keeps units between scheduled dates. Missing signal days remain on the calendar. S2/S3 callers convert stored log returns with `expm1`; their first entry and maintenance trades incur fees. Drawdown includes initial capital. Cost stress replays the same target schedule under the altered fee rate because altered fees also change subsequent NAV/turnover.

Weekly xsect portfolios retain contracts between rebalance dates. Fast/reference paths use the same executable core. Weekly long-short target frames retain explicit rebalance dates, including through placebo target transformations. Trend/carry daily targets resize against actual marked holdings. Hourly liquidation-fade returns compound; its full-capital daily charge reduces the actual book at the final hourly bar, so next-day trade sizing includes that charge. Missing daily/hourly interior bars cannot silently become zero returns on held contracts.

Classic backtesting and V2 now use actual notional turnover with single one-way fees; positive funding is received by shorts in V2. Risk-stop exits charge the actual marked closing notional. Both use calendar returns and 365-period default annualization. Classic runner alignment preserves missing dates instead of inner-joining them away. Thin-LS retains unavailable-signal dates and occupied contracts.

O4, O8, pp2, correction, champion and Bybit overlay helpers use retained per-name book inputs when available. Overlay fees are computed once on actual scaled positions. O8 and the champion drawdown illustration include initial capital. `portfolio.maxdd` now uses simple-return NAV rather than the older stress helper's log-return calculation.

## Archival boundary and remaining qualifications

- Returned frames retain `BookInputs` in memory for exact overlays/cost stress. `archive_returns(frame_or_series)` strips only these large inputs and preserves light accounting/version/status metadata before Parquet serialization. The original frame remains executable. Archives contain return summaries, not all replay inputs.
- An overlay given an old aggregate-only frame performs only the duplicate-fee correction and carries `overlay_status=approximate_summary_only`. It cannot reconstruct exact cancellation, holdings or turnover. Full historical overlay claims remain unvalidated; an aggregate result is not promoted to executable evidence.
- Supplied missing funding now fails. Old missing-funding-as-zero or missing-price-as-zero histories require independent coverage/settlement qualification; no settlement or funding vintage was invented.
- Engines fill every interior clock period between supplied source endpoints. Existing start/end APIs clip to the supplied source span; callers requiring an exact registered window must preflight both endpoints. The bounded correction must reject a source/window mismatch.
- The log-return convention remains available solely for the declared diagnostic kill-test. It is not executable PnL and historical verdicts are not reproduced by the repaired holdings model.
- No new liquidation model was introduced. Nonpositive NAV fails, and V2's optional intrabar stop remains its declared stop-level fill assumption. Historical costs/stops/metrics require separately registered empirical correction.

## Regression evidence

The initial audit suite produced **20 expected failures** before implementation: initial-capital drawdown; S2/S3 caller conversion; initial entry fees; weekly/opt unit drift; missing signal clocks and held returns; actual drift turnover; hourly compounding; calendar Sharpe; duplicated overlay fees. Log: `docs/audit/verification/accounting-red.log`.

Additional failures were pinned before their repairs: V2 single fees/signed funding/explicit mark failure and charged stop exits; actual scaled overlay turnover; fee-stress replay; O8 fees/DD; supplied missing funding; target-only missing symbols; preservation of full capital charges; next-day sizing after hourly daily charges; preserved weekly cadence after target transformations; the imported portfolio drawdown helper; and the Parquet archival boundary. Individual red logs are retained under `docs/audit/verification/accounting-*-red.log`.

The thin-LS AST fixture initially omitted the default `TAKER_BP` binding. That fixture was corrected, and the unchanged committed function was separately executed with the same synthetic panel: it returned two dates rather than three and omitted the held loss. The corrected baseline failure is retained in `accounting-thin-ls-red.log`; the setup error is not counted as a behavioral reproduction.

Final synthetic suite: **43 cases**. The impacted accounting/causal suite and thin-LS results are recorded below; no historical-data parity test ran. Existing tests describing free maintenance trades, zero settlement, first-row unknown returns, or target-only fee stress were replaced with hand-derived expectations under the approved contract. Causal signal timing tests remain in the verification suite.

Commands use the sibling Python runtime while importing this correction checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -m pytest -p no:cacheprovider tests/test_accounting_audit.py tests/predlab/test_pp.py tests/predlab/test_opt.py tests/test_xsect_portfolio.py tests/test_xsect_trend.py tests/test_xsect_carry_xs.py tests/xsect/test_ls_common.py tests/xsect/test_convention_fix.py tests/xsect/test_combo.py tests/xsect/test_liq_fade_pnl.py tests/strategies/test_causal_convention.py tests/strategies/test_causal_convention_validation_stack.py -k 'not TestLegacyParityPin and not parity_with_sep2_forensic_simple_numbers' -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -m pytest -p no:cacheprovider tests/predlab/test_xfam_lib.py -q
git diff --check
```

Final targeted outcome: **156 passed, 2 deselected in 31.89s** (`accounting-impacted.log`); thin-LS suite: **21 passed in 2.54s** (`accounting-xfam.log`). `git diff --check` passed. The two exclusions are explicitly historical-data parity checks, whose old result contracts were superseded and whose data were not opened.
