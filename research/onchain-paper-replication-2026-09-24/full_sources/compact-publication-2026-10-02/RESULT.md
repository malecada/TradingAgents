# Compact durable metadata publication

The actual compact_closure.Receipt now publishes an exact binding and full closure
record under a fresh, exclusive onchain_compact_publications workflow/experiment
namespace. The registered plan and job must select the same publication policy.
All three success files and a possible failure record must fit their individual
metadata cap and a conservative four-file output allowance before the claim.

Predecessor bytes and exact inventory are rechecked before every exclusive write.
The last live callback is followed by original closure and callback-free owner
verification and exact saved-byte admission. Failed attempts poison the owner and
retain both partial files and any already-written completion file together with
the failure marker. The returned receipt remains tied to the current active owner.

## Retained synthetic evidence

- red01.log: 1 missing-module failure, 2 deselected, 2.75s; session29695 exit1.
- check01.log: 3 passed, 417.98s; session90914 exit0.

Actual registered two-graph fixtures verify exact durable binding content,
republication refusal, changed saved metadata refusal and a final Published.lease
callback that first succeeds and then revokes the owner. The latter must preserve
both complete.json and failed.json and cannot be retried under the same identity.
The pure type test refuses arbitrary caller objects. Guards are mocked and all
numerical inputs are synthetic. The reviewer executed no empirical work.

## Boundaries

No old-format FeatureJournal event, compact-owner terminal, representation seal,
ResearchRun output, native loader dispatch, cold reuse or financial fit is created.
This is durable metadata publication, not the terminal training handoff. Logical
output reservation excludes filesystem allocation overhead, all upstream retained
artifacts and transient/Python metadata allocations. Whole-workflow physical
accounting, registration amendments and independent admission remain required.

## Direct source hashes

- `tradingagents/research/onchain_replication/compact_publication.py`: `a620e5f84c2ec5095ae1715aae4a7962e64180075d139e424c671a2d486e935a`
- `tests/research/onchain_replication/test_compact_publication.py`: `413a5da987ecc2a78dd209ed2bb84b3f539903217d4ac373a5e6f6aa1bd8719a`
