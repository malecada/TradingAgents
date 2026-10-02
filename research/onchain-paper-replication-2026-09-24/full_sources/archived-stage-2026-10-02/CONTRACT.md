# Explicit archived scientific-stage join

Introduce an additive stage verifier combining the accepted cold archive reader
with real retained checkpoint trees and score streams. Historical local stage
functions remain unchanged. Expected owner/scope, exact scientific/archive
policies, pair denominator, log/stream/archive terminal hashes and a live lease
are caller inputs. Policies are frozen as canonical plain data before callbacks.
This content join is not current-owner or empirical admission.

An optional event visitor receives immutable unpacked frames only after their
event chain and state transition have been checked. A visitor failure leaves
the read attempt failed. Existing callers omit it and preserve their result
schema. The stage visitor enforces per-pair/global checkpoint counts and checks
each actual verified progress frame against its checkpoint intent/state tree,
including the actual pair purpose and identity. It then writes 40-byte
event/reference records, indexed by cumulative checkpoint ordinal, into its
fresh attempt. No population-sized in-memory reference list is needed.

After full cold event replay, the reference stream's hash must equal the replay
checkpoint digest. Every local checkpoint directory is bound to its exact event,
ordinal and manifest hash, then validated by the maintained intent/state-tree
validator. Count, inventory, numerical policy and logical checkpoint bounds are
retained. For MCM, the maintained stream validator checks every score tail/batch
and compares the complete ordered ordinal/purpose/value digest with the event
stream. An internally consistent but different score stream must fail the join.

Completion is exclusive to the fresh attempt. After publication and its live
callback, source archive manifests, new read receipts, checkpoint references,
actual checkpoint state files and score streams must all pass again. Failure
evidence stays in the new attempt; source evidence is read-only. Repeated claims
against successful or failed attempts are refused without rewriting them.

The reference and metadata allowance is explicit and the local 10GiB floor
remains. Logical counts are not a physical quota, real RSS measurement, remote
transfer budget or concurrency bound. Original checkpoint and score payloads
remain local, and local source manifest metadata is still required. Remote bytes
are observed during cold replay, not continuously afterward. Generic current-
owner/publication/terminal integration and whole-workflow resource admission
remain separate work.
