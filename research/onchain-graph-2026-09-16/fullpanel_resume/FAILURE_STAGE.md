# July 26 continuation failure: stage investigation

Read-only investigation on September 22, 2026. Execution source:
`c739b6f0958e23b90ff5038dd46c9356581369c3`. Execution root:
`/home/malecada/Data/onchain-research/TradingAgents-onchain-fullpanel-resume`.
No source payload was decoded, hash bucket scanned, numerical operation rerun,
or retained artifact changed. Only this note was written.

## Finding

The process reached the July 26 graph-count branch, after source decoding,
source/prefix serialization, preceding-day validation and following-block
boundary validation. Termination occurred before the first durable Local40
count shard. The exact internal counting substage is unknown.

The 4 GiB high-watermark pressure is consistent with the retained resource
receipt, but changing that watermark alone is **not established as sufficient**.
There is no observed code-level unbounded accumulation or confirmed leak.
There is a concrete memory-scaling risk in the full-day native graph/count
operation and its simultaneous Python result structures. The failed run does
not establish that this day, or later days, fit below the 6 GiB hard limit when
high-watermark throttling is removed.

## Retained evidence

The following inventory uses filenames, sizes and filesystem timestamps only;
matching size does not establish matching payload bytes.

| July 26 artifact | Original attempt | Continuation |
|---|---:|---:|
| Source event shards | 110 | 110 |
| Transaction-hash shards | 2 | 2 |
| All source shard bytes | 85,447,212 | 85,447,212 |
| Prefix shards / bytes | 3 / 663,131 | 3 / 663,131 |
| Count directory | Exists, empty | Exists, empty |
| `phase.json`, independent report, daily output | Absent | Absent |

All source and prefix member names and sizes match between attempts. The
continuation's new hash root is empty: no July 26 append began. Its lifecycle
contains the 206 restored seed daily outputs, totaling 53,296,232 serialized
bytes; no new daily output was published.

Continuation filesystem timestamps in UTC:

- Last `child.log` write: **18:03:51.525659**, with the last line identifying
  July 26 `extract` as starting.
- Last event-shard write: **18:04:23.927809**.
- Last prefix-shard write: **18:04:24.185802**.
- Empty count-directory creation/modification: **18:04:24.572792**.
- Reported unit termination: approximately **18:05:58**.

These timestamps place roughly 33 seconds between extraction announcement and
the count branch, followed by roughly 94 seconds before termination. They do
not support interpreting the entire approximately 875.97-second guard lifetime
as a slow source decode: most preceding time was seed restoration/publication.
The original attempt also reached an empty count directory, timestamped
16:13:30.912450 UTC. That similarity localizes both partial attempts but does
not prove the original interruption had the same cause.

The compute `final.json` records `phase=failed`, signal exit status 9,
`memory.high=4,294,967,296`, `memory.max=6,442,450,944`, and
`memory.swap.max=536,870,912` bytes. Its sampled peak is 4,447,776,768 bytes
(approximately 4.14 GiB), with 16,136 high events and zero max, oom, oom_kill
and oom_group_kill events. These are aggregate cgroup observations, not a
Python/native heap breakdown or an unconstrained peak requirement. Attribution
to systemd-oomd comes from the coordinator's separate service investigation;
the receipt alone establishes signal termination, not the sender.

Receipt SHA-256:
`2f45e1104330f3eff2d2d9c70c4c9b4db4326eceb6cf9f3e6e39860bcecc8b06`.

## Source localization and memory mechanism

The execution checkout and active checkout copies of `fullpanel/day.py`,
`pilot/numeric.py`, `panel_readiness/boundary.py`, and `fullpanel_resume/run.py`
were checked byte-for-byte against the named source commit; all matched.

`fullpanel/day.py` creates `count/` only after source shards, prefix shards and
both boundary checks. For this non-reuse date it then calls
`numeric.count_day`, sorts returned local rows, and finally writes count shards.
The empty directory therefore bounds the failure to that interval. There is
no persisted substage marker or stack trace to distinguish bounded checks,
graph construction, native counting, conversion of results, isolated recount,
summary, or final row sorting.

`pilot/numeric.py:146` retains the full event list and overlap selection, runs
bounded induced-subset checks, counts the completion window, then retains its
complete per-node result while recounting the isolated day. The bounded
oracle itself uses at most three subsets of 30 events; it is not a full-day
enumeration of event triples.

`panel_readiness/boundary.py:5` builds a Raphtory graph containing every selected
event, invokes native `local_temporal_three_node_motifs`, and materializes a
Python dictionary with 40 counter values per node. Its completion adapter also
holds event-ID/active-node sets and selection lists. Native graph/count memory
and the full Python result can coexist during conversion. Completion and
isolated-day counters coexist during the second recount. The runner also
retains parsed seed summaries. No retained measurement separates these costs
or distinguishes anonymous memory from file cache.

The unchanged 10,000-row shard writer and the 110 completed event shards imply
between 1,090,001 and 1,100,000 eligible July 26 events, without decoding them.
The frozen transaction expectation is 1,679,068 rows. For context, retained
July 24/25 summaries report 556,773/674,719 eligible events and 386,677/492,498
nodes. July 26 node count, degree concentration and native intermediate sizes
are not available. A larger full-day counting workload is therefore plausible;
the inventory does not establish its peak memory or algorithmic complexity.

## Decision limit

A watermark adjustment is a plausible guard-policy response to confirmed
high-event pressure, subject to the separate guard review and an explicitly
admitted successor. It is not a demonstrated numerical memory fix. A claim
that the hard cap will suffice, or that only the watermark caused failure,
would exceed this evidence. Conversely, these files do not demonstrate a
logical leak, infinite accumulation, or incorrect numerical definition.

Any authorized successor should retain the failed attempt and distinguish
count substages in resource evidence while keeping the numerical definition
and existing admission criteria intact. This investigation performs no
successor launch, gate change or numerical redesign.
