# Independent compact training admission review

Accepted for the bounded registered resident-population join described below. No remaining material blocker was identified within that scope. This is not sampler, complete-calendar, native producer or empirical admission.

The review read the maintained implementation, current and preserved tests, saved failure/success logs, and the relevant owner, descriptor, dataset, calendar, graph-hash and original workload-route contracts. No test, financial experiment, historical job or empirical array read was performed by the reviewer. Only this review note was written.

## Corrections and evidence

1. The original `_science` passed a datetime to `expected_week`, whose UTC parser accepts strings, and compared differently formatted timestamp strings. `check01.log` retains the positive-path failure and deliberate interruption: 1 failed, 2 passed in 126.57 seconds. Current `compact_training.py:119` uses `stamp(step)` and compares normalized UTC instants. This repairs both the API mismatch and `Z`/`+00:00` equivalence.
2. The initial lease checked route configuration only before the external owner callback. `red02.log` demonstrates that callback changing `_seed` was accepted: 1 failed, 11 deselected in 15.77 seconds. Current lines 165–176 check pinned owner/graph references and configuration both before and after that callback, then join owner identity and Binding hash.
3. The original duplicate-week test compared raw start strings. Two separately registered graph identities for the same UTC start, expressed as `Z` and `+00:00`, could both enter the training population and duplicate sampling exposure. `red03.log` reproduces this: 1 failed, 12 deselected in 15.65 seconds. Current line 92 compares `utc(g.start_utc)`. The new test registers the additional graph and asserts raw-string uniqueness versus normalized duplication before requiring the specific duplicate-week refusal.

`red01.log` retains 8 missing-module failures in 94.69 seconds. `check02.log` records all 12 then-current cases passing in 169.87 seconds, including actual registered admission, metadata refusal before graph iteration, altered graph/example/config/fold/seed refusal, future input rejection, terminal-owner revocation, full resident graph/example drift checks, admission-before-stage sequencing and the late lease regression. The final source differs from its preserved check02 version only in normalized duplicate-week uniqueness. Final `check03.log` records 2 passed, 11 deselected in 30.28 seconds: successful actual admission and the new equivalent-timestamp refusal. A combined final-source 13-case run is not claimed.

## Accepted contract

`_metadata` joins the actual compact Owner and current Binding to the same selected execution-job and producer-plan backend, training input, descriptor and graph-input references. The training control is an exact schema with a full supplied ExampleManifest hash. Graph manifests are read with the existing ancestry reader's registered hash, containment, type, same-device, single-link and per-file size checks. Full Owner boundaries bracket admission and full checks; compact metadata reads between those boundaries do not repeat a complete source scan per manifest.

`_science` recomputes the representation descriptor and actual resident graph hashes, validates supplied example membership hashes/order and fold/input/label clocks, joins each input date to its expected available weekly graph, refuses normalized duplicate weeks, and derives the same ordered training-only graph selection used by `sample_neighborhoods`. Dictionary settings retain the registered configuration with explicit fold training bounds; capacity and available-center checks precede sampling. Exact required Owner type, nonblocking transition lock and refusal after stage creation prevent admission through a foreign owner or an already-started matching workflow.

The receipt exposes read-only public views and frozen configuration/record mappings. Full `check()` rehashes resident graph/example inputs and rechecks source/input authority. Cheap `lease()` checks current ownership and pinned route views under the explicitly frozen-input contract; it does not rehash every resident array or ExampleManifest on each future draw/comparison. This is an in-process contract, not protection against arbitrary replacement of private methods or coordinated private-state forgery.

## Limits not established

The inherited `population()` fixture deliberately retains only the first two train and test rows from `build_examples` and recomputes their membership hashes. Exact registration therefore proves the supplied rows, not the complete calendar, exclusion accounting or full-fold denominator. Calendar/coverage reconstruction, Fold member-hash derivation, exact daily lookback completeness, price/label correctness and price-source reconstruction remain separate admission obligations. Graph-source hashes are joined to the supplied registered population; raw-data semantic recomputation is not performed here.

No neighborhood draw, weighted RNG provenance, durable sample proof, dictionary matching, native dispatch, output publication, cold/historical reuse, physical quota, process-RSS bound, full-fold throughput or financial result was tested. The fixtures use real ResearchRun/Binding/compact Owner machinery with mocked guard surfaces. Existing ancestry metadata-reader behavior is inherited; no new hostile-filesystem race or nonblocking-open guarantee is claimed. The receipt correctly records `sample_provenance_admitted=False`.

## Exact reviewed bytes

- Maintained `compact_training.py`: `812c2db5aba9fb9797b42ffe687467c608280b9579c382d436aab2c201ee98c3`.
- Current `test_compact_training.py`: `29261c98b51fd0051217b7d0d0b03352fa0587f0bc8ec6195a608fe55c62cb6c`.
- Preserved `training-check01.py`: `cc59a14e62d5ad3a0ac0503ed3e2694af1dd27bc21694c8c63d5e57f3ccdc75a`.
- Preserved `training-red02.py`: `81dafc4a58715e66c9f9bebc8ff5e36158f2fd1209d89e2304a7d00bb3515316`.
- Preserved `training-check02.py`: `63e30eebb34c81399e19d98ea7abddbc06e7211221913c153d6da75293bda937`.
- `red01.log`: `553d4fe73f3edd4a2a895a5382315bab201ee2e4da5f1aaaabd63540852ca717`.
- `check01.log`: `33a346bb39aba233d06f1260c91970958cadfa43b5a0f74f57280a62e6d5b363`.
- `red02.log`: `c00110b172d1e2757abf6d41ec0280d7c126119a425a0f816d69b2234a61b8aa`.
- `check02.log`: `cc9a88e6252caf152f450ee8fdffa9c4ba466a596bff3f58669d084853672c8c`.
- `red03.log`: `13693433cbb33b00a3a9642e5963b3c85cc176176f48f789823d30e8b46ec227`.
- `check03.log`: `e2281ff88d7c30acd7aaebee2fa93826f144a88a1ebb7ea3cc7ca2efcedfcbc5`.
