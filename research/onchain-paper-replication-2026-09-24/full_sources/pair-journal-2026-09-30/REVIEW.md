# Independent artifact pair-journal review

Initial source acceptance is withheld pending the concrete continuity finding below and resolution of the reservation-contract ambiguity. Review used source and retained test logs only; no tests, registered jobs, array bodies or empirical inputs were executed/read. Only this review was written.

## J1 — published pair does not prove its recorded continuation

At initial `journal.py:79–86`, artifact publication checks exact path/hash, manifest size, owner, numerical identity and kind, but never checks the PairSession manifest's `parent`. The reserve event records the current predecessor at lines 113–120, yet a child can reserve that predecessor and then call `PairSession.create` under the derived child owner instead of `resume`. Its fresh progress or completion has the expected owner and identity, so publication is accepted despite `parent=None`. The journal would present continuity that the actual artifact does not establish. This is an artifact join, distinct from externally admitted ResearchRun/death ancestry.

Require the first publication of a successor pair session to bind the exact inherited latest reference and its artifact owner. Later publications within that same session must retain its fixed session-parent relation; they should not pretend the previous same-session checkpoint was supplied to PairSession.resume. A new pair starts with no parent. Persist enough owner/session-parent information to verify these distinctions during replay as well as live publication. A meaningful regression should create a real parent PairSession checkpoint, then prove that a child `create` result, stale parent reference or wrong parent owner is rejected, while actual child `resume` followed by multiple child publications succeeds.

## J2 — artifact reservation does not enforce full artifact bytes

Initial `journal.py:82` compares only the outer pair manifest's size with `artifact_bytes`; reservation accounting at lines 121–124 treats that quantity as the artifact allowance. A small manifest can reference a much larger saved numerical state. Thus this is presently a caller-declared reservation ledger, not an enforced bound on the complete artifact's logical bytes. Physical allocation is already explicitly excluded and need not be conflated with this missing logical linkage.

Either make the caller obligation explicit and avoid any complete-artifact byte-bound claim, or bind the reservation to the exact PairSession policy/conservative checkpoint envelope before allocation and verify the expected saved metadata/file extents before publication. Such verification can inspect compact manifests and file stats without loading numerical array bodies. Reject under-reservation before numerical work wherever possible; a post-publication overrun must remain charged/retained and cannot authorize continuation. Ancestor-inclusive accounting alone does not repair an understated per-artifact reservation.

## Sound inspected mechanisms and remaining scope

The journal requires exact positive non-boolean integer quota values, an exclusive new directory beneath an existing resolved root, and derived artifact owner/session paths from journal name, owner, workflow and purpose. A shared `pairs` root permits real parent references while each session remains distinct. Event references form a hash-linked ordered sequence; failed-parent replay checks exact event inventory, bounded depth/cycles, workflow/policy and pending gaps. It reconstructs inherited reservation/event counts rather than resetting them. Reserving one event also leaves room for the corresponding publication; owner/start/terminal metadata allowances remain conservatively charged. These logical allowances do not bound Python metadata, RSS, physical filesystem allocation or outer runtime resources.

Durable writes use exclusive files, fsync file contents and fsync directories. A publication-write failure poisons the live journal and preserves the orphan artifact and durable reservation. A failed terminal with a pending reservation blocks ordinary successor creation; no numerical or metadata recovery is guessed. The separate admitted reconciliation procedure is not implemented. The caller still owns graph/source compatibility, workload-purpose membership, run/lease admission, prior-owner death, exclusive access and all omitted sibling attempts. This layer must not be described as solving those registered requirements.

The inspected saved `green03.log` records 12 tests passing in 0.472 seconds. Eleven tests are compact metadata fixtures; one uses real maintained PairSession creation, two same-owner checkpoints and a resumed child through completion. It establishes shared-root compatibility, but not J1's negative continuity case or J2's complete-artifact accounting. `red03.log` records 12 missing-`target` errors after the test interface changed; it is not a clean behavioral counterexample for all twelve assertions. Earlier failure logs and pre-correction sources remain retained. No broad-suite, resource, financial or empirical claim follows from these tests.

Initial reviewed SHA-256 values:

- `journal.py`: `8553beb65049f15cbb6b48968c7dda1c6c95154e064d5446a3735943cc7dc508`
- `test_journal.py`: `e5af80caf9b4d76426f3da8a5f471a0e5758e03487fba174a2438221e464e1f0`
- `green03.log`: `f4377bab9dc0437737d5d06c6bc63381553f208683108a8c6f17f6f6b7c923f2`

