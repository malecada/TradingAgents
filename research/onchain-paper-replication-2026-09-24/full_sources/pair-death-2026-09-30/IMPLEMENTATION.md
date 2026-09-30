# Failed-owner death observation candidate

The isolated stdlib death.py verifies compact failed-owner evidence without
process action, array/input-body reads, ledger mutation, journal repair or replay.
It was implemented outside Graph10's105 frozen source bindings; the maintained
package and HEAD remain unchanged. It is not imported by any production caller.

A later admitted successor must supply the exact expected experiment/source and
registered evidence references. This function does not itself authenticate that
caller, perform ResearchRun admission, establish parent ancestry, prove source
compatibility, admit workload membership or authorize continuation. The returned
continuation_admitted, outputs_verified and arrays_read flags are false. It is a
read-only checked observation, not a lock or a permanent execution permit.

Evidence paths are fixed to the expected predecessor's actual research_runs and
generic executor directories. Claim, failed terminal, launch, owner, live guard,
observer-death certificate, postmortem cells, unsealed journals and observer are
required. A retained final guard must also be supplied. Every file is a regular,
nonsymlink, single-link same-device metadata file at most2MiB; there are at most10
files. No-follow reads compare inode/type/size/modification/change-time/block
signatures before and after, and verify caller-supplied SHA256. Stat signatures
and death observations are rechecked before return. The access clock is omitted
because reading legitimately changes it.

The exact failed claim/source, launch owner, live monitor and worker command,
death certificate and observer terminal/owner/cell hashes must agree. Observer
inventory includes every applicable executor evidence file, and its unsealed
journal count is checked. This does not independently recompute lifecycle output
hashes or validate every cell, journal or checkpoint; their numerical/admission
checks remain separate. A complete predecessor is refused.

Current boot must match. The exact monitor PID/start ticks must no longer be
alive; the supervisor PID must be absent. Existing historical owner records lack
supervisor start ticks, so unrelated PID reuse conservatively blocks this route
instead of authorizing any process action. A different boot likewise requires a
separate reviewed path. The owned cgroup must be absent or explicitly unpopulated.
No process is killed or stopped, and an inability to establish death is refusal.

The tests use synthetic compact files only and mock OS boot/process/cgroup
boundaries. They do not establish live kernel death or actual ResearchRun
integration. Eighteen tests pass in green02.log (.317s), including the full
read-only join, monitor/supervisor/cgroup/boot refusal, identity/hash/path/link/
size failures, completed parent, missing observer, optional final inclusion,
observer inventory and a changed second liveness check. red01.log retains14
missing-component failures; green01.log retains14 passes in .427s. No historical
job is rerun and no financial outcome is produced.

Next integration: admit the entire exact failed-parent chain through the actual
successor and registered policy; connect death evidence with pair-journal and
representation ownership; reconcile bounded pending/orphan publications without
repeating completed pairs; validate dictionary/MCM workload membership; then
exercise complete parent-failure/child-continuation parity under a real guard.

Independent finding D1 identified that an optional final guard appearing during
validation could escape the initial evidence-inventory check. red02.log retains
two failures: that appearance and a broken final symlink, with two other final
cases passing. The corrected implementation rejects links and rechecks final and
complete-terminal inventory after the last liveness observation; all saved file
stat signatures are also checked again. Original source/tests are retained.
green03.log records20 passes in .140s. bindings-v2.json is the current binding
manifest; original bindings.json retains the pre-review snapshot and must not be
misread as current source hashes. Actual continuation remains unimplemented.
