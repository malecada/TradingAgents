# Independent initial cold-publication review

Acceptance is withheld for the metadata gaps below. These findings concern the
claimed saved publication/content inspection; they do not demand the explicitly
deferred scientific denominator, source compatibility or current-worker admission.

## CP1 — incomplete terminal and journal evidence

At `publication.py:108–111`, a graph proof is accepted from a hash-pinned path
without enforcing its registered workflow/experiment/graph attempt path, reading
and joining its start record, or reconciling its attempt inventory. The final
lease at lines 123–129 checks failed markers only at the representation seal,
representation publication, pair-workflow and feature-journal roots. A graph
attempt containing both `complete.json` and `failed.json` is consequently not
refused. A missing or changed graph start record likewise does not affect this
inspection. These are terminal-evidence conflicts within the native publication
being certified, rather than a numerical producer replay requirement.

Also, feature `owner.json` and `start.json` are only required as inventory names
at line 128. Their content, type and hashes never enter the read/lease records.
Arbitrary replacements of those two records can coexist with a successful
`historical_publication_metadata_verified` result. Read and join the actual
owner/start metadata and retain it in the bounded reread set.

Require exact graph attempt paths and start references, reconcile complete-only
attempt inventories initially and finally (including broken failed links), and
check owner/workflow/graph/event/policy consistency. Add negative tests for a
graph complete+failed conflict, missing or foreign start, and changed feature
owner/start. No numerical archive replay is needed for these checks.

## CP2 — output read authority is registered but not selected

At `publication.py:112–120`, the graph event's `output_input` need only name some
registered input with the supplied hash. It is not required to equal both the
producer plan and execution job's selected `graph_output_input`. The resulting
policy supplies the manifest/artifact limits used for real native array reads.
An event referencing a different registered, more permissive policy can therefore
pass this authority boundary.

Before component inspection, require the exact selected plan/job output-policy
name and hash, and join the graph proof and start to that same policy. Preserve
the native batch-policy checks already present. Test a registered but unselected
alternative policy, with allocation forbidden, so refusal is shown at metadata
admission rather than a later numerical boundary.

## Evidence and scope

Saved `check03.log` reports six tests passing in 0.354 seconds. The positive test
forbids `seal.finish` and verifies two saved native graph hashes. The corrected
wire negative changes a loaded score within its valid range and reaches the
wire-hash refusal; it does not mutate the closed retained checkout. Other join
negatives inject decoded records through the reader, and do not constitute full
rehashed malformed filesystem chains. The existing tests do not exercise CP1 or
CP2. No tests or producers were executed during this review and no empirical
arrays were read by the reviewer.

Independently calculated SHA-256 values:

- `publication.py`: `c573fb26ca1de4b0e016550c7c318d3e4eb33e7d36a0f44e7f8a072d74a2a4e8`
- `test_publication.py`: `eea476271792122417b5170e69cd0515a4bc54753198ec9d180b69cfcc9bff28`
- `check03.log`: `9b9fc70bf756c6e17e1432f25aa95f99f0b292ba00e3b2372bc1371c2b3c6ecb`
- `SCOPE.md`: `adbbfd53356f7e4bb3c7f621b5186bb807adad35f80849450d460650838fde88`

The explicit false flags for current-run admission, scientific denominator
revalidation, source compatibility and producer replay are appropriate. The
numeric helper checks bounded saved native content and wire hashes; this review
does not establish full current reuse, resource-policy compatibility, atomic
snapshots under continuous mutation, financial performance or empirical release.
