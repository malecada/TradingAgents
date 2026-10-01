# Static retained-payload lower bound

The earlier score-only estimate omitted the newly implemented compact pair log.
Each event is 168 bytes; every completed pair retains at least a begin and a
completion event. For the recorded nine-graph, 32-motif resource inventory,
577,498,112 MCM cells therefore imply 194,039,365,632 bytes of pair-event payload.
Score tails and float64 batches add 50,819,833,856 bytes. The saved MCM output
and graph-feature artifact each retain a float32 matrix, adding 4,619,984,896
bytes. These selected payloads total **249,479,184,384 bytes (232.35 GiB)**.

This is a conditional logical lower bound, not a measured disk requirement or
whole-workflow upper bound. It assumes one complete MCM per recorded graph;
it is not an adopted pilot population or an additional sample exposure.
It excludes progress/checkpoint state, headers and metadata, filesystem
allocation, all dictionary work, graph inputs and saved edges, scratch,
models, prior attempts and transfer/backup staging. No arrays or outcomes were
read. Exact source/input pins and per-week arithmetic are in lower-bound01.json.

At calculation time the current volume had 21,311,746,048 bytes available, with
the authorized 10 GiB floor still required. Even the smallest recorded graph's
selected payload lower bound is 22,614,280,704 bytes, before these exclusions.
The current format cannot be admitted to that local free-space budget unchanged.
A reviewed storage/disposition route or a prospectively verified persistence
change is required; remote backup capacity alone does not make the currently
local same-device writer capable of using it. Earlier evidence must remain intact.

Next actions: complete exact physical and peak-live accounting, establish a
verified storage/offload route compatible with terminal revalidation, resolve
hub/pair capacity limits, and independently review and commit the cumulative
resource amendment before empirical execution. The full motif architecture and
all asset/history/comparison requirements remain unchanged.
