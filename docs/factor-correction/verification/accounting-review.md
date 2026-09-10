# Independent factor-correction accounting review

Reviewed 2026-09-10T12:26:52.595253+00:00 before financial execution. The broad archive/charter commit is `acb8c8b`; the fixed experiment registration is `9cedcc4`. Implementation files were reviewed at the hashes below, before the pending source freeze. No production input prices, holdout observations, model fit, real strategy replay, central ledger write or source edit was performed by this review. The only new file written by the reviewer in this phase is this note.

## Disposition

No unresolved material finding remains within the reviewed accounting-wrapper scope. Previously reported variant/diagnostic failure isolation, malformed-input handling and trace-schema defects are resolved and independently verified. Source must still be committed and normal registry preflight must pass before the registered empirical invocation. This synthetic review does not establish historical input parity, executable venue economics or a strategy-validation result.

## Findings and corrections verified

1. **Variant failures previously suppressed later variants.** The earlier single outer exception boundary could leave fewer than five variant records and erase a measured primary outcome. `guarded_variants` now attempts all five independently, and a preparation failure explicitly supplies all five unavailable records. A unit regression proves continuation after a synthetic zero-execution failure. An additional synthetic invocation of the actual `main` flow forced a zero-funding failure and verified that later legacy measurement remains present, along with all 18 cells and 90 variant records.
2. **Invalid shadow previously invalidated the primary.** Shadow arithmetic now has its own exception boundary and a missing primary schedule produces an unavailable diagnostic. The same synthetic full-wrapper check forced every log shadow to fail while every primary remained a qualified benchmark measurement. No invalid shadow was reclassified as executable PnL.
3. **Market schema/type failures previously escaped before the denominator was preserved.** Missing OHLC fields reproduced a KeyError and an object-valued price reproduced a TypeError. The data-admission and preparation boundaries now cover ValueError, KeyError, TypeError and OSError. A synthetic malformed-Date-schema main invocation retained 18 unavailable cells, 90 unavailable variant records, 18 unavailable shadow records and 18 intercepted ledger calls.
4. **Trace interface initially mismatched the wrapper.** The final engine provides both `nav_before/nav_after` and `pre_nav/post_nav` aliases. It also provides `stop_outside_envelope`; its absence originally caused a mandatory diagnostic lookup failure. The new gap-stop regression preserves the assumed97 stop fill above the synthetic85 high and flags it, without changing the book. Trace and non-trace equity/metric parity tests pass. Read-only diff inspection found trace collection and its optional keyword argument, with existing accounting/risk arithmetic unchanged.

## Accounting, historical comparison and denominator checks

The old V2 function is AST-extracted from the pinned archive, supplying NumPy without running historical imports or CLI side effects. A hand-built long book with prices100,110,121 and 1% input fee returned100,108,118.8, matching the original doubled-fee calculation. This test used no saved market inputs.

Archived signal builders and grid construction are used directly. Target arrays are constructed once per configuration and reused across the four repaired cost/funding variants and legacy engine. Prior-history signals, stateful Donchian history, in-window sizing reset, original sqrt252 sizing volatility and the first no-return valuation row remain consistent with the charter. XS prior calendars use the later source start and require equality; development dates must equal the entire registered clock. No development inner-join loss, skip-missing sleeve aggregation or post-cutoff source admission was introduced.

The old scalar comparator uses sqrt252 with sample standard deviation, compounded return, the original drawdown convention without the initial NAV, and the original row count. BEST comparison checks the exact two-sleeve date index and values with rtol0/atol1e-10. The primary reporting function instead uses sqrt365, all return/cash-tail rows and an initial NAV for drawdown, as registered. No empirical parity claim was made in this review.

The invalid-log diagnostic replaces only the primary price contribution using frozen primary exposure and effective stop-mark returns. Primary fee/funding/impact fractions and the primary stop schedule remain fixed; it is therefore correctly labeled a frozen-exposure distortion diagnostic, not a new executable strategy book.

The registered90 outcomes are five variants nested under18 fixed configuration records, with18 separate invalid-log diagnostics; they are not90 independent hypotheses. Measured primary rows remain `qualified_benchmark_measurement` with `validated=False`. No standalone adoption threshold, DSR selection gate, new winner selection or holdout claim appears in the wrapper. The equal-weight aggregate remains a two-sleeve benchmark return index rather than a pooled executable account. Historical input-lineage, spot/proxy-price, assumed daily funding, threshold-stop-fill and permanent-halt qualifications remain necessary.

## Verification performed

Focused command:

```text
../TradingAgents-predlab/.venv/bin/python -m pytest tests/test_factor_correction.py tests/test_factor_v2_trace.py tests/rebuild/test_factor_signals.py tests/strategies/test_v2_sizing_golden.py tests/test_accounting_audit.py -q
```

Result: **78 passed in1.30s**. The earlier invocation during implementation returned19 passed/3 failed; all three were the already reported new RED regressions for the not-yet-added `guarded_variants` helper and envelope trace field. They are green in the final invocation.

Additional scratch checks ran the actual wrapper `main` only against handcrafted three-row constant-price fixtures in automatically deleted temporary directories. Registration/preflight, target construction and ledger append were intercepted in-process. No real registration was bypassed for an empirical invocation and no central ledger was opened for writing. One case forced a zero-funding variant failure plus invalid shadows; the other removed the Date column before admission. Both retained all18 cells/all90 variant statuses/18 intercepted ledger calls. The first retained measured primary and legacy outcomes; the second marked every variant unavailable. The archived BEST development-only output was read solely as the wrapper's comparison artifact; no current market dataset was read.

Output-directory repeat refusal, initial-loss drawdown, full cash tails, signed funding, actual marked exit charges, long/short trace arithmetic, simple/log distortion, signal causality and sizing golden contracts are covered by the focused checks. Run-time source/gate checks and original ledger-prefix/output integrity must also be verified during the separately authorized result review.

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| `scripts/audit_factor_floor_2026_09_10.py` | `c2cd3be3c8f7096e6f1311bd031d4253d720c1f329e8e80d497a6b8d33552861` |
| `scripts/baseline_strategy_v2.py` | `8de678e024c7ad7dcd63c2d5e4bbca90c2b466ec665309fee87ddf32b29e6572` |
| `tests/test_factor_correction.py` | `e0934258148ec0a35c8c441cf8e71588b6427e77f45456aaea08e464dbfdb963` |
| `tests/test_factor_v2_trace.py` | `57a079a49814b606f98daeee68eb9eee228d05b56c7d2163866c395d1b4d69b1` |
| `docs/factor-correction/charter.md` | `6de3590e721552d8fb5a9cb7fd7a7a8f1d89f832b667306d00170d914488eac7` |
| `docs/factor-correction/original/manifest.json` | `22378abdf38294f554f0785e7d4ce45d4b1e889e120d47accc5a1de51ee4d4b1` |
