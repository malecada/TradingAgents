# Independent dispatch boundary review

No material blocker identified in the inspected dispatch delta. This does not close CNP1 or accept the pending complete producer integration.

`job_payload.execute_fit_payload` selects native reuse first, then the explicit compact producer, and skips the old native producer selector when either applies. Existing population/cell/descriptor/output preflights remain in place. The compact route uses the actual resident graph loader and the existing aggregate declared graph-payload check. The producer's `(PreparedFeatures, terminal)` return shape matches the eager loader's tuple handling.

CompactProducerError is propagated before the ordinary unavailable-representation handler, so a claimed compact failure cannot become an unavailable cell followed by continued fitting. Full producer finalization is called for every prepared compact representation before execute_batch and again after execute_batch publishes its outcomes/control outputs. A failed final rejoin escapes rather than returning a successful batch; already-written evidence remains retained. Ordinary preclaim graph-loading errors retain the existing unavailable behavior.

dispatch-check01.log reports **12 passed and 3 subtests passed in 19.14 seconds**, including existing route checks. The three new parameterized cases use the real resident loader but stub compact selection, producer, finalizer and batch execution. They establish old-selector avoidance, fatal producer propagation and the exact pre-check/batch/post-check ordering, including a post-batch error escaping. They do not prove actual compact source/owner admission, actual model fitting, numeric parity or OS-guard/resource feasibility. Missing-module/old-selector red evidence is retained separately.

No tests were rerun. Inspected source hashes:

- job_payload.py: `0ed0d982c91b0ba1336770401d94781067c5b4cb4cc0ce4386109625b822da57`
- test_compact_dispatch.py: `e99b65d8af66a0b79153765df2f44b2a94e4f56c01ea74d8c46bfa6145c73f02`
