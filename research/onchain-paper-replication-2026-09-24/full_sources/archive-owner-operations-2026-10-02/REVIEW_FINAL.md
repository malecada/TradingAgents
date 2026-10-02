# Independent final operation-reservation disposition

Accepted for durable whole-operation reservations bound to the existing current compact owner. AOO1–5 in REVIEW_INITIAL.md and REVIEW_CORRECTIONS.md are resolved within this scope. Earlier findings, source/test snapshots and failed evidence remain preserved. No tests, transfers or empirical jobs were rerun by the reviewer.

The metadata category now uses the registered workflow metadata limit. Attach's failure path calls internal `_close` while holding the owner transition and preserves the primary error. Public operation leases are serialized, active/terminal state is checked after callbacks, and writer leases require the original stage to remain active. Newly owned descriptor closes use fatal one-shot cleanup with primary preservation. Failure-marker publication explicitly rethrows CleanupFailure rather than swallowing it. Finally, the component's own transition decorator and attach release the captured acquired lock, while post-callback checks refuse changed owner/selection/transition bindings. The old owner's transition decorator is unchanged.

The initial fixed reservation now includes4*META_LIMIT. Independent arithmetic for the positive fixture's one writer and four reads is `4*8192 + (1,000,000+3*8192) + 4*(600,000+3*8192) = 3,555,648` metadata bytes, matching the literal test assertion. Remote payload remains200*168 and decoded member allowance7*200*168 for that stage. These are full-capacity reservations, not measurements of actual transfer or retained physical allocation. The prospective selection's full required-stage control allowance remains explicit.

## Retained evidence

- Initial check01: **3 failed, 1 passed in131.14s**, including the original key error; it is not passing acceptance evidence.
- Review-red01: **3 failed, 6 deselected in78.94s**, reproducing public close during lease, masked attach failure and ordinary constructor close error.
- Corrected baseline check02: **9 passed in309.78s**, including completion-write failure and actual owner poisoning after intent publication.
- Review-red02: **2 failed, 9 deselected in66.66s**, reproducing swallowed failed-marker cleanup fatality and wrong-lock release.
- Final targeted check03: **5 passed, 6 deselected in196.09s**: full finite positive claims with exact final totals, public close during lease, attach primary preservation, failed-marker fatal propagation and late lock replacement.

There was no combined final eleven-case run. Source deltas, actual fault injection points, exact cause assertions, retained reservation checks and original-lock reacquisition were inspected independently. Cleanup regressions inject errors after a real close; they prove fatal propagation and lock release, not recovery of an actually leaked descriptor. The late owner-revocation baseline creates a real poisoned owner after durable intent publication. No broad exhaustive fault-injection claim follows.

## Accepted boundary and limitations

Attach consumes the prospective selection under the actual owner's nonblocking transition lock and reserves an exclusive deterministic namespace. Claims bind actual owned stages, one writer per stage and finitely many later reader claims. A sole active operation, durable intent before handoff, exact metadata/inventory checks and retained counters prevent ordinary reuse or refund after ambiguous failure. Failure to publish completion retains the spent claim. Successful completion records only a caller-supplied reference. Source/current-owner authority is rechecked; no historical owner or reopen route is admitted.

This component does not install an archive writer, dispatch transport, meter actual bytes, validate a caller reference's archive/scientific result, seal archived stages into the owner, switch publication/terminal readers or admit post-owner-close consumption. Subsequent adapters must consume these claims and check live authority before actual operations. Tests use synthetic actual ResearchRun/Binding/Owner fixtures with mocked OS guard. No real network, OS-guard execution, empirical data use, whole-workflow physical quota/RSS feasibility or atomic filesystem snapshot is established. Physical allocation, protocol/diagnostic overhead and transport buffers remain separate from the logical reservation.

## Inspected SHA-256

- archive_owner_operations.py: `856acd0dc9398a4f9709a4161c33d4b644e9ee9641bf401471b53954ecbfc11b`
- archive_owner_policy.py: `81b0e2fa4220c45461ffad850209e92819b65a56a7037887d1d7ba92c97956c9`
- test_archive_owner_operations.py: `6b7e39b26b5ec1bbe6d98b451316a042a9a0489ef06590ad91436652ebd74b61`
- operations-check02.py: `afa68ea915702583b01bac42353c0574c231f2eb519b94ac805d88df6d3e85f6`
- test-check02.py: `a0c05240b5e2197e5744ac617b0512476317646f09bf47b70914e24fa56b117c`
- check01.log: `ebd607b8065eba7728e37e13d974a93260c1f085801849d0f91f60ff85515a4e`
- review-red01.log: `fe1ea0775565e5cd937e49011756f3e8e310e1d938a30e9015b9bcb4449f8287`
- check02.log: `d5a619cd39b670361b9c57f7b911eb04ba0dfeeb75c13342582b4d1f78f8fa55`
- review-red02.log: `8af2e80333d2b3c12471c9814cc34f48a8185b3ccf23ffb1ba2ad196872fb518`
- check03.log: `3cdf212c37eb3b03e30006f6e27b44b9882922e45789c8ea146dd3ee6ff1ed3c`
