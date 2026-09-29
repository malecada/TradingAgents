# Independent cold-offload preservation review

September 29, 2026. The user explicitly requested moving data to the Storage Box to free local space. This review covers only the nine named inactive archive/probe files and the proposed finite one-shot move. It does not authorize raw transaction, graph or SQLite eviction, historical job restart or financial execution. Inspection was limited to script/tests, manifest, old compact guard receipts and local stat/tracking metadata. No archive bodies, credentials, remote calls or transfer/test jobs were accessed or executed by the reviewer.

## Initial identities and denominator

- `manifest.json`: `c5bf300c71c190b3d991543ad0b58ac8972fdf33cfad2afb8616c024e8e15fe9`
- `offload.py`: `9c9e1b68e17b724dfecdbde419f2f80b24f8959486f25b037850559730f39cfc`
- `test_offload.py`: `ba63f8040699a87d05977ad130e109767bd1ca96ba31d0bda09c5e171171a1b7`
- `green01.log`: `38bf320bde0206302c1e57a1b42621b895232f0c74ebfec8c7b81ec6681fa5a0`

Independently reconstructed manifest arithmetic: **9 files, 3,584,497,664 bytes**, largest file **535,347,200 bytes**, below the 536,870,912-byte single-download scratch ceiling. All nine lstat identities match their manifest records, are regular nonsymlink files with one link and are untracked by Git. Every referenced owner receipt hash matches; all are terminal `failed` with verified cleanup and absent recorded cgroups. These checks establish the listed inactive local objects at review time; the reviewer has not independently rehashed their bodies.

Twice the body total is **7,168,995,328 bytes**, leaving **1,420,939,264 bytes** below the 8 GiB network payload allowance for block rounding and compact metadata transfers. Actual transport accounting reserves upload sizes and rounded download bounds and refuses budget exhaustion. The 262,144 kbit/s transfer setting converts to **32 MiB/s**. The guard declares 256 MiB maximum/192 MiB high memory, zero worker swap, 3 GiB ongoing host reserve, 3.5 GiB startup reserve, 20 GiB local disk floor and 3,600 seconds. The initial free-space check adds 512 MiB body scratch plus 16 MiB metadata margin above the disk floor. These are finite execution limits, not a measured guarantee of transfer success.

## Per-file preservation assessment

The script refuses changed/nonexclusive source files, tracked targets, active old owners, prior attempt receipts and existing remote identity. It retains an `O_NOFOLLOW` source handle with an exclusive nonblocking advisory lock while transferring. Full downloaded body size/SHA checks and another source check precede creation/upload/readback of complete restoration metadata. A local verified receipt and original-path `.remote.json` are exclusively created, file-fsynced and directory-fsynced before the final path/descriptor identity checks and unlink. Source directory sync follows unlink. This ordering supplies independently downloadable bytes and local/remote restoration mappings before removing the original name.

Failed downloads or restoration metadata transfers retain original sources and scratch; successful scratch is removed only after per-file eviction receipt publication. A crash between unlink and the eviction receipt still leaves the already durable verified receipt and sidecar, so reconciliation can determine the remote object and checksum. No retry or cleanup of failed evidence is implicit. Advisory locks and repeated stat/hash checks assume the documented inactive owners; they are not protection against a hostile filesystem writer racing the final unlink.

Transport source uses the existing identity/known-host paths through SSH/SCP with strict host checking and batch mode. The reviewer inspected transport code but did not open the connection file, identity key or known-host contents. Full object readback demonstrates recoverability at execution time; it does not prove permanent remote immutability or a second independent remote replica.

## Required receipt-state correction and tests

**P2 — local terminal completion precedes completion-metadata verification.** Initial `worker` publishes `complete.json` before putting it remotely and verifying its download. Failure during those final operations writes `failed.json` beside `complete.json`. Per-file body/restoration preservation remains intact, but the two competing terminal names make aggregate outcome interpretation ambiguous. Use a nonterminal completion-candidate record for that roundtrip and publish terminal `complete.json` only after it succeeds, or provide equally explicit distinct body-completion versus transfer-completion semantics.

Initial five synthetic tests passed according to `green01.log`; they cover successful preservation, corrupt body download, restoration-metadata upload failure, initial source drift and an existing verified receipt. Add failures during local verified/sidecar publication before unlink and completion-metadata transfer after already moved bodies. Assert the source remains for every failed pre-unlink durability step and that aggregate completion cannot appear before its stated final verification. These tests are important for the requested physical source removal.

**Execution acceptance pending the above correction/tests and final frozen source bindings.** The exact original inventory and its scope are suitable for the requested cold move; no execution or deletion has occurred as part of this independent review. The prior graph-residency failed suite remains failed and unchanged.

## Corrected pre-execution acceptance

The new `finish` helper writes a nonterminal `completion-candidate.json`, uploads it as the remote completion record, downloads and hashes it, and only then publishes local `complete.json`. A failed final metadata operation leaves candidate/per-file evidence without falsely publishing local aggregate completion. This closes the P2 ordering issue. A local write/fsync failure or interruption still requires guard/receipt reconciliation; success must never be inferred from a filename alone.

