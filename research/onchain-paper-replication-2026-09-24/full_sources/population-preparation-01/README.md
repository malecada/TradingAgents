# Population preparation integration

The chronological population can now be built from hash-bound weekly graph
metadata and an admitted price panel without loading graph arrays. The same
calendar implementation serves both full graph objects and metadata references.
Every required week and decision date remains accounted for, including explicit
unavailable and late graphs, warmup exclusions and the training-label purge.

The producer binds the complete Fold to its frozen calendar, every graph
manifest, unavailable-week evidence, the price panel and its source, and graph
configuration/source membership. A registered fit payload can publish population,
example binding and assembly evidence within the same admitted claim. Preflight
validates actual input or published output binding bytes before representation
computation. Comparison cells retain the existing common-label/mask/scaler checks.

Fifty-three focused tests passed. They include two synthetic SVM fits through
the generated population and three binding-reference regression cases. No real
financial population or fit was executed. The full historical suite has not been
rerun for this incremental snapshot; its previous evidence remains separately
pinned. Graph array content is deliberately not rehashed during metadata assembly;
the existing loader must verify it before representation fitting.

Ruling: expose metadata-based population assembly as a narrow additional
interface, sharing the existing causal calendar rather than duplicating it.
No graph semantics, protocol setting, mandatory asset/year/arm or empirical
budget changed. Full source-to-graph production and large-workload feasibility
remain incomplete. The initial ETH study remains an intermediate milestone.
