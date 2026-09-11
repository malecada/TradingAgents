# One-child budget amendment successor

This package preserves the original `tradingagents/research/` package unchanged.
It copies the original admission, lifecycle and structural verification behavior,
then adds a narrowly scoped, independently verified certificate for exactly one
named child of a failed run. It has no strategy, market access, empirical inputs,
real certificate or automatic research launch.

Original copied file SHA-256 values:

| File | Original SHA-256 |
|---|---|
| `__init__.py` | `b34ced6fb4b6dd9dc1ae15645c40d62687ae7fa85f104ff77a6f1f49f874d2af` |
| `admission.py` | `fbb9c00ef14f193255e7405c16bec380123ecb71cced64aa63f106e8ff8ba836` |
| `lifecycle.py` | `2d15a74935f251edd3dea19d2bf72b0e0477de01495f6c79670ce9c1da813364` |
| `verify.py` | `70f7e33d1ee8e4edebf4292f7fa74d6b2410f0c20d2db20511d19efacc725313` |

`ResearchRun.start` and its arguments remain unchanged. The new child imports
`ResearchRun` from `tradingagents.research_amended`. Its gate pins the successor
`runtime_hashes()`, which includes all successor Python modules and the preserved
original modules used by independent historical receipt verification. Original
claims retain their original runtime hashes and source commits.

## Scope and accounting

The original family object is unchanged: its budget, prior-attempt count,
mechanism identifier and history reference cannot be rewritten. All same-mechanism
claims remain counted, including failures and interrupted claims. Without a
certificate, original exhaustion rules still apply. The extension is valid only
when the original budget is exactly exhausted, the target is new, and its parent
is the latest family attempt with a failed terminal receipt. Every prior relevant
claim must have one structurally valid terminal receipt. All historical experiment
objects must remain identical in the new registration. Every dataset definition
from the failed parent's committed registration must remain present and identical,
including its identity, history reference and exposures; retaining only a dataset
label is insufficient. No family/program renaming,
chaining, second amendment, exclusion of failed attempts, repeated ID or reuse of
the same certificate for another child is admitted.

The certificate grants an effective budget of original budget plus one only to
its named target. Its claim stores the reference and effective accounting. Start
is serialized with the original exclusive lock; subsequent reads, writes and
completion revalidate the same certificate. A claim consumes the one attempt even
if input validation fails, its context exits early, or the process is interrupted.
An abrupt failure can leave a claim without a terminal receipt; that state cannot
become another permitted attempt.

## Exact schema

References below are objects with exactly `path` and `sha256`. Paths are local,
nonsecret, committed paths. Every certificate, manifest, review and repair artifact
must match both the execution and design commit and current working-tree bytes
at admission. Canonical hashes mean SHA-256 of sorted-key compact JSON with
`allow_nan=False`.

The target experiment adds `budget_amendment: {path, sha256}`. Its referenced
certificate has exactly these fields:

- `schema_version`: integer 1; `amendment_id`: normal lifecycle identifier.
- `program_id`, `family_id`, `mechanism_id`, `family_sha256`: original identities
  and canonical hash of the complete original family object.
- `increment`: integer 1; booleans are invalid.
- `target_experiment`, `parent_experiment`.
- `target_contract_sha256`: canonical hash of the full target experiment object
  excluding only its `budget_amendment` field, avoiding a circular certificate hash.
- `prior_claims`: exact mapping of every prior same-mechanism experiment ID to
  `{claim_sha256, terminal, terminal_sha256}`. Terminal is `failed.json` or
  `complete.json`; the bound parent must be failed.
- `review`, `repair_preflight`, `economic_manifest`: artifact references.

The economic manifest has exactly `schema_version: 1`, `baseline_experiment`,
`economic_source_files`, `baseline_harness_source_files`,
`target_harness_source_files`, and `experiment_invariants`.

The economic source map is nonempty and unchanged in parent and target. Its union
with each respective harness map must exactly equal that experiment's registered
source map, without overlapping keys. The two harness maps explicitly identify
the permitted replacements/additions. The invariant object is the entire parent
and target experiment excluding only `parent`, `charter`, `question`,
`source_files`, `runtime_hashes`, `outputs`, and `budget_amendment`. Thus inputs,
windows, cells, stage, reuse, selection and any registered configuration fields
remain identical. The complete target contract hash additionally binds all
permitted harness/resource/output differences. Classification of code as economic
or harness requires independent human review; the helper does not infer semantics
from filenames or execute code to prove equivalence.

The approval JSON has exactly:

- `decision: "approve-single-amendment"`, `target_experiment`, `increment: 1`.
- `target_contract_sha256`, `economic_manifest_sha256`.
- `independent_review`: reference to the final independent assessment.

The repair-preflight JSON has exactly `status: "pass"`, `target_experiment`,
`economic_manifest_sha256`, and a nonempty `reports` list of artifact references.
These are hash-bound human approval and repair evidence, not cryptographic proof
of reviewer identity, scientific value, absence of earlier empirical computation,
or financial correctness. An engineering-only approval cannot pass the required
decision field. Financial execution still requires the separately reviewed,
committed target gate and concrete certificate.

## Verification and validation

`verify.py` retains structural reconstruction of committed claims, outputs and
terminal denominators. `verify_amendment.py` independently reconstructs the
certificate, history inventory, preservation manifest, review/preflight bindings
and accounting; it imports neither admission nor lifecycle. Frozen original
verification checks historical claims/terminals. No historical output is rewritten.
This verification proves retained-byte/contract consistency, not economic validity.

Synthetic checks use disposable Git repositories and invented inputs. They cover
complete and failed amended lifecycles, the original exhausted path, malformed
increments, altered family/history/economics, wrong target/parent, omitted or
changed receipts, review/preflight rejection, repeated and concurrent starts,
interrupted claims, chained amendments and independent verifier tampering. A full
synthetic lifecycle also runs under the frozen v2 guard at 512 MiB sampled
aggregate RSS, two CPUs and 120 seconds.

Run from the active checkout:

```sh
.venv/bin/python -B -m pytest -q -p no:cacheprovider --import-mode=importlib tests/research/test_amended_lifecycle.py tests/research/test_lifecycle.py tests/research/test_verify_examples.py
```
