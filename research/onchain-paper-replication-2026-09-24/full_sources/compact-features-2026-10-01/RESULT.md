# Compact graph tensor result

The actual compact MCM result now feeds an explicit registered conversion to
independent CPU float32 scores and int64 graph edges. Both plan/job selections,
source identities, graph ordering, original score bytes and final callback-free
provenance checks are enforced under one owner transition lock. These fixed
inputs preserve the downstream trainable MLP/GAT architecture.

Fresh red01: one missing-module failure, five deselected, 72.41 seconds,
session81416 exit1. Current-source check01: all six tests passed, 474.59 seconds,
session5042 exit0. Positive checks establish values, dtype, independent backing
storage and changed tensor rejection. Negative checks cover registration route,
source, memory allowance before torch allocation, final callback graph mutation
and concurrent owner transition refusal. Fixtures are tiny, synthetic, fresh
registered runs with mocked guards; no empirical job or accuracy evidence.

SCOPE.md documents the per-conversion numeric allowance and its limitations.
No graph artifact publication, full representation/native route or empirical
admission follows from this boundary. All 1,420 financial fits remain pending.
Next graph publication/saved admission; complete-calendar adapter proceeds
independently before representation closure and full resource accounting.

Correction to original mutation coverage: direct assignment to GraphSnapshot
edges only exercised immutable-array write rejection in check01. The original
test is retained as test-check01.py and review as REVIEW_CHECK01.md. A corrected
fixture explicitly replaces graph edge storage and asserts the original graph
hash changed after refusal. Targeted check02 passed one case, five deselected,
81.91 seconds, session74858 exit0. Production source is unchanged; no combined
final six-case run is claimed. This supplies actual final-callback graph drift
coverage rather than relying on a read-only array exception.
