# Storage Box preservation checkpoint

The user-provisioned Storage Box has 5.0 TB available according to the initial
SSH capacity check. Strict host-key checking and dedicated-key authentication
succeeded. Endpoint metadata remains in locally ignored `connection.json` and
in the private backup; no password or private-key contents are stored here.

The compact snapshot is pinned to commit
`dfe646f084c1d05f4837ba06ece6c7a41baa9bab`. Its 16,110 Git blobs total
72,643,513 uncompressed bytes, stored in a 21,313,138-byte archive. It includes
the study, source, tests, compact evidence, four closed price claims and the
closed resource-pilot claim. Retained raw price response bodies are included.
Large transaction bodies, graph/MCM arrays and pilot SQLite scratch are excluded.
The contract and snapshot manifest define the exact scope.

The separate compressed inventory records 59,083 distinct retained ETH files
and filesystem identities totaling 103,524,489,043 bytes. Sizes were checked
against frozen source maps. Expected hashes were retained from those maps;
raw contents were not freshly hashed. Backing up this inventory does not back
up the transaction bytes themselves.

The one-shot backup uses an exclusive remote checkpoint directory, six finite
payloads and a final completion marker. Each uploaded payload must be downloaded
and hash checked before local completion. It uses a 512 MiB memory ceiling,
384 MiB high threshold, zero swap and a 900-second guard. Originals are retained;
no deletion or automatic retry is implemented. Terminal evidence must be checked
before interpreting this checkpoint as complete. Never relaunch this identity.

Future transaction preservation requires a separate finite contract with batch
ownership, resumable checkpoints, fresh source-hash checks, remote retrieval
verification, network and time limits, and explicit treatment of partial failures.
No financial experiment or historical claim is released by this storage setup.
Archive storage does not supply the RAM or local scratch capacity required by
the remaining graph/MCM and model work.

The transfer completed in 45.803 seconds with child exit zero, verified cleanup
and 118,751,232-byte sampled peak memory. `complete.json`, six per-file receipts
and `compact-guard/final.json` retain the outcome. The completion marker also
matched after retrieval. Independent review is recorded in the study's
`IMPLEMENTATION_REVIEW.md`; later documentation and receipts are outside the
pinned archive. Transaction raw backup remains incomplete.

Independent verification matched all 16,110 recovered members against both the
manifest and the pinned Git blobs, checked all six payloads and the completion
marker, and confirmed no remaining owned process or cgroup. The compressed
inventory and its decompressed hash matched. No material finding remains for
this compact checkpoint; these checks did not read transaction raw bodies.
