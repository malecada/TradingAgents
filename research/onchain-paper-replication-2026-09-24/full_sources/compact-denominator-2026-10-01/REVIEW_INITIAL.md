# Independent initial review

Acceptance withheld pending CDEN1 and terminal correction evidence. Review is read-only; no tests or numerical/empirical jobs were executed. The first five-case adapter check was active during source inspection.

## CDEN1 — lookback expansion precedes the known mismatch refusal

`compact_denominator.py` checks that registered `calendar.lookback_days` is a positive integer but does not bound it or first compare it with the admitted example step counts. The preserved validator's `input_dates()` constructs a tuple of one date string per lookback day, and the included-row branch invokes it before its row-length equality check.

A registered configuration with the otherwise identical synthetic fold/coverage, `max_calendar_days=64`, a representable lookback of 500,000 days, and actual two-step examples reaches a 500,000-string expansion before rejecting the mismatch. Fold reconstruction does not prevent this: the Fold member hash covers the fold row and coverage, not the lookback field. Extremely larger lookbacks can instead overflow datetime; that incidental bound is not the registered metadata allowance.

Required correction: reject disagreement with actual admitted input-date/price/graph/availability lengths before calling the validator and enforce a stated bound on configured lookback expansion, including the exclusion-only path. Preserve the original validator unless an explicit successor change is intended. A small synthetic trap around validator expansion can prove prompt preflight refusal without allocating a large tuple. The exact chosen cap must be recorded honestly; silently truncating lookback is not acceptable.

## Other scope observations

The adapter binds actual Training authority, selected plan/job input names and exact descriptors, source-admitted preserved validation code, registered fold/coverage identity, actual graph metadata and the full ExampleManifest hash. Its returned lease rehashes original examples/fold/graphs after the live Training callback. The retained validator accounts for all calendar dates, train/test rows and exclusions and checks per-input graph clock/order and the exact required union. Price-based exclusion reasons remain explicitly unverified and are not evidence of independently reconstructed price availability or labels.

`test_original_population_rechecked_after_final_callback` patches every Training lease. The mutation may occur at the first callback, so it supports callback-induced population-drift refusal, not specifically the final-callback boundary. No dedicated final-timing claim is warranted from this case alone.

No graph completion, sampler proof, representation/native admission, financial fitting, cold reuse or full-process memory bound is established by this metadata-only component.
