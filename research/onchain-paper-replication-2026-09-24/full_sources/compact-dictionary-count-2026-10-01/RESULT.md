# Dictionary capacity versus exact completion

The compact owner now supports an explicitly selected
`capacity-with-exact-completion-v1` dictionary contract. Both registered producer
plan and execution job must select `compact_dictionary_count_policy`. Before
stage allocation, `begin_dictionary` derives the conservative comparison and
matrix-entry capacity from the registered dictionary dimensions, pins its
configuration hash and complete capacity record in the stage intent, and reserves
the full matching-evidence allowance.

Completion requires a separate integer actual count within that capacity. The
completed compact PairLog must independently contain exactly that count with no
pending pair. Missing, boolean, negative, excessive and in-range false counts
are refused. No reservation is refunded. Existing exact-count dictionary/MCM
stages retain their original semantics and cannot supply a lower denominator at
seal time. Aggregate closure sums verified actual completions, not capacity.

This distinction preserves the existing dictionary algorithm: identical ordered
sample subsets share an already-complete distance matrix. Counting a shared
matrix as fresh matching would invent comparisons; requiring the conservative
upper bound as the completion denominator would reject valid completed work.
No matching equation, clustering choice, sampler or financial configuration is
changed. This capacity contract alone does not establish that the producer
performed the entire scientifically admitted dictionary workload.

## Independent investigation

The reviewer constructed a bounded synthetic constant-score example with five
samples, two motifs, partition threshold two, partition size three and seed12.
The conservative bound is22 directional comparisons/36 matrix entries across
four levels. The actual workload makes20 comparisons and retains32 unique
entries because final subset `[0,4]` reuses its earlier matrix. Investigation-02
retains exact visits, comparisons, source hashes and the109candidate search count.
It is orchestration evidence with constant0.5 scores and a manually constructed
SampleManifest, not numerical parity or sample-draw provenance.

The first investigation's frozen-hierarchy JSON serialization failure and partial
bytes, including incomplete JSON/trailing whitespace, are preserved verbatim.
Source/document whitespace checks exclude that failed output and raw logs.
Corrected investigation-02 result SHA-256 is
`aefcb3d800365edcbf6860d71719808ecd9144c223124253d0fcade2a5ac8f69`.

## Fresh verification

| Identity | Result | Evidence |
| --- | --- | --- |
| red01 | 7 missing-API failures,79.18s,session86164 exit1 | `red01.log`, `test-red01.py`, `owner-before.py` |
| check01 | 7 passed,100.86s,session21701 exit0 | `check01.log`, `test-check01.py` |
| check02 | 2 passed,6 deselected,41.24s,session2453 exit0 | `check02.log` |

Check01 uses actual checkpoint-engine matching over identical-feature isolated
neighborhoods. It verifies20 actual comparisons against22 reserved comparisons,
32 retained distance entries against36 capacity, dictionary identity agreement
with scalar scores, and six argument/selection/exact-mode refusals. Its descriptor
seed remained the fixture default11 while samples used12; those bytes remain
preserved without any registered scientific-seed claim.

Check02 explicitly aligns descriptor/sample seed12 and required graph identity.
Its positive case constructs the actual20-comparison dictionary, feeds that
dictionary into an actual ten-comparison MCM, and closes the owner with exactly
two stages and30 actual comparisons, rather than32 reserved-capacity comparisons.
Its negative case supplies an in-range count1 for an empty completed log and
verifies refusal at the saved-log denominator join, poison and no stage receipt.
The maintained source is unchanged between check01 and check02; the test changes
extend and correct the evidence. No combined current eight-case run is claimed.
Independent `REVIEW.md` accepted this count contract, SHA-256
`efc141efd92859f1b0183649dbcbd99b4e1cb6b0a738e199c5bb8211c99da0e3`.

The ResearchRun registration, source/input checks, first-owner Binding and compact
matching evidence are actual. Kernel guard enforcement is mocked. Samples are
generated with the existing sampler but lack the new compact durable sampler
publication/admission path. Representation admission remains false, the
FeatureJournal remains unsealed, and no resource pilot or financial fit occurred.
Coverage remains77/109 and all1420 financial fits remain pending. Next implement
the compact admitted training-sample route and dictionary producer/publication,
then join numeric outputs and neural features into full representation closure.
