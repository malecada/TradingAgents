# Revision 02 — sampler route qualification

The active corrected drafts are in `revision02/`. Revision01 remains preserved
at the original paths and as an exact copy in `revision01-original/`, including
its original SHA256SUMS. Neither build01 nor validation01 was rerun or altered.

The initial README and drafts overstated the20GiB floor as a universal sampler
blocker. That wording is superseded. Source inspection shows:

- `compact_sampler._prepare` selects `resident-leased-v1`, backed by the retained
  leased core. It uses resident weights/probability arrays with a16bytes-per-center
  direct bound. It does not instantiate MappedWeights and does not impose that
  optional implementation's20GiB disk floor.
- `neighborhoods.sample_neighborhoods` instantiates MappedWeights only when
  `weight_workspace is not None`. That optional route checks20GiB plus reserved
  mapped workspace. It is not selected by the current compact sampler.
- The selected resident route retains sample neighborhoods in memory. Its direct
  weight bound excludes retained samples, NumPy choice scratch, active index,
  parent graphs, Python objects and other buffers. These RAM allowances and
  coexistence lifetimes remain explicit unknowns requiring outer guard admission.

The user10GiB floor remains for all routes. No guard was weakened or changed.
The correction removes a wrongly generalized blocker; it establishes no physical
feasibility. Resident metadata/publication/checkpoint/archive/transfer disk
allowances are still unresolved. An optional mapped-route choice would need to
satisfy its20GiB+workspace guard or a separately reviewed prospective amendment.

The revision retains all32original records/populations,43compact pins, nine graph
calendars,77/109coverage, conditional249,479,184,384-byte payload arithmetic and
unadopted cumulative61budget unchanged. Scientific dictionary reuse and all other
unresolved decisions remain. Prospective executable source/policy hashes remain
null with reasons. The four inspected source files are pinned and copied under
`revision02/observed-source/` as observations, not admission source closure.

Commands from the checkout root:

```sh
.venv/bin/python -B research/onchain-paper-replication-2026-09-24/full_sources/resource-parallel-preparation-2026-10-02/revision02/qualify_routes.py > research/onchain-paper-replication-2026-09-24/full_sources/resource-parallel-preparation-2026-10-02/revision02/build02.log 2>&1
.venv/bin/python -B research/onchain-paper-replication-2026-09-24/full_sources/resource-parallel-preparation-2026-10-02/revision02/validate_revision02.py > research/onchain-paper-replication-2026-09-24/full_sources/resource-parallel-preparation-2026-10-02/revision02/validation02.log 2>&1
```

Both exited0; no failures occurred. The read-only validator repeats the compact
hash/count/formula checks and additionally verifies route applicability fields,
resident RAM unknowns, direct-array arithmetic, source snapshot hashes and exact
preservation of every original manifest-listed byte. It imports or executes no
production sampler or empirical job. All writes are in this owned evidence
directory; source/test freeze and production gates remain untouched.
