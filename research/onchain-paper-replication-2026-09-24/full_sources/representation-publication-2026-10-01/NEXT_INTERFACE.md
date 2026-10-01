# Next integration boundary: sealing, then native batch reuse

Read-only interface investigation performed during check03; no empirical
execution or acceptance of the future adapter is implied.

The next minimal implementation is an exclusive current-owner seal/output
handoff. The maintained prepare_registered_features creates a fresh journal and
executes numerical prepare_features, so it cannot be called for this completed
representation. Its historical semantics remain unchanged.

Before either seal, admit the exact completed publication proof, event, schema3
binding, selected binding_output and journal_output from both registered routes,
all predecessor content/extent references, run/source/runtime/guard identity,
and complete pair-event state. Reject pending pair reservations, orphan or
conflicting terminal markers, swapped outputs and drift before mutation. Use
OwnedJournal.seal('complete'), FeatureJournal.seal('complete') and registered
ResearchRun.write_json only after that evidence is captured. A new terminal
contract must replace live-owner leases after the first seal; existing
Binding.check/lease, ticket_lease and savedGraph.admit terminal refusals must not
be relaxed. The run and its guard remain active while the numerical journals
become terminal.

Two output writes are not transactional. A failure after either numerical seal
or between binding/journal outputs must preserve sealed evidence and explicit
partial-publication failure. Recovery requires separately admitted saved outputs;
no producer is restarted. New tests must cover output-route swaps, before-seal
drift, pending/conflicting pair state, mutation during sealing, and failure
between output writes while preserving terminal identities.

The following component is a terminal native-feature index and batch loader.
read_feature_journal(lazy_features=True) defers graph_complete arrays but still
materializes sample/dictionary/MCM stages and reconstructs the dictionary.
Native kind=array leaves become NumPy arrays through the generic component
loader; graph models require the reviewed CPU tensor conversion. Generic
ArrayReference uses np.load/mmap and is not the accepted strict reader.

The terminal index must revalidate exact terminal/publication/binding/provenance
and required graph references without replaying numerical production. Preserve
original-MCM/source-value joins at initial terminal admission; a declared graph
proof hash alone is insufficient. Load only deduplicated requested graph keys
through the strict reader and accepted tensor boundary, with a pre-allocation
aggregate limit for retained output tensors plus the current native load/copy
and scratch. Total RSS, model activations, parent graphs and Python/page-cache
costs need the separately registered outer guard.

Both evaluation.batch_factory and evaluation.evaluate_cell dispatch on
isinstance(features, FixedFeatureMap). A reviewed compatible subclass or an
explicit native-map branch is necessary in both locations; an arbitrary Mapping
would bypass batching and may eagerly traverse every graph. verified_hashes must
verify actual admitted content and feature wire hashes, including empty edges.
Tests must cover repeated keys sharing one allocation, absent keys, aggregate
budget refusal before arrays, source/value/hash mismatch, zero producer replay,
and lease drift/cleanup. No neural architecture or frozen scientific setting is
changed by these integration requirements.
