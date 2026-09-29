# Optional mapped sampling weights

The production sampling component now accepts explicit `weight_workspace` and
`max_weight_bytes` keyword arguments. Its default eager behavior and scientific
configuration remain unchanged. The optional path stores weights, probabilities
and cumulative probabilities as three float64 mapped files, preserving the
pinned NumPy 2.3.0 global reduction/scan order and one PCG64 draw per selection.
No source graph, center, edge, motif or scientific limit is removed.

This is component integration only. The registered feature-production pipeline
does not yet supply these arguments. Empirical use still requires an admitted
scratch policy and exact output paths, with the resource guard covering that
filesystem, process allocations and page cache. Mapped storage is not a bound
on graph memory, neighborhood memory, runtime or file-cache residency.

The directory is exclusive and retained. Its intent binds the training graph
hashes, scientific configuration and seed. Actual encoded intent and terminal
receipts are capped at 32 KiB each; planned bytes include their separate rounded
allocations and a directory block, plus three rounded numeric-file allocations.
Startup checks require that allocation above the 20 GiB free-space floor, and
numeric files use posix_fallocate before mapping. Filesystem overhead and changing
free space remain reasons for runtime guard enforcement; the size calculation is
not a filesystem-wide guarantee. Budget/version/metadata/disk failures before
reservation create no scratch directory. Allocation and caught workload failures
retain partials and a failed receipt. Flush, close and fsync are each attempted
for every created mapping even when an earlier cleanup operation fails.

Success flushes/closes the scratch files and binds the sample identity. Scratch
never supplies an automatic recovery contract. A kill that prevents Python
cleanup can leave intent and partial arrays without a terminal receipt; outer
guard evidence must classify the interruption. No identity may be overwritten
or reopened automatically. Previously completed samples must be reused through
their admitted sample manifests, not reconstructed from these weight files.

## Verification evidence

- red01: 14 intended missing-API/module failures before implementation.
- green01: 22 passing sampler/neighborhood/dictionary/MCM checks.
- green02: 36 passing checks including feature-journal behavior.
- Independent review found a skipped close after flush error and inadequate
  metadata rounding for large filesystem blocks. Red02 directly reproduces the
  flush failure. Its large-block case wrongly reached disk_usage and then failed
  because the mocked statvfs lacked a field; it was not a clean budget-assertion
  counterexample. The fixture was corrected to supply independent free-space
  telemetry; original failure evidence remains unchanged.
- green03: 38 passing checks after those corrections.
- green04: all 23 mapped-sampler cases pass, including exact five-seed graph
  sample identity/probability/RNG parity and skewed weight vectors of 257, 4,097
  and 131,071 elements. Tests also exercise invalid weight mass, zero weights,
  low disk, metadata/version/budget refusal, partial allocation, caught
  interruption and flush failure with mapping closure.

The earlier 6,400-choice standalone probe remains separately preserved; no
terminal empirical job was rerun. Full named offline verification and final
independent release assessment are recorded separately when complete. There is
no empirical claim, new data capture, financial fit or change to C01–C18 status.

## Named offline completion

Offline01 completed3,316tests plus97subtests,2CUDA skips:standard2,768in1102.18s;neural548in390.99s. Guard1496.89seconds,peak2,678,321,152bytes,child0,cleanupverified,zero memory-limit events. All8sourcebindings match. No empirical job/fit or registered policy enablement occurred. Independent terminal review is recorded in CODE_REVIEW.md before release.
