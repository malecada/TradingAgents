# Independent saved-forecast code review

Review date: September 10, 2026. Binding registration: `38d9a67e6ff042cb1fd870877b3e0222f40fdc08`; scope: the forecast charter, implementation plan, pure inference module, runner and synthetic tests. No empirical input values were read and no registered bootstrap, fit, strategy calculation or network request was executed. Previously passed worker suites were not repeated.

**Verdict: PASS after one failure-preservation correction.** Final clean-source preflight and independent saved-result review remain required; this is not an empirical result or authorization to change the frozen policy.

## Reviewed guarantees

- The runner validates the exact ordered sixteen-cell grid, declared baseline identities, development bounds, known missing origins and the 35 pinned inputs. Corrected vectors and baseline hashes must also agree with the original correction receipts. Arrow applies the timestamp filter before dataframe materialization; the latest permitted origin is March 31, 2025 at 00:00 UTC.
- The pure module requires unique, ordered UTC clocks, matching targets, boolean masks and the saved raw/effective/fallback algebra. The known volume origin is inserted as unavailable, while the known variance origin remains present and unscoreable. No missing loss is replaced by a zero-valued observation. Valid baseline-fallback pairs retain zero differential.
- Circular geometric bootstrap blocks sample the physical clock jointly for masked numerators and eligibility counts. Every draw is retained, with unavailable inference when its required denominator is invalid. Degenerate differences cannot receive a formal significant result. No alternative method or block selection occurs.
- Runner validation admits primary inference only for the four volume cells. The other twelve retain null primary p-values and Holm input one. All sixteen slots enter Holm adjustment; unavailable cells remain recorded. Direction's absent AUC interval prevents a conjunctive original-floor claim. Effect and stability descriptors remain retrospective qualifications.
- The immutable output namespace is reserved once. Successful completion checks all input hashes, the original 748-row financial-ledger identity and full registry provenance again. New forensic records stay separate from the financial ledger, and the result identifies every output checksum. No fitting, old experiment main or fetch function is called.

## Resolved finding and independent probe

The initial runner verified all hashes and receipts before reserving the output namespace. A missing baseline therefore raised without durable attempted-start or failure evidence. The original isolated probe observed `Output directory exists: False` and `Artifacts: []`.

The corrected runner reserves `start.json` with admission pending after preflight, exact gate validation and existing-output refusal. Hash, financial-ledger and receipt validation now occur inside the protected failure path. Admission succeeds explicitly before forecast values are parsed. A global failure retains all sixteen unavailable identities with `accepted_metrics: false` and does not emit an accepted result.

The same independent in-memory missing-baseline probe was repeated against the fix, using a temporary root, sixteen synthetic identities and monkeypatched preflight/hash verification. `read_frame` was guarded to raise if called. It retained exactly `start.json`, `failure.json` and `failure-forensic-ledger.jsonl`; all sixteen records were unavailable, accepted metrics were false, and neither `admission.json` nor `result.json` existed. Exit status was zero for the assertions. Worker regression cases additionally cover missing/changed inputs, conflicting prior receipts, ledger mutation, per-cell unavailability and postflight provenance changes.

## Reviewed source identities

| File | SHA-256 |
|---|---|
| `tradingagents/predlab/saved_forecast_inference.py` | `beb235d7b911cbed5cd1930f36bf426e0f61e8f767cb723c41bd2f3adf249714` |
| `scripts/audit_saved_forecast_inference_2026_09_10.py` | `895294e649cf02fc4dfe716bb28c72d5ac918239f40407d07c4888284018b53f` |
| `tests/predlab/test_saved_forecast_inference.py` | `d0589bc61aeadab6354b3fc07077b90c4e6e96fd9e4c2fdee3dbc79ff4a50a9f` |

The prior static input admission independently verified 112 distinct pins across both diagnostic families, all 104 timestamp-only Parquets, 270 original external receipts and the unchanged central ledger. Input admission does not establish stationarity, resolve penalized-model nesting, recover missing targets or validate any strategy.
