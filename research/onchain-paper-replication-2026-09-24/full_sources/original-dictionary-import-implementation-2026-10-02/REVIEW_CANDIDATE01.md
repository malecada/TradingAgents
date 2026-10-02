# Independent review of import-preparation slice01

Disposition: **withheld for the checked materialization-record integrity defects below**. The proposed separation of original scientific identity and current backend execution identity is coherent with the accepted contracts, and the source honestly remains an unadmitted preparation slice. It neither implements the genuine resource Binding factory nor creates a durable import Owner/stage or usable MCM capability. Correcting the two findings is necessary but will not complete that route.

Review was read-only source/contract inspection and standard-library hashing, JSON and AST parsing. No candidate/research-module import, NumPy/Torch import, test execution, graph materialization, Binding, Owner, claim, model, guard or job occurred. Only this new review file was written. Source and author evidence remain unchanged.

## Exact reviewed evidence

All11 entries in `manifest01.json` were independently checked for exact size/hash, including preserved RED/GREEN logs and four interface snapshots. Python syntax was inspected by AST only. Pins:

- `manifest01.json`: `f1b0ff0e2f83eb6ced384763206b508508d69b2dfae847ef4a0d653384600218`.
- `original_import_preparation.py`: `def74f8cc2908f0bcab8a557e55237aaea508202994ea21420aaae4f49d2f9ed`.
- `original_dictionary.py`: `c9dff424496c0ea7726a14a9816566f1db8c9be483d21e40940289e675a2ac2e`, byte-identical to accepted candidate03.
- `IMPLEMENTATION01.md`: `c2e3082a7f70202cf2c7633f37ea65b86787088958e987efe62b21dfd6002f83`.
- `test_contract01.py`: `60763d72fb61e6978d2ae7a0303b94468af90e711b23383f15cadf7628f306a8`.

Contracts inspected: `IMPORT_STAGE_CONTRACT01.md` (`dd30ae84e9c8d8230d1d258384742a4b97e1f7c2e9c71f394a9a884e14625bae`), `IMPORT_MATCHING_IDENTITY02.md` (`0d24f03a3541ca7a170c7f6abf845840469e34379c26827c0b9f8ae7e36e0b07`) and `IMPORT_KERNEL_IDENTITY03.md` (`1410b9a407fa9289476fe8dbb289bd109af82aad11d76592cf219641a3bb2443`). The later two contracts qualify the original stage proposal's fresh-stream/kernel assumptions.

## Material findings

### OIP1 — checked materialization record does not authenticate its provenance or extent

`original_import_preparation.py:151–166` stores `_evidence` and public `numeric_bytes` without pinning either, while `_object_pin` contains only PreparedImport, Dictionary and representative-object identities. `check()` rejoins the prepared metadata capability and compares the dictionary hash and motif identities, but it never authenticates the returned evidence object's representative indices/bundle against that original capability, nor recomputes or pins the reported numeric extent.

A source-derived counterexample is replacing `_evidence` with a dataclass replacement that keeps `dictionary_identity` unchanged while changing `representative_indices` or `_bundle_sha256`. All existing conditions in lines158–162 remain true; lines164–165 then emit altered provenance as a checked record. Independently, assigning `numeric_bytes=0` changes the returned extent without affecting any check. This counterexample was not executed; it follows directly from the fields used in the predicate and returned record.

Impact: although no MCM authority is granted today, downstream preparation or a future stage could freeze a false original-column/bundle or numeric reservation record after calling `check()`. It contradicts the claimed original evidence/content pins and the accepted contract's immutable ordered ancestry.

Required correction: capture the exact original evidence object and a callback-free immutable record of its bundle, representative indices and scientific identities at construction; rejoin that record with the still-live original capability after external authority checks. Keep a private extent pin and verify it against actual materialized arrays or a retained verified extent contract. Do not trust a mutable public extent. Reject original-evidence substitution, reordered/changed sample indices, changed bundle, underreported extent and mutation during an external lease. Add focused non-numerical mechanism sentinels for these fields; genuine numerical materialization remains a separate guarded proof.

### OIP2 — Dictionary.identity and array-object replacement are omitted from the object contract

`original_import_preparation.py:155,161–162` pins representative object IDs, but not their array object identities, and checks only `dictionary_hash(self._dictionary)` against evidence. The actual `dictionary.py:98` hash function recomputes semantic content **without using `Dictionary.identity`**. Consequently mutation of that field can leave `MaterializedOriginal.check()` successful while the contained Dictionary advertises a different identity. Equal-content replacement arrays also retain matching graph hashes and representative object IDs, bypassing the contract's specified original-array identity boundary.

Impact: the container and checked record can disagree about the dictionary identity; a future typed MCM consumer using `.identity` could bind a different workload. Equal-content object replacement is not presently a numerical change, but it violates the explicitly required anti-substitution contract and would leave no evidence of the original numeric allocation being replaced.

