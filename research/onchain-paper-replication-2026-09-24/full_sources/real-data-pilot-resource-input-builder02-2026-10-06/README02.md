# Resource builder02 storage-domain correction

Use build_inputs02.py with the same arguments and metadata contract as builder01. Sealed01 is preserved and WITHHELD for full-size preparation because its local budget condition incorrectly included cumulative transferred payload allowance. No other selection/scientific behavior is changed.

The physical_store object retains baseline_evidence, baseline_allocated_bytes, baseline_logical_bytes, reserved_growth_bytes and reserved_control_bytes. It now additionally requires:

- retained_diagnostic_bytes: at least131072×max_commands +8388608. Successful get staging moves to the caller; each command retains one bounded transport JSON. Serialized Context calls and first-failure poisoning bound remaining diagnostic payload to one in-flight/failed get. The8MiB archive maximum is distinct from the selected typed4MiB chunk maximum.
- caller_scratch_bytes: at least3×8388608 for one source/snapshot/readback lower bound. This does not prove the full combined peak of nested original writer, score-tail, typed transfer and read-cache buffers; Root must submit a conservative complete overlap allowance.
- allocation_overhead_bytes: a separate positive finite declaration for inode/block/directory overhead beyond logical payload/control bytes. The builder does not measure or certify this overhead.

reserved_control_bytes still covers typed max_control_bytes, archive max_workflow_metadata_bytes and transport max_control_bytes. reserved_growth_bytes still covers all retained original f32 outputs. Logical growth sums growth, retained controls, diagnostics and caller scratch. Allocated growth additionally includes the allocation overhead. Each total plus its unchanged baseline must fit the same original root storage budget. Floors and actual runtime storage watchers are unchanged.

Cumulative network max_payload_bytes, max_diagnostic_bytes and transport control guards are untouched. Their declared ceilings remain prospective operational limits, not claims of simultaneous local allocation. Connection configuration remains null DRAFT; there is no execution or capacity authority.
