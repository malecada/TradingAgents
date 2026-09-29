# Cold transport evidence relocation

The user requested moving data to the existing Storage Box to free working space.
This finite operation selects exactly nine inactive transport archives and
synthetic throughput payloads, totaling 3,584,497,664 bytes. All original owners
are failed, cleanup-verified and absent. The exact original paths, stat identities,
SHA-256 values and owner receipts are frozen in manifest.json. These are retained
failed-attempt bytes, not disposable evidence. Raw transactions, graph arrays,
SQLite stores, configurations and previous receipts are outside the target set.

Each file is copied to an exclusively created remote directory, downloaded in
full and compared against its original size/hash. Its restoration metadata is
also uploaded and downloaded for verification. A local verified receipt and a
sidecar at the original path are fsynced before removal of the local body. Source
identity is checked again immediately before removal. Failed downloads and
partial remote objects remain intact for reconciliation. No automatic retry,
overwrite of historical receipts, or relaunch of an old identity is permitted.

This changes availability: the selected cold files will require restoration from
the Storage Box before a local byte inspection. A .remote.json sidecar is a
location record, not a substitute for the original file. The existing failed
attempts remain failed; moving their bytes cannot convert their dispositions.

## Limits and execution evidence

The guard enforces a 256 MiB memory maximum, 192 MiB high, zero swap, 3 GiB host
reserve, 3.5 GiB startup available memory, 20 GiB root disk floor and 3,600 seconds.
Transfer allowance is 8 GiB at a ceiling of 32 MiB/s, one file at a time. Recovery
scratch is at most 512 MiB per body plus bounded compact metadata/diagnostics.
SSH uses the existing verified key and pinned known-host file; credential contents
are not read. The script refuses insufficient fresh local or remote capacity.

red01.log records the missing implementation. green01.log records five passing
synthetic checks: successful preservation and local removal, corrupt download,
metadata-upload failure, source drift and an existing receipt. The latter four
preserve the local original. Red02 and green02 additionally cover durable local
receipt/sidecar publication failures and completion-metadata failure after body
relocation. All eight checks pass. A separate completion candidate is retained;
the local complete.json is published only after its remote round-trip succeeds.
REVIEW.md records independent pre-execution review.
The exact source/manifest/transport/guard bindings are frozen before guard01.
This is preservation work, not an empirical claim or financial fit.

## Restoration

Use the connection_path in manifest.json with its declared SHA-256. The existing
SSH key and known-host paths are specified by the approved connection metadata;
never embed a password or disable host verification. Download the remote_object
named in the file's verified receipt to a new temporary path. Verify its byte
count and SHA-256 against both manifest.json and the roundtrip-verified remote
NN-restore.json. Refuse restoration if the original path already exists; check
available capacity before downloading. After verification, install the file at
the original path and fsync the file and directory. Retain the sidecar/relocation
receipts as historical evidence and record the restoration in a new receipt.
Do not launch any original failed job. If an offload was interrupted, reconcile
verified/evicted receipts and actual local paths first; do not rerun guard01.

Full-suite verification remains incomplete after the separate disk-reserve
failure. A successful relocation only creates more headroom; it does not prove
that the next suite or full-size matching/neural workload will fit.
