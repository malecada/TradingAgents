# Initial independent review — acceptance withheld

## MA1 — admitted resident output can change without invalidating its lease

`route.py:180–189` returns the strict reader's writable ndarray directly. `Admitted` also permits replacement of its `mcm` attribute (`route.py:31–33`). The returned lease checks saved evidence, graph and dictionary prerequisites, but does not bind the resident matrix. An ordinary assignment such as `result.mcm[0, 0] = 0.5`, or replacement of `result.mcm`, can therefore leave an unchanged proof record and a passing lease over different in-memory values. This breaks the admitted-output contract without requiring reflective access or a process-security attack.

Return an immutable bytes-backed matrix through a read-only/pinned attribute, or explicitly bind and recheck the resident buffer on every lease. Reserve any temporary second payload before allocation; simply clearing an owning ndarray's WRITEABLE flag is reversible. Regressions should exercise element writes, writeability re-enablement/base access, output replacement and refusal before loading when the necessary copy budget is unavailable.

## MA2 — graph-order refusal is broader than the per-graph publication route

`route.py:161–162` rejects every earlier `embedding_progress` or `graph_complete` event, including events for another required graph. The publisher allows sequential per-graph work. A journal ordered as G1 MCM, G1 embedding/completion, G2 MCM therefore cannot admit G2 even when its own history is valid. This is a conservative availability mismatch, not acceptance of invalid output.

Make graph-stage ordering specific to the selected graph, retaining any necessary global representation-completion refusal, and cover another graph's prior completion in the compact history tests. Alternatively narrow the stated scope explicitly to histories without any earlier embedding/completion event.

## Other inspected boundaries

Local weak-key issuance closes the earlier publicly constructible dictionary-receipt gap within the stated in-process trust model. Issuance pins the actual owner/journal, receipt, dictionary, record, callback, class method and preparation input hashes. Repeated checks recompute dictionary identity, configuration and matching identity around the original lease. Proof/start/event joins, exact selected policies, complete counts/order/scope, component preflight and final compact checks are explicit. No additional material blocker was identified in those boundaries during this initial review.

The active synthetic suite is not treated as closed or passing here. No tests, matching, historical jobs or empirical-array reads were performed by this review. Full-fold resources, physical quotas, cold-start/historical reuse and empirical admission remain outside scope. Saved-byte score validation is not independent recomputation of every score's numerical provenance.
