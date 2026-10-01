# Independent initial review — source approach accepted, integration pending

No material blocker was identified in the inspected output-lifetime correction. Final acceptance requires the new closed executor integration and final source/evidence bindings. No tests, jobs or empirical numerical reads were performed by the reviewer; only this review was written.

The failure being corrected is precise: maintained execute_batch legitimately publishes controls and ledger outputs after fitting, whereas the predecessor terminal lease required its original exact output inventory forever. This successor preserves the old transition checks and changes only the returned post-completion lease to admit bounded, monotonically observed same-run output additions. It does not weaken numerical terminal ownership or reopen a producer.

`Outputs` requires the actual ResearchRun and exact current baseline. Every baseline hash remains required. Additional names must be registered for that same admission and present in the actual published-output registry; disk membership must equal registry membership. All observed files are checked through the strict reader for containment, regular/single-link/same-device identity, bounded size and content SHA. Stored signatures also refuse replacement of previously observed files, including replacement with equal bytes. New observations are committed to the tracker's state only after all files, final inventory and registry checks pass. Deletion or rebinding of any observed output refuses. This validates output identity, not the semantic accuracy of its ledger or control contents.

Construction and observation acquire the actual lifecycle writer lock. This prevents adopting a file between `_immutable` publication and its registry update, and avoids a spurious failure from the writer's temporary file. A failed write leaving a disk-only output remains a refusal rather than becoming a baseline. The derived sealer creates and invokes the tracker only after completing its original exact transition outside the seal lock; its earlier leases retain the old no-reacquisition path. The returned callback uses the tracker and therefore does not introduce the nested-lock deadlock discussed during design review.

The source diff is limited to the local output-tracker import/source declaration and post-completion callback in a derived sealer; its publication dependency points to the existing corrected publication helper. The derived native-map diff changes its sealer import only. The executor wrapper selects that module through the actual fixture chain and inherits the strengthened metric/prediction/checkpoint assertions. Its full execution has not yet been observed. Earlier dated accepted sources and both failed executor identities remain separate evidence.

Saved focused check01 records six passing methods in 3.343 seconds. The fixtures use real temporary ResearchRun publication and cover legitimate additions, original/new byte and registry mutation/deletion, equal-byte replacement, partial disk/registry state, foreign names, broken links, pending files, oversize refusal, invalid inputs and omitted baseline. The controlled writer/observer case pauses the actual writer after file publication but before registry update and confirms observation waits for the lifecycle lock and completes afterward. The initial red result was missing-component failure, not execution of these cases against an older tracker.

The existing selected seal metadata cap bounds each newly observed output; a larger real ledger exceeding it remains unsupported until prospectively admitted. Repeated streaming checks, concurrent mutation outside the coordinated writer, whole-workflow RSS/physical quotas, cold/historical saved admission, job_payload dispatch and empirical release are not established. The unchanged native-map wrapper-lifetime and archived pair-payload qualifications remain in force.

Reviewed SHA256 values:

- `outputs.py`: `a0d44a625cebf30060764c2515f23dae150671c2ade221a11c17ec91d533d727`.
- Derived `seal.py`: `a85fe1fa35859acbf948162e60e45cb33e6e76aaedb7532340eacd902c52d1ec`.
- Derived `native_map.py`: `0462c2eb5cb8991b35e631b1ea45669afd70f9df97656cd4d8ec1e2abfcb7ef7`.
- `test_outputs.py`: `d13654962e881c15df0ef5ba1a0fc0e66e3239b546c0569345daecd8bccdd02c`.