## Correction review — accepted artifact-only scope

The corrected component is accepted within its explicitly caller-declared artifact-ledger scope. J1 is corrected. J2 is resolved as an explicit API/contract limitation, not by implementing whole-artifact byte enforcement. Registered ownership, actual allocation bounds and reconciliation remain open requirements.

The original reviewed `journal.py` is preserved byte-exact as `pre-correction/journal-before-parent-join.py`, with initial SHA-256 `8553beb65049f15cbb6b48968c7dda1c6c95154e064d5446a3735943cc7dc508`. The complete correction diff was inspected; all 17 entries in `bindings-v2.json` independently match current bytes. Original findings above remain part of the review history.

For J1, `target()` now derives both the exact artifact owner and fixed session parent. A new session following an inherited progress reference must identify that reference and its artifact owner. Subsequent publications in the same session carry the original fixed session parent rather than incorrectly claiming a fresh resume from each previous checkpoint. The reservation records this value, replay independently recomputes and checks it, publication checks that the actual pair manifest contains the same parent, and the resulting pair state preserves owner and session-parent fields. Thus a child `create` with parent null cannot impersonate continuation. The same `apply()` validation is used during failed-ancestor replay; the fix is not limited to the live publisher.

`red04.log` is a clean behavioral counterexample: the new missing-parent rejection assertion failed because no ValueError was raised. `green04.log` records 13 passing tests in 0.462 seconds after correction. `green05.log` records 14 passing tests in 0.501 seconds. The added real PairSession negative case constructs a real parent checkpoint, reserves a child continuation and deliberately calls child `create`; publication is rejected and the resulting artifact remains retained. The expanded positive case resumes the exact parent into a child, publishes progress, confirms that the second child target retains the same session parent, then publishes completion. These fixtures are meaningful evidence for the actual API boundary. They do not constitute an exhaustive hostile-artifact or multi-generation replay proof; the latter join was also assessed statically.

For J2, the field and parameter are now `declared_artifact_bytes`. The method docstring and `IMPLEMENTATION.md` explicitly say that publication measures only compact outer metadata and does not enforce aggregate numerical-file bytes. The future admitted caller must derive a sufficient reservation from the pinned pair policy before allocation, validate the complete saved extent envelope, enforce actual bounds and account for other retained workflow artifacts. This correction prevents the caller-declared ledger from being presented as a demonstrated complete-artifact bound. The missing enforcement remains substantive work before empirical use; neither the 14 tests nor this acceptance supplies it.

Quotas still reject nonpositive/non-integer (including boolean) values at the public policy boundary and at artifact reservation, charge ancestor history, and preserve failed/pending reservations. Hash-linked event sequencing, exact failed-parent paths, acyclic depth limits and exclusive directories remain unchanged. Complete artifacts without successful journal publication still require separately admitted reconciliation. The component remains single-owner and caller-controlled; it does not prove unlisted sibling attempts, workload-purpose membership, live guard/death admission, numeric-source compatibility or physical storage safety. The 64 KiB metadata and eight-ancestor limits remain finite operational limits, not a demonstrated scalable full-workload ledger.

No maintained production package, consumer, empirical gate or scientific capacity changed in this correction. This component is not covered by the previously closed 3,559-pass package suite merely because it calls that package. No tests or jobs were rerun by the reviewer.

Corrected reviewed SHA-256 values:

- `journal.py`: `b549e8a606f2b68f70cad672c66243f261be6297d8368435a74a061e8fb93096`
- `test_journal.py`: `c7710e3b97c0d002a494ab97639bc776a4349ff93594bb2d3a6afa51410669f2`
- `IMPLEMENTATION.md`: `4ec7df1458416a011a4defd4f4a612b2c84dc1fac5e0e222e2dae2b090a60d5c`
- `bindings-v2.json`: `3ccae111c6008044fcce1e32ea385e8afd7c7c9955d5e989cee5b6be5d78b68b`
- `red04.log`: `c8a2f1d403e98ef8ca36a57b85b34bdcdff0af7cb870c6e152fbcd80c5292506`
- `green04.log`: `ec7cc175c039890e19435e971762cabad8db325d3b833d22d7e51a9d9b445ceb`
- `green05.log`: `b7fc0b8b3e6dffc09dc2a4517691e320ec0884aa75bc95a1f0231afd40477c07`
