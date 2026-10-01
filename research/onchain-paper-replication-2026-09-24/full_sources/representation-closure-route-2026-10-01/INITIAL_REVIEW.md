# Initial independent review — acceptance withheld

## RC1 — earlier event snapshots use an unrelated producer's metadata cap

`closure.py:76–78` snapshots each graph_complete event with the graph-output metadata ceiling, but every other event with the MCM-output metadata ceiling. This includes samples_complete and dictionary_complete, whose accepted event-reading route uses the issued dictionary ticket's registered artifact policy `max_manifest_bytes` (`sample-artifact-route/route.py:119`). The MCM publisher likewise reads its prior event prefix under that artifact policy (`mcm-publication/publication.py:78`).

Consequently the closure can reject an otherwise admitted sample/dictionary event solely because its serialized extent exceeds the unrelated MCM sidecar limit. A larger but valid same-object JSON serialization illustrates the mismatch; this is a conservative availability defect, not unsafe acceptance. Current tiny fixtures do not establish behavior when those selected ceilings differ materially.

Resolve the earlier event cap from the actual ticket's registered artifact input and retain it in the metadata snapshot/lease. Graph and MCM events can retain the ceilings appropriate to their own publication contracts. Add a focused regression with differing admitted ceilings and verify both initial read and repeated lease. A smaller deliberate closure-input cap would need an explicit selected contract, not an incidental borrowed producer limit.

This finding is based on source inspection; no counterexample was run by the reviewer. Original source, tests and active-run evidence must remain preserved before any correction.

## Other inspected joins and qualifications

The exact MCM/graph completion union refuses missing and duplicate required identities before graph-array admission. Actual registered denominator and issued dictionary admission remain mandatory. Each real saved graph admission joins original MCM values and releases its numeric receipt before the next graph. Retained compact proof/start/event snapshots, component inventories/signatures and dictionary/sample leases support later checks after that release. Binding lineage includes required graphs and dictionary training-only graphs; its schema and configuration fields follow the maintained motif binding conventions, with the explicitly extended workload identity.

The sequential numeric ceiling restricts declared per-graph read/conversion policies, not all resident parent/dictionary/sample data or process memory. The record byte cap is checked on the constructed encoded metadata and is not a preallocation memory limit. There is no durable representation event or seal, model fit, historical/mapped admission or empirical release in this component. Final acceptance requires closed corrected evidence and bindings.

Review activity read implementation, compact metadata source and test source only. No tests, historical jobs, empirical numerical arrays, raw data or SQLite stores were read or executed. Only this initial review file was written.
