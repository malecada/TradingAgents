# Compact sampled numeric publication

The maintained `compact_samples.py` publishes numeric components only from an
actual current compact Draws object. Registered execution job and producer plan
must both select the same `compact_samples_input`. The selected policy, Binding,
training record, draw receipt and resident sample fingerprint are joined to the
new artifact context. The strict reader's preserved source must be separately
committed and admitted. No random selection is performed by publication or reading.

Before creating an exclusive attempt, the publisher estimates the exact component
manifest, NPY headers and numeric bytes under the existing component-store format.
Intermediate metadata construction has a running lower-bound cap; the final exact
manifest must fit at most 2 MiB. The artifact allowance plus three bounded receipts
(start, completion and possible failure) is reserved without refund. Original and
loaded numeric arrays require twice the retained payload allowance. This excludes
Python metadata, I/O scratch, graph parents, filesystem allocation and process RSS;
outer registered guards and later whole-workflow accounting remain necessary.

The component reader verifies the complete manifest, exact inventory, array shapes,
types, headers, byte counts and hashes before payload allocation. Loaded arrays and
metadata must exactly match the original resident samples; byte-view chunks avoid
an array-sized equality-mask allocation. Full checks join current source/training/
draw authority with the original live result and retained artifact. There is no
reopen or cold-load admission API. Failures preserve partially written files and
poison the compact owner; existing complete and incomplete attempts are refused.

## Retained synthetic checks

| Identity | Outcome | Evidence |
| --- | --- | --- |
| red01 | 1 missing-module failure, 8 deselected, 23.47s, session2623 exit1 | `red01.log` |
| check01 | 1 failed, 8 passed, 244.19s, session65740 exit1 | `check01.log`, `samples-check01.py`, `test-check01.py` |
| red02 | 3 failed, 9 deselected, 87.92s, session28076 exit1 | `red02.log` |
| check02 | 5 passed, 7 deselected, 152.72s, session38337 exit0 | `check02.log` |

Check01 proved successful exact saved numeric publication and reading, source/
route/size refusal before namespace creation, retained partial-write failure,
duplicate attempt refusal and late reader-file mutation refusal. Its allocation
trap patched shared NumPy `empty`, unintentionally blocking PCG64 state metadata
before reaching the artifact reader. The corrected trap replaces only the strict
reader's NumPy view; normal RNG metadata operations remain allowed.

Independent REVIEW_INITIAL identified two additional callback gaps: a final lease
could mutate original resident samples or draw evidence after numeric equality,
and a post-sizing lease could grow resident arrays before the writer. Dedicated
regressions reproduced all three attempted paths. Corrections now verify pinned
resident samples and draw files callback-free after the final live callback,
then the new artifact. Before the numeric writer, the same pinned draw/sample
verification plus the exact saved start check follows the last external callback.

Check02 verifies the positive publication/read path, the isolated preallocation
refusal and all three callback regressions. Earlier passing refusal/preservation
cases remain separate evidence; no combined final-source twelve-case run is
claimed. All engineering checks are terminal.

## Scope and next requirement

Fixtures use the real temporary research registration, source admission, Binding,
compact Owner, Training and Draws routes with mocked kernel guard surfaces and
an inherited supplied two-train/two-test-row population. This does not establish
complete calendar/denominator, price/label reconstruction or measured full-scale
physical resource use. Numeric sample publication is true in its receipt;
scientific sample-provenance admission is explicitly false.

Next join the saved draw records and numeric artifact to the actual bounded
induced training neighborhoods, selected-index hashes, retained-byte prefixes,
registered configuration and exact dictionary workload scope. Preserve the
admitted core's weighted-selection/RNG lineage and existing independent sampler
oracles. No arbitrary SampleManifest may replace this current-owner proof.
Dictionary production, representation closure, native selection and reviewed
committed resource amendments still precede empirical execution. Coverage77/109
and all1420 pending financial fits remain unchanged.

Independent [corrected review](REVIEW.md) accepted this bounded contract.
The [initial findings](REVIEW_INITIAL.md) remain preserved. Final review SHA:
`e726625744c7a856f7c575c87646f688ef51db11c8cdbec7c8403763b0186626`.
