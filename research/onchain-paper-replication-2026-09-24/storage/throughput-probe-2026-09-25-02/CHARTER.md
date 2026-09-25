# Single versus dual-connection transport diagnostic

The user explicitly authorized testing whether the higher-capacity internet
connection can speed preservation. This grants this bounded diagnostic alongside
the existing backup, superseding the earlier blanket no-concurrent-test rule only
for this probe. The existing backup's code, limits, inputs and identity stay fixed.
No financial experiment, historical raw read/replay, paid resource or provider
contact is included.

Hypothesis: per-connection transfer behavior leaves bandwidth unused; two
connections increase aggregate transport rate. Measure sequentially one connection,
two parallel connections and one connection again, separately for upload and
verified download. Use two generated32MiB random payloads, the same size/data
across stages; disable no checks. Random bytes avoid compression/zero-file bias.
Transport remains the already reviewed SCP-upload/SSH-dd-download implementation,
with its per-connection cap raised from8 to64MiB/s only for these probe objects.
Each direction's clock includes connection setup, excludes local hash verification.
Each uploaded object is downloaded and SHA256-verified before removal. All phase
measurements and failed attempts remain. No retry or rerun under this identity.

Maximum payload allocation0.375GiB (planned256MiB+128KiB), maximum2probe connections
plus the existing backup,512MiB cgroup cap/384MiB high,zero swap,two-CPU affinity,
4GiB host runtime reserve/4.5GiB startup,20GiB disk floor,<=128MiB generated files,
900second overall bound. The original249GiB preservation allowance is unchanged;
combined conservative preservation-plus-diagnostics allowance250.625GiB. The failed first probe retains its1.25GiB allocation and402.891814s spent time.
This new identity adds at most900s diagnostic time; cumulative diagnostic
measured-plus-prospective ceiling1302.891814s. It runs alongside the backup;
financial claim accounting is unchanged. Stop on resource/transport/integrity error.

The remote directory is exclusive and separate from every research backup. Only
this probe's four generated remote payloads and generated local payloads/downloads
may be removed after their verification. The empty remote directory and compact
local receipts remain. On failure retain partials. No research data may be deleted.

This is a diagnostic under concurrent background traffic, not an isolated link
benchmark. Report before/after drift and timing variance; no automatic throughput
claim or production concurrency change follows. A successor preserving verified
backup receipts would need exact prospective boundaries and independent review.

## Explicit successor rationale

Probe01 completed the first128MiB single roundtrip but timed out during two
parallel uploads at180seconds. It is terminal, cleanup verified, and all partial
generated files/receipts are retained. This does not establish a parallel speedup
or slowdown. Probe02 keeps the same measured transport, fixedstage order and
resource/time controls; only per-file payload changes to32MiB to obtain the full
bracketed comparison within those bounds. No probe01 job, object or output is
reused or overwritten; original backup03 continues unchanged. Smaller transfers
have proportionally greater connection-setup overhead, which remains disclosed.
