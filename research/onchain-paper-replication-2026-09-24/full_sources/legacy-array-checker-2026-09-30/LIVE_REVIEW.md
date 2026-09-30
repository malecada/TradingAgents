# Independent live-to-terminal observation

The initial inspection observed `verification01` running under committed HEAD
`99b3032a31f7e5b61090ec5adf690c94d352712c`. The reservation names monitor
1780342, start ticks `1687347`, boot
`da045a9a-8050-4716-b784-249c9e822769`, and manifest SHA256
`f5dcd478dd159f927e58a2c3798497fa669d4940636fdd7d01df0ea1e2eebd4b`.
The live receipt joins that monitor, source and manifest to unit
`onchain-replication-df4552aaa20a4859bb7828cfdd72770f.service`, the exact reviewed
worker command, checkout and guard receipt directory. Payload started PID is
1782287; CPU-ready wrapper PID is 1782284.

At elapsed 42.209 seconds the saved live lease was approximately 0.10 seconds
old. It recorded CPU IDs [0,1], per-thread readbacks for 1782284/1782287/1782288,
kernel memory maximum 3 GiB/high 2 GiB/swap zero, host reserve 3 GiB/startup
reserve 6 GiB, checkout disk floor 10 GiB and wall limit 1800 seconds. Sampled
peak was 785,903,616 bytes with all memory events zero, host availability
7,770,046,464 bytes and disk free 19,936,821,248 bytes. The release receipt
recorded kernel controls verified.

All 1,870 current files and their exact committed bytes were independently
checked against the frozen manifest with no mismatch. During that check the
job became terminal. The subsequent read-only live assertion therefore
refused its running-state premise before direct `/proc` start-tick, kernel
control and affinity readback. Those live kernel/process checks are **not**
claimed independently observed here; the preceding values are saved guardian
evidence.

At 2026-09-30 20:00:26 UTC, final receipts reported complete, child exit zero
and cleanup verified, elapsed 78.319339304 seconds, peak 1,153,769,472 bytes and
zero memory events. The payload reported both graphs complete, mappings closed
and all four node-feature errors zero. Monitor 1780342 and the exact cgroup
were independently absent; no active or activating replication unit remained.
The saved cleanup stop return code 5 remains preserved alongside inactive/dead
unit state and empty ControlGroup.

This is a bounded live-to-terminal observation, not final execution closure or
source-freeze release. Exact final receipt/result hashes, all known child
deaths and producer/manifest/result joins still require closure review. No
array bodies, raw data or SQLite were read; no tests, jobs, source changes,
staging or commits were performed. Only this review file was written.
