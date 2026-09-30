# Sampled guard exit-race correction candidate

The registered-hub offline01 standard phase reported one failure:
`test_success_under_resident_cap_and_two_cpu_affinity`. Its child returned zero,
but the dated sampled guard reported `live process has no VmRSS field`. The raw
status text was not retained, so the exact observed transition is unknown. This
is consistent with a disappearing memory descriptor during process exit; it is
not proof of an OOM or an empirical graph/paper-method failure. Neural verification
continues under the unchanged full-suite source/HEAD freeze.

An isolated byte-copy of the dated guard now takes at most one fresh procfs
snapshot when the first status has no RSS and is not already terminal. A second
real RSS value is counted. An observed missing process or Z/X state contributes
zero for that exited process. Persistent missing telemetry on a live or unknown
state still raises, as does malformed RSS. No limit is raised or disabled, no
historical outcome is rewritten, and no arbitrary telemetry exception is swallowed.
This bounds the extra read; it does not guarantee every possible exit timing is
resolved or improve the historical sampled guard's process-tree guarantees.

Red01 records four deterministic transition errors among six tests. Green01 has
six passing checks in 0.001 seconds. These synthetic status sequences establish
behavior, not the missing raw state of the observed standard-suite failure.
Independent review is pending. After the live full run closes, the proposed
promotion is scripts/research_resource_guard.py with maintained test imports
pointing there, plus deterministic regression tests. The original dated
research/strategy-search-2026-09-11/resource_guard.py remains byte-identical.
The current on-chain cgroup resource guard is unchanged. A new named full offline
identity is required after correction; offline01 must remain a failed attempt.

The original full verification is now closed: standard 2,767 passes, 97 subtests
and one failure in 1,035.23 seconds; neural 766 passes/two CUDA skips in 514.67
seconds. Outer guard child 1, cleanup verified, zero memory events and peak
2,028,310,528 bytes. It remains a failed verification, not an empirical attempt.

After closure, the candidate was promoted byte-for-byte to
scripts/research_resource_guard.py. The old dated helper remains unchanged; the
old maintained test bytes are retained here. The maintained import now points
to the corrected current helper, with six deterministic exit-state regressions.
Promoted-green01 records nine focused checks passing. The isolated live candidate
also passed three subprocess contracts in 0.203 seconds. A distinct full
offline02 is prepared; no empirical release is inferred from these focused checks.
