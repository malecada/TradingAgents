# Initial independent review — acceptance withheld

Scope: the proposed current-owner, unsealed representation publication and its transition from the accepted exact-prefix closure lease to post-append validation. Source and compact synthetic evidence were inspected independently; no tests, research jobs or empirical numerical files were executed or read. Only this review file was written. The full integration check01 was still active at review time; its result is not assumed.

## RP1 — stat-only handoff can accept changed predecessor content

`publication.py:40` records file signatures, and `publication.py:49–50` checks those signatures without reading content. After the old closure receipt is discarded at `publication.py:144`, these checks are the retained protection for graph/MCM numerical files. An equal-length overwrite can preserve all observed signature fields on the current filesystem and pass this boundary.

The saved `snapshot-check01.log` directly demonstrates this: `test_same_size_content_rewrite_refuses` overwrites a tiny synthetic file after constructing Snapshot, but `check()` returns successfully. The run closed with four methods, one failure, in 0.010 seconds. Other methods passed for the entry allowance, added/replaced directory membership and hardlink/symlink refusal. This is evidence of a content-drift failure; the log does not separately instrument which timestamp fields coalesced.

The same root cause remains at `publication.py:101–104`: the newly published scalar representation manifest is strict-inspected once, then only its signature is checked after completion-proof writing. That late-manifest counterexample is inferred from source and the observed signature collision, not yet demonstrated by a saved integration regression.

Required correction: retain and recheck bounded content hashes and exact extents for the predecessor files, with exact inventories and the existing path/type/link/device checks. Initialization must bind those hashes to the already admitted closure proof/component references and their array descriptors. Merely hashing whichever bytes exist when Snapshot is constructed would leave a window between actual numerical admission and snapshot creation: the inherited closure lease itself retains signatures for those arrays. The new scalar component must likewise be rechecked against its prebound canonical manifest hash after completion writing. Preserve the reproduced failure and source bytes, and exercise both initialization against admitted content and later drift. Hashing must remain bounded to the admitted extent plus an overrun check; resource and I/O scope must describe the additional streaming reads.

## Other inspected boundaries and evidence limits

The source selects the output policy through both registered routes, reserves the attempt exclusively, retains failed artifacts, precomputes the scalar manifest/event and completion-proof sizes before journal append, and checks the actual event and strict component against the expected values. The prefix-to-tail design retains the registered denominator receipt, issued dictionary ticket, owner/source and prefix metadata checks. No additional material source finding is asserted at this stage.

Acceptance remains withheld pending RP1 correction, closed integration evidence and final source bindings. This review does not establish durable saved-representation admission, journal sealing, ResearchRun output publication, historical or mapped reuse, physical quota enforcement, total process memory coverage, financial timing/accounting validity or empirical release.

Reviewed hashes:

- `publication.py`: `4430f6ab8d48254c3aeed9bf1a19e5ad1df9b5465e58ea834646e096c8372df7`.
- `test_snapshot.py`: `0886051a54c869e0bd55ed9af4c31aa5465a686d3c6ffea1360a0b2f0eaf55ef`.
- `snapshot-check01.log`: `4511f8b4a63e00bb1576302c8614d67da47bddfe9470dd78ee2a9d42033f117f`.
