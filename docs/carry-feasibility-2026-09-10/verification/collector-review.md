# Collector and reporter independent review

Verdict: PASS for the bounded pre-result implementation scope. The final offline suite passed **56 tests in 0.22 seconds**. No market request, real quote, account access, strategy calculation or original-artifact edit was performed by this review. The collector, reporter and mathematical source were changed by their owners; this review owns the new test module and documentary evidence only.

## Contract and tested boundaries

The binding charter fixes two assets, three observations, two capital amounts, two reserve cases, two fee cases and nine terminal stresses: **48 entry cases and 432 unique measurement identities**. Synthetic integration exercises both the complete and unavailable paths through the actual collector, its filesystem receipts, the registered dimensions and the real pure cash module. On the unavailable path, a transport denial produces one actual attempted request followed by retained not-attempted receipts; all 432 unavailable scenarios remain. The successful fixture issues exactly four metadata/time requests and twelve depth requests, freezes the same two selected contract IDs and retains all 432 scenarios. No tests reinterpret these synthetic outcomes as market evidence.

Coverage includes earliest-expiry selection with lexical identity tie-breaking, inclusive 7/180-day boundaries, excluded perpetuals/types/status/collateral, contradictory spot base/quote identities, duplicate identities, missing order filters, native minimum/max notional fields, exact clock-unit validation, five-second calibration/quote bounds, the conservative clock-uncertainty age bound and future-event tolerance. Missing spot event timestamps stay qualified. The cash-module integration rejects crossed books while retaining unavailable cells. The public transport tests prove a single GET attempt, absence of account headers/body, byte-identical raw storage, immutable namespaces, timeout/invalid-JSON receipts, forbidden endpoint rejection and preserved denial headers.

## Findings and disposition

1. **Resolved — contradictory spot metadata could enter the pair.** A BTCUSDT name could override an ETH base or USDC quote. Two failing fixtures demonstrated admission. The collector now checks both base and quote fields and retains the rejected inventory row.
2. **Resolved — HTTP error headers were discarded.** A saved 429 body lost Retry-After and rate-limit evidence. The error branch now retains the selected source headers.
3. **Resolved — an existing measurement ledger was detected too late.** A second acquisition reached transport before discovering the old ledger. The collector now refuses existing output/ledger state before beginning capture.
4. **Resolved — provider denial did not stop subsequent requests.** Four fixtures for 403/418/429/451 demonstrated another transport call. The shared stop flag now preserves subsequent calls as not-attempted receipts. Requests already in flight in a concurrent batch are not represented as cancelled.
5. **Resolved — malformed metadata items lost the scenario denominator.** A symbols list containing null or a string raised AttributeError before a retained result. Both metadata lists now require mapping items; two full-run regressions retain all 432 unavailable identities.
6. **Resolved — reporter could claim completeness or screen success without binding input hashes and identities.** Static review found missing ledger/evidence hash checks, dimension validation and existing-report refusal. The reporter now checks the capture inventory and containment, ledger and evidence hashes, all 48/432 identities and their dimensions, and refuses existing reports. Synthetic tests reject a changed ledger, nine duplicate positive screen identities despite an updated hash, and a pre-existing report. A full unavailable fixture renders all four screens as unavailable and never promotes a strategy.

## Evidence and limitations

Exact final command, run from the integrated checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -B -m pytest tests/test_capture_dated_carry_2026_09_10.py -q
```

- `collector-initial-tests.log`: four initial failures, 39 passes.
- `collector-denial-red.log`: four denial-continuation failures.
- `collector-followup-tests.log`: two malformed-item failures, 52 passes; prior fixes already passed.
- `collector-integration-report-red.log`: despite the filename, its first execution occurred **after** the reporter fixes and contains four passing tests. It is not claimed as RED evidence.
- `collector-final-tests.log`: 56 passes, including complete/unavailable collector integration and the valid unavailable-report path.

Network and clock dependencies are replaced only at their external boundaries. File writes use temporary directories; calculation fixtures are invented and clearly separated from market inputs. The global-denial test supplies a mathematical sentinel solely to prove that unavailable source data never reaches financial arithmetic. Other integration tests use the actual pure mathematical module. No earlier passed financial suite or historical data was rerun. The review does not establish account/product access, authenticated fee applicability, spot event freshness, simultaneous fills or margin survival. All rows remain explicitly non-executable and non-validating under the charter.

## Reviewed byte identities

- `scripts/capture_dated_carry_2026_09_10.py`: `e122af69bb6a71d6226cf8c63d67f80bdfc005da0bf53b1990f6ef615243cabc`.
- `scripts/report_dated_carry_2026_09_10.py`: `cdce3c8cf1e33d5cdbc58a69f16ac8317b2c33e9dba67acce3992670500237a2`.
- `scripts/carry_feasibility_math_2026_09_10.py`: `3e15bf12c3edfc765e4a6c52f2d4b8c0e7d1fe337c16dded893b7c9483e9928b`.
- `tests/test_capture_dated_carry_2026_09_10.py`: `a801a47b430500a879df7108f7db42bb84693ab2348ed04ab999b96c7f563a85`.
- `docs/carry-feasibility-2026-09-10/charter.md`: `bb2e4c06e7d101226ba1b33c60e62b268dabc746ccb1373cb96e7809efb5d096`.
- `docs/carry-feasibility-2026-09-10/verification/collector-final-tests.log`: `96ca25aa4fcbd941fcd63ad3c28ff7f65bf36b5076007542937f0f28cddf58c7`.
