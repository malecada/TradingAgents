# Refusal worker03: complete bounded inventory

Status: source-only candidate, unreviewed and not admitted. Preparation01/02 and accepted narrow R1 evidence remain unchanged. This candidate changes only the outer inventory integration and template protocol, and adds one stdlib inventory module; the genuine worker/Target/oracle/native parser/preclaim bodies are byte-identical.

## Behavior

The old compact row estimate disagreed with the actual native receipt serializer. Its flat reference index overflowed8KiB even for2311 admissible scalar rows, and an individually escaped path could overflow a page. Every new leaf, intermediate index and root now uses the exact native serializer `json.dumps(sort_keys=True,allow_nan=False)` plus newline. All rows, all output bodies and all hierarchy bounds are checked before the first inventory file is published. A row that cannot fit8KiB is refused before publication, without truncation or omitted members.

The explicitly selected `inventory_policy` is required in the prospective release. It declares maximum32768 members,4MiB actual encoded-row aggregate,2048 leaf pages,32 child references per index and at most2 intermediate index levels. All inventory files, including the root, remain8KiB; the global authority metadata cap is unchanged. At most2115 inventory files are representable. The old768-page/flat-index layout is superseded for this new prospective identity family only. Root must review this protocol before any execution.

This is representation capacity, not permission to exceed the shared32768-entry/1GiB watch. Publication reserves entry room for the root plus every inventory file and all four possible tail files, and checks prospective logical headroom before writing. A tree already occupying the global entry cap therefore refuses before publication. The actual whole-tree watch and10GiB free-space floor are checked after each newly written inventory file; final post-tail storage remains authoritative for actual allocation. No assumed filesystem allocation size substitutes for those checks.

The complete reader verifies root/page/index schemas, exact canonical serialization, bounded hierarchy shape, every child digest/extent/count, complete deterministic page membership, sorted unique original members, and actual complete current-tree membership with only the precisely named new inventory/tail files excluded. Every original regular file is joined again to its size, allocation and original raw hash. Original directories retain their original prepublication observations; subsequent directory growth is explicitly qualified and counted by the real post-tail watch. Missing/duplicate/coherently omitted members, changed files, added unrelated members and broken refs refuse.

The root inventory ref enters `authenticated-refusal.json`; the actual outer post-tail wrapper verifies the existing native storage-tail checks, original terminal→proof body hash, inventory root ref and complete raw hierarchy/tree again. These inventory checks supplement, never replace, the existing full genuine native/ResearchRun/refusal/oracle authentication. Preclaim has its existing separate native/no-claim/cleanup route, preserved byte-for-byte; no postclaim inventory is falsely claimed for it.

## Time qualification

Native RuntimeMax1800 and the existing checked active-loop1840 policy remain unchanged. The old60-second closure and51300-second whole-suite wall-bound claims are removed from generated protocol and intent. They were not enforced, and separate stop/wait/inventory allowances do not sum to a whole-outer guarantee. Closure and complete-outer bound fields are now null, with an explicit false whole-outer-deadline flag. Individual native/active-loop, scan and raw-inventory checks remain; no hard whole-outer deadline or ETA is claimed.

## Source and accounting

`source_inventory03.json`:170 exact origins /144 package entries.167 targets are unchanged; outer and template tools change, and refusal_inventory03.py is added. The numerical worker/motif dictionaries/strict oracle/mutations are unchanged. `install-delta03.json` has exact before/after rows. All27 sentinel registration/release/input templates are regenerated with the complete source map and typed inventory policy. The separate27variants/16classes/4preclaim/max23claims/17Owners/19journals/1088prospective identity comparisons and129maximum scored pairs remain unchanged. No scientific budget transfer, financial fit, original512 replay or scope reduction occurs.

## Evidence

All named checks use checkout-local `.venv/bin/python -B`, stdlib/source and explicitly synthetic metadata only.

- Actual predecessor paging/save extraction reproduces2311ASCII rows→71refs→8240bytes and its8KiB refusal; the new plan retains all2311 within8KiB per file (`predecessor-bounds03.log`). No closed empirical tree was read by this candidate's tests; the investigation's closed816-row measurement remains its own evidence.
- Four inventory tests cover2311rows,32768 short rows, exact serializer equality, a feasible-component escaped path refused before publication, and a near4MiB1026-leaf plan requiring two index levels (`inventory-max-GREEN03.log`).
- Five actual-reader tests use tiny synthetic files: full membership/tail, changed body/unknown member/changed root ref/corrupt page refusal, coherently rebuilt omission refusal, unsupported row with zero writes, and entry-headroom refusal with zero writes (`reader-GREEN03.log`).
- Two integration tests exercise the actual post-tail wrapper with explicitly synthetic storage response, validate terminal/proof/root hash joins, and prove unchanged worker/parser/preclaim bytes and maintained native/active-loop limits (`integration03.log`). This is not a genuine storage/guard observation.
- Seven R1 first-fatal/ordinary/success/marker-failure tests pass with the selected actual stdlib CleanupFailure class. The later failure-marker reader test also passes.
- Six inherited adapter tests plus one worker hook-order test pass. Finite template generation verifies the protocol differs only by the declared inventory policy and honest time qualification.

The initial expected RED tests for missing new inventory implementation and all subsequent logs are retained. Final named selection contains27 source/metadata tests; this count must not be confused with27 genuine future refusal executions. Partial inventory publications on write/readback failure are preserved; original passed terminals are never overwritten and R1 emits the additive failure marker when possible. If a failure marker itself cannot be written, the selected error still escapes and observed external outer exit remains required.

## Remaining

Independent different-author review is required. Root must compose current accepted primary sources, freeze genuine capsule/runtime/source/input/registration and exact finite release, review the new inventory policy, and measure fresh capacity before launch. All actual27 refusal cases,1088 genuine comparisons, native controls, process/cgroup cleanup and external recovery remain unexecuted. The hierarchy proves finite metadata representation in source fixtures; it does not prove actual suite capacity, storage throughput or cleanup timing.
