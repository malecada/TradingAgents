# Independent corrected pair-owner route review

Accepted within the registered metadata-owner component scope in SCOPE.md.
POR1–POR3 and the subsequent precreation foreign-session gap are closed. No
material blocker remains in this bounded review. This does not admit empirical
execution, numerical artifacts or the complete production workflow. Reviewed
at HEAD `233bd5c9f8c4be1d2254a1d73fdec46c9978928e`.

POR1: `history` now rechecks each ancestor's exact binding/start/failed/event
directory inventory, including absence of complete terminals and broken
terminal symlinks. It rereads the retained hashes and replays the parent journal
to require equality with the initially admitted inherited state. These checks
run during admission, inside the lifecycle lock, in the mandatory creation
callback and on every OwnedJournal lease. Extra historical terminal/event files
are no longer omitted merely because they were absent from an earlier snapshot.

POR2: precheck snapshots every published compact manifest through the bounded
ancestry reader. Later history checks verify those hashes and require inherited
sessions to remain present. Live leases enforce inherited sessions ⊆ observed
sessions ⊆ reservation-derived allowed sessions, and replay current events.
An uncreated current pending session remains permissible, but loss of an
inherited session or publication-manifest drift refuses. The corrected
missing-session fixture moves the session outside the workflow root, avoiding
an unrelated root-inventory rejection.

POR3: the local derived Journal requires a callable `before_create` argument
and invokes it after parent replay/quota checks immediately before its mkdir.
The ownership callback repeats historical checks, then owner and exact session
inventories, then a fresh workload lease as its last operation before creation.
The first workflow-root mutation also has a fresh lease. Guard expiry during
locked reads or constructor replay therefore refuses before the new owner
directory. The original dated journal remains unchanged; inspection confirms
the local derivation adds its provenance docstring, mandatory callback parameter
and callback validation/invocation only.

The residual foreign-session gap is closed by the exact observed==allowed
check in the creation callback. Before a new owner exists there are no current
reservations to justify additional sessions. red03 reached the intended old
failure: open refused eventually, but the new owner directory already existed.
The final check03 regression now requires that directory to remain absent.
The final implementation differs from ownership.py.check02 by precisely this
one additional inventory assertion.

The registered claim/plan/job/control and historical binding-certificate joins
were also inspected. Every admitted representation ancestor must correspond to
the exact failed pair parent route and owner/start identity, with no omitted
pair workflow owner. Pending inherited reservations refuse. Nine 64 KiB
certificate allowances are conservatively deducted from the registered logical
journal allowance, keeping the derived policy identical across successors;
reported reserved_bytes adds that fixed prepayment back. This supports logical
reservation accounting only, not physical disk allocation measurement.

All 58 direct-file hashes independently match bindings.json SHA256
`976fb122a8fb21d1e874ab1e4b5ee14274fcad65f263a73e9b07dcaa9a926c21`.
Saved check03 records all 13 tests passing in 581.182 seconds. Original
check01, red02's six failures across four cases, and red03's single failure
remain retained. check02 was deliberately interrupted by SIGINT: its log ends
with KeyboardInterrupt, the interruption receipt and exact source/test/helper
snapshots are preserved, and recorded PID 2711985 is absent. check02 supplies
no passing-suite claim; its reported exit130 is consistent with the retained
interruption evidence. No closed identity was rerun by the reviewer.

Final reviewed SHA256 identities:

- `ownership.py`: `43198ef10c3cc5f9b457edc5d37a9c1bcf1e34deb603d973ced2cd788d3508bb`
- `journal.py`: `e51d087c49651e12867dc6297d366d5839cc675923839be75193c37e2bb03421`
- `test_ownership.py`: `8af3e4df3aebdc5813b374357aaca04f0d820fb72a7e6608b702a0b8c196da4e`
- `SCOPE.md`: `0a92cf12d2923c09bfc7a492e5a66c6c82d47a393b28aadd1d78192c2e134002`
- `check03.log`: `d7d3365b6a46f2d4692ff07a97d710799004f84a4624b2db178144d33a7548d7`
- `red02.log`: `ca0c89e8df3c2d95aac83dc79f0ba47d0e2d881bb531f5bffcb93d7edfd5ca3d`
- `red03.log`: `4c86eee10eb660f8ce93e1b5e8928e38b44f9b23bb297a1d0d8dd42da5211a29`
- `check02-interruption.json`: `bd8926f8f374998ac2d9100e4ad3cb6e499bbf4a71b61840e11f4901c19bc84f`

Limits remain material: tests exercise a first owner and one real synthetic
ResearchRun successor with mocked guard/death observations. The publication
fixture is compact fabricated metadata, not a validated numerical checkpoint.
Multi-ancestor production integration, dictionary/MCM artifact routing, physical
whole-workflow quotas, orphan reconciliation, scalable indexing/leases, mapped
graph ownership and complete representation reuse remain outstanding. The
58-file inventory is not a complete empirical execution closure, and the long
synthetic test duration establishes no full-fold feasibility claim.

Only this review file was written. No tests/jobs, numerical-array/raw-body/
SQLite reads, source or test edits, registration/ledger changes, staging or
commits were performed. No historical result, budget, financial fit, paper
agreement or strategy validation is changed by this acceptance.
