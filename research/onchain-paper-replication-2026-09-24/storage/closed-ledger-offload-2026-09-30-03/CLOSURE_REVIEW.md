# Independent closed-ledger preservation terminal review

September 30, 2026. **Accepted: closed-ledger-preservation-terminal**, limited to the original completed graph05 ledger. This is an independent reconciliation of compact receipts, bound source identities and local absence/stat evidence. No archive, SQLite or array body was reopened, no remote object was downloaded again, and no test or job was rerun.

## Exact object and preservation evidence

The manifest identifies only `eth-paper-graph-resource-20260930-05/aggregation/ledger.sqlite`, with 3,265,302,528 bytes and SHA-256 `f58448c7ac396999aa1b56f15e33623db67c4c2834319be5cbd3935bba456c23`. That exact size/hash matches the unchanged original artifact index; the original completed claim, terminal, owner and guard metadata also retain their manifest-pinned hashes. No raw store, graph array or graph06 ledger is included.

The original and recovered manifests are byte-identical. The four per-file records (`00-verified.json`, `00-evicted.json`, `00-restore.json`, `00-recovered-restore.json`) and the original-path `.remote.json` sidecar are byte-identical, SHA-256 `56a2514b3adcd4dce5027614dfbca2885be72496625a1c38ec19adce7ba599f3`. They identify the same original object, exclusive remote body and restoration metadata, and record successful body roundtrip verification. The receive receipt reports exactly 3,265,302,528 bytes received with return code 0. Its recorded duration is 427.923 seconds; this observation is not a promised transfer rate.

`completion-candidate.json`, remotely recovered completion and local `complete.json` are byte-identical, SHA-256 `8fe0c53fd89ec925c07bfb80334d2274d7ec13a8d7977488bbacce7055833281`. The aggregate contains exactly the verified per-file record and the same total bytes. Restoration and aggregate receive receipts both report successful exact-size delivery. The reviewed worker publishes local completion only after the aggregate remote roundtrip succeeds.

The original ledger path is absent, the matching restoration sidecar is present, and successful `00-recovered.bin` scratch is absent. The original artifact index was not rewritten to hide the relocation. A later historical local-body check must first restore to a new temporary file, verify this size and SHA-256, and restore the original path only when absent. The old graph job must not be rerun as a restoration mechanism.

## Owner, limits and source continuity

The original guard final is complete, with child exit 0, cleanup verified, no limit reason and elapsed time **2,004.001215647 seconds**. Its command is the reviewed storage03 worker. Monitor PID 844635, worker PID 844639 and the exact `onchain-replication-205a4e3e939647ccbd34294c5442b722.service` cgroup are absent on independent readback. The saved unit state is inactive/dead with successful exit; cleanup stop return code 5 is reconciled by that terminal state and absent cgroup.

Kernel controls record 256 MiB maximum, 192 MiB high and zero swap, with the declared 3 GiB runtime reserve, 3.5 GiB startup reserve, 10 GiB disk floor, 14,400-second wall limit and two-CPU affinity. Peak sampled cgroup memory is **202,854,400 bytes**. There are **46,469 memory.high events**, with zero max/OOM/OOM-kill events; this is successful bounded throttling, not zero memory events. Sampled peak is not a cold-cache memory requirement.

All 22 original bindings and all 26 contextual release bindings independently rehashed correctly. HEAD remains `62c5b6ea66e95cc67a404d1f13898619a88237fc`. The local connection descriptor was checked only by SHA-256, never by printing or inspecting its contents. This review also rehashed every compact reference in `closure01.json` and checked its joins to the original receipts.

## Scope of acceptance

The full-body source hash, downloaded-body hash and ordering before eviction are supported by the reviewed producer and its retained successful receipts. This review is not an independent second body hash, download, SQLite consistency test or guarantee of future provider retention. It does establish a consistent preserved restoration route for the exact original bytes, with successful guarded completion and no remaining owner.

The closure snapshot reports 23,614,681,088 free bytes; independent review observed 23,613,476,864. Both exceed the prospective graph07 requirement of 22,396,522,013 bytes. Capacity remains time-sensitive and must be checked again before launch. This acceptance clears the preservation prerequisite only; it does not admit graph07, adopt its budget or establish any matching/financial result.

Additional audit identities:

- `guard01/final.json`: `e8e0b3cc5e15a53e279dade47083b1a90197db87ff3609e12e1810da1899575a`
- `manifest.json`: `c5c8eaecaed40bf245e91c5fe1fbec2d33ab3676927d295b3c8f5f1c6f0289ae`
- `closure01.json`: `0249c91b5987ad4371aa0831abccf759af0cd4312dd3e1597f842812d17611b2`
- `bindings.json`: `5c6238522e519174fec6a505bd120f4fca37b15eb5637841e6964b2f46257728`
- `release-bindings01.json`: `a33bc05bfb524d653cbdecfbcfe46e5648d05d1a354278895693ec013b0790f1`
