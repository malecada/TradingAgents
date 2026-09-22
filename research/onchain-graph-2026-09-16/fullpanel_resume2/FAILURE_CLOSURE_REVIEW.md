# Independent failure-only closure review

Approved for exactly one append-only failed terminal for
`eth-full-history-feature-panel-resume-20260922`, after preservation and the
script's immediate stopped-unit/process checks. This approval does not permit
a new claim, replay, raw decode or a resource-contract change.

Reviewed identities:

- Predecessor source: `c739b6f0958e23b90ff5038dd46c9356581369c3`
- `close_predecessor.py` SHA256: `31671b5ed5e19ec927fab5f136ea8cee8bedef3c911fe5894a89dfbf69efe63a`
- `interruption-observation.json` SHA256: `59910ec6898133c0a9064f0c6a23946ddf471252ffc739155bf5ea898d6b5a1b`
- `failure-closure-bindings.json` SHA256: `2f8c667fb5e9542b67af73bef449999828e4266c1c150098e75658b49469a752`

Independent read-only checks confirmed the actual execution HEAD, structurally
valid claim, prior 14 / cap 15, and absence of both lifecycle terminals. All
206 published outputs match the original seed hashes; no newly completed date
exists. Every one of the observation's 1,747 files matches its size and SHA256,
totaling 289,954,127 bytes. This includes the new July 26 partial source scratch,
three unpublished prefixes, guard records and logs. The continuation hash root
is empty. No payload was decoded or recounted.

An independent UTC journal query confirms that systemd-oomd killed the named
unit at **2026-09-22 18:05:58 UTC**, reporting ancestor memory pressure of 52.41%
above 50% for more than 20 seconds with reclaim activity. The final guard
receipt is failed and cleanup is verified. Retained kernel max/OOM/OOM-kill
counters are zero and high events are 16,136. The unit now has MainPID 0,
empty ControlGroup and failed state; the process inventory shows no predecessor
executor. The journal explains this termination. It does not identify the
earlier reboot's cause or prove that this job was the sole source of ancestor
pressure. Missing child exit/terminal memory evidence remains unknown.

Source inspection confirms that closure checks exact script/observation
bindings, unchanged original evidence and empty new hash root, revalidates
source/claim/input admission, then calls the existing locked, immutable
`ResearchRun.fail` path. It subsequently verifies the failed lifecycle and
unchanged evidence. It does not call start or finish, replace outputs, infer
missing success counters or change any original registration. The consumed
15th attempt and exposed calendar remain preserved.

No material blocker was found for this bounded closure. Preserve the full
observation-bound evidence before closure and retain the reviewed source and
bindings in the committed record. This review does not approve a 16th attempt
or establish whether a changed MemoryHigh setting will let the workload finish.
Those require their own source/contract review and pre-claim verification.
