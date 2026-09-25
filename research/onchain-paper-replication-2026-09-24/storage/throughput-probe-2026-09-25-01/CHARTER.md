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
verified download. Use two generated128MiB random payloads, the same size/data
across stages; disable no checks. Random bytes avoid compression/zero-file bias.
Transport remains the already reviewed SCP-upload/SSH-dd-download implementation,
with its per-connection cap raised from8 to64MiB/s only for these probe objects.
Each direction's clock includes connection setup, excludes local hash verification.
Each uploaded object is downloaded and SHA256-verified before removal. All phase
measurements and failed attempts remain. No retry or rerun under this identity.

Maximum payload allocation1.25GiB (planned1GiB+128KiB), maximum2probe connections
plus the existing backup,512MiB cgroup cap/384MiB high,zero swap,two-CPU affinity,
4GiB host runtime reserve/4.5GiB startup,20GiB disk floor,<=512MiB generated files,
900second overall bound. The original249GiB preservation allowance is unchanged;
combined conservative preservation-plus-diagnostic allowance250.25GiB. This adds
at most900s diagnostic time alongside the already accounted backup execution;
financial claim accounting is unchanged. Stop on resource/transport/integrity error.

The remote directory is exclusive and separate from every research backup. Only
this probe's four generated remote payloads and generated local payloads/downloads
may be removed after their verification. The empty remote directory and compact
local receipts remain. On failure retain partials. No research data may be deleted.

This is a diagnostic under concurrent background traffic, not an isolated link
benchmark. Report before/after drift and timing variance; no automatic throughput
claim or production concurrency change follows. A successor preserving verified
backup receipts would need exact prospective boundaries and independent review.
