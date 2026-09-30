# Independent prospective synthetic-profile review

Conditionally accepted for one fresh finite synthetic invocation after the commit/push and fresh checks below. No blocking source or oracle defect was identified. No profile was executed for this review and no checkpoint, empirical graph or historical matrix body was opened. Acceptance does not establish measured feasibility or approve production use.

All 96 compact bindings independently matched at HEAD `eb5ddb51aa49537ec53fca6b3a3d7f4803d29900`. The manifest includes the actual composite and component source, their relevant review/evidence, production imports, configuration, runtime description, worker, launcher and protocol. Reviewed SHA-256 identities are:

- `probe.py`: `70445106c2e089e26e068e323ac91caa8ec7743747a353859f5d66d5befef22e`
- `run_guard.py`: `d38dc0860a6c8d593e41486254d74094482e60b92c014f246e650de46c0fe834`
- `PROTOCOL.md`: `e269db331419e6fa3fbafc46a9190c2473a64154244eedd7a867994c2f69c8bc`
- `bindings.json`: `6cf6b39867ae13f7ea976eac2b143bf0f6653f981d430f8b0f19827641ca7c64`

## Independent reconstruction

The fresh pair has 2,000 nodes per side, zero edges and constant zero scalar node attributes. Node agreement is one; the admitted scalar normalization produces the uniform soft matrix within the stated `1e-14` diagnostic tolerance. With alpha one, a complete diagonal hard assignment has node contribution one, no edge contribution, and exact scalar score 0.5. The frozen schedule yields 48 iterations and temperature termination; it does not change the 4,000,000-pair cap.

For stable row-major ranking of a tied square matrix, selected diagonal entry `i` has flat index `2001*i`. The first 65,536 scanned entries therefore select indices 0 through 32: exactly 33 diagonal pairs. The final selected index is 3,999,999, so completing all 2,000 pairs requires exactly 4,000,000 scanned entries. Those are ranked entries, not the old hardener's repeated matrix-scan chunks.

The inherited annealing implementation requires 4,000,000 initial node operations plus 48 iterations of one outer setup and 62 scale, 63 row, 63 column and 62 exponentiation blocks: 4,012,048 operations in two calls under the worker's 4,000,000 operation allowance. The probe records these counters rather than asserting that exact annealing count. Its explicit assertions cover the final schedule, uniform matrix, prefix, full ordered pair list and score. There is no nonzero-edge update workload in this fixture.

## Ownership, identity and resources

Both checkpoints use exclusive new directories. After prefix publication the initial state is closed and discarded, then restored against its manifest SHA; cursor/pairs and soft-matrix SHA are checked. After final publication, the actual restored ranking mapping is explicitly closed before replacement. The second restored final state is scored, compared with the previous score, and its actual map is explicitly closed before the result is published. A failure does not produce a successful result; the finite guard must close the worker and preserve partial outputs. Successful explicit lifecycle assertions do not prove every injected failure path here.

The admitted 128 MiB retained-state limit covers 128,000,000 numeric bytes. Ranking's 80 MiB allowance covers the component's 68,036,000-byte explicit allocation formula; conservative overlap with annealing is 164,036,000 bytes. Native sort workspace, input graphs, Python state, validation and I/O remain outside these component formulas and inside the process guard. The uniform-error diagnostic itself creates dense temporary arrays, so measured process peak must not be presented as the ranking kernel alone.

Each 128 MiB checkpoint allowance exceeds the component's 128,197,120-byte conservative logical requirement. Two admitted maxima total 268,435,456 bytes. The required 512 MiB dispatch headroom exceeds that total, but it is not a filesystem-allocation theorem or reservation against other host writers. The worker records actual logical file extents; physical allocation and complete retained-directory footprint require the later closure review if claimed.

The launcher and worker agree on 1 GiB memory maximum, 768 MiB high, zero swap, 3 GiB host reserve, 4 GiB startup available RAM, a 10 GiB disk floor and 1,800 seconds. The unchanged guard assigns and verifies two inherited CPU affinities. Initialization, validation, sort creation, sparse scoring and checkpoint I/O remain atomic inside that finite wall limit.

## Conditions and interpretation

Before dispatch, commit and push the exact reviewed manifest and all bound files; record the resulting HEAD and verify the pinned runtime, all 96 hashes and committed bytes. Confirm no active replication unit or competing Graph 10 owner, no reserved attempt paths, at least 4 GiB available RAM and at least 10 GiB plus 512 MiB free on the guarded filesystem. The extra disk headroom and exclusive-owner checks are protocol/preflight requirements, not checks newly added to this thin launcher. Freeze HEAD and bindings through closure; do not restart a failed identity.

The resulting guard, worker log, checkpoints, exact owner absence and post-run bindings require independent terminal reconciliation before claiming success. Annealing timing explicitly includes atomic ranking creation. Any observed times will be specific to this structured zero-edge fixture and host state; neither comparison with old profile timings nor the faster sorting algorithm alone establishes a controlled speedup. Full nonzero-edge schedules, real hubs, dictionary/MCM/neural feasibility, GPU behavior, production backend/cache lineage and financial results remain outside this profile.
