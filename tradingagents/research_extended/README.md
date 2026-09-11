# One source question after the consumed repair

This separately versioned successor authorizes only `dated-mark-20260911` when
its exact source-only information-value approval and committed certificate pass.
It is not a reusable extension manager and grants no financial book execution.
`tradingagents/research/` and `tradingagents/research_amended/` remain unchanged.
Admission/lifecycle/structural verification are copied from the latter; the new
certificate admission and independent reconstruction are separate implementations.
The copied v1 reconstruction preserves its certificate/economic invariants while
making the historical inventory boundary explicit.

`ResearchRun.start` retains its arguments. Import it and `runtime_hashes()` from
`tradingagents.research_extended`. Runtime hashes include the seven successor
Python modules and both preserved runtime packages. The original exclusive lock
protects creation. Input reads, output writes and completion revalidate source,
artifacts, inventory and target accounting. A created claim spends the grant,
including failures and interrupted runs; no automatic retry or descendant grant.

## Fixed accounting and historical verification

The original complete family object must still record budget4 and prior1.
Exactly four current prior program claims must exist, including exactly one v1
repair certificate. That repaired run must be complete and the latest attempt.
The original historical1 plus those four claims consumed effective budget5.
Only the named target receives effective budget6. The ordinary path remains
exhausted. Family/program/mechanism renaming, changed historical contracts,
removed/changed dataset definitions, missing terminals and further grants fail.
All family, experiment (including unrun/unrelated entries), and dataset objects
from every relevant historical committed registration remain identical. Physical
registration files must equal their latest versions at the completed parent source
commit, permitting legitimate append-only updates before that boundary. Ancestor
runtime prefixes must also equal the original claims and consumed v1 runtime maps;
merely repinning altered ancestors in a new gate is insufficient.
All historical code, charter and certificate-linked evidence remains unchanged.
New datasets may be appended with ordinary explicit exposure-history checks.

The frozen v1 verifier scans the entire live ledger. It therefore stops being
applicable to the repair certificate after a reviewed same-family descendant is
added: its exact old inventory no longer equals the live inventory. This limitation
is preserved, tested and disclosed, not patched away.

`verify_v1_snapshot.py` independently reconstructs the repair at its exact closed
certificate inventory and committed source. Later claims are outside that historical
snapshot; an unbound claim predating the snapshot fails. This helper grants no new
budget. `verify_extension.py` separately inspects the complete live ledger and
requires that all four predecessors equal the closed repair inventory plus its
completed repair claim. A later extra claim therefore cannot disappear through
historical filtering. Structural/hash consistency is not scientific validation or
cryptographic proof of reviewer identity/completeness of undisclosed research.

## Artifact schema

References are exact `{path,sha256}` objects, local/nonsecret and present with
matching bytes in execution/design commits and the working tree. Canonical hashes
use sorted compact JSON without nonfinite numbers. The target adds
`budget_extension: {path,sha256}`.

The certificate has exactly:

- `schema_version:1`, `extension_id`, `program_id`, `family_id`, `mechanism_id`,
  `family_sha256` for the unchanged complete family object.
- Integer `increment:1`, `original_budget:4`, `prior_effective_budget:5`,
  `effective_budget:6` (booleans rejected).
- `target_experiment:"dated-mark-20260911"`, `parent_experiment`,
  `target_contract_sha256`: full target excluding only `budget_extension`.
- `prior_claims`: all four IDs mapped to exact `claim_sha256`, `terminal`
  (`complete.json`/`failed.json`) and `terminal_sha256`.
- `consumed_amendment:{experiment_id,certificate:{path,sha256}}`.
- `review`, `preflight`, `change_manifest`: artifact references.

The change manifest has exactly `schema_version:1`, `baseline_experiment`,
`target_experiment`, `baseline_contract_sha256` (whole parent),
`target_contract_sha256`, and `changes`. Changes contain exactly each changed
parent/target top-level field, excluding only the target's `budget_extension`:
`{field:{before:{present:boolean,value:<only when present>},after:{...}}}`.
This records a different source question; it does not assert unchanged economics.

Approval fields are exactly `decision:"approve-single-source-extension"`,
`target_experiment`, integer `increment:1`, `target_contract_sha256`,
`change_manifest_sha256`, and `independent_review:{path,sha256}`.
Preflight fields are exactly `status:"pass"`, `target_experiment`,
`change_manifest_sha256`, and a nonempty `reports:[{path,sha256},...]`.
A generic engineering approval or repaired-run approval cannot substitute.

The runtime does not infer information value or source-only semantics from code;
independent review must bind that judgment to the exact target and artifacts.
No real certificate or research execution is created by importing the package.

## Synthetic verification

`tests/research/test_extended_lifecycle.py` creates only invented disposable Git
histories and provides `build_extension(root,target_updates=None,datasets=None)`
for a separately owned actual-runner preflight. It checks complete/failing target
lifecycles, historical snapshot versus live-ledger behavior, exact budget/history,
concurrency, interruption, changed artifacts, dataset resets, further grants,
independent tamper rejection and the512MiB/two-CPU/120second guard.

Use the checkout-local locked interpreter and reviewed offline profile:

```sh
.venv/bin/python -B -m pytest -q -p no:cacheprovider --import-mode=importlib tests/research/test_extended_lifecycle.py
```
