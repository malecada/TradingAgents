# Fresh archive-backed compact pair writer

Add an explicit PairLog subclass; never change the old local writer/reader.
Only new files created under this writer's exclusive namespace are eligible for
its disposition. Full chunks are closed and archived before the next chunk is
opened, so numerical acknowledgement can still read the latest event locally.
The final partial chunk is archived only at completion with no pending pair.
Each closed chunk is replayed against its in-memory prior state/head, copied and
round-trip verified through archive_chunks, then linked into an ordered immutable
manifest with owner/start/ordinal/extent/head/content/remote receipt bindings.
Only after final callbacks and full content/metadata checks may this writer
remove its own chunk, upload snapshot and readback copy. Immutable copy/manifest/
disposition evidence stays local. No old or unowned source is accepted as input.

finish writes the unchanged compact terminal and replays every archived chunk
through archive_consume and archived_pair_log before publishing the archive
completion. Exact metadata/inventory and post-publication live checks remain
required. No checkpoint-tree/score-stream/current-owner or empirical admission
follows until those separate routes are implemented. Failure is terminal with
retained partial evidence; no retry, fallback or historical replay.

Finite chunk count and metadata logical allowance are prebound. The minimum
local free-space floor is10GiB. Successful payload retention is bounded to the
current chunk plus temporary copy/readback and one verification read; this is
not a measured physical/RSS/transport upper bound. Transports and actual guard,
source policy admission, aggregate scratch/metadata/graph/score costs remain
caller obligations. Tests use fresh synthetic filesystem transport only.
