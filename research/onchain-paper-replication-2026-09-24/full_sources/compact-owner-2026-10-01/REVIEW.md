# Independent compact owner review — initial and correction findings

Acceptance withheld. This note preserves the initial findings and the remaining Binding-replacement issue identified during corrected-source review. It does not claim a terminal result for the active check03 suite. No tests, empirical jobs or source edits were performed by this reviewer.

## Initial findings

The original source, retained as `owner-check01.py`, had four material gaps:

- **CO1: runtime state was not bound back to owner/intent metadata.** `Owner.lease` compared saved byte strings to disk, but changing `maximum`, `reserved`, policy or a stage's count/scope could redirect execution/reservations while those byte strings stayed unchanged. Require a pinned runtime contract, rederived intent and cumulative reservations.
- **CO2: dangling terminal symlinks escaped inner leases.** Marker checks used `exists()` only. Refuse both existing entries and symlinks for compact and representation terminal markers.
- **CO3: wrapper bytes were not reserved.** The cumulative counter included primitive log/checkpoint/score allowances but excluded owner start/completion, stage intent and stage receipt. Reserve these before namespace creation, including failure retention.
- **CO4: stage creation used a stale lease.** Scope computation reads numerical sources after the boundary lease, then Stage immediately created its directory. Recheck the live owner immediately before `mkdir`. The mutable reservation/creation transitions also needed serialization or a declared single-thread contract.

The initial check01 fixture passed a frozen mapping into PairLog's dictionary-only schema: its saved result is **2 failed, 8 passed in 112.29s**. The separate four reviewer counterexamples then report **4 failed, 10 deselected in 42.16s** in red02. Corrected check02 reports **14 passed in 152.17s**. The corrections inspected introduce configuration and intent checks, a pinned reservation counter plus boundary recomputation, `2*65536` owner bytes and `2*8192` per-stage bytes, bounded stage intent encoding, symlink-aware markers, a lease immediately before creation, and nonblocking locks around begin/finish-stage/finish. These directly address the listed mechanisms. A dedicated concurrency execution is not claimed from the listed tests.

Additional red03 evidence reports **2 failed, 15 deselected in 26.85s**: a valid stream for a different required graph and a log with the wrong iteration bound were accepted. The current `_stage_bindings` checks the registered iteration limit and stream graph against the selected stage name before sealing and again during aggregate verification. Final acceptance of those changes awaits the complete saved test result.

## Remaining blocker: actual Binding replacement

**CO5 — `Owner.configuration`/`Owner.lease` do not pin the actual Binding.** The configuration digest includes policy, matching settings, namespace, identity and owner bytes, but omits `self.bound`. Assigning another actual fresh Binding leaves those checks unchanged. The following `lease` and `boundary` calls follow the replacement run/guard while `owner.json` and the compact identity still name the original claim/context. This is a one-field runtime mutation, not merely alteration of private digest fields.

Pin the exact admitted Binding and its run/record/context/journal identity, and validate that pin before invoking a bound check or lease. A second genuine Binding fixture substituted after attach must refuse. The constructor's initial `type(bound) is Binding` check does not protect subsequent use. No such counterexample was executed by this reviewer.

## Scope

The component creates an explicit fresh compact namespace and joins registered plan/job backend and policy selection to a real Binding. It does not derive scientific dictionary/MCM workloads, publish numerical representation artifacts, admit a successor, select native production or replace the representation seal. Inner leases depend on a separately enforced frozen source/input contract; full source/input/runtime checks occur at boundaries. Logical reservations exclude filesystem overhead, matrices, scratch and preceding attempts. Zero-pair dictionary fixtures are ownership checks, not sampler/dictionary provenance evidence. Actual guards remain mocked in these tests.

## Retained identities

| Evidence | SHA-256 |
| --- | --- |
| `owner-check01.py` | `c95836799340de113a9db8e45040579e7a692f76b0dbcabaff350f3ba9eef71f` |
| `owner-check02.py` | `ec7f8d4cd9f687f8d9c316d44d194e578986dd0bbbde116fbe72546e749a205e` |
| `test-check01.py` | `0c83a3ad6515ae3229f6c0d98a3a1bc7d715a565db41cde7797b713d51d1973a` |
| `test-check02.py` | `ff1b989f449ff36047d9692c20a881d7a012772b14db04f9d4491001033b8ab3` |
| `check01.log` | `53f36dd2dc813e3d94f8aaaa323ede78e1369a085cf0e29a57179a07f682129e` |
| `red02.log` | `f89079d2691b7696be6217a15735f6d5cc2984bd72abc0e8bddc2b1464d5a1cd` |
| `check02.log` | `aa16df06c2a250d10923daf993f93806eca222db3b886ab00463095d5c274d2c` |
| `red03.log` | `3a808513817a59d5cc7123e69ef2018b64fcb6cca3b12e4bd53a0173da48bd71` |