Required correction: require actual Dictionary identity equal the immutable original evidence identity as well as the recomputed semantic hash. Pin each original array object together with dtype, shape and content fingerprint/extent, retaining existing graph-content checks. Refuse dictionary-identity changes, graph/array substitution and post-lease mutation before returning checked metadata. These tests must target the actual check boundary, not merely repeat the extent helper's formula. Preserve candidate01 and its evidence; use a new numbered corrected candidate.

## Coherent preparation already present

`prepare` requires exact `matching_owner.Binding`, invokes its live checks, verifies the two prospective module hashes against admitted source, reads the actual passed `job_input`, requires `compact_resource`, and checks absence of the compact Owner namespace before calling public original admission. It does not fabricate a sample proof or cast the old dictionary into fresh Produced. `_selection_now` checks job/producer descriptor equality and workflow hash, original-control selection/hash, and required stages; the copied original admission additionally joins the registered control/body hashes, complete required-graph list and original matching settings.

The prepared configuration captures run directory, claim, snapshots, selected job/input/source details and live Binding state. Rechecks invoke genuine Binding and original evidence checks, then repeat selection/source/configuration joins. These are prospective public API requirements, not proof that the actual current factory can produce such a Binding: the inspected `baseline/matching_owner.py:162–164` still hardcodes `execution_job` and rejects every kind except fit. The new relative-import file is not installed as a runnable package path. No real public Binding execution is established.

`required_stages` selects dictionary-import followed by sorted unique registered MCM hashes before Owner birth. Allowing1–9 targets is suitable for a declared tiny fixture; empirical admission must still require all nine and the full23-cell parent map. This helper alone does not enforce or complete that empirical denominator. `stage_contract` remains an unsigned, unadmitted prospective constructor argument, not an Owner receipt or completed stage.

The numeric path first obtains validated original JSON through the existing capability and checks `8*(node_count*node_width + 2*edge_count + edge_count*edge_width)` before NumPy allocation. It preserves representative order, IDs/endpoints, memberships, sample/training hashes, matching/configuration/hierarchy and original identity, then constructs float64 features/int64 endpoints and recomputes actual scientific and matching graph hashes. It performs no sampling, fitting, clustering or distance-matrix work. The16 MiB cap is numeric payload only: existing JSON/Python objects, repeated parsing, AttributedGraph immutable copies, hash `.tolist()` scratch and total process peak are excluded and must be budgeted. This source path has not been numerically executed.

`execution_contract` compares current matching settings with the registered original matching configuration and separately derives original config-only matching identity and `cache_key({'config': current, 'backend': BACKEND})`. It preserves the original Dictionary's scientific matching hash rather than rewriting it. Current source/runtime/Binding ingredients are included, but no Owner/import receipt exists. Explicit `mcm_execution_admitted=false` is truthful; the returned JSON is not an execution capability. `MaterializedOriginal` similarly remains a distinct unadmitted type with `owner_stage_completed=false`; existing compact MCM does not accept it.

The copied original adapter preserves its prior first-fatal descriptor cleanup and post-callback evidence joins. The new numeric build runs inside `with_evidence`, which checks originals after callback success/failure before returning. No new durable writer or closure path is present in this slice, so no durable-stage fatal/uncertain-close correctness follows.

## Evidence limits and remaining route

There are exactly two distinct test methods. RED01 fails because the prospective source file is absent; GREEN01/GREEN02 report the same two helper methods passing. They AST-extract only `require`, `required_stages` and `materialization_bytes`, covering a small set of stage-order and array-extent cases. They do not instantiate PreparedImport/MaterializedOriginal, exercise genuine Binding, authenticate original provenance, import NumPy, test fatal paths or traverse an Owner/MCM route. This review inspected those logs and source without rerunning them.

Required next work remains explicit: implement the genuine resource job/Binding factory and actual job_input propagation before journal side effects; authenticate the original26 Git-source and full admission/input/intermediate ancestry independently; create the real preselected Owner import stage with exact durable intent/completion/inode inventory, cumulative reservations and held-token authority; mint a genuine typed imported execution capability only after completed-stage rejoin; and connect producer, imported kernel admission, unchanged numerical matcher, score stream, returned workload and publication through the same original/current identity pair. Existing fresh-route checks and original historical bytes must remain intact.

The genuine bounded two-target synthetic proof still needs real ResearchRun/Binding/Owner/stage, exact original numeric ordering/scores, callback/revocation/refusal and partial-second-target preservation, plus fresh-route regression. No mocked helper proof substitutes for it. The55,439,818,752-byte complete MCM inventory and its score-tail storage/physical/archive route remain unresolved; all7 neighborhood,7 matching and9 MCM cells remain in scope. None of the1,420 financial fits or paper numerical-agreement claims is established by this partial source.
