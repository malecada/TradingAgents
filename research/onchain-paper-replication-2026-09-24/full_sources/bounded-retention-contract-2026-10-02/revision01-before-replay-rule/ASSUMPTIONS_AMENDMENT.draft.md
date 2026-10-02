# Unadopted prospective assumptions amendment

Target for a future additive amendment: IMPLEMENTATION_ASSUMPTIONS.md's October1
compact operational variant, currently specifying retained progress/failure
snapshots. No existing assumption or evidence is changed by this draft.

Proposed text, effective only for a newly registered
`bounded-matching-restart-v1` run after independent review:

> This operational variant preserves the existing matching equations, arithmetic,
> temperature and hardening order, checkpoint cadence, exact ordered purpose and
> score records, RNG states, dictionary sampling/population and all scientific
> outputs. It changes only retention of newly declared temporary matching
> restart-state bodies. At most two saved active generations coexist, subject to
> separately reserved replay/failure bodies and control evidence. This is a
> logical saved-payload cap; live engine arrays, serialization/copy buffers,
> filesystem blocks, parent graph/sample/model state and whole-process RSS need
> independent outer bounds.
>
> Full snapshot verification, immutable per-checkpoint metadata and explicit
> monotone retirement receipts precede acknowledgement. A newer verified state
> or durable exact successful completion event anchors retirement. Required
> deterministically preselected replay evidence is retained as full recoverable
> bytes under a separate reservation. Retired progress bodies cannot be replayed
> or used for automatic recovery, and their hashes do not claim recoverability.
> Failed/interrupted claims preserve all surviving states and partial evidence;
> they cannot automatically resume, retry or reclaim allowance.
>
> Historical raw data, states, manifests, gates, completed/failed claims and spent
> histories remain preserved. Existing local and archived-event formats continue
> to require their original checkpoint trees. Only the explicit new version
> interprets prospective retirement receipts. This variant is not admitted by an
> implementation test, a retained hash or this assumptions statement.

Required adopting documents: independently accepted CONTRACT.md/POLICY inputs,
source/runtime closure, exact population/reuse and replay-selection manifest,
physical/RSS/cumulative limits, full new registration/gate and immutable
preservation rules. The preexisting unadopted61ceiling is unchanged:33spent+
12body+15financial+1resource. This amendment alone consumes or grants no attempt.

Required independent test evidence is specified by REVIEW_ACCEPTANCE.json. In
particular, expected scores must come from independent arithmetic/reference
inputs, not production-generated expected answers; the selected replay set must
not depend on observed scores, convergence success or favorable retention cost.
No scientific acceptance threshold is relaxed.
