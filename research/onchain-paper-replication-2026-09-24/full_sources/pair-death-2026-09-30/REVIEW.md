# Independent failed-owner death component review

Acceptance withheld for D1 below. This is a bounded review of compact failed-owner death evidence, not of the deferred registered ancestry/continuation wrapper. Source and retained synthetic evidence were inspected without running tests, jobs, empirical bodies or numerical arrays. No implementation or frozen Graph10 source was changed; only this review was written.

## D1 — optional terminal evidence is not rechecked after validation

`death.py:76` checks whether `guard/final.json` exists against membership of `final` in the supplied proof, but only before reading the other evidence. The final recheck at `death.py:114–116` covers the signatures of files that were present initially, contradictory `complete.json` and OS liveness; it does not recheck the optional-final inventory.

A concrete counterexample is an initially absent final receipt, followed by creation of `guard/final.json` during the first `dead()` observation. Every supplied evidence hash/signature remains unchanged, both liveness observations can correctly report dead processes and an empty cgroup, and `complete.json` remains absent. The verifier then returns success despite omitting terminal guard evidence that now exists. This violates the component's explicit complete observer-evidence snapshot claim; it does not require implementation of registered ancestry or numerical recovery.

Recheck final presence against proof membership near the final snapshot/return boundary. A symlink, including a dangling one, should not silently count as absent terminal metadata. Add a synthetic negative that creates the optional final during the first mocked liveness callback, leaving all other evidence and OS answers valid; require rejection. This finite recheck remains an observation rather than a concurrency lock, which the API already states.

## Inspected sound behavior and limits

The expected experiment and source restrict fixed proof paths. Claim failure joins the supplied claim hash; owner joins launch, live monitor PID and exact worker command; death joins live hash and owner/boot/cgroup/unit/command. The observer inventory exactly matches maintained `job._observer_evidence` keys for launch, live, optional final, death, cells and journals. Existing supplied final metadata must join that inventory and the live identity. Metadata reads are bounded, same-device, regular, single-link and nonsymlink with no-follow descriptors and stable signatures excluding atime.

Monitor death uses saved PID/start ticks on the same boot. Supervisor absence deliberately refuses PID reuse because no historical supervisor ticks exist. The owned cgroup must be absent or unpopulated, and liveness is observed twice. The return explicitly withholds continuation, output and array verification. Cell/journal inner semantics, admission of trusted expected identity and proof references, actual workload membership, ancestor budgets and checkpoint correctness remain caller obligations and are not claimed by this component.

The retained `green02.log` reports18 passes in0.317seconds; `green01.log` records14 passes in0.427seconds. The fixtures use real compact metadata/hashes while mocking OS boot/process/cgroup boundaries. Their success does not establish live kernel death behavior. No suite was rerun during review. The optional-final fixture at `test_death.py:115–123` covers initial omission and included final evidence, but not D1's change during validation.

Inspected source SHA-256: `716811b184a85706b5b616ce5386940e79d9cb6b1beb8fd0ba0398a7a2de4900`. Test SHA-256: `bd78601d69b5be3c937df1fe0255fe624b159bdf0bfd98bd958cd2323f46e7f3`. `green02.log` SHA-256: `8e99fc606562598efc52e3b32701e0e4a1d8a6a0179fc6eabe6370e6a681e5ca`. Review HEAD remains `6c4d9402cb06f135cb799afac1be00708f3b229e`.

## D1 closure — September30,2026

Accepted for the isolated failed-owner death observation scope. D1 is closed; no remaining material blocker was identified within that component scope. This supersedes the initial withholding while retaining its counterexample and the failed evidence.

`death.py:76–80` now rejects optional-final and complete-terminal symlinks, including dangling links, and checks inventory initially. Lines118–120 repeat the liveness observation, then inventory, then every retained file's stable signature before returning. The missing final inventory is therefore rechecked after the last mocked OS observation, and mutations to supplied metadata during that observation also cannot escape the final signature pass. This remains a finite observation rather than a lock.

The new tests at `test_death.py:134–143` directly cover a final appearing during the first monitor-death callback and a dangling final symlink. They preserve valid dead-process answers and unchanged supplied evidence, so rejection targets D1 rather than incidental proof-hash failure. Retained `red02.log` shows the two expected failures and two passing related cases before correction. `green03.log` reports20 passes in0.140seconds after correction. No tests were rerun for this review.

All223 entries in current `bindings-v2.json` independently match their file bytes. Its212 inherited entries exactly match the prior owner-component manifest, with11 additions. The original `bindings.json` is retained as historical evidence and is not a current source inventory. Preserved `death-before-inventory-fix.py` and `tests-before-inventory-fix.py` exactly match the initial review's source/test hashes. All105 frozen Graph10 source hashes still match, and HEAD remains `6c4d9402cb06f135cb799afac1be00708f3b229e`.

Verified SHA-256 identities:

- `death.py`: `f76a96274e77d4f728d9d7e0b93db2a8bb4e663654ae59c0480f6c66192c3ff8`.
- `test_death.py`: `2f07d956490abe8d8463fb8f8794d13d9c6a9c6e881586007e78698889f18329`.
- `green03.log`: `2b2f97dbca14c3f8862f5850c298f6fd275287bb0b94633008b81485f0166b8e`.
- `bindings-v2.json`: `667167e208c5abe3f17f9d16663ce6d274279cf594caa940e6a21a41a35d33c4`.

Unchanged limits: OS death/boot/cgroup boundaries remain mocked in the saved tests. Trusted expected identity and exact registered proof references must be admitted by a later caller. Actual ResearchRun ancestry, workload membership, cell/journal inner semantics, source compatibility, numerical checkpoints, orphan reconciliation and continuation are neither implemented nor admitted here. No live process death, empirical body, array, job or financial claim was tested. Only this review section was appended; source, ledger, registration and the active Graph10 job were untouched.
