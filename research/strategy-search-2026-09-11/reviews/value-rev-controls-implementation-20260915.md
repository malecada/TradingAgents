# Pure value_rev control assembly — implementation

September 15, 2026. This additive helper implements declared parity checks only. It does not execute the legacy engine, choose a pending interpretation or admit source/empirical work. The old value runner, readiness helper, charter, gates and six frozen runtime packages remain unchanged.

Owned source: `tradingagents/research_value_controls.py`, SHA-256 `3aaf1171d94563ba2ccc75129128e8f4e4e273d3d36ad0ad4e55fedfad97d632`.
Owned tests: `tests/research/test_value_rev_controls.py`, SHA-256 `8579940d8f10aa65060ecbd741573a44c0e4ffcb594f60fe9c15d80590d7f172`.

## Interface and behavior

`assemble(cells, *, decision_ms, execution_ref)` checks one proposed decision bundle. Four output identities always remain present:

| Helper identity | Frozen gate metric | Frozen breadth |
| --- | --- | --- |
| fees_tercile | mcap_over_fees_90d | tercile |
| fees_decile | mcap_over_fees_90d | decile |
| revenue_tercile | mcap_over_revenue_90d | tercile |
| revenue_decile | mcap_over_revenue_90d | decile |

The labels are an explicit mapping to existing cells, not new empirical configurations. Each cell supplies its own metric-eligible cohort; different metrics can declare different cohorts. Strategy, C1 and C2 must match that exact cell cohort and breadth. All cells and roles must match the one caller-supplied decision clock and common execution reference. The reference contains input/policy SHA-256 declarations, explicit lag milliseconds and action time. Action cannot precede decision; no Monday, two-day lag or funding convention is inferred.

Each signal supplies its own declared cohort, breadth, decision clock, execution reference, explicit `high_is_long` or `low_is_long` orientation, score-source hash and required-symbol score/availability mapping. Scores must be finite bounded numeric literals and available no later than decision. The helper does not rank or multiply scores, choose an orientation, calculate a ratio, compound a return or assign a weight. Zero and negative numeric scores are accepted as declared scores; this makes no decision about missing/zero economic fee or revenue observations.

A missing, extra, nonfinite or late required score makes its role unavailable. A mismatched cohort, breadth, decision clock, lag or execution reference is unavailable. There is no universe intersection, shrinking, zero fill, sign default or control replacement. Required symbol identities and per-symbol unavailability remain in each role; valid supplied roles remain visible when another role is missing. Missing cells retain all three role placeholders. Unknown cell identities reject the bundle rather than expanding its four-cell denominator.

Results are labeled `readiness-only; pending registered interpretation`, with `source_admission: false` and `empirical_admission: false` at bundle, cell and role levels. `declared_aligned` means only that supplied fields align. An assembly digest binds the emitted normalized description, including scores; it is not a durable stage record, signature or verification of the caller's source hashes. No filesystem, network, dataframe, source loader, portfolio, ledger or legacy module is imported.

## Verification and limitations

Fourteen invented-fixture tests passed in the checkout-local Python 3.13.13. The reviewed 120-second, 512 MiB sampled aggregate RSS, two-CPU guard completed in 0.104 seconds with peak 21,463,040 bytes. Test runtime was 0.017 seconds. See `value-rev-controls-tests-20260915.guard.json`.

Coverage includes both breadths and unequal metric cohorts; strict per-role cohorts; missing, extra and duplicate coverage; late/unknown clocks; NaN/infinite/missing and permuted-NaN scores; explicit orientations without reversal guesses; input, policy, lag and action mismatches; deliberately nondefault caller lag retained without empirical admission; missing cells/roles with full denominator; unknown-cell rejection; deterministic assembly and digest changes when scores change; input preservation; and false admission flags at every result level. No empirical or engine-based test was run. No test failure remains.

Source hashes, score values, clock witnesses, eligibility cohorts and execution-policy references are caller declarations. This helper does not verify that they describe real observations, bind an admitted P0 pair, implement registered price/funding accounting, satisfy publication availability or have received interpretation approval. It neither resolves the audit's common-universe/C2/funding/endpoint ambiguities nor proves placebo count matching or held-contract parity. Those remain separate source/engine admission work. The additive helper can detect a declared mismatch before any such execution.
