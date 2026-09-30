# Conditional preservation of the closed graph05 ledger

Preparation only. The new identity preserves the exact closed graph05 ledger
named in manifest.json. Expected bytes and SHA-256 come from its original artifact
index; preparation reads only compact metadata and file stats. The graph05
producer and saved-array verifier already have accepted independent closure.

Execute only after graph06 producer and verifier are closed and independently
accepted, and preservation02 is closed and independently accepted. Recheck the
March graph07 projection against actual free space: if sufficient, do not launch.
Preservation02 and this operation must be sequential; each full recovery scratch
must fit above the existing 10 GiB floor. No prospective reclaimed bytes count
as actual free capacity.

The worker and synthetic eligibility fixture copy preservation02 with only the
exact graph05 identity and descriptive graph number changed. Transport is byte
identical. Full source hash, upload, full download/hash, restoration metadata
roundtrip, durable verified receipt/sidecar and source revalidation precede unlink.
Completion metadata also roundtrips. Failures and scratch are retained; no retry
under this identity. No SQLite connection opens. Raw files, arrays and graph06
ledger remain excluded. Original artifact-index bytes remain unchanged; future
local-path checks require restoration and hash verification first.

Limits are unchanged: 256 MiB maximum, 192 MiB high, zero swap, two CPU affinity,
3 GiB host reserve, 3.5 GiB startup memory, 10 GiB disk floor, 14,400 seconds.
Startup disk must exceed 10 GiB plus this ledger size plus 16 MiB. Payload limits
are 4 GiB per file and 8 GiB total; transport operation deadlines are 5,400 seconds.
Independent review must assess current indirect dependencies as well as the
worker's direct active-claim check. Commit reviewed preparation before execution;
recheck all bound hashes, exact stat identity, absent journals/sidecar, old owners,
exclusive new identity and fresh host resources immediately before launch.

No remote operation, body read, eviction or verified backup is claimed here.
No financial claim or paid resource is added. Existing failures remain preserved.
