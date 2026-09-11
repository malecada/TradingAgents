# One fixed seventh dated-family investigation

This additive runtime admits only `dated-spread-book-20260911` through a distinct
book-investigation certificate. Original `research`, `research_amended` and
`research_extended` modules remain unchanged. No implicit chain, general budget
manager, live order or eighth investigation is authorized. Import `ResearchRun`
and `runtime_hashes()` from this package; the `ResearchRun.start` interface and
original exclusive lock remain unchanged.

The target contract—not the admission engine—pins eight primary books, sixteen
same-quantity scalar diagnostics and seventy-two stress states. This package
performs no financial calculation and grants no execution simply on import.
Every claim, read, output write and completion revalidates its bindings; a claim
consumes the sole grant even if failed or interrupted.

## Exact accounting and three distinct verification boundaries

The unchanged original family remains budget4/prior1. Five completed/failed
program predecessors plus historical1 consumed effective6. The latest parent
must be completed `dated-mark-20260911`. Exactly one repair and one source grant
must be present. Only the named book receives increment1 and effective7.
Ordinary paths remain exhausted; repeated targets or another grant fail.

The frozen independent v1 snapshot checker is reused with its runtime pinned.
It reconstructs the repair at its closed three-predecessor inventory.
`verify_v2_snapshot.py` independently reconstructs the source certificate at
its closed four-predecessor inventory and retains the nested v1 proof. Later
claims remain visible outside those historical boundaries; an unbound claim
predating the boundary fails. These snapshot functions grant no later allowance.
`verify_grant.py` separately requires the complete current five-predecessor
inventory, exactly the closed v2 inventory plus its completed source claim.

The frozen v1 and v2 live-ledger verifiers are not represented as passing after
their respective descendants. Their refusals on expanded inventories remain
expected limitations and are tested. Structural/hash verification is not economic
validation, proof of a reviewer's identity or proof of undisclosed research history.

All family, experiment (including unrelated/unrun objects) and dataset definitions
in historical relevant registrations remain identical. Physical old gates equal
their latest bytes at the completed source parent's commit. Historical sources,
charters, outputs, certificates, reviews and linked preflights remain unchanged.
Runtime prefix equality preserves original/, amended/ and extended/ versions;
repinning altered ancestors in the new gate is insufficient. Only explicitly
registered new datasets may be appended under ordinary exposure-history checks.

## Certificate and supporting artifacts

References are exact local nonsecret `{path,sha256}` objects, matching current,
execution-commit and design-commit bytes. Canonical hashes use sorted compact JSON
with no nonfinite numbers. Target field: `budget_book_grant:{path,sha256}`.

The certificate has exactly:

- `schema_version:1`, `grant_id`, `program_id`, `family_id`, `mechanism_id`,
  `family_sha256` of the unchanged complete original family.
- Integer `increment:1`, `original_budget:4`, `prior_effective_budget:6`,
  `effective_budget:7`; booleans are rejected.
- `target_experiment:"dated-spread-book-20260911"`,
  `parent_experiment:"dated-mark-20260911"`, `target_contract_sha256` of the
  entire target excluding only its `budget_book_grant` field.
- `prior_claims`: exactly five IDs, each mapping to `claim_sha256`, `terminal`
  (`complete.json` or `failed.json`) and `terminal_sha256`.
- `consumed_grants:{repair:{experiment_id,certificate:{path,sha256}},
  source:{experiment_id,certificate:{path,sha256}}}`.
- `review`, `preflight`, `change_manifest`: references.

Change manifest: exact `schema_version:1`, `baseline_experiment`,
`target_experiment`, `baseline_contract_sha256` (whole source-parent contract),
`target_contract_sha256`, and `changes`. Every changed top-level field has
`before` and `after` objects containing `present:boolean` and `value` only when
present. Comparison omits only the target grant field. This records a different
book question; no unchanged-economics fiction is used.

Approval: exact `decision:"approve-single-book-investigation"`,
`target_experiment`, integer `increment:1`, `target_contract_sha256`,
`change_manifest_sha256`, `prior_claims_sha256` (canonical current five-claim
inventory), and `independent_review:{path,sha256}`. A source-only approval cannot
substitute. Preflight: exact `status:"pass"`, `target_experiment`,
`change_manifest_sha256`, nonempty `reports:[{path,sha256},...]`.

Admission and independent verification reconstruct these separately. The scoped
financial review still has to establish the target's accounting and information
value before committing a real certificate.

## Synthetic fixture and checks

`tests/research/test_spread_lifecycle.py` exposes
`build_spread(root,target_updates=None,datasets=None)` returning
`(root,spec,certificate,source_commit)` and `rebind_spread(...)`. It reuses the
preserved sibling `test_extended_lifecycle.py` fixture to construct invented
history, completes the source attempt, and writes `spread-registration.json`.
Caller-created financial-runner fixture files remain untouched. Dataset additions
cannot replace existing definitions. Copy both fixture modules together or import
by the original absolute path when using a disposable full-CLI preflight.

Tests cover both frozen live-ledger refusals, nested historical proofs, exact
accounting, duplicate/concurrent/interrupted attempts, unfinished predecessors,
historical objects/files/runtime changes, both consumed certificates, source-only
approval rejection and independent recommitted attacks. The guarded fixture uses
two CPUs,512MiB sampled aggregate RSS and120seconds. No empirical data or network.
