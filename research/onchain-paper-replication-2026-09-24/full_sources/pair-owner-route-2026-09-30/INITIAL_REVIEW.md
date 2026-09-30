# Initial independent pair-owner route review

Acceptance withheld for POR1–POR3. Findings refer to the preserved
`ownership.py.original`. The saved check01 report records eight tests passing
in 313.390 seconds; those fixtures do not exercise the counterexamples below.
No tests or jobs were rerun and no numerical arrays/raw bodies were read. Only
this review file was written; implementation, tests and other evidence remain
under their existing owner.

## POR1 — historical terminal and event inventories become stale

Locations: `ownership.py.original:104–105`, `123`, `137–138`, `150`, `179–181`.

Precheck rejects an existing complete parent and replays the parent's exact
event inventory through journal.load. Later locked checks and live leases only
reread known hashes. They do not repeat the absence check for each historical
pair owner's complete.json or the exact historical event inventory. A complete
terminal or extra event file appearing after precheck/open is absent from the
snapshot map and can pass the later checks. The representation ancestry check
does not cover these separately stored pair-owner directories. The original
complete check also uses exists without rejecting a broken terminal symlink.

Impact: a contradictory terminal or extended failed pair history can be omitted
when admitting or continuing a child owner.

Correction: revalidate every historical pair terminal's allowed inventory and
exact event membership under the lifecycle lock before creating the child and
on every live owner lease. Treat terminal symlinks as occupied, including broken
links. Add counterexamples for complete/event appearances during final
precreation checking and after child open; preserve the failed histories.

## POR2 — inherited sessions/publication references can disappear or drift

Locations: `ownership.py.original:123–133`, `158–169`.

Initial admission requires the observed session set to equal the historical
reservation-derived set. OwnedJournal.lease instead accepts any subset of the
combined allowed set. It therefore does not require inherited sessions to
remain present. The inherited journal state is copied rather than replayed;
publication manifests read internally by journal.load are not added to this
component's snapshot map. Changing an inherited published manifest can also
escape this lease. Current-owner publication events are replayed and checked,
so the omission is specifically in inherited state.

Impact: a lease can claim a preserved inherited pair owner while a required
session is missing or its published compact reference has changed. A later
numerical consumer might refuse when that pair is used, but the owner lease
itself has not enforced its declared preservation contract.

Correction: require all historical sessions to remain present while allowing
only explicitly pending current reservations to lack sessions. Revalidate the
exact historical publication metadata references and event inventory on every
lease, or retain equivalent complete immutable metadata snapshots. Tests should
remove an inherited session and alter an inherited publication manifest after
opening the child. No numerical-body reread is needed for these checks.

## POR3 — guard can be lost during final reads before journal creation

Location: `ownership.py.original:177–194`.

Inside the lifecycle lock, the current workload lease is checked before the
historical snapshot rereads. If the guard is lost during those reads, root,
journal and certificate creation can still proceed. Rejection occurs only at
the final owned.lease after the new owner has been published. The lifecycle
lock does not prevent monitor death or lease expiry.

Impact: the advertised refusal before creation is not maintained across the
final metadata-read interval, leaving an avoidable partial new owner.

Correction: finish the historical metadata/inventory checks, then perform a
fresh current workload lease immediately before the first owner-creation
mutation. Exercise guard loss as a side effect of the final snapshot read and
assert no new owner directory. Keep the final post-publication check as an
additional boundary; it is not a substitute for the immediate precreation one.

The intended conservative certificate prepayment and registered historical
claim/plan/job/control joins remain subject to corrected review. Eight passing
initial tests do not establish physical quota, orphan reconciliation, numerical
continuation or scalable live-lease behavior. No empirical execution or
historical registration/ledger change is authorized by this review.

Preserved initial SHA256 identities:

- `ownership.py.original`: `dd5157c8b34a7152d8b4708db4b845b2ca5f7d2619c5fd0bd511c4a51de8a5c7`
- `test_ownership.py.original`: `cb68733aa20d533810b12fc2d7c3eb396624308e302ef66818d17737e281a44b`
- `check01.log`: `df6e770ffadba9e8c123a428f394f46b65257c1035e407afcc30ca066227c680`
