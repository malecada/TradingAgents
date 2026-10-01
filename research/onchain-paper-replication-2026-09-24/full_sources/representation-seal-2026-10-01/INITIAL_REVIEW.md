# Independent initial review — acceptance withheld

Read-only review of the current-owner publication/seal/output transition found three material gaps. No tests, jobs or empirical array reads were performed by the reviewer. Only this review was written. The saved preflight log establishes two passing helper/refusal methods in 0.117 seconds; it does not establish integration closure.

## RS1 — actual denominator checks are lost before the first seal

`seal.py:82–87` receives the completed publication proof, but does not retain or reconstruct the publication's actual registered denominator receipt. The final pre-seal checks at `seal.py:201–204` invoke the issued dictionary ticket, owner lease and new phase lease. Those do not replace the denominator receipt's checks of the actual ExampleManifest, Fold and exact resident graph objects/population. In particular, workload Route.lease checks its bound metadata; it does not rehash those objects.

A mutation or replacement after publication returns and before sealing can therefore leave stale denominator/lineage evidence accepted at the first terminal transition. Re-admit the actual denominator from the same registered route after publication and lease it immediately before the first seal. For the claimed in-process terminal contract, explicitly transfer the necessary object identities, graph hashes, manifest hash and Fold/descriptor checks to post-seal validation rather than invoking a now-invalid live owner lease. A targeted injection after publication returns should refuse before either seal. This counterexample is inferred from source, not an executed reviewer test.

## RS2 — archive enumeration allocates before the entry cap

At `seal.py:147`, `children=list(current.iterdir())` enumerates and retains the complete directory before `tree()` applies `max_snapshot_entries`. An oversized or foreign archive inventory can exceed the intended bounded metadata allocation before rejection. Enumerate incrementally, apply the remaining allowance before retaining each child and reject unexpected entries early when an expected inventory is available. Keep the existing type/link/device and directory identity checks. Exercise refusal before full iterator consumption with a small deterministic synthetic iterator or filesystem fixture.

## RS3 — own transition records trust post-write bytes

`seal.py:72–77` encodes the intended record, writes and syncs it, then derives its trusted SHA from the current file. A rewrite during the sync boundary can be adopted as the initial baseline. For example, the returned immutable receipt may describe the expected `final` record while its `seal_proof` reference names altered completion bytes. Start records have the same issue.

Compute the expected SHA from `raw` before writing, then require the bounded Metadata read to match that expected digest before adding the reference to `written`. The terminal journal and ResearchRun outputs already use precomputed expected hashes; use the same approach for the wrapper's own records. A deterministic sync-hook rewrite should demonstrate refusal and retained conflict/failure evidence. No such regression has yet been inspected.

## Inspected safeguards and limits

The implementation otherwise preserves distinct selected registered outputs, refuses prior attempts and unresolved latest pair work, snapshots admitted model-input content and extents, reconstructs exact terminal encodings, checks phase-specific journal inventories and output registry state, and keeps output writes outside the lifecycle lock held across sealing. Existing live owner/ticket refusals are unchanged. Historical pair-kernel payloads receive only their explicitly qualified directory/signature treatment, not numerical verification.

Acceptance is withheld pending correction, closed synthetic integration evidence and final bindings. No claim is made about cold or historical reuse, native lazy batch loading, physical quota, total RSS, financial accounting/timing, or empirical release.

Reviewed SHA256 values:

- `seal.py`: `cae81b440a4b66490c9031c73177e3892ecf9a08c1072bf95d3680af4a55e310`.
- `test_seal.py`: `b3506b3fcd048a7b7b6e194f62758953369ca20d8329e28a0e2909b829f8e8be`.
- `preflight-check01.log`: `76b4bf18c2c73647f504ca81434561737a3df613bbcb2a8a662ba326d463fd8b`.
