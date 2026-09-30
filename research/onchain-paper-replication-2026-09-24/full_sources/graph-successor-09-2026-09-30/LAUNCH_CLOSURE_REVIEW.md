# Independent graph09 pre-admission launch failure review

September 30, 2026. **Accepted as a failed, closed launch with no admitted research claim. No graph result or empirical cell completion occurred.** Review reconciled the original launch, owner, observer, guard and child-wrapper receipts, source/input hashes and current process/path absence. No body, array or SQLite was opened and no launch was repeated.

The retained launch and owner bind experiment `eth-paper-graph-resource-20260930-09`, nonce `ee890e14eed24561b7970d3f6daaa269`, source `311f698ea406454d2d0bfc46ed1602901c300530`, supervisor **1122456**, monitor **1124827** and recorded start ticks **9205662**. Current HEAD matches that source. All 88 source pins and 120 compact input entries still hash correctly. The observer's launch, owner and guard evidence hashes independently match and its disposition is exactly **`not_admitted`**.

Guard final is **failed** with `RuntimeError: host reserve fell during cgroup setup`. At the final pre-release startup check it recorded **9,660,710,912 available bytes**, **2,965,504 below** the registered **9,663,676,416-byte (9 GiB)** startup requirement. Elapsed time was **4.53458403100376 seconds**, cleanup verified, no high/max/OOM events and no elapsed-time kill. Kernel maximum/high/swap remained 6 GiB / 5 GiB / zero; the 3 GiB runtime reserve, 10 GiB disk floor and 28,800-second wall limit were not lowered.

The `resources.py` control flow checks startup availability before publishing `release.json`; its child wrapper waits for that release before spawning the worker. The actual release file is absent. `child_exit.json` records **exit 125, reason `signal before release`, workload PID null**. Guard `child_exit_code` is null and must not be described as an empirical worker exit code. The guard's sampled peak is **8,359,936 bytes**; the child wrapper separately recorded **8,531,968 bytes** in its terminal snapshot. These are setup telemetry, not graph memory measurements.

The exact supervisor, monitor and wrapper PID **1127216** are now absent, and the cgroup for `onchain-replication-ec2eca3f30c9434db30047f0ea78b0e1.service` is absent. Saved unit state is failed with exit-code result and status 125, while cleanup is verified; this is consistent with pre-release termination, not a successful run. No live reviewer observation was captured before the rapid failure, so the recorded start ticks are owner-receipt evidence rather than independent live readback.

`research_runs/eth-paper-graph-resource-20260930-09` and its source artifact directory are absent. There is no claim, empirical terminal, source decoder output or eight-cell empirical ledger to close. The launch/run directory itself is durable failed-attempt evidence and remains reserved. Graph09 must never be restarted under this identity.

All **15 existing family claim/terminal pairs** remain byte-exact, plus the preserved **17 historical attempts**, so the accounting is still **32 consumed with adopted ceiling 59**, **12 body and 15 financial batches reserved**, and all **1,420 unique fits pending**. Preflight's ready/effective60 calculation was prospective admission; without a first adopting claim it does not adopt the extension. Ceiling 60 remains the reviewed proposal. This is no refund: the launch attempt stays visible, but no additional empirical claim was published or charged by the lifecycle.

A prospective identity10 may target the same still-unfulfilled December graph only through a newly reviewed registration and first-adopter identity correction, preserving this failed gate/owner/observer/guard and the exact 32-spent snapshot. It is not a repeated graph09 launch or a new extra allowance. The proposed dispatch headroom is **9 GiB + 128 MiB = 9,797,894,144 available bytes** before launch, while retaining all registered limits and the mandatory runtime startup recheck. Such a margin is not a guarantee against host-memory movement; wait if resources are insufficient. No successor is released by this failure review.

Exact original evidence hashes:

- `launch.json`: `ecf79f8301ee1cbb6e0b40030c9f2ae4647d1dab7d1981f56e3d5b4a059c8c7f`
- `owner.json`: `811aa5e64752e03500fee565671729a373138929fa28ab1a9a6fca9e878df478`
- `observer.json`: `f458c07a097090e40beeb1d1087c2c127631c0478f16fd022b491353b8635361`
- `guard/final.json`: `634476cf054b4c3f5423426ec3a2bce394931789ec99bd330c41326124d97385`

Only this review was written. No test, admission/generator execution, network call, body read, empirical job, source modification or commit was performed. Timing, financial returns, source semantics and graph feasibility were not measured by this failed setup.
