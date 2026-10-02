# Independent review correction — candidate06

Candidate06 is frozen. check09 CLOSED with **62 passed in3.18seconds**,
session98486, exit0. CORRECTION_CLOSURE.json binds source/test snapshots, exact
runtime and the raw correction logs/XML. git diff --check passed. This supersedes
only the final-candidate status in REPORT.md and earlier closure records; all
candidate05 bytes and44-case evidence remain unchanged.

The independent reviewer identified four material gaps in the earlier candidate:

1. Generation wrappers did not enforce exact membership. Active and terminal
   checks now require precisely the original `state` child and its original inode,
   including after numeric retirement. Foreign wrapper files are rejected.
2. A final external lease could set poisoned/closed and still acknowledge. Every
   external callback now rejoins original runtime state and explicit revocation
   after returning, before any subsequent transition or acknowledgement.
3. Replacing public config/counters could exceed original limits before terminal
   checks. Module-owned weak authority records pin original root, claim, lock and
   complete runtime state; every callback and public operation rejoins that pin.
   Only internal transitions refresh it. Counter/config/proof/expected-map/root
   substitution is refused before another allocation. A pre-call counter refund
   permanently revokes the instance even if public fields are restored. Failure
   records use original spending and never write through a replaced public root.
   Constructor inputs are copied before the first callback, then used consistently
   in both immutable claim and runtime config. Inspection getters also rejoin the
   original authority.
4. Original external EventRef objects were discarded too early. The actual current
   progress/completion reference and immutable expected event remain in the owned
   operation record. Their durable bytes are reread after external callbacks, at
   pre-retirement guard boundaries and immediately before returning acknowledgement.
   Mutation before retirement retains numeric bodies; later mutation after prior
   irreversible retirement still refuses terminal acknowledgement and preserves
   surviving metadata/replay/failure evidence. No missing body is reconstructed.

independent-red01 CLOSED:12failed4passed44deselected25.27seconds/session5768exit1.
The failures reproduced all four findings; several individual runtime replacements
already failed at later checks, which did not cover the identified preallocation
bypass. check08 then passed60cases in3.22seconds/session18641. A further direct
pre-call counter test exposed non-permanent refusal (independent-red02:1failed,
1passed60deselected); refusal now poisons the original module-owned authority.
check09 passed all62cases. No actual-owner fixture or neural test was run in this
slice; all mutations stayed under disposable temporary local roots.

The module-owned anchor is an internal Python authority record, not a sandbox
against arbitrary modification of private module globals. Integration must supply
original scientific/source/owner authority and whole-stage resource/population
joins. Existing one-pair limits, no-restart semantics, retained manifest bytes,
FIRST replay ordering and all prior physical/empirical exclusions remain unchanged.
Independent corrected-source acceptance is pending.
