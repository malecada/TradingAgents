# Independent failed-primary recovery review — 2026-10-03

Disposition: **accepted for the exact external-recovery scope below**. No material discrepancy was found between the selected remote blobs, retained archive, separately recovered tree, and preserved failed claim. This is recovery verification, not a successful experiment, new launch permit, or validation of MCM output.

## Exact reviewed evidence

- `REMOTE_FAILED_PRIMARY_RECOVERY01.json`: SHA-256 `ece5bfc599a351d1caf077d73296fac880c2a513548064f8ef81354be4205830`.
- `recover_failed_primary01.py`: SHA-256 `cea2ae9584c9e685a43d452c31f0ca609d54e690536b5afca75618b6b7ae616f`.
- Actual recorded remote commit and independently checked bare `FETCH_HEAD`: `0325504b48fe0270734e20e1d0b67a1ffe738738`.
- Failed capsule HEAD: `529c7a3769fcfea28d3a617270b3025aebbce1f5`; numerical source anchor: `5c41d44b9d9a803d456af45d6de6844e392bf21b`.
- `EXECUTION_PRIMARY01.json`: `8828c2b0dc248d0937ef78232210674ab69d3661ed8b2694042018f990d5ac7b`.
- `RETAINED_PRIMARY01.json`: `23efc546928547341204b0a31d570af4b9d2b9f8c1cd57a53e6b28a84fc5d8c7`.
- Archive SHA-256: `9516fdec7f532a6765c150d1e2396f25bc1e5369d82488c6ddfe81b326898f12`, exactly 2,279,073 compressed bytes.

The recovery source was read rather than executed. Its successful receipt records an actual `ls-remote` comparison before creation of the fresh bare repository, a depth-one partial fetch of the fixed commit, subsequent selected blob retrieval, and exclusive creation of the separate recovered archive/tree. The network provenance claim rests on that completed root-owned operation and its exact source/receipt, not merely on a configured remote or a local Git object. This independent review performed no network operation, refetch, extraction, recovery rerun, numerical import, admission, or job launch.

## Independent reconstruction

A separate stdlib-only read-only verifier used `git show` with lazy fetching disabled, terminal prompts disabled, optional locks disabled, and Git transport prohibited. All 13 selected blobs were reread from the already-fetched `failure-recovery01/repository.git`, compared against the receipt's byte counts and SHA-256 hashes, and compared byte-for-byte with the same fixed commit in the original repository. The check used the fixed recovery commit rather than assuming current branch HEAD remained unchanged.

The archive was independently streamed without extraction. Every member name was unique and matched the complete manifest inventory; modes, regular-file sizes, and SHA-256 bodies matched. Every body also matched the separate `failure-recovery01/recovered-failed-capsule01` tree and original failed capsule. The recovered tree's complete recursive inventory contained exactly the manifest's members, including its root. There were no symlinks, archive hardlinks, unexpected entries, or multiply linked recovered regular files.

| Retained quantity | Independently verified value |
| --- | ---: |
| Complete archive/tree members, including root | 701 |
| Regular files | 495 |
| Directories, including root | 206 |
| Regular-file logical bytes | 5,448,369 |
| Original recorded allocated bytes, including directories | 7,536,640 |

The allocation figure is the sum of the original retained manifest's per-entry allocation records, previously checked against the original filesystem in the failure investigation. It is not a claim that restored filesystem block allocation or inode identities equal the original. Recovery preserves names, types, modes, bodies and evidence of original allocation; it does not recreate live capability identity.

The recovered Git HEAD was checked directly. All 153 selected source bodies matched their declared hashes and the recovered original capsule commit. The 142 package bodies additionally matched the numerical anchor commit. All 26 historical `commit:path` source bodies were read from recovered Git and matched the original input index, and all 11 original JSON inputs matched their declared hashes. The registration file matched its admitted release hash. The release and retention bytes also matched the failed execution record's exact pins. These are byte/provenance checks, not a second execution of schema admission or scientific calculations.

## Failed disposition is preserved

The recovered claim SHA-256 is `f475dd6c04d7dfc5e9d94bba30b5d3e686d1b71b5f5394dfa1aa0b174797f61e`. Its source and registration join the frozen release; `failed.json` joins that exact claim and records `ValueError: compact metadata bound`. No successful claim completion exists. All four recovered output bodies match the failed terminal's output-hash map and the recovery receipt:

- `cell-ledger.json`: `cc5a6afe2c94c8495f99e70da93e6ce4aa4c386b0b42d60740513cbec5cd4691`.
- `resource-binding.json` and `resource-journal.json`: each `1578d59cfdf12c20215bd21db258d841fb6aba00fc63a9e6a9e278472456932b`.
- `resource-summary.json`: `40c69a9802f6e4c5c29ffbd4fcc1273673a4324b165913c68da0104552888ac6`.

The complete two-cell ledger remains first target **failed**, second target **unavailable**, with the same metadata-bound reason. The real dictionary import receipt remains present with SHA-256 `98c6953c79b31af1431815f0f3d64422aa9bc7471fd3a637528c51855a9bd4f7`. The scientific owner remains failed; no compact MCM stage or compact output namespace appears. Zero completed MCM targets and zero scalar reference comparisons remain the truthful result.

The recovered original outer terminal still has `proof: null`, and original outer cleanup still has `unresolved_pid_absence: true`. Recovery did not rewrite either. The later original-machine PID/cgroup absence observations were assessed separately in `original-import-metadata-bound-investigation-2026-10-03/INVESTIGATION01.md`; copied files cannot independently establish present process absence. The identity remains permanently closed, with `repeat_allowed: false`, one consumed engineering attempt, and no refund or paper-budget transfer.

The earlier execution record's statement that raw recovery was not yet complete is preserved as a historical observation. This later verified receipt supplies the additive recovery evidence without altering that record or upgrading its failed disposition.

## Exact limits and next boundary

Acceptance covers the 13 selected remote blobs and the complete failed capsule archive/tree they authenticate. It does not assert recovery of the installed shared runtime, external empirical stores, every repository blob, or missing Git history. The historical objects actually queried above are available; unqueried history is not inferred. Absolute original path registrations do not authorize running the relocated capsule, and recovered inode metadata is not a live Owner or lease.

No numerical correctness, full-sized storage or memory capacity, financial fit, paper agreement, or additional refusal-class proof was tested. The genuine imported stage and failed metadata preflight remain distinct from MCM completion. A metadata correction still needs its own source review and a new identity with the required cumulative engineering amendment and exact release; neither this recovery nor the unused second primary case permits repeating the closed attempt.
