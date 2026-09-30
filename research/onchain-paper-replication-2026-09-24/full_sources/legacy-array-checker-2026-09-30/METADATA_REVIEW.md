# Independent compact metadata adapter review

Decision: accepted for the declared pure adapter scope, with the test-coverage
qualification below. No empirical-array execution is released by this review.
Reviewed against checkout HEAD `697c08d533b5489d035bfc9f495d9d621dcd5c6d`.
Only this review file was written; no tests, producer jobs or verifier were run.

The actual source was inspected independently. All 31 retained compact JSON
files were read and their hashes and byte lengths independently compared with
preparation SHA256
`a070b530842873b78fe144402405f613fe8a2e6625bf97600b5512b8dc0eb62e`.
Independent reconstruction confirms the complete 109-cell identity set and
7 complete/102 unavailable dispositions. The original pilot claim remains
FAILED. Its claim/terminal, source, supervisor/guard, observer and retained
closure joins are consistent with the adapter's checks. Complete graph phases
are not promoted to a complete overall claim.

Both graph phases join the retained intent/result/manifest, original source
index, seven contiguous daily members and reconstructed external coverage.
Raw configuration binding and canonical configuration identity are distinct
and agree with the actual receipts. The January graph declares 2,049,095 nodes,
3,182,055 directed edges and 8,373,297 raw rows/4,415,050 admitted rows. The June
graph declares 1,768,268 nodes, 2,518,332 directed edges and 7,581,093 raw rows/
3,601,893 admitted rows. Each row denominator reconciles admitted plus excluded
rows. The ten array declarations total 1,037,092,456 bytes; their names, paths,
declared hashes and extents join the saved manifests. These are declarations,
not independently verified array content.

One non-blocking test-evidence limitation was found at
`test_metadata.py:25`, `test_metadata.py:42` and `test_metadata.py:51`.
The mutation helper updates only the changed compact object's preparation pin.
Removing a ledger row consequently fails the stale closure/observer ledger
hash join at `metadata.py:75` before reaching the denominator check. Reversing
coverage members fails the stale graph coverage reference at `metadata.py:107`
before reaching daily-order checks. These tests demonstrate refusal, but do
not independently establish the named semantic protections. For specific
regression coverage, propagate the affected reference hashes in the in-memory
fixture and assert the intended diagnostic. The relevant production checks
are present and the fixed real receipts satisfy them; this gap does not block
the narrowly pinned adapter acceptance.

Reviewed evidence identities:

- `metadata.py`: `15badf51b087f19b0a483cc69dca8dbc8c9587ea5ef26ec72fb8233add4db520`
- `test_metadata.py`: `d116ffeeed9d6986df911bd47253dbca2d9ef236e0fd618ffa2ca690c0f51516`
- `metadata-red01.log`: `17a72f05570eaaecd7c15ac138d31671d3490340a2a1e26565fbdacddf05899f` (ten missing-implementation failures retained)
- `metadata-green01.log`: `b6777d1afddb391e4f5fd870c9bbdc3b833d85b9677f71608b71335a17c98b97` (ten passes, 0.067 seconds, observed saved report only)
- `METADATA_SCOPE.md`: `184fa704e76401491d42baf4e0bf0067d6232c337f002f7b2b4c816409ca58fb`

Acceptance depends on the caller independently binding the exact preparation,
source, configuration and runtime. The validator does not authenticate its
caller-supplied preparation, perform filesystem reads, acquire ownership or
protect files against concurrent changes. A future wrapper must supply those
guarantees and separately admit any array reading. No empirical arrays,
SQLite databases or source bodies were read in this review. Actual saved-array
numerical correctness, transaction uniqueness, value/exclusion semantics,
future execution cleanup, resource adequacy and financial performance were not
tested. No budget, ledger, historical policy or empirical outcome was changed.
