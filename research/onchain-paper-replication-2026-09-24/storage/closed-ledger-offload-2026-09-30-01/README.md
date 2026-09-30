# Closed graph ledger preservation

Preserve the completed graph03 aggregation ledger, 3,755,220,992 bytes, on the
existing Storage Box using one new exclusive local/remote identity. The expected
SHA comes from the original closed artifact index. Preparation reads only compact
metadata and stat identity; full hashing occurs inside the finite guard. The
active graph04 ledger, raw transaction stores and all graph arrays remain local.

This is operational byte preservation, not a new experiment or a closed-job
rerun. Exact source path, stat identity, original artifact-index/claim/terminal,
owner/guard closure, absence of SQLite journal/WAL/SHM, untracked-file status and
absence of a direct live-claim reference are checked. The previous owner's PID
being present causes conservative refusal. Compact current admission was checked
separately for indirect dependencies; this is not a universal dependency finder.
No SQLite connection or database mutation is performed.

The previously reviewed offload_one and finish helpers are imported unchanged.
They hash the source, upload to an exclusive new remote directory, download the
entire body, compare bytes/hash, roundtrip restoration metadata, publish durable
local receipts and a source-side .remote.json mapping, revalidate the source, then
unlink it. File and directory fsync and an exclusive advisory lock are retained.
Partial transfers and failed scratch remain. Terminal or reserved identities are
never relaunched; reconcile exact receipts after interruption.

Restoration: download the sidecar's remote object to a new temporary file, verify
its exact byte length and SHA, then restore the original path only when absent.
The historical artifact index remains byte-identical. Its ledger location becomes
cold: any later verification requiring that local body must restore it first.
A sidecar alone does not claim body availability; completion requires actual full
remote byte roundtrip and restoration-metadata roundtrip. Historical local-only
backup claims remain historical; only this file gains verified remote evidence.

Limits: 256 MiB memory.max, 192 MiB memory.high, zero swap, two CPU affinity,
3 GiB host reserve, 3.5 GiB startup availability, 10 GiB disk floor and 14,400 seconds.
Full-file recovery scratch is now at most 4 GiB, versus the previous transport
archive helper's 512 MiB per-file policy. The new worker explicitly requires free
space above 10 GiB plus exact file size plus 16 MiB. Payload allowance is 8 GiB
including upload/download; SSH rate is the prior 262144 kbit/s setting. This
resource policy change concerns preservation scratch only, not scientific limits.
The outer guard stops on resource failures; no guaranteed throughput is claimed.

Four new synthetic eligibility tests passed; they were added after the initial
eligibility implementation, so no pre-implementation failing test is claimed.
Unchanged helper preservation tests and prior live success remain retained at
cold-offload-2026-09-29-03. Independent source/manifest/resource review and fresh
host/disk/identity checks are required before one launch. Bind all imported code,
manifest, connection metadata and disk policy. No key/password contents are read
or printed; the existing SSH transport authenticates using its configured key.

Independent review found the old inherited 1,800-second per-operation timeout
unsuitable for the larger file at historically observed throughput. Initial
candidate bytes and the finding are preserved. A preservation-local subclass
now supplies 5,400 seconds for both upload/SSH commands and bounded download,
while retaining byte budgets, rate limits, diagnostics, exclusive destinations
and no retries. The outer guard is 14,400 seconds to cover two such operations
and hashing/metadata work. At 1.1 MB/s a direction would take about 3,414 seconds;
this is conditional timing, not promised throughput. The old transport remains
unchanged. Two mocked transport tests check actual deadline forwarding and byte
charges after a retained missing-module red test. No network probe is claimed.
