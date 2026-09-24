# Retained ETH transaction-byte preservation

The user authorized proceeding with work enabled by the newly available Storage
Box. This transfer preserves existing bytes; it does not decode transactions,
refit models, reopen a historical claim or consume a new financial experiment.

The frozen inventory contains 59,083 distinct files totaling 103,524,489,043 bytes.
The exhaustive plan contains 195 contiguous batches, each at most 512 MiB raw and
4,096 files. The first batch is a separately bounded pilot; the remaining 194
require review of measured pilot evidence before launch. Each phase and batch
has an exclusive durable identity. Never relaunch a terminal identity or duplicate
an active controller. Continuation requires a new identity and reconciliation of
all completed and partial remote batches.

Each source must retain its resolved path, size, timestamp and expected SHA256.
Packing freshly checks every original file hash. Each bundle is uploaded,
downloaded and checked against both its archive hash and every original member
hash. The completion marker is separately retrieved before local completion.
Original files are never removed. Only the two generated temporary tar copies
are removed after full verification; failed partial copies remain preserved.

Limits: one batch at a time, two CPU affinity, 512 MiB memory maximum, 384 MiB
high threshold, zero swap, 3 GiB host reserve, 20 GiB local disk floor, at most
2 GiB temporary data and 8 MiB/s per transfer direction. The first phase has a
30-minute ceiling; bulk has an eight-hour ceiling. Remote admission reserves
phase raw bytes plus 1 GiB for padding/metadata above a 256 GiB free-space floor.
The contract caps reserved file payloads at 2 GiB pilot plus 248 GiB bulk; SSH
protocol overhead is excluded. Downloads use bounded `dd` plus a local streaming
byte/rate/deadline checker. Extra bytes are rejected before writing to disk.
Hetzner documents direct `dd` over port 23 in its SSH access guide.

The contract binds exact source and input hashes. Account routing stays in the
existing locally ignored connection metadata; password/private-key contents
are neither read by application code nor stored in this checkpoint.

Ruling: retain successful backup checkpoints independently of later job failure.
This bounds lost transfer work without replaying closed research. A complete
subset is never labeled a full raw backup. Graph/MCM arrays, SQLite scratch and
other historical raw stores are outside this inventory and remain separate
preservation requirements. Same-device raw originals remain intact.

Synthetic checks exercised partition conservation, duplicate/oversize refusal,
source metadata/hash mismatch, archive member corruption/path rejection,
interrupted transfer retention, exclusive publication, bounded extra/short
responses and stalled child cleanup. Fifteen tests passed before release review.