Added tests inject failure at local verified-receipt and sidecar publication, preserving original bytes in both cases. Separate completion tests cover success and transfer failure with existing per-file eviction evidence. Saved `green02.log` reports **8 tests passed in 0.028 seconds**. Retained `red02.log` has two missing-`finish` function errors, not an executed failure-ordering counterexample; the initial defect was established by source ordering. The reviewer did not rerun the tests.

Final identities:

- `offload.py`: `33e0efa52dfb82fb2fa8a87216f6d63a96dd1c8740caafbfe94b17e0619b4e49`
- `test_offload.py`: `73b8b4762100c0fd96ae372a6bce573122b27f7ccd0e53b12f627bd0193cb576`
- `bindings.json`: `9cf75118518dee81132c582eab3c5913975168fc2026d609875b8be191aa0298`
- `green02.log`: `c57e833f026773c218c965cc8726b7bfb3b9b889adb427cb6bf285f303c799de`
- `red02.log`: `9286607997ff2c275e14bac37cfe2600c069d98236cbbacd5d49ae6659663350`

The exact inventory hash is unchanged. Eight of the nine bound files (source, tests, manifest, transport and imported runtime dependencies) were independently rehashed and match. The remaining entry is the existing connection metadata: its recorded pin matches the manifest's connection pin; the reviewer did not open that file. The worker freshly hashes all nine bindings and separately checks the connection/transport pins before using the transport. Fresh source identity, inactive owner/cgroup, untracked status, local scratch and remote capacity checks remain mandatory runtime conditions already enforced by this script.

**Accepted for one guarded execution of this exact nine-file cold move under the user's explicit storage-offload instruction.** Acceptance includes local body removal only after the reviewed per-file roundtrip/restoration/receipt checks succeed. It does not assert that any upload, restoration verification, source removal or space recovery has yet occurred. Do not retry a reserved identity or treat partial completion as nine-file success; reconcile retained per-file evidence. A final independent closure must use saved transfer receipts, sidecars, guard outcome and actual source-presence metadata, without converting historical failed jobs or the separate failed offline suite into successes. No broader eviction or empirical release is included.

## Terminal failed guard01 closure — zero file evictions

Independent compact receipt review confirms the one permitted attempt **failed** after **484.791213 seconds** because host available memory fell to **3,164,483,584 bytes**, below the unchanged **3,221,225,472-byte (3 GiB) runtime reserve** by **56,741,888 bytes**. This was a host-memory reserve stop, not a disk-floor or worker OOM failure. The worker's sampled peak was **201,809,920 bytes**, with **6,642 memory.high events** and zero max/OOM events. The final disk observation remained above its frozen 20 GiB floor at 24,412,225,536 bytes.

The guard reports `phase: failed`, verified cleanup and null `child_exit_code`; separately retained `child_exit.json` records workload exit **-15 (SIGTERM)**. These are distinct saved observations, not a successful child exit. Cleanup properties show a failed/stopped unit with empty control-group path. The recorded monitor PID **3665680** and cgroup are absent at independent review. The older running `unit_properties` snapshot does not override terminal cleanup.

The **6,322-byte inventory manifest** completed its metadata roundtrip: downloaded bytes equal the original manifest and the saved transport receipt reports exit 0. No per-file `verified` or `evicted` receipts, original-path sidecars or aggregate `complete.json` exist. All nine original local paths remain, and independent metadata inspection confirms their exact original stat identities. The parent's saved `closure-check01.json` additionally reports rehashed body/size matches for all nine and no mismatch among the nine frozen bindings; the reviewer did not repeat archive hashing or open connection/credential files. Accordingly, **zero file moves/evictions and zero reclaimed bytes are established**, and no body-level remote recoverability is claimed. Partial remote state is retained and was not queried, resumed or removed by this review.

Evidence SHA-256 values:

- `guard01/final.json`: `8630c4c1ad9dc6c70dd1f0e0916a79ec860ac8690d506cfe6ec768ac4fec8525`
- `closure-check01.json`: `a4d47476a3537a2b48f208cfcdfbdf63f05d100317516cd57cd80e3432a03dda`
- `recovered-manifest.json.transport.json`: `7f7bf705a6a78d313449a62cb038b0ae4c75f6b2ddddc4cdfd43d3f2ede3f8eb`

**Failed-attempt preservation closure is accepted; successful offload is not established.** The closure snapshot reports 4,177,031,168 host-available bytes and 23,751,630,848 free disk bytes at its timestamp. That host-memory observation is below the separate offline02 startup requirement of 6,442,450,944 bytes; the offline02 receipt directory remains absent at review. The prospective user-authorized **10 GiB disk** policy changes no RAM reserve and did not alter this attempt's frozen limits. No retry, successor dispatch, remote query or empirical release follows from this closure; preserve the terminal identity, partial remote objects and all original sources.
