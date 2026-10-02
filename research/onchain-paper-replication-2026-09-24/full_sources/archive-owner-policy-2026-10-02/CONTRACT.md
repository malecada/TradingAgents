# Registered archive selection and prospective allowances

The next owner boundary is a read-only registered selection, attached to an
actual fresh compact_owner.Owner. It must match both execution-job and producer
plan selection, the bound descriptor's archive-policy hash, current run/source
and numerical owner authority, the exact admitted policy bytes and transport
identity. No historical owner or already-started stage may acquire a new storage
selection retroactively. A saved selection rechecks current authority before
yielding a writer policy.

The fixed required-stage population and original event/checkpoint maxima drive
the conservative accounting. Each possible stage has a unique deterministic
remote prefix derived from its actual owner identity and stage name. Bounds
cover remote event payload, writer metadata, finite repeated stage-read metadata
and reference files. Decoded transfer allowance includes one upload, one copy
readback, one writer-finalization replay, and each declared cold stage read.
These are prospective logical/decoded-member allowances; SSH framing, transport
staging, physical allocation and remaining scientific payloads are excluded.
The engineering gate permits at most1024 prospective verifications per stage;
a larger control population requires an explicit reviewed change to this bound.

This selection itself creates no namespace, transfers no data, installs no
writer and spends no read attempt. It does not meter or enforce future operation
counts. The subsequent owner adapter must consume the selection and maintain
durable finite claims/reservations before dispatch. Stage writing/sealing,
current-owner publication and terminal selection remain on the historical local
route until that explicit adapter is implemented and reviewed. No empirical
admission or whole-workflow resource feasibility follows from this gate.
