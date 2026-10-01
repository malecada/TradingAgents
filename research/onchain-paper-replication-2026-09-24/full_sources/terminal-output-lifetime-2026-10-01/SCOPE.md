# Terminal feature lifetime across registered output additions

The predecessor native-batch-executor/check02 failed after both synthetic fits:
restored prediction reached the original sealer's exact output inventory and
rejected the legitimately published batch ledger/control files. That failure and
all predecessor sources remain unchanged. This successor derives only seal.py
and native_map.py and adds an output-observation helper; no financial execution
or cold/historical admission follows.

The sealer's original strict transition checks remain in place, including inside
the lifecycle lock. After publishing its complete proof, it creates the tracker
from the exact pre-existing plus its own binding/journal hashes. Only the returned
terminal lease uses this tracker. Original outputs remain pinned. Additional names
must be declared by the same admitted run and present in its actual published
output registry. Every observation takes the same lifecycle lock as write_json,
checks exact registry/directory membership and streams each bounded file through
the strict reader. Original and newly observed SHA and file signatures are pinned;
deletions, registry replacements, same-byte inode replacements, changed contents,
partial/disk-only/registry-only/foreign entries and oversized files refuse. New
pins are accepted together only after every check passes. This establishes file
identity, not semantic correctness of a batch ledger or protection against
unobserved external mutations subsequently restored between observations.

The selected max_metadata_bytes bounds each output; admitted output-name count
bounds the number of files. No whole-workflow disk/RSS/performance claim follows.
The tracker is a private compositional helper, not an admission ticket. Its source
and the derived imports are included in the new source closure. Source/runtime,
input, graph/dictionary/MCM/terminal provenance checks remain in the derived lease.
No nested lifecycle acquisition occurs in the original transition. The current
caller must not call the returned lease while already holding the lifecycle lock.

Focused red01:6methods/25subtest failures0.007s due missing tracker, exit1.
Focused check01:6methods pass3.343s, session93280exit0. Actual temporary ResearchRun
publication covers valid additions, original/new mutation/deletion/registry change,
same-byte replacement, invalid registry/file states, caps and controlled concurrency.
The writer pauses after durable file creation but before registry publication;
the observer must wait for the writer's lifecycle lock to release.

A new registered executor integration inherits the strengthened synthetic test
and selects the derived native map. It covers actual proposed direction/regression
fit, checkpoint artifacts, exact expected prediction rows and restored-model
prediction parity, metric reconciliation, wrapper release and duplicate refusal.
Tiny synthetic settings are unchanged and explicitly differ from paper-scale
settings; the kernel guard remains mocked. No financial data or model fits occur.
The maintained metric float64 correction is included as already documented by
native-batch-executor/FAILURE_CHECK01.md, with52 focused checks passed. The two
failed integration identities remain closed and are not relaunched.
