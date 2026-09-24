# Incremental independent implementation review

Tasks2–3: separate read-only reviewer independently reproduced four defects in
synthetic fixtures. Corrections before empirical use:

- Expected complete weeks are enumerated from declared coverage; empty source
  streams and absent expected weeks fail explicitly. ETH member status/count and
  expected per-member/total decoded counts are mandatory. Actual retained source
  inventory/date/block bindings still require stage-specific admission before
  decoding; adapter checks alone do not establish canonical-chain completeness.
- Aggregate-edge≤transaction inequality now applies only to ETH. BTC proportional
  projection can have more edges than transactions; its own rational conservation
  remains Task10's responsibility.
- Artifact directories and price intents synchronize parent directories before
  subsequent work. Newly created ancestors are synchronized too.
- Graph array buffers now use immutable bytes; attempts to reenable writes fail.

Four regression examples failed before the corrections, then passed.29 data-layer
checks pass. The original Task3 completion covers synthetic adapter software only;
C03 real source coverage and C04 real source-to-graph reconciliation remain pending.
No empirical data was decoded by the reviewer or implementation tests.

Task4: scalar Eq1 scores checked against independent exhaustive assignments through
four nodes; literal one-step half coefficient and48-step schedule tested. CPU
float32 tensor scores and soft matrices match within C06 tolerances on current
fixtures. GPU check skips explicitly because CUDA is unavailable; C06 GPU evidence
and full-size execution remain pending. Independent math review in progress.

Task4 independent review found a float32 iterative-roundoff failure outside the
initial fixture corpus. The retained regression failed before correction. A new
pre-result precision amendment preserves original protocol bytes and declares
float64 internal matching with float32 outputs.44 focused checks now pass,1 CUDA
check remains skipped. No objective or tolerance was changed. Active matching
configuration: config/matching-stable.json via protocol-freeze-v2.json.

Task5 independent review found mutable nested sampling/dictionary metadata and
partitioned clustering ties resolved by chunk order instead of original sample
order. Immutable nested records, content-bound dictionary identities, stable
original-ID ties and expanded memberships now have retained regression checks.
Task5 small synthetic tests pass; whole-graph sampling storage and speed still
require measurement and cannot be inferred from these fixtures.

Task6 independent two-head directed GAT scalar calculation (including mixed-sign
logits) agrees within1.39e-16. The frozen full architecture and initialization
match implementation. Two retained failing regressions caught an entirely masked
batch graph disappearing at pooling and NaN padding poisoning MLP gradients.
Both were corrected before fits: contiguous original batch IDs remain required,
empty admitted graphs reject, and masked inputs are zeroed before the MLP.
53 focused tests passed,1 CUDA parity check skipped at this checkpoint. Full
post-change offline validation and empirical scale checks remain pending.

Task7: independent review found no clock leakage in the frozen expected-week join,
label purge or unique training-input scaler. Retained fixes reject regression
broadcasting and contracted prediction batches, preserve constructor failures,
recover a final-epoch checkpoint without refitting, and prohibit continuing a
completed cell even when another cell caused the enclosing run to fail.
Synthetic registered Git fixtures exercise original and new continuation claims;
interruption after epoch1 and after finalepoch3 reproduces uninterrupted weights
and loss logs exactly. Original claim identities remain consumed. Real worker-death
proof and exact empirical factory/input membership still require release review.
Task7 pure checkpoint tests also reject corrupt bytes, absent RNG and provenance
mismatch. No empirical fit has been performed.

Task9 software review: independent four-chunk HLSTM calculation matches exactly;
asymmetric classification/regression fixtures and within-year moving-block
bootstrap match the frozen conventions. Actual baseline fits and comparison
coverage are pending. Resource guard review and synthetic containment evidence
are recorded separately in the forthcoming resource amendment.
