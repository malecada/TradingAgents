# Independent initial compact dictionary production review

Acceptance withheld for CD1–CD3 below, pending corrected source and terminal evidence. Review was read-only while check01 remained active. No tests, historical jobs or empirical numerical files were run/read by the reviewer. Only this review note was written.

## CD1 — Completed stage inventory and original inode are not checked

`compact_dictionary.py:155–160` joins the actual stage object, closed state, intent and compact-stage receipt, but omits the exact completed stage-root inventory and original stage inode. `compact_stage.verify` checks the matching/checkpoint subtrees; its outer-root inventory is explicitly a caller obligation. Owner.boundary only checks stage intent at that level, while the old Stage.lease correctly refuses closed stages.

Consequently, a foreign or failed-marker entry under the completed dictionary stage can escape Produced.check until eventual aggregate Owner.finish. A replacement stage directory carrying identical files also lacks the original inode comparison. Require the original stage directory identity and exact `{intent.json, matching, checkpoints, stage-complete.json}` inventory at every completed-stage evidence check, including the final callback-free check. Test foreign/failed entries and late callback insertion; retain rejected evidence rather than cleaning it away.

## CD2 — Cleanup exceptions can bypass owner revocation and failure evidence

In produce's exception handler, owner poisoning and failed.json publication occur after log.fail and fallback log.close. If both cleanup calls raise, the handler exits before revoking the owner or attempting the output failure receipt, and the primary exception may be replaced.

Guarantee owner revocation and failure-receipt attempt in a finally path even when terminal-log publication/close fails. Preserve the original exception and annotate cleanup failures; an unresolved close must remain fatal. The transition lock must remain held throughout. Immediate poisoning before log.fail is not required: log.fail still invokes the live stage/proof lease, so the proposed finally ordering preserves that contract. A regression should inject both cleanup failures and assert revoked ownership and retained attempt residue.

## CD3 — Namespace creation uses a stale live check

At lines 198–201, the last live proof lease precedes full callback-free evidence/parent hashing and durable parent-directory preparation. Those operations may be lengthy. No fresh live check immediately precedes root.mkdir. A guard lost during that work can therefore reserve an output namespace before the later stage boundary refuses.

After parent setup and canonical-root checks, repeat the live proof lease immediately before creating the exclusive attempt. Keep the callback-free numerical checks at their consumption boundaries. A regression should revoke the lease during parent preparation and prove the attempt root is absent.

## Other source observations

The prospective matrix reservation covers all conservative unique-subset entries and a separate readback allowance. The legacy identity-input cap is applied to all admitted sample numeric payloads before fit invokes dictionary_hash, conservatively covering whichever representatives are selected. This limits numeric input, not legacy .tolist/JSON expansion, SciPy scratch or total RSS.

The producer uses Proof.scope in the stage/log/matcher and verifies the returned workload scope. It seals the actual completed log count under the registered capacity-with-exact-completion policy without refunding the conservative reservation. Representative sample indices preserve actual object identity/order; memberships cover each original sample exactly once. Publication omits duplicate sample arrays.

The returned dictionary and every retained matrix are fingerprinted before seal/live callbacks. Rechecks before writing and after final callbacks join numerical data, Proof and stage/output evidence. This addresses the previously identified risk of accepting a new baseline after callbacks modify the numerical result, subject to CD1's missing outer stage checks.

The compact_owner change is a thin existing locked public wrapper around the same internal completion body. The producer owns the transition lock when invoking the internal path. Scientific sample admission is consumed here, but complete-calendar, price/label, full representation/native selection and empirical/resource admission remain separate. No final check01 result is claimed in this note.

Reviewed source SHA256:

- `compact_dictionary.py`: `7f3bee0f2986a9163864b83e6583fa576e205b5c04a87034ab3a8e32123ffa27`.
- `compact_owner.py`: `9ab7ee80246f100324944a2c38295672ceb912b0fa578ea0c21c511cc2c004cc`.
- `test_compact_dictionary.py`: `3ef56f5daf19d67918a59d1ae29b0de4f711994b3e66d5c01deb558855c05f3f`.
