# Independent frozen candidate01 review

Final acceptance is withheld for the concrete cleanup corrections below. No reviewer tests, network actions or empirical work were performed. Read-only hashing verified all seven candidate source/test snapshots against current bytes and all 26 raw logs in `candidate01.json` (`25cca87b0664b235a26485e477196de896490ba8e7f022d175fedad1bb80b9ea`). The frozen record is `2f4fc5d83218fbbf2a6977f0d924b73e1dafac342d9984b6b1f583772651fba3`.

## NPH5 — Shutdown can discard a fatal arriving during join

`neural_authority.py:101–117`, `ParentAuthority.close`, captures `self.failure` before joining the authority thread, then assigns the stale local value back afterward. A handler already in flight can fail during that join and publish the actual original fatal object into `self.failure`; successful socket close then overwrites it with `None`. The launcher can acknowledge shutdown despite that failed original transition. Merge the post-join thread failure before cleanup/final assignment, preserving original fatal identity. Use an event-coordinated in-flight handler regression; the existing test sets failure before shutdown and does not cover this race.

## NPH6 — Scope construction downgrades uncertain authority cleanup

`neural_physical.py:193–196` notes and suppresses every exception from `authority.close()` while rethrowing the construction primary. With an ordinary construction failure and an uncertain owned socket close, `PhysicalCleanupFailure` is downgraded to the ordinary primary. Promote fatal cleanup chained to an ordinary primary, while preserving an already fatal primary's identity. A bounded constructor fault injection is sufficient.

## NPH7 — Selected guard loses physical cleanup fatality

`resources.py:400–402` converts all `BaseException` objects into a string and later returns state. A one-shot client descriptor/socket cleanup fatal from the selected physical scope need not set the authority server's failure, so no later launcher check necessarily restores its fatal identity. Preserve the selected-route fatal through independent unit cleanup and best-effort receipt publication, then rethrow it. The selected guard's final directory fsync/close at `resources.py:437–439` also still uses ordinary `os.close`; apply the same one-shot primary-aware contract to this owned descriptor. Existing omitted-policy behavior need not change. Target actual selected physical exceptions rather than only a generic ordinary limit failure.

The main original-authority correction addresses NPH1–4 in source: an original carried anchor joins a live original parent; parent memory owns once-only root births and claim hashes; no mutable disk-state rebaselining or parent-loss fallback remains; reads admit regular type/extent before parsing; descriptor-held traversals join root identities. Bounded abstract-socket requests add no secret or external service. The parent-loss refusal is intentional and prevents any unconditional observer/failure-ledger publication promise.

Raw `check13` reports 141 passed and one fixture API error, followed by `check14` with two corrected selected cases passing and 37 deselected in 8.95 seconds; production bytes did not change between those checks. Socket cleanup red12/check12 is preserved but does not close NPH5–7. Synthetic worker accounting covers actual invented nine-cell model/checkpoint output and lifecycle metadata; guard/source admission is mocked. Separate actual RLIMIT subprocess evidence is not an actual systemd/cgroup launch. Logical/allocated accounting is sampled, configured scratch coverage is not a filesystem sandbox, and physical feasibility for the original nine graph populations remains untested.
