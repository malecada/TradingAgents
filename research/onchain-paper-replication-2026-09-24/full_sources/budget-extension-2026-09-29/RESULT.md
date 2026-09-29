# Prospective cumulative budget extension

An explicit `cumulative_budget_extension` supplies a separately committed
ceiling without modifying historical family, claim, terminal or exposure
objects. It pins a complete closed-claim snapshot, unchanged original family,
allocation, initial adopter and independent accepted review. Failures spend
their allowance, every historical attempt remains counted, active claims prevent
first adoption, later claims carry the extension and ceilings cannot roll back.
The generic structural verifier independently checks the saved ceiling and
committed metadata; it does not independently replay the full admission history.

Focused green03 completed58tests with child0 and verified cleanup. Coverage
includes17historical attempts, omitted/listed live claims, a second extension,
rollback refusal, working metadata drift and other-mechanism isolation. The
independent review's narrower untested cases remain disclosed in REVIEW.md.

Real metadata-only compatibility verification passed all61existing claims and
preserved all121claim/terminal byte hashes. No raw input was opened, budget
extension adopted, new claim created or empirical attempt refunded by that check.

## Preserved failed and superseded checks

- red01:12fixture setup failures from a redundant no-change Git commit; not
  intended feature failure evidence.
- red02:12intended failures before implementation.
- green01:49passes; green02:57passes after edge-case additions.
- The real ledger then exposed a P1 compatibility defect: historical dated-mark
  metadata already uses `budget_extension` for an unrelated certificate. red03
  reproduces the collision. The new field was renamed; historical bytes stayed
  unchanged. Independent review closed the finding on the corrected hashes.
- offline01 was deliberately stopped through its guard after that finding. Its
  partial output and successful cleanup remain; it is not a passing suite.
- offline02 is the new frozen named verification, bound by source-bindings-v2.
  Its terminal result is now closed below.

The proposed51→52study allowance is separate from implementation acceptance.
An accepted budget review alone never releases a data job, fit, resource purchase,
trading or deployment. The study retains its full paper-scope obligations.

## Corrected full verification closure

Named offline02 completed3293tests plus97subtests, with2CUDA skips. Standard
batch2768/1141.06seconds and neural525/426.08seconds both passed. Guard child0,
verified cleanup, zero memory high/max/OOM events. All seven source-bindings-v2
hashes match the verified source. Elapsed guard seconds: 1571.4648030209992;
sampled peak bytes: 2569056256. The stopped old
offline01 remains excluded. No empirical claim was created by verification.
