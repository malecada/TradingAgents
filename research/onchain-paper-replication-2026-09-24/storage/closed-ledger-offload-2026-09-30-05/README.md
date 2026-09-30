# Conditional preservation of the closed graph07 ledger

Preparation only. Preserve exactly the already closed graph07 SQLite ledger in
manifest.json, after active graph08 producer and saved-array verification close
with independent acceptance. Storage04 must remain closed and accepted. Graph07
producer and array verification already have accepted closure. Expected bytes and
hash come from the unchanged original artifact index; current file stats match.
Preparation reads no ledger body and performs no remote operation.

Recheck actual free space against the reviewed December requirement of
22,103,159,134 bytes. Skip this operation if enough space is available. Otherwise
prepare and independently review the actual release dependencies, then commit and
push outside any active freeze. Source size is 3,760,664,576 bytes; a full recovery
copy plus 16 MiB scratch must fit above the 10 GiB reserve before launching.
Preserving this ledger may still be insufficient for December. Reclaimed space
counts only after accepted recovery and deletion, followed by a fresh capacity
check. No second file or additional transfer is authorized by this manifest.

Worker and eligibility fixtures copy accepted storage04, changing only graph06
to graph07. Transport is unchanged. Full source hash, upload, complete recovery
download/hash, restoration metadata roundtrip, durable verified receipt/sidecar
and source revalidation precede unlink. Completion metadata also roundtrips.
Preserve every partial and failed attempt. Never relaunch a reserved identity.
No SQLite connection opens. Raw files, graph arrays, active graph08 ledger and
other artifacts are excluded. Preserve the original index. Historical local-body
verification requires restoration of the recorded bytes and verified hash.

Limits: 256 MiB maximum, 192 MiB high, zero swap, two CPUs, 3 GiB host reserve,
3.5 GiB startup, 10 GiB disk floor and 14,400 seconds. File limit remains 4 GiB,
transport payload 8 GiB, operation deadline 5,400 seconds. Require exact compact
hashes, source stat identity, absent journals/sidecar, absent owners/units, fresh
resources and a new exclusive identity immediately before execution. Independent
review must check indirect consumers beyond the worker's direct input check.

The initial metadata preparation wrote only the three copied source files and
manifest, then stopped because the new eligibility log did not yet exist. No
bindings, empirical claim, transfer, guard or eviction was published. Retained
source/manifest bytes are used for the subsequent eligibility check and binding
preparation; they are not overwritten by rerunning a generator.

Actual release and preflight are deliberately absent until graph08 producer and
verifier close and capacity is checked again. This preparation establishes no
new off-device backup, financial admission or permission to touch an active job.
