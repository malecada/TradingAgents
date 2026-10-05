# Root-selected refinement

Root explicitly chose the sampled stage-interval option: genuine baseline at entry, genuine live leases, bounded monotonic freshness, interval-gated fingerprint/full validation, and full exact stage/chunk/pre-publication/final checks. Do not introduce approximately200 source/input syscalls per cell or a generic sealed-FD authority framework. This refines the per-lease filesystem-observation suggestion in CONSTRAINTS01; that earlier note is preserved as advice, not an accepted candidate.

The selected interval must be finite and mandatory, use the actual monotonic clock, and be included in prospective registration before an empirical run. Successful check timestamps are recorded only after checks finish; stale, negative/backward or nonfinite elapsed time and any evidence mutation must refuse. A fresh timestamp never adopts changed source/input identity. Failed checks cannot return a usable fast capability. Existing per-call genuine claim/Owner/native lease checks stay active. Changed mutation-detection timing is an explicit engineering assumption, not an assertion of continuous immutability.

Root's direction and these constraints were sent directly to continuation_successor_implementation. Concrete source and tests remain pending; no candidate acceptance or launch authority is implied.
