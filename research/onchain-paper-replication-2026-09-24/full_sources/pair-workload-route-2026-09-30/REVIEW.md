# Independent corrected workload-route review

Accepted for the read-only registered-control, resident-graph and induced-sample
admission component described in SCOPE.md. WR1 and WR2 from INITIAL_REVIEW.md
are closed. No material blocker remains in this bounded review. This does not
release empirical execution or complete the production pair workflow. Reviewed
at HEAD `94db95ec055714627775ab7fbb7cb51294bea01f`.

WR1 is corrected at `route.py:119–122`: the complete actual ExampleManifest,
including ordered train/test rows, masks, source/fold identities and exclusions,
must hash to the registered control's `example_manifest_sha256`. That control
is itself named by both selected job and producer plan and hash-bound in the
descriptor. Equality is required before graph iteration. Recomputing a changed
test population's own mask can no longer substitute an unregistered denominator.
The retained red02 report demonstrates both reordering and duplicate-row
acceptance in the old implementation; the corrected report records refusal.
The tests explicitly preserve the required graph union, preventing that older
descriptor field from masking the missing population check.

WR2 is corrected at `route.py:44–51`: every compact workload snapshot is reread
through the existing ancestry metadata reader with its expected hash. That
reader enforces root/path containment, regular single-link same-device files,
the compact size limit and stable before/after reads. The new hard-link
counterexample previously passed the hash-only lease and now refuses. The
oversize/stability protection is confirmed by source inspection of that reader;
this component's saved suite does not contain a separate oversized-file case.

Other inspected joins remain consistent: exact imported route source admission;
maintained owner/source/runtime binding; positive integer schedule/quota control;
actual graph/configuration/fold/seed descriptor reconstruction; exact registered
graph-reference population; example and graph availability clocks; and induced
sample topology/attribute identity. sample_scope rehashes admitted parents,
checks the eligible training population and sample record/center membership,
and reconstructs each induced neighborhood. The added local-feature tamper
case is rejected even though the original sample metadata identity is unchanged.
The derived dictionary workload scope is compared with a purpose from the
accepted workload implementation before any numerical pair callback runs.

All 36 declared direct-file hashes independently match bindings.json SHA256
`50fe2204767697eb50d4db64b8440c96f19488af23fafeaca0c4e03ac35f484a`.
check02 records all 13 tests passing in 74.146 seconds. Original source/tests,
the ten-pass initial report, initial withheld review and three-failure red02
report remain retained. The declared reconstruction of the red02 test source
was checked: it differs from the final test file only by the two-line fixture
addition registering the full example hash. Its present reconstruction hash
does not establish the exact test-file bytes measured at red02 execution.

- `route.py`: `a71d890fae6681c29bd2a4b49241068fbf1936001bc4392880025ca1fd2f668c`
- `test_route.py`: `25cefd085ab2848ad65e3b7f3aa7bffc5215ab9db11c9f341ef1c243c83428e5`
- `SCOPE.md`: `6924735999abdcf0ce8a55d22b4153b64b6f9327dc89de5c48ac0c4d29f098b1`
- `check02.log`: `089e2153953e24800e2cfb20aa4cf11de16012d637b36db680ff59e2e5fc6df0`
- `red02.log`: `17fbab47810355b1678adf92ff8281ae8bb857a74124ae88f5a6d7c1dbed084b`

Acceptance is identity admission, not independent raw-data/calendar correctness:
the registered expected-date denominator and price/source semantics still need
data admission. The suite uses actual temporary ResearchRun/Binding fixtures
with mocked kernel guard observation. It does not replay weighted RNG draws or
validate reported draw probabilities. Real sampler publication provenance,
mapped population ownership, MCM/dictionary artifact routing, pair-journal
ancestry, physical whole-workflow quota, orphan reconciliation, scalable
journal/lease checks and complete representation reuse remain outstanding.
The 36-file inventory is not a complete empirical source/runtime closure, and
route leases do not replace full source/runtime checks plus outer source freeze.

Only this review file was written. No tests/jobs were executed, no empirical
arrays/raw bodies/SQLite were read, and no other source, tests, registrations,
historical results, budgets, staging or commits were changed. No financial fit,
performance, paper coverage or strategy validation follows from this acceptance.
