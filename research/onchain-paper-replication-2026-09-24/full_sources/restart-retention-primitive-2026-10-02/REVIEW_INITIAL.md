# Independent initial review — candidate05

Acceptance withheld for four concrete boundary defects. Review is read-only source/evidence inspection; no tests, numerical jobs or network operations were run. Findings concern the unselected one-pair helper's own advertised integrity/admission contract, not missing full-stage integration or empirical capacity.

Reviewed source SHA256 `40f6e9b552b65ad80ece23aedd725d4bfe5202bf0c64e0095a99c6be64804b78`, test `2c0c6fe391e13036c02196c56b637d1b9a4db948368dfe8ec03ed7663b6deab6`, candidate05 manifest `e1dcb20333ab0fcef8af4ae96dcd6317145fb0c17959ab996559d58e5c75e42a`. `FINAL_CLOSURE_02.json` SHA256 `8a989d5442aa340f6a8cbbcba5bd9e5fc586976f8a945ad044f8fd3b5bfcb255` source and evidence bindings were independently checked. Raw check07/XML contains44 passed in2.05seconds; these passing cases do not cover the findings below. All earlier failures and snapshots remain preserved.

## RRP1 — generation wrapper inventory is unchecked

`restart_retention.py:184–196` checks root names, each generation inode and the nested `state` tree. `verify` similarly checks the generation inode and retired state tree. Neither requires the generation wrapper itself to contain exactly `state`. A foreign file placed at `generation-<ordinal>/foreign` is outside every checked numeric/metadata tree but does not change the accepted root inventory. Terminal verification can therefore accept undeclared retained bytes and incomplete inventory accounting.

Require exact wrapper membership in active and terminal verification, including after final callbacks. Add a negative with a foreign wrapper member, distinct from the existing extra-file test inside `state`.

## RRP2 — final lease revocation can still acknowledge success

`_guard` at lines198–203 checks `not poisoned/closed` only before calling the external lease. Its post-callback check covers the lock and local files, not terminal status. `_operation` at line215 also only rejoins the lock. A late-armed final lease can set `poisoned=True` or `closed=True` and return normally; a checkpoint or finish can still acknowledge success on that boundary.

Rejoin live status after each external authority callback and before acknowledgement, with the intentional successful finish transition distinguished from callback-induced closure. Add actual late-armed checkpoint and terminal revocation cases, without merely revoking at the first lease.

## RRP3 — mutable runtime limits and spending are not joined before allocation

`_local` checks the claim hash but never requires `self.limits`, `self.policy` and `self.pair` to equal that original claim, nor derives current spending/counters from original admitted reservations. `_reserve` at lines228–235 trusts those mutable attributes. Replacing `store.limits` through a lease can permit a second generation where the original max_generations was1; eventual terminal rejection comes after forbidden allocation. Counter reduction can similarly bypass cumulative admission. Frozen dictionaries do not prevent replacing attributes.

Construction also freezes runtime values before its first lease, then builds the claim from original mutable caller dictionaries after that lease at lines173–177. A callback can make the saved claim and runtime values disagree. Capture canonical input snapshots before any callback and use them consistently. Pin/rederive original runtime authority and monotone spending at all allocation/retirement boundaries, including root, generation/current/proof state as relevant. Add preallocation limit replacement and spending-reduction regressions, and a construction-time caller-dictionary mutation check.

## RRP4 — external durable events can change after their last read

`checkpoint` reads `_event(publish_progress(...))` and discards the actual EventRef before subsequent leases, replay copying and predecessor retirement. `finish` rereads completion before `_retire`, but `_retire` and the final `_guard` execute later callbacks. Those callbacks can change/remove the original durable event while proofs/terminal retain only the earlier copied expected JSON, allowing acknowledgement despite loss of the required current external anchor.

Retain the actual current event reference and rejoin exact bytes after relevant final callbacks, including before irreversible retirement authorized by that event and before acknowledgement. Target both progress and completion with late event mutation. This is a requirement of this helper's current durable-event API, not a demand to retrofit hypothetical archived binary-log locations.

## Positive boundaries and limits

The source correctly copies/verifies FIRST replay before any superseded numeric retirement, keeps original engine manifest JSON and directory/inode evidence, and retires only original declared `.npy` members. Reservations include retained engine control metadata and do not refund successful retirement. Duplicate already-closed calls refuse outside failure handling. The captured-lock correction releases the original acquired lock and preserves fatal primary identity. Existing tests use real saved engine states, include hardening/rectangular cases, independent literal score arithmetic, retained replay reload and compound failure evidence.

These observations do not waive the four gaps. No actual-owner/stage selection, binary PairLog integration, complete scientific population, physical/RSS bound, remote recovery, financial timing/cashflow/fee/funding or empirical admission has been tested by this primitive suite. Input/source/owner hash truth and externally expected numerical completions remain caller obligations. Corrections should preserve candidate05 and add narrowly targeted evidence; no historical rerun is requested.
