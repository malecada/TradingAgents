# Refusal worker preparation02: R1 late failure retention

Source-only successor to preparation01 and independent review `782807f197f96b2f9f67c1b404ab1057917bbfb876943fb17236e90da0e7ac4a`. No job, guard, claim, registration adoption or numerical import occurred. All preparation01 sources, reviews, raw failures and manifests remain unchanged.

## Concrete change

The postclaim outer's additive `post-terminal-failure.json` attempt now occurs after every independent signal-handler restoration attempt. The final marker is conditional on the selected error from the body, post-tail checks, and restorations. It records the final selected error class. The original immutable `terminal.json`, including a previously published passed terminal, remains unchanged. The actual raw post-tail reader rejects the additive failure marker before accepting a previous tail.

Both restoration attempts run even when one fails. Existing `select` first-fatal semantics and canonical CleanupFailure handling are unchanged. MemoryError or non-Exception fatal identity survives later cleanup failures; a later first fatal supersedes an ordinary error. The marker is attempted once, and its own write failure is retained without masking an already selected fatal. If durable marker publication itself fails, the invocation still raises, and observed outer exit plus original failure evidence remain mandatory: absent marker alone is never proof of a successful invocation. Successful finalization writes no failure marker.

An inverse transformation that moves the marker try-block back into the post-tail exception handler produces the exact whole preparation01 outer AST. No other outer behavior, numerical code, admission mechanism, native limits, selected source check, sampling history or accounting changed. The worker, genuine Target hook, preclaim controller, native parser, strict oracle supplement and finite template renderer are byte-identical to preparation01. Copies in this directory are convenience snapshots; unchanged install origins still refer to their immutable preparation01 bodies.

## Source composition and finite templates

`source_inventory02.json` contains the complete sorted 169-target source inventory, 144 package entries and exact origin/body pins. Only `fixture_tools/refusal_outer01.py` changes its body hash and origin. `install-delta02.json` provides the precise prior and new row, with 168 unchanged targets. No capsule or Git commit is claimed.

`prepare02.py` verifies every origin, regenerates exact qualified source maps and all 27 sentinel template cases, and confirms protocol equality to preparation01. `qualified-registration-draft02.json`, `qualified-release-draft02.json`, and `generated-input-index02.json` contain source-only, unregistered metadata under `/qualified-unregistered-synthetic` and sentinel `a*40` with deliberately non-runtime metadata. The renderer is preserved verbatim. No input body population, actual runtime assertion or real registration has been created. Root must freeze genuine inputs and runtime separately.

The denominator remains 27 variants / 16 classes / 4 preclaim / maximum 23 claims / 17 Owners / 19 journals / 1088 prospective original array identity comparisons, separately from at most 129 scored pairs. The native policy and old source limitations remain unchanged: 3 GiB high=max, zero swap, two CPUs, host reserve, 1800 seconds, 4 MiB files, 8 KiB compact receipts, sampled 1 GiB writable tree and 10 GiB floor. Existing original authority documents retain their separate original bounds.

## Verification evidence

All checks used checkout-local `.venv/bin/python -B` and only stdlib/source/tiny metadata fixtures.

- `tail-RED01.log`: the seven corrected-contract tests run against actual preparation01 tail show four failures, two missing-marker errors and one success. This is the expected predecessor RED, not a real failed claim.
- `tail-GREEN02.log`: all seven actual extracted-tail tests pass against preparation02: ordinary restore failure, prior first fatal, later first fatal after ordinary post-tail failure, failed marker preserving first fatal, cleanup failure replacing ordinary error, clean success, and single post-tail failure marker after all restorations.
- `tail-genuine-GREEN03.log`: the same seven tests pass using the exact pinned selected stdlib owned_io.CleanupFailure class. This is source loading of owned_io only, with no research package import or real authority object.
- `parity02.log`: two tests pass: unchanged worker/parser/preclaim/template bytes and inverse-move exact full outer AST equality.
- `marker-reader04.log`: the actual pinned raw post-tail parser refuses an additive failure marker despite an older passed terminal in a tiny explicitly synthetic metadata directory.
- `adapter02.log` and `worker02.log`: six plus one inherited source/metadata tests pass, including the finite27 renderer and genuine Target-before-mutation source seam.
- `preparation02.log`: full source pin readback, exact sentinel template regeneration, unchanged protocol and explicit absence of numerical/research package imports.

The RED corpus and all logs are retained. No source/test failure was suppressed or labeled empirical evidence.

## Still unproved

Independent different-author review of this exact successor is required. Root must still compose later accepted primary metadata/source corrections, freeze genuine capsule/source/runtime/input/gate/release evidence, obtain observed fresh capacity and admit any real finite execution. All 27 actual native refusal cases, 1088 genuine array comparisons, actual Owner/journal effects, guard controls, process/cgroup cleanup and recoverability remain unexecuted. This narrow change does not resolve the inherited bounded inventory index's potential compact-metadata capacity refusal or establish cumulative suite storage feasibility. Imported resource completion is not scientific Published completion; no paper budget, original closed 512-sample work, training result or financial fit is changed.
