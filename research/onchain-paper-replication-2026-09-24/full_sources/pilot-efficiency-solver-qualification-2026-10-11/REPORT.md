# Bounded NumPy edge agreement: complete synthetic solver qualification

The explicitly selected C05 route is functional through `ImmutablePairSession`.
The absent policy retains the original exact numerical route. This is ordinary
source engineering, not an empirical pilot, numerical admission, or paper result.
No raw inputs, dictionary cells, graph population or scientific settings changed.

## Selection and memory

`matching_numeric_policy.NumericAgreementAdapter` selects the fixed
`bounded-numpy-agreement-c05-v1` policy. Eligible uncached edge chunks contain
256–1024 entries; feature width is two or four, contiguous immutable float64,
finite magnitude at most256, and NumPy error mode must remain the exact default.
Both index vectors are copied into immutable bytes backing, at most16,384bytes
combined per call. Existing bounded helper scratch remains O(1024×4); no complete
edge-product matrix is materialized. Rough conservative additional numeric data
and transient index buffers are below256KiB per call, excluding the existing
solver state, array object headers, allocator/runtime and native libraries.
NumPy reduction/exp reassociation is explicitly C05 atol1e-8/rtol1e-6, not bitwise
scalar equivalence. No float32/GPU path or new threads are selected.

The exact existing lazy caches remain preferred. Scalar node agreement,
normalization, temperature/iteration schedule, ordered edge accumulation,
hardening, scoring, checkpoint state and operation accounting remain unchanged.
Refusal returns through the existing authenticated native edge lease, when
present, then the original scalar route. A refused NumPy chunk changes neither
output nor cursor; overflowing scalar/native fallback preserves its completed
prefix and poisons the state as before. Genuine source/runtime/Owner/claim
admission belongs to the enclosing caller; the adapter creates none.

## Tests and measurements

`TESTS01.txt` retains47passing focused tests; `TESTS02.txt` records the extended
53passing tests/2.07s. `TESTS03.txt` adds direct native telemetry and no-double-count controls:55passing tests/2.88s. Policy, helper, reference and composite checkpoint tests
cover directed/empty/tied/extreme features, method tampering, frozen tolerances,
injective assignments, operation chunks255/256/1023/1024/1025, overflow at an
interior chunk entry, checkpoint restoration and telemetry on/off parity.
The frozen scalar reference independently computes the full comparison outputs.
Tied outputs are assessed by feasibility and objective, not presumed unique
assignment identity. Existing exact-path checkpoint tests remain passing.

`qualify.py` and `RESULTS01.json` retain the fixed complete48-iteration corpus,
three current/selected runs per geometry, with actual compiled width-two edge
and compiled normalization source/library/runtime/ABI checks from the preserved
pilot35 binding. The current comparator includes the adaptive lazy cache and
one-million-operation call budget. Timings include graph construction/immutable
copy, state allocation, backend entry/body checks, per-advance state checks,
immutable index copying, normalization, hardening, scoring and cleanup. They
exclude real Run/Owner/lease/extraction-store/publication/offload costs.

| Nodes per graph | Edges per graph | Edge width | Median current/selected wall | Selected matching cells/s |
|---|---|---|---|---|
|3|7|2|1.053×|109.28|
|9|81|2|0.972×|8.98|
|12|144|2|4.237×|3.60|
|16|256|2|4.789×|1.18|
|12|144|4|10.882×|3.56|

The first two strata use the unchanged cache and do not use NumPy. Small-case
variation is not a material gain. Width-four current edge work falls back to
scalar. Every complete comparison passed C05 soft matrix/score, identical
operation cursor sequence and assignment feasibility. Peak process RSS was
383,884KiB; accumulated timed wall29.687s. These finite results do not prove the
pilot memory bound or whole-pilot throughput.

`crossover.py`/`CROSSOVER01.json` separately include immutable index-copy cost and
use the actual hashed native edge library. Native/NumPy ratios at counts
8/32/64/128/256/512/1024 were0.263/0.839/1.494/2.807/4.653/7.650/10.947.
The premeasurement256-entry threshold remains unchanged. The smaller favorable
threshold is not adopted from these outcomes. This crossover is a component
diagnostic, distinct from the complete solver table.

## Currentness, telemetry and remaining joins

Session checks pin the adapter class, constructor and fill/current/snapshot
functions, helper functions, relevant NumPy function identities, immutable graph
buffers and explicit selection. Replaced or shadowed adapter functions refuse
before state mutation. Existing real source/runtime and native lease checks
remain. The final source snapshot additionally includes the session's stronger
fill-seam identity check added after the benchmark; the55-test run covers it.
That identity comparison and the later legacy-native success counters are not claimed as newly measured performance results. The numerical bodies and selection threshold remain unchanged. `SOURCE_SNAPSHOT02.json` identifies the final source.

Telemetry is opt-in. `state_scan` measures genuine mutable-state validation.
Chunk histograms count attempts; scalar counters count completed individual
agreement calls, excluding cache copies. NumPy counters count accepted complete
chunks/entries and fallback counts record refusal attempts. Native counters now cover genuine True acceptance from direct legacy dispatch and selected-adapter fallback. A success-only local progress marker prevents counting NumPy as native or counting native fallback twice. `RESULTS01.json` predates the direct-legacy counter addition and consequently lacks that baseline counter coverage. Partial failing native chunks
are not credited as completed native chunks. Telemetry makes no authority claim.

Root integration must authenticate the new policy/helper/session/annealing bodies
in the actual runtime closure, join this explicit numerical policy to successor
configuration/continuation contracts, and separately prove genuine currentness,
resource/admission, publication/offload timing and exact preservation. No claim
that these synthetic rates sustain415,968,128pilot cells follows. Complete pilot
feasibility and all paper financial fits remain pending.
