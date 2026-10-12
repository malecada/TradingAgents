# Target entry-boundary value coalescing

Status: UNINSTALLED; focused synthetic engineering qualified only. No empirical authority, financial admission, run, numerical import, source release, elapsed improvement or capacity claim is established.

The candidate extends `target_lease` with private `_return_value=False`. An explicit true request requires exact boolean `boundary=True` and forwards the existing current invocation `Lease.check(..., _return_value=True)` result. Invalid interval/value requests close the contract and scheduler before target registration. Default calls retain their original callback arguments and discard any return. No cached result is stored on Target, Lease or execution.

Selected leased `Target.check` captures that entry-boundary value in a local variable. It retains the interval `self.lease()`, registered manifest SHA/body read, canonical identity comparison and final full boundary plus graph/content/motif/scope guards. Only the redundant middle `execution.check()` is removed. The no-lease path still calls execution once through self.lease and once after the manifest read, in the original order.

The underlying `Lease.check`, `_full`, `_checked_value`, `Target.final`, `Target.lease`, `_pins` and `derive_scope` are unchanged. Existing Lease.check already collects this invocation's actual full return, checks scheduler freshness, rejoins Owner currentness, stage integrity, original metadata, fingerprints, identity and the captured baseline, then returns an independent decoded dictionary. The candidate does not substitute an interval-only value or reuse a historical successful admission. The new forwarding wrapper retains genuine Target/Lease type and execution identity requirements.

## Static reduction and remaining work

The selected direct Target.check path currently performs three execution checks: entry boundary, middle explicit execution check and exit boundary. The candidate performs two. Each removed ImportedExecution.check currently contains two source admissions. This eliminates two admissions per selected successful Target.check, or ten for five explicit checks in compact_mcm._prepare. Interval thresholds may cause additional checks through self.lease; those remain. The candidate adds the already-existing checked-value rejoin to the entry boundary; its cost is unmeasured. The previously measured native36 aggregate of 160 source admissions is not a callsite trace and cannot establish how many times this seam executed. No wall-time saving is inferred from the static count.

Root integration must refresh authenticated source/currentness/expected-code pins and review the changed check boundaries before any registered execution. Whole-stack genuine authority/currentness proof remains unperformed by this source-only fixture. No source files outside this directory were edited.

## Explicit failure-timing change

The manifest read remains between fresh entry and exit validation. A current/original mutation during that read previously could fail at the removed middle execution check or its identity comparison. The candidate detects a persistent mutation at the retained final full boundary. Thus callback order and exact failure priority across these two locations are not identical. If metadata changes during the read and the final boundary subsequently raises MemoryError, the candidate reports MemoryError; baseline reports the earlier execution-identity mismatch. A focused test records this difference. A transient mutation that is restored before final validation need not be observed; no atomic writer exclusion or between-boundary mutation detection is claimed.

Failures in target_lease/Lease.check close both contract and scheduler, including post-read final-boundary metadata, content or revocation failures and late fatal exceptions. A manifest mismatch still fails before the final boundary and remains outside the poisoning wrapper. A graph hash mismatch in the outer final guard also remains outside that wrapper. These two unchanged cases refuse without newly poisoning the lease; claiming universal poisoning would be incorrect. Selected post-read current/original mutations that baseline rejected outside the wrapper now fail inside the final wrapper and poison it.

## Verification actually executed

Pinned `.venv/bin/python test_boundary.py --baseline`: 15 tests, expected RED with five failures and nine errors (including subtest failures/errors). Baseline lacks the new forwarding keyword, retains three execution checks, and has the old late-failure timing/poison behavior.

Pinned `.venv/bin/python test_boundary.py`: 15 tests PASS in 0.363 seconds. Tests compile actual source AST function bodies and use plainly synthetic metadata callbacks to exercise their control flow. They do not instantiate empirical Owner, run an admitted ResearchRun, impersonate authority or load numerical libraries. Actual existing stdlib Interval scheduler code is used. Coverage includes fresh entry+exit counts across repeated invocations; unchanged legacy order; independent decoded values; interval nonreturn and invalid request poisoning; original checked-value mutation refusals; post-callback current/original/baseline/fingerprint changes; post-read metadata/revocation/content/graph refusals; manifest priority; late fatal failures; explicit mixed-failure timing; unchanged guard ASTs; no numerical imports.

`prepare.py` provides fixed literal replacements with exact occurrence counts, saves original and candidate source bodies, emits unified patch/inverse files, and asserts both byte-identical literal inverse and AST inverse. `source-manifest.json` records baseline and candidate SHA256. Evidence hashes are in `artifact-manifest.json`. No empirical or full test suite was run.
