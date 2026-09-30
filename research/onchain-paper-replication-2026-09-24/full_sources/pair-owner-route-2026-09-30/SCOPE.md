# Registered pair-journal ownership component

This isolated component joins the accepted resident graph/workload route to the
actual admitted ResearchRun/Binding. First owners require an unused pair workflow
root. Successors require exact failed pair-journal references for every admitted
failed representation ancestor, including actual claim/source/registration and
workload-control binding certificates. Both producer and selected job must name
the same explicit parent route. Pending reservations require reconciliation.

Certificate storage is prepaid conservatively for the maximum supported chain
(nine 64 KiB allowances). The derived logical journal quota therefore remains
identical across successors. This is not a measurement or enforcement of
physical disk allocation. Representation and pair journals have separate roots;
existing strict representation owner inventories remain unchanged.

Initial check01 passed eight tests in 313.390 seconds, exit zero. Independent
INITIAL_REVIEW nevertheless withheld acceptance for historical terminal/event
inventory drift, inherited session/publication changes and guard expiry during
final admission reads. Original source/tests and every failing attempt remain
preserved. red02 reproduced six failures across four cases in 215.928 seconds. check02
was deliberately interrupted (exit130) after review identified an additional
precreation foreign-session gap; its partial log, interruption receipt and exact
source/test snapshots remain retained. red03 reproduced that gap in one case,
51.177 seconds. The corrected full check03 passed all 13 cases in 581.182 seconds, exit0.
Final acceptance is recorded separately in REVIEW.md.

The derived local journal.py preserves the original dated journal source and
adds a mandatory callback after parent replay/quota checks immediately before
journal directory creation. The ownership callback rechecks exact historical
inventories (including broken terminal symlinks), bounded publication manifests,
inherited replay state and session membership, then calls a fresh workload lease.
Before creation observed sessions must equal inherited admitted sessions; live
leases permit additional sessions only if reserved by the current owner.
The first root mutation also requires a fresh workload lease.

The red02 source snapshot predates the local journal import and moves its
missing-session fixture only outside the pairs directory; the corrected tests
move it outside the workflow root to avoid a trivial root-inventory failure.
No reconstructed test file is represented as an execution-time snapshot.

## Limits

- Synthetic temporary Git registrations, actual lifecycle claims and owner
  bindings are exercised. Kernel guard/death observations are mocked.
- A compact publication fixture contains metadata only; it is not a validated
  numerical checkpoint, solver output or resource measurement.
- No physical whole-workflow quota, orphan reconciliation, scalable lease/index
  algorithm, complete representation reuse, dictionary/MCM artifact routing or
  mapped graph population admission is established by this component.
- Repeated ancestry/source validation is intentionally conservative and slow;
  these checks do not establish full-fold feasibility on the available machine.
- Multi-ancestor production continuation requires additional integration evidence;
  the present real-claim fixture exercises a first owner and one successor.
- No maintained source, frozen scientific protocol, budget or historical result
  is changed. No financial fit, empirical pilot or paid resource is launched.
  All 1420 planned financial fits remain pending.

## Preserved execution evidence

| Identity | Source and test evidence | Outcome |
|---|---|---|
| red01 | Original test before implementation existed | 8 tests, 9 missing-implementation failures |
| check01 | ownership.py.original, test_ownership.py.original; original external journal | 8 pass, 313.390s, exit0 |
| red02 | ownership.py.original, test_ownership.red02.py; original external journal | 4 tests, 6 failures, 215.928s, exit1 |
| check02 | ownership.py.check02, test_ownership.py.check02, journal.py.check02 | Deliberate SIGINT during first test, exit130; no pass claimed |
| red03 | ownership.py.check02, test_ownership.red03.py, journal.py.check02 | 1 test, 1 failure, 51.177s, exit1 |
| check03 | Current ownership.py, test_ownership.py, journal.py | 13 pass, 581.182s, exit0 |

Each identity is retained and closed identities must not be relaunched. The
interruption receipt records the exact stopped process and reason. All tests
use the pinned repository interpreter, `PYTHONPATH=.` and `-B`, with the named
standalone test file; red02 selected the four new regressions and red03 selected
the additional constructor session-insertion case. Full check03 includes the
original checks and all five added regression methods. No generic pytest or
legacy experiment entry point was run. These isolated tests are not a new broad
offline-suite receipt or a full empirical source closure.
