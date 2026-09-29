# Registered mapped-sampler policy

The optional mapped sampler can now be selected through an admitted input named
by `sampling_input` in both the representation producer plan and job payload.
The exact policy schema is `schema_version: 1`, `mode: mapped`, and a positive
integer `max_weight_bytes`. Unknown keys, Boolean numeric fields, mismatched
input names and changed input bytes are refused. No arbitrary scratch path is
accepted through this policy. Existing registrations without the option retain
the eager path and scientific identities.

Job execution preflights all sampling policies before any population producer,
graph loader or representation fitting. Only proposed/MCM diagnostic arms can
request sampling. Completed-reuse jobs reject unused sampling options. The
registered producer checks its own policy admission again and records both the
input name and admitted SHA-256 in its attempt claim.

Scratch belongs to `sampling-weights` under the current exclusive representation
journal. Resolved path containment and filesystem identity are checked under the
lifecycle lock before creating representation directories, and checked again
before calling the component. Scratch must remain within the registered root
and on its filesystem; a future external scratch policy would need a separately
reviewed volume/guard contract. The mapped component still enforces exclusive
reservation, disk/budget limits, cleanup and retained failures.

Execution policy is excluded from scientific sample, dictionary and feature
identities. An explicitly registered successor may change the scratch byte
allowance while reusing exactly verified sample checkpoints. A saved sample
checkpoint bypasses the sampler and does not create a successor scratch folder.
Defaults and completed numerical reuse remain unchanged.

## Interruption boundary

The mapped sampler seals its scratch receipt before `samples_complete` is
published to the representation journal. If publication fails, a completed
scratch receipt can exist alongside a failed journal with no sample checkpoint.
The scratch receipt binds an identity, not reconstructible sample objects.
This state is retained and is not automatically reopened or treated as recovered
samples. Only the verified persisted sample checkpoint supplies the supported
no-resampling continuation guarantee. Any further work needs a new admitted
attempt with its actual prior exposure retained.

## Tests and review

Red01 retained nine missing-API/admission failures; red02 retained four ordering
failures where population work could precede policy preflight. Green01 passed
22 checks across policy, registered-feature and job-payload fixtures. Red03 then
demonstrated that a late path-containment check could write a journal outside the
registered root before rejecting it; the check was moved before all such writes.

Expanded fixtures compare complete mapped/eager feature bindings, verify policy
schema and byte drift, exercise root escape, preserve the scratch/publication
failure boundary, and continue a source-bound failed parent without resampling.
The successor's full binding and dictionary match an uninterrupted oracle.
The successful job-forwarding fixture performs real registered graph loading,
sampling, dictionary construction and MCM; its final model-fitting call is
stubbed, so this fixture does not establish new end-to-end training parity.
Independent review and final test receipts record the release status.

This increment enables an admitted option in software. No real experiment gate
has enabled it; no empirical claim, new sample, provider request or financial fit
has been executed. Full-fold graph residency, large-neighborhood matching and
full-model capacity remain separate requirements. Budget remains 25 of 52,
with all 1,420 financial fits pending.

## Full offline verification

Focused green02 passed 37 tests in 90.60 seconds after the containment correction.
The named offline01 suite subsequently passed 3,334 tests plus 97 subtests, with
two CUDA skips (2,768 standard and 566 neural tests). The finite guard completed
in 1714.36 seconds with child exit 0, verified cleanup, 1,934,086,144 sampled peak
bytes and zero memory pressure-limit/OOM events. All 16 frozen source bindings
match; the owned cgroup and monitor process are absent. This is synthetic
engineering verification, not actual-data resource feasibility or financial
evaluation. Final independent terminal review is recorded in CODE_REVIEW.md.
