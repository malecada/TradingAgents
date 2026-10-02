# Independent correction review

Final acceptance remains withheld pending terminal check02 evidence and the two residual boundaries below. No tests were rerun and implementation files were not edited.

The current delta corrects the registered metadata key, uses an internal close path during attach's already-held transition, serializes public operation leases, repeats terminal/active checks after callbacks and introduces primary-aware fatal descriptor close helpers. Completion preflight failures now pass through the failure path, and prospective control metadata plus the registered free-space floor are checked. Those changes address the main mechanisms in AOO1–3. The added tests cover real public close attempted from a lease, original attach exception identity and lock release, constructor close uncertainty, completion publication failure and actual owner poisoning after intent publication. Their final outcome is still pending.

## Residual AOO4 — fatal failure-evidence cleanup is swallowed

`archive_owner_operations.py:203–211` catches every BaseException from `_write` and only annotates the supplied primary error. `_write` now raises `io.CleanupFailure` when its owned descriptor close is uncertain. Thus explicit `Operation.fail(OSError(...))` can return normally after that fatal cleanup failure; ordinary claim/completion failures can likewise rethrow an ordinary primary despite an unresolved descriptor. The new helper alone does not preserve fatality through this catch.

Keep poison and spent reservations, but propagate `CleanupFailure` from failure-evidence publication, chained to the original cause. Ordinary inability to write evidence may remain a diagnostic on the primary. Add a targeted close uncertainty during failed.json publication; constructor-only close coverage does not exercise this path.

## AOO5 — mutable lock reference can strand the acquired owner lock

The selection-owner/transition relationship at lines106–107 is checked only before callbacks. Ledger._transition is mutable, and the inherited transition decorator releases `self._transition` by looking it up again in finally. A callback can replace the ledger's lock with another Lock. Final checks do not notice; finally attempts to release the new unlocked lock, masks the intended result and leaves the actual acquired owner lock held. The same release pattern is used by attach through a later owner._transition lookup.

Capture the exact acquired lock for unconditional final release, and reject owner/selection/transition identity changes callback-free after external calls, or make these bindings immutable for this component. Avoid broad changes to old owner routes solely for this adapter. Test a late lock replacement and verify refusal plus availability of the original lock afterward. This concerns the advertised current-owner binding and failure cleanup, not a general process-security guarantee.

Scope remains durable whole-operation reservation, with caller-reference-only completion. Nothing here proves transferred byte counts, archive content, stage scientific correctness or post-owner-close admission. All nine-case evidence remains synthetic and uses the fixture's mocked OS guard.

Inspected current hashes:

- archive_owner_operations.py: `afa68ea915702583b01bac42353c0574c231f2eb519b94ac805d88df6d3e85f6`
- test_archive_owner_operations.py: `a0c05240b5e2197e5744ac617b0512476317646f09bf47b70914e24fa56b117c`
