# Independent corrected sample-artifact review

Accepted for the current first-owner, array-backed sample-event admission
component described in SCOPE.md. SAR1 is resolved; no remaining material blocker
was found within this bounded scope. Acceptance does not authorize a producer,
empirical run or historical sample reuse.

The actual source, fixtures, retained originals, red/green logs and scope were
inspected independently. All 107 declared compact/source/dependency bindings
match current bytes. bindings.json SHA256 is
`00c2c320b18439d4e159936bb6e76da41255e0abb89dea8d8ea4d17d143f501f`.
This direct component set is not a complete empirical source/runtime closure.
Only this review file was written; no test, job or numerical file was opened or
executed by the reviewer.

The only correction from route.py.original adds `journal.directory == directory`
to the repeated live event check at route.py:105. Consequently both admission's
final checks and an existing receipt's lease retain the actual FeatureJournal
directory join. red02 preserves the two intended failures: a redirect after
sample_scope and a redirect after receipt creation. The initial eight-test pass
does not supersede that defect evidence.

The inspected route requires the actual OwnedJournal and FeatureJournal types,
current registered workload/owner checks, a first owner with no parent, explicit
event zero and hash, one samples_complete event, matching in-memory and durable
event records, and exact bounded current journal inventory. Both selected job
and producer name the registered read policy; event context binds its hash and
the workload control. Unknown inventory and terminal markers include dangling
links in the refusal path. Lease checks retain metadata hashes/signatures,
component inventory/signatures and the current owner.

Slot preflight rejects JSON numeric lists and non-native/wrong-rank numeric
fields before np.empty. Every array belongs to a graph numerical field, with
node dimensions and edge count/width joined. The reader receives half the
registered payload allowance, accounting for its resident arrays and the
AttributedGraph immutable copies. Subsequent sample_scope validates the actual
training population, sample order/configuration identity and induced graph
contents. Detailed record/parent/numerical validation is after bounded loading;
this review does not claim it precedes all array allocation.

Saved check02 reports 13 passing tests in 201.698 seconds. It covers SAR1, the
original publication/refusal cases, dtype/rank/shape refusal, live parent and
broken terminal-link refusal, and twelve drift subcases. Those twelve change
directory, terminal, event, policy, inventory or stored parent immediately after
read_component or sample_scope returns. They establish caller-boundary checks,
not mutation injection inside those routines. The accepted reader's separate
tests cover internal read drift. Tiny fixtures use actual temporary Git
registration, ResearchRun, journals and persisted synthetic samples; kernel
guard observations remain mocked. No reviewer rerun is claimed.

Evidence SHA256:

- route.py: `e049307f0acd01e4646cba2d7b7e79d4f634db058faafe87e0591c986ffea7d3`
- test_route.py: `287d698bfcbf0ca74b67969af70eb74d08eb457563b8c70f12f9eec9552cd887`
- red02.log: `e464e2380010900902921ee787fbbc47dbb24ffa9210d26f585475b6454ae5b3`
- check02.log: `e418c6b037478b736a2c2030acb71cabb85b5abac01833404cb4a4ee5b153004`
- SCOPE.md: `1439a752c0fe5fc6584563188a69295025dbc60c41044a6b2c102bf37ee5dd0c`

No atomic snapshot against continuous mutation, whole-process RAM/physical
quota, elapsed-time or cumulative-I/O bound is established. Immutable outer
ownership and the actual guard remain prerequisites. The new array-backed
publication is distinct from the existing JSON-list serializer. Its production
writer, weighted sampler/RNG provenance, failed-owner reuse, actual dictionary
purpose routing, dictionary/MCM publication, complete representation reuse,
mapped/scaled feasibility and orphan reconciliation remain outstanding. No
financial fit, scientific configuration, trial allowance or historical result
is changed by this component acceptance.
