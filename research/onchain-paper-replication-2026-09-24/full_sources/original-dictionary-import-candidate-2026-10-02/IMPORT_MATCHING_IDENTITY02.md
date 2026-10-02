# Separate original dictionary and current execution identities

This amendment corrects the requirement in IMPORT_STAGE_CONTRACT01 to keep the
MCMScoreStream admission path unchanged. That requirement is incompatible with
an honest import. The original dictionary has a scientific matching hash, while
the current scalar backend requires a backend-qualified execution matching hash.
Neither the original dictionary configuration nor its matching hash may be
rewritten to impersonate a freshly fitted compact dictionary.

The imported numerical capability must expose two separate immutable identities:

- `dictionary`: the genuine original Dictionary, including its exact original
  identity, configuration, matching_config_hash, samples, ordered representatives
  and memberships. Its full original ancestry remains independently bound.
- `execution`: a distinct typed capability owned by the current import stage.
  It binds the original dictionary identity and matching hash, current admitted
  matching configuration, the exact scalar BACKEND, current source/runtime,
  Binding/owner/import-stage receipts and a backend-qualified matching hash
  `cache_key({'config': current_matching_config, 'backend': BACKEND})`.

Admission must authenticate that the original matching configuration is the
registered scientific configuration and that the current configuration retains
the same numerical settings. Backend execution metadata is separately declared;
it cannot silently replace a scientific setting. This proposal grants no
equivalence verdict for a backend whose numerical contract is unverified.

The fresh compact route retains all existing checks. A narrow imported stream
constructor or class method may accept only the genuine imported execution
capability, rejoin its lease/content/stage evidence before namespace allocation,
and enter the same existing row-major compute, checkpoint, score-tail and batch
logic. No duck type, rewritten Dictionary, forged Produced/Proof, mutable caller
hash argument or generic callback can bypass the current type boundary. The
constructor's identity admission and workload assembly are explicitly within
implementation scope; the numerical matching and retention kernels remain
unchanged.

ScoreBatches' six-field scope remains intact. `dictionary` names the original
scientific Dictionary identity, `ordered_motifs` authenticates the original
column order, and `matching` names the current backend-qualified execution hash.
The workload hash additionally binds the original matching hash and genuine
import execution capability identity. This makes the ancestry explicit without
adding unrecognized scope fields or hiding the original behind a replacement
dictionary. Both hashes are retained in the import receipt and resulting typed
MCM evidence, and recomputed during content/lease checks.

The imported compact_mcm entry point must derive its expected scope from those
two identities. It must not reuse the fresh route's dictionary.matching_config_hash
as the current execution hash. Publication's current backend-qualified matching
check can remain substantive; its selected job-input/owner-stage seams still need
explicit resource-route support. Existing fresh dictionary/output readers and
all original dated bytes remain unchanged unless a separate source change is
declared and reviewed.

Finite proof must reject original matching-hash mutation, current execution-hash
mutation, changed backend/scientific configuration, swapped original dictionary,
representative reorder, transplanted execution capability, revoked stage/owner,
and mutation after an external lease. The genuine two-target MCM fixture must
verify both identity families in every receipt and exact original column order
and values. Fresh compact regression remains required. No empirical cell or
financial fit follows from this contract or a synthetic proof.

Proposed additional source ownership is limited to MCMScoreStream identity
admission/workload assembly and the imported compact_mcm scope adapter, alongside
the separately listed original-dictionary stage modules. It does not authorize
changing matching mathematics, score-tail retention, storage budgets or the
original scientific hash to avoid an admission failure. This is preparation for
independent review; no source implementation or numerical run has occurred.
