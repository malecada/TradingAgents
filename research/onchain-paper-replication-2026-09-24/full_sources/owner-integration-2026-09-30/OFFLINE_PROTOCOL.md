# Finite maintained-owner integration verification

This directory owns one new `offline01` execution of `scripts/verify_offline.py`
after the maintained source, focused tests, exact bindings and independent review
are committed and pushed. Every previous offline job is closed and stays closed.
The launcher is derived from the accepted matching-package launcher with
its descriptive string and distinct guard owner kind changed, plus exact
dynamic package-source and named offline-test inventory checks. It checks current
and committed bytes for every binding, frozen HEAD, the explicit10GiB disk policy
and absence of competing active/activating replication guards before dispatch.

Launch from the repository root with PYTHONPATH=.: `.venv/bin/python -B
research/onchain-paper-replication-2026-09-24/full_sources/owner-integration-2026-09-30/run_offline.py
--source <full committed pushed HEAD>`. The source manifest is mandatory and
must exist before launch; preparing this protocol does not execute anything.
The immutable `offline01` receipt directory must be unused. A failed or complete
attempt cannot be relaunched under the same identity.

The manifest retains the preceding accepted237-file engineering closure and
adds the maintained modules, focused tests, current integration evidence, all
tracked Python files under tradingagents/tests/scripts and every named offline
test path. Added untracked package/test membership is checked explicitly at
dispatch. Final independent reviews are separate from this manifest to avoid
hash cycles; they must nevertheless be committed before execution.

The resource envelope remains3GiB hard memory,2.75GiB high, zero worker swap,
two CPUs,3GiB host reserve,6GiB startup RAM,10GiB free-disk floor and3,600seconds.
The prior package profile finished within this envelope in1,583.99seconds.
Additional owner/successor synthetic tests add runtime; this prior measurement
is not a guarantee for the new suite. Guard/lease and source/HEAD freeze remain
in force throughout execution. Independent implementation can proceed only
outside frozen source/test bindings and dynamic package membership.

Retain both standard and neural summaries, guard final/live/child-exit metadata,
raw child log, all failures, resource counters and cleanup. Verify exact source
bindings again, monitor/cgroup absence and independent closure before claiming
broad success. No paper data acquisition, graph generation, matching pilot or
financial fit is admitted by this engineering verification.
