# Fresh prelaunch environment route for unchanged Graph 10

Graph 10 has never launched, reserved an execution owner, read its empirical
inputs or claimed an attempt. Original gate SHA-256
4769eae1d84bb35b175b1604b6982ad67e97f42bc65309f1532d3de2bbea5f46 remains immutable.
The completed temp-check01 and closed dispatch-wait01 are retained. The temp
check passed, but every sampled wait observation failed the stricter graph RAM
minimum. Its terminal evidence is now stale for launch and cannot be replayed.

This version changes only the prelaunch route: run_temp_check02.py writes one
exclusive temp-check02; preflight02.py reads gate-v2.json, requires temp-check02
complete/clean and no older than300seconds, and writes execution-preflight02.json.
All original helper bytes remain pinned. The graph identity is still
eth-paper-graph-resource-20260930-10 with the same original failed pilot parent,
December23–30,2024 data,8,617,920 rows/232spans,seven daily cells plus graph,
configuration, runtime, source wrappers, outputs and resources. The11 inherited
experiment objects and all original bindings remain unchanged.

The existing proposed budget60=32spent+12body+15fit+1December allocation is
unchanged, unadopted until a valid claim. Adopted ceiling remains59. No allowance
is added, refunded or consumed by refreshing engineering temp evidence. All1,420
financial fits remain required. This amendment does not reopen Graph09.

Check no active owner, absent Graph10 claim/execution/source identities, pushed
HEAD, RAM>=9,797,894,144 and disk>=22,103,159,134 before starting temp-check02.
Use sequential checked subprocess calls: a refused resource check must stop before
the temp check; any temp/preflight failure must stop before graph dispatch. After
the temp check run preflight02 and recheck RAM/disk immediately before launching
the exact gate-v2/Graph10/source tuple once. Preserve every result. Never restart
closed temp-check01/02 or a reserved graph identity, lower limits, or extend
freshness. Source HEAD freezes at any actual graph launch.

Independent exact-diff review and commit/push are required before this route is
used. This amendment is preparation only and does not establish fresh conditions.
