# Xsect relocation readiness — no transfer or deletion

The exact `/home/malecada/master_thesis/TradingAgents/data/xsect` subtree was inventoried with lstat/scandir only. No file body or symlink target was read. The bounded scan completed in0.070seconds:3,797 entries including root,3,783 regular files,14 directories, zero symlinks, zero other inode types and zero multiply linked regular files. No scan errors occurred; limits were60seconds/100,000entries. INVENTORY01.json records typed path/mode/device/inode/link-count/size/block/timestamp metadata. This is a non-atomic observation, not a content manifest or writer-exclusion proof.

| Observed measure | Bytes |
|---|---:|
| Regular logical bytes | 6,915,716,585 |
| Regular allocated bytes (`st_blocks*512`) | 6,923,898,880 |
| Directory allocated bytes | 204,800 |
| Total observed allocated bytes | 6,924,103,680 |
| Conservative payload-only gain upper bound, excluding every hardlinked file | 6,923,898,880 |

No hardlinked file receives gain credit. Even including directory allocation, the upper bound is only6.924GB decimal (about6.449GiB). It is below a7.04GB decimal shortfall by115,896,320bytes; if that gap meant GiB the deficit is larger. Open files, filesystem snapshots/reflinks, concurrent writers and allocation behavior can reduce actual recovered free space. Only fresh post-removal filesystem free-space observations could establish gain. No deletion is authorized by this estimate.

## Existing reviewed tooling and scope

- `storage/raw-preservation-2026-09-25-05/README.md` documents the reviewed retained-ETH workflow: bounded chunked transport receipt capture, one512MiB raw bundle at a time, full recovered-member verification, retained failure partials and originals preserved. Its two-GiB staging requirement and native/host/disk limits are historical selections, not automatically suitable for xsect or concurrent native21.
- The existing `tradingagents/research/onchain_replication/preservation.py` implements bounded file hashing/bundle construction and full recovery verification (`build_bundle:64`, `verify_bundle:102`, `transfer_bundle:127–169`). It uploads archive+manifest, freshly downloads both, verifies every recovered member, roundtrips the completion marker, and deletes only generated successful archive copies. It uses local tar/readback staging; it is not a zero-staging remote stream and does not remove original xsect files.
- `storage/closed-ledger-pilot-offload-2026-10-05-01/README.md` documents an existing reviewed full upload/download, restoration-metadata/receipt and source-revalidation-before-unlink sequence. Its offload.py is explicitly restricted to one exact closed Graph10 ledger, with original owner/closure checks and sidecar refusals. It must not be pointed at xsect unchanged.
- `storage/raw-preservation-complete-2026-09-29/REVIEW.md` records historical verified copies for the retained ETH raw inventory, expressly not a current full remote recheck. Those are a different scope, not xsect backup evidence.

Scoped filename/text searches in the study storage records and selected preservation/recovery source locations found no verified external xsect copy. This is a limited search result, not proof that no copy exists anywhere. No network, SSH configuration, credential, transport operation or remote capacity check was performed; current StorageBox existence/capacity/recoverability is unverified here. Existing tooling is present; existing xsect preservation credit is zero based on this inspection.

## Required before original removal

Root would need to establish the exact historical xsect provenance, consumer expectations and inactive/writer-excluded source snapshot; obtain content hashes and exact recovery inventory under the existing permitted preservation route; choose fresh bounded remote/staging scope and resource limits compatible with the active workload; upload and freshly fully recover every selected byte plus independently usable path/provenance metadata; verify recovered sizes/hashes and complete denominator; durably retain receipts and a recovery locator outside the removed tree; and revalidate unchanged originals before any separately reviewed removal. Partial upload, remote listings, aggregate sizes or old ETH receipts do not suffice. Preserve historical identity/paths and make any later consumer restore and verify exact bytes; do not silently substitute a new dataset. Failed copies/attempts remain recorded. Current scan alone does not establish those prerequisites.

Only this new readiness directory was written. No transfer, unlink, SQL query, empirical run, Main/Git edit, registration or claim was performed. Root owns any actual relocation decision.
