# Independent lifecycle successor review — ACCEPT SOURCE ONLY, UNINSTALLED

No material defect was found in the changed constructor/close seams. Acceptance is limited to frozen connected02 manifest `d309ed04d988e7655628e4d42e6852d7ebc039cf08ef023a247b5dcdaa5dfc55` and session source `7f847b02d2c4ca4e17a0b0962a97c49498b0559268b1187aad682c446eec3460`. Connected01 remains permanently WITHHELD; its original review, failed first harness and all evidence were untouched.

## Verified correction

The constructor allocates and publishes a terminal cleanup closure before backend acquisition (`matching_immutable_session.py:105`). It captures the original close callable after acquisition and guards subsequent attribute/pin construction (`:122`). Constructor failure attempts cleanup locally before rethrowing the identical primary; this covers the period before PairExecutor can receive the completed session. Session close uses the independently retained cleanup closure (`:181`) instead of the mutable backend/close fields checked by currentness. A failure invalidating session state still attempts the owned cleanup and retains the primary.

The terminal closure marks the attempt before calling the original close, retains an ambiguous error, and raises that same error on subsequent cleanup calls without re-invoking the original capability. This preserves the prior compiled04 no-retry convention. It does not claim that a descriptor closed after an ambiguous error. Arbitrary corruption of all ownership state, signal interruption at every instruction, helper-internal allocation failures and universal hostile process-memory guarantees are outside this focused result.

## Independent bounded evidence

`review01.py` completed105 checks, including61 manifest-body joins and16 actual-source lifecycle cases. This is not a replay of the previous67/104-check matrices. The full original session class and unchanged PairExecutor call were AST-extracted with fake numerical/graph dependencies; each selected fake backend owned an ordinary real file descriptor. Numerical/native imports were blocked. No array, native library, memfd, compiler, Owner, Admission, Run, claim, financial experiment or network was used.

On actual connected01 source, the three original REDs were reproduced: replaced backend, replaced exposed close and post-acquisition pin-tuple MemoryError each omitted the owned close, poisoned the executor, attempted engine cleanup and left one descriptor for explicit harness cleanup. On connected02, the identical cases call original owned close exactly once, preserve the refusal/MemoryError, attempt engine cleanup and leave no descriptor. A replacement exposed close is never called.

Additional independently selected cases cover failure assigning each of `_normalizer`, `_normalizer_pin` and `_normalizer_functions`; one-time close-capability lookup failure; constructor primary plus close failure; advance KeyboardInterrupt plus failures in both backend and engine cleanup; ambiguous close; state invalidation primary plus close failure; success and unselected backend. The primary exception object's identity was retained in the primary/fatal cases. Engine cleanup was attempted independently even when the backend failed. Three additional terminal close calls on constructed sessions never repeated the owned close; ambiguous cases re-raised the same close error object. Ordinary residual descriptors were closed explicitly by the harness, with that count recorded separately and no candidate closure credit.

CPU3/nice10; pinned `.venv/bin/python -B`; AS512MiB, CPU20s, FSIZE4MiB, alarm25s and external timeout30s. Actual183,171,001ns and23,784KiB peak RSS. Exit0, empty stderr. No failed harness occurred. Every case observation, script and log is retained in this review directory.

## Exact source joins and reuse

All61 connected02 artifact hashes/sizes matched the frozen manifest. The prior independent WITHHOLD review hash14b7da52 was reverified. Restoring only the old constructor and close AST bodies makes the entire session AST identical to connected01. `batched_numeric_reuse.py` contains exactly one corrected session hash, and replacing that literal with its old value restores the entire prior file byte-for-byte. No guard was weakened.

The other four connected module copies, finite policy and compiled helper are byte-identical to the sources authenticated by the original independent review. All six actual to01 inverse patches restored the prior candidate bytes. All six installed-baseline inverse patches restored the current installed files exactly. Original forwarding, adaptive-cache, operation/checkpoint/ranking, default no-load and policy/parser evidence is reused only for these unchanged bodies. No unchanged numerical or source/parser fixture matrix was rerun.

## Remaining limits

This is a Python caller-ownership result using ordinary descriptors. Genuine sealed memfd/dlopen lifetime, actual runtime/library/primitive fingerprints and inventory, complete connected numerical state/checkpoint/assignment/score equivalence, numeric cache/binding behavior, source/Owner admission, whole-process/native capacity and real performance remain untested. Immutable compiled04 evidence supplies only its prior finite unchanged-body support; universal bitwise or exception-timing equivalence is not asserted.

After the active pilot ends, the responsible root still needs the previously queued exact source-union/runtime/Owner admission and bounded connected factory/session numerical and lifetime checks before installation or execution. No Main, candidate01/02, prior review, registration, STATE or Git mutation was performed by this review. No new claim, launch or performance promise follows.
