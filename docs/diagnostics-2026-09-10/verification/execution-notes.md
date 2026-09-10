# Diagnostic execution record

Scope: the two September 10, 2026 diagnostic charters and their implementation plans.

- Settlement deferral and preservation baseline committed as `a3afb85040fd13d65fdc69908a32054bf9dc173d`.
- Charters, exact input hashes, two new gates and preservation infrastructure committed before implementation/results as `38d9a67e6ff042cb1fd870877b3e0222f40fdc08`. Both registry preflights passed on the clean commit.
- Forecast and factor modules are being implemented independently in new files. Root controls source commits and empirical execution; synthetic tests precede results.
- The binding charters take precedence over implementation-plan shorthand. Existing financial records and research verdicts remain preserved; new results use dedicated forensic ledgers.
- Shared interfaces checked: each runner consumes its own frozen gate and original input files, writes a separate exclusive output directory and leaves the central ledger untouched. The preservation verifier covers both namespaces. No implementation files are shared between the two workers.
- Both plans were checked against their charters: masks and calendar resampling are mandatory for forecasts; staged NAV and signed turnover identities are mandatory for risk. Neither task requires signal construction, model fitting, backtesting, new data, or a holdout read.
- Runtime: `PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -B` (Python 3.13.13). The default system Python is not used.

Implementation review, execution and result-verification entries follow below when completed.

- Static admission passed: 112 distinct pinned files, 104 timestamp-only Parquet checks, 270 external original receipts and all 62 earlier gate objects. The original 748-row financial ledger remains byte-identical. No financial values were analyzed during admission.
- Pre-result review requested complete reference-risk ratios and exceedance counts for all four exposure definitions, plus stop-successor sizing ages. These implement the existing factor charter without changing a trading policy.
- Pre-result review found that initial input-validation exceptions needed durable failure evidence. Both runners must reserve their new namespace before admission reads, preserve global admission failures with the full unavailable-case denominator, and never parse mismatched bytes. A global provenance failure invalidates the attempted run; it is not an accepted result or permission to retry.
- Pre-result review also required the risk runner to check the original financial ledger against the baseline and compare complete registry provenance at completion. This prevents unchanged-during-run checks from accepting a ledger already altered before admission or a gate changed during inspection.
- Both independent code reviews passed after those corrections. Root verified that all four executable source hashes still match the reviews. Forecast verification passed 57 tests (29 new, 28 existing); factor verification passed 80 tests (38 new, 42 existing). Test and review evidence is retained beside this record.

- Reviewed executable source committed as `cd8d9e3f064bb40273ba493e597e371e6f199b66`; the working tree was clean before execution. Both guarded runners completed once, retaining all 16 forecast and 36 risk identities. Run logs are `forecast-run.txt` and `risk-run.txt`.
- Independent saved-result verification passed 11,891 assertions without rerunning inference or a strategy. Both result identities, all 32,000 stored draws, all 852 price stops, complete calendars and original accounting agree.
- Results and Section 96 retain conditional-inference and proxy-accounting qualifications. The earlier 1,157 maximum cash-tail count was a prose error; the original trace establishes 1,158 already-halted dates. No prior result was rewritten.
- Final preservation passed: 7,214 baseline files byte-identical; only the declared append-only findings/correction paths and two semantic gate additions differ. All 62 prior gate objects, 270 external original inputs and the 748-row financial ledger remain preserved.
- Human report review passed on numerical reporting; its two precision edits were applied. All completion links are populated. Raw pytest failure logs retain their original trailing whitespace; source, JSON and Markdown whitespace checks pass.
