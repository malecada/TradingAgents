# Resource guard v2: bounded engineering review

**PASS for the declared single financial process with synchronous leader-thread
helpers, default 512 MiB sampled RSS, two allowed CPUs and 120-second wall limit.**
This engineering disposition does not reopen the exhausted dated-family budget
or admit any financial rerun. A tighter options resource contract requires its
own launcher/configuration and complete synthetic workflow preflight.

## Process-exit correction

`resource_guard_v2.py:13-32` handles ENOENT/ESRCH as a departed task, recognizes
zombie/dead states, retries unknown live RSS once after 20 ms, and uses a restored
RSS value if available. Persistently unknown live RSS raises with PID and state;
it is not replaced by zero. The existing memory, wall, launch-failure and exclusive
report behavior remains. The added detection latency is explicitly disclosed.
The old guard SHA256 remains
`4a4d6d17d144fa769bccd4f799828cc6c63dc55d89a521a24716c0fd17f5cbf1`.

All four focused v2 synthetic tests passed independently. Additional independent
invented status sequences verified running-without-RSS followed by zombie or
dead state: both return zero only after the bounded second observation. Existing
tests cover restored RSS, disappearance, persistent unknown live RSS, ESRCH,
oversized resident allocation, timeout and failed process launch.

## Lifecycle and statistics preflight

The new preflight runs the invented eight-book nonsingular OLS/HAC calculation,
two `ResearchRun` examples in automatically removed temporary repositories, and
100 short synchronous Git helpers. Source inspection confirms that the lifecycle
examples create their own toy registration, claims, input reads, output writes,
completion and verification. No actual registered research inputs are read.

An independent invocation under the exact v2 CLI wrapper completed successfully
in 4.061285 seconds, with sampled aggregate peak 431,153,152 bytes and child
`ru_maxrss` 212,852 KiB. All eight invented exposure calculations and both toy
lifecycles completed. This exercises the source-check subprocess interaction
missing from the earlier preflight. The prior failed v2 synthetic report and
the coordinator's fixed successful report remain separately retained.

The larger aggregate sample is consistent with conservatively double-counted
shared memory during synchronous child creation; it is not evidence that the
individual financial process exceeded its resident threshold. The measurement
also shows why a 256 MiB options contract cannot inherit this 512 MiB preflight
as proof of its own headroom.

## Scope and remaining integration requirement

This is sampled process monitoring with possible transient overshoot, including
retry latency, not an instantaneous kernel RSS cap. Leader-thread child traversal
does not support detached/background children or subprocesses launched by other
threads; the registered process model must retain that restriction. Two-CPU
affinity limits compute concurrency and numerical-library thread settings; it
does not prove a universal two-OS-thread process ceiling.

At this reviewed version, the CLI has no custom RSS/CPU arguments and defaults to
512 MiB/two CPUs. `run_guard` accepts a custom RSS threshold, but `_limits` and
thread variables still select two. A 256 MiB/one-CPU options invocation therefore
needs explicit reviewed parameterization or a separate preset, then its own
synthetic full workflow under that exact entry point. This is a pending options
integration requirement, not a blocker for the reviewed default v2 behavior.

| Reviewed source | SHA256 |
|---|---|
| `resource_guard_v2.py` | `feb2c1ed2984100b069261cceaf6d7a1bdac4406eff3dee5b18fdc51f6965298` |
| `resource_lifecycle_preflight.py` | `0d6f980f5f1e9fc5e60f84e789d55b619825fe5fb88410c7833339553cedf669` |
| `tests/research/test_resource_guard_v2.py` | `02fdd7c8c091a168a530b5caa4079bc595f724206b1bb570b204e4962fb99421` |

Untested: actual research inputs/results, economics, account execution, exact
historical process transition, arbitrary descendant topologies, instant between-
sample memory maxima and external backup. No additional higher-effort review is
needed for the specific exit-transition correction. Dated execution remains
deferred under the preserved exhausted budget.
