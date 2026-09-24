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
