# Independent live-owner review

The observed invocation is consistent with the reviewed single-profile release. This is a live observation at approximately 2026-09-30 11:39:11 UTC, not terminal acceptance. No body reads, tests, new jobs, process controls or source changes were performed.

HEAD is the recorded committed source `e6417c6f2f59c1ccf9fdb9ffd2af4c5b59020977`. All 100 bindings independently match both current bytes and that commit. The fresh preflight at 11:38:01 UTC records absent identities, no active replication units, 9,687,330,816 available RAM bytes and 24,673,259,520 free disk bytes. RAM met the profile's 4 GiB startup requirement but was 110,563,328 bytes below Graph 10's 9,797,894,144-byte dispatch requirement. Disk exceeded both the profile's 12 GiB prerequisite and Graph 10's requirement. The recorded Graph 10 priority decision is therefore consistent with those observations.

Direct `/proc` readback confirms monitor PID 1163863 has exact start ticks 9655861. The saved observation associates it with session 50890 and unit `onchain-replication-9e948629b8e94d198f10af289ec6eadc.service`. Worker PID 1163870 is in that exact cgroup and has CPU affinity 0–1. The cgroup contains its wrapper and worker, not a second independent profile. The active-unit listing and matching cgroup-directory listing contain only this replication unit.

Direct kernel reads confirm `memory.max=1073741824`, `memory.high=805306368`, and `memory.swap.max=0`. All live memory high, max and OOM counters are zero. Saved live guard controls also retain the 3 GiB host reserve, 4 GiB startup, 10 GiB disk floor, 1,800-second wall limit, reviewed worker command and two-CPU readback. No limit reason or retry is recorded.

At the inspected live sample, elapsed time was 61.841714096 seconds and sampled peak memory was 169,181,184 bytes. Phase was running with no child exit code. `started.json` exists; `result.json`, `guard01/final.json` and checkpoint receipt files did not yet exist, and the child log was empty. Those observations establish an owned running worker, not an independently observed internal algorithm cursor or completed checkpoint.

HEAD and all bound files must remain frozen while this owner is active. Graph 10 and other replication jobs must wait for terminal cleanup. A later result requires actual guard closure, source rehashing, complete retained checkpoint/score reconciliation and exact owner absence; no full-schedule success, numerical outcome or feasibility is inferred here.
