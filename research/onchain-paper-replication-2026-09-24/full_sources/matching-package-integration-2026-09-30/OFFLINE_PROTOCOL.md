# Finite package verification

Run exactly once: `.venv/bin/python -B <this-directory>/run_offline.py --source
<FULL_COMMITTED_PUSHED_HEAD>` from the repository root, with PYTHONPATH=.
The wrapper verifies exact current and committed bytes for every source-bindings
entry before creating its exclusive offline01 receipt. Existing receipt refuses
reuse. The named target is scripts/verify_offline.py; historical offline01/02
jobs elsewhere are closed and must never be rerun.

The closure retains the previous 163-file offline02 closure byte-for-byte and
adds six maintained matching modules, the new test, derivation/evidence,
this protocol and the new wrapper. source-bindings.json is the immutable explicit
closure; the execution owner additionally binds its hash and actual source HEAD.
Independent package and release reviews must be retained before dispatch.

Limit: 3 GiB memory.max, 2.75 GiB memory.high, zero swap, two CPUs as enforced
by the standard guard, 3 GiB runtime reserve, 6 GiB startup RAM, 10 GiB free disk,
and 3,600 seconds. No competing replication unit may be active or activating.
The guard lease is authoritative; do not duplicate a live monitor. Freeze source
and HEAD while running. No empirical input bodies are inspected by this wrapper.
The named offline target owns its existing admitted synthetic fixture inventory.

After exit inspect both standard/neural summaries, final/child-exit receipts,
OOM/max/high counters, cleanup and exact monitor/cgroup absence. Recheck every
pinned source and HEAD. Preserve failures and partial output. A test failure is
not permission to relaunch this identity. Independent closure precedes any claim
of broad-suite success. All financial fits remain pending.
