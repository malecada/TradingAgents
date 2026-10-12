# Verification overhead census

Bounded source-only findings. No admission, historical verification matrix, numerical run, network request, source edit or launch was performed. Main at investigation was reported as 2d9a078861281135fb837d181e263f7ad21b841a. Source manifest records bytes at publication; parallel source work may continue.

## Exact call graph

`imported_authority_lease.Lease._full` (219–228) invokes `ImportedExecution.check` (`original_import_stage.py:163–179`). That check retains two Prepared checks around intervening content/metadata work: entry through stage.lease, then explicit final check at173. `original_import_preparation.Prepared._check` (74–84) calls Binding.check, original-capability checks, current selection reads and candidate-source hashes.

`matching_owner.Binding.check` (219–224) performs run._active, run._check_source, run._check_inputs, fresh numerical-source/Git-anchor verification (`_source`,255–270), runtime inventory, and live Binding.lease. `lifecycle.ResearchRun._check_source` (145–156) calls admit and compares returned registration/experiment/input/binding contracts. The cheap `_active` (134–138) hashes the own claim and checks terminal markers; it is not source admission.

## Fresh current proof versus historical proof

`admission.admit` (350–418) checks current HEAD, committed/current registration and charter, design ancestry, helper runtime hashes and current source bytes. `_source_files` (107–175) uses fresh bounded Git size/body transports and current working-file comparisons. Bound.check separately hashes registered input bytes and checks numerical source/runtime.

`admit` at440 invokes claims across all run directories. `claims` (306–328) calls `verify.verify_claim` (275–355), which freshly reads claim bytes and historical Git registration/design, extension/review, source/charter/selection, binding and capture-manifest bodies. `_verify_sources` (184–216) checks actual returned body SHA256 through `_verify_batch` (141–161), not just object names. This is not verify_run: historical output trees are not scanned by claims. claims checks contradictory terminal markers.

`admit` (443–475) freshly recomputes relevant families, used count, parent and exposure history. `budget_extensions.effective_budget` (44–87) freshly joins the selected extension snapshot's claim/terminal bytes, adopted ceiling and first-adopter/frontier requirements. These current budget checks must remain distinct from historical parsing reuse.

## Proven call counts and measurements

The preserved first-batch census establishes two historical sweeps per ordinary full lease. One composite batched boundary has three forced full leases plus one direct Owner boundary: seven source admissions. Original39's sealed batch delta had19full leases ×2 plus4direct Owner admissions =42source admissions,370.972752exclusive wall seconds. Composite authority_boundary was85.299795exclusive seconds; pair_numeric48.361941seconds. These disjoint phase rows must not be added to inclusive callback timers.

The existing115-claim benchmark recorded7.445166seconds sequential versus5.560611seconds two-worker means,25.31247% component reduction. It used two samples per mode on CPUs2/3, with unchanged fresh transports and equal ordered-record digest. It does not establish whole-admission/job speedup, simultaneous memory, or transaction-sharing gain. Do not multiply these separate-epoch component means into a claimed measured original39 attribution.

## Sharing boundary and semantic limit

A private transaction confined to one genuine ImportedExecution.check, or separately one composite boundary, is the narrow candidate scope. No existing success-proof transcript/rejoin API supports replacing historical proofs with cheap snapshots. Deterministic parsing/comparison derivations could be shared only after fresh historical Git-byte rejoins at the original checkpoints; that preserves proof timing, with unmeasured savings.

One historical proof followed by only claim/frontier checks is an explicit change in historical-proof sampling. Fresh directory rosters and exact claim/terminal bytes detect persistent metadata replacement and concurrent new claims; fresh budget/exposure aggregation is still required. They do not prove historical Git unchanged, and current source checks do not cover every old commit. File-stat or refs fingerprints are insufficient for original fresh-body semantics.

The lifecycle flock (`lifecycle.py:76–83`) coordinates cooperating writers only, does not lock Git or exclude external writers, and cannot simply surround existing nested read_input locks without deliberate reentrancy handling. Context/thread/run identity, bounded lifetime, fatal propagation and no grant before final rejoin are necessary. No cross-call success cache or persistent Git reader is supported.

Full historical entry and exit proofs retain endpoint detection, but omit an intermediate change-and-restore observation if intermediate checks are removed. This must be labeled changed sampling/failure timing. Ordinary two-Prepared entry/exit remains2→2 and saves zero sweeps. A composite7→2 can save five sweeps only under separately selected/reviewed changed semantics; no gain is measured. Parent has chosen to investigate explicit changed historical sampling, not to call it an equivalent Git cache.

## Evidence reused

- `research/onchain-paper-replication-2026-09-24/full_sources/pilot-first-batch-hotpath-census-2026-10-12/FINDINGS.md`
- `research/onchain-paper-replication-2026-09-24/full_sources/pilot-claims-parallel-readonly-benchmark02-2026-10-12/INTERPRETATION01.md`
- Independent boundary challenge: `research/onchain-paper-replication-2026-09-24/full_sources/pilot-verification-overhead-boundary-review-2026-10-12/` (separate reviewer; not a new empirical proof).
