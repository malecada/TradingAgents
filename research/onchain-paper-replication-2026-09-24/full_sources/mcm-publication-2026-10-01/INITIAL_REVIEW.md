# Initial independent review — acceptance withheld

## MP1 — required float32 output is rejected by sample-only sizing helper

`publication.py:113` passes the completed MCM matrix to `producer.encoded_size`. That producer is the retained `sampler-proof-route-2026-10-01/producer.py`; its line 46 accepts only native float64 and int64 arrays. The MCM kernel and the publication accounting check require float32. Consequently every ordinary successful computation reaches a deterministic `ValueError('native sample numeric types required')` before its component/event can be published. The attempt is left reserved/failed even when all output allowances are adequate.

Use a local, explicitly admitted sizing implementation for the supported float32 MCM payload, preserving the historical sample helper. Compare its predicted manifest, NPY and total encoded bytes with actual serialization for the supported contiguous layouts. Retain the failed original source/test/log and rerun the authorized synthetic component suite under the corrected source. The existing small-artifact negative test catches any ValueError, so its apparent pass under this version cannot establish that the intended artifact-cap check was reached.

The active `check01.log` already reports an error in the positive saved-MCM test at review time; its terminal traceback and denominator remain pending. No run was started or interrupted by this review.

## Other inspected boundaries and limits

The local driver differs from its accepted predecessor in the kernel import path and retained internal lease receipt. Inspection found no further material blocker in exclusive per-graph attempt creation, selected output-policy joining, logical reservation arithmetic, event-count preflight, existing graph-progress refusal, encoded event sizing with lifecycle serialization, inherited dictionary leases or final component inventory/signature checks. These conclusions remain provisional until the positive publication path reaches those boundaries and the final evidence is reviewed.

The review did not execute tests, numerical matching, empirical jobs or numerical-array reads. It inspected source and compact saved logs only. No saved-MCM consumer admission, historical continuation, mapped/full-fold capacity, whole-workflow physical quota, process RSS or empirical result is established. The output remains a current-owner per-graph publication component; all historical attempts and evidence must remain preserved.
