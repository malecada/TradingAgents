# Graph activation checkpointing engineering increment

September 29, 2026. This follows registered graph-production integration and
addresses G4 in the September25 GRAPH_MEMORY_REVIEW. No real financial fit,
retained-data decode, GPU execution or source acquisition is authorized by this
engineering verification. Closed empirical identities remain closed.

The optional model configuration field `graph_activation_checkpointing` is a
strict boolean, default false. The proposed execution mode checkpoints each
unique graph encoder inside a training forward with gradients enabled, using
non-reentrant recomputation and preserved RNG state. Fixed MCM inputs need no
input gradients; all MLP/GAT parameters must still receive gradients. Learned
embeddings remain shared only inside that forward, never across optimizer steps.

The pinned Torch implementation documents that non-reentrant checkpointing
supports fixed inputs and keyword arguments. Inference and masked steps retain
the existing path. No frozen configuration file is changed. Empirical enabling
requires a declared configuration and source amendment before resource pilots.

Synthetic verification will compare saved tensor bytes, predictions, loss,
parameter gradients, Adam updates, dropout RNG state, and exact saved-checkpoint
replay over repeated references to two distinct graphs. Saved tensor accounting
is an engineering diagnostic, not measured process peak or full-graph capacity.
Checkpointing does not remove the largest single-graph intermediate allocation,
fixed feature residency or the separate full-neighborhood matching blocker.

Status: test draft prepared outside test discovery while the preceding offline
suite completes; implementation not yet changed.

Initial red01 was refused by the reviewed test profile because the draft lived
outside its admitted directories (exit4, cleanup verified). It was copied into
the reviewed synthetic test directory after the preceding offline02 neural phase
had collected its fixed57modules; offline02 does not cover this new module.
Red02 demonstrated the four intended missing-feature failures and one successful
checkpoint-replay control. Two additional failures exposed an invalid non-prefix
mask in the new inference fixture, corrected to valid prefix padding before the
next red run. All attempts are retained; neither is represented as a pass.

Red03 retained four intended missing-feature failures and three passing controls.
Inspection found AlternativeGraphTemporal inherits forward while initializing
its own graph encoder. Red04 therefore added three failing comparator checks.
A shared configuration initializer now validates the boolean for both model
classes. Non-reentrant checkpointing applies only during gradient-enabled
training, one invocation per unique graph object inside the forward.

Green01 passed15 tests in10.75s. Saved tensor reference bytes changed from
1,444,104 to206,458 on the fixed two-graph fixture. Predictions, gradients, Adam
updates and dropout RNG match; saved-model/optimizer replay is exact. These
bytes sum hook-retained tensor references and do not measure RSS or unique
storage. The three inherited graph comparators also match their ordinary path.
The named onchain neural subset is running as neural01; independent review is
in progress. Frozen configuration files remain unchanged.

## Independent review correction

REVIEW.md found a device-RNG discovery defect: the pinned Torch checkpoint
implementation discovers accelerator devices only through positional inputs.
The initial call supplied graph tensors through keyword arguments. The reviewed
operator stop ended neural01 with verified cleanup before modifying production
code; it is not a passed suite. Initial source-bindings.json remains unchanged.

Review-red01 failed the positional-tensor device discovery regression. The
corrected `_encode_graph` accepts the existing graph signature explicitly and
passes all tensor arguments positionally to checkpoint. Unexpected graph keys
still fail argument binding. A conditional CUDA dropout comparison was added;
this host has no CUDA, so it is skipped and makes no GPU parity claim.

Review-green01 passed30 tests with one CUDA skip in5.29s, including the separate
bounded-hash increment's14 checks. Final saved reference bytes are1,444,104
ordinary and220,890 checkpointed; positional tensor inputs now enter the hook's
accounting. CPU predictions/gradients/updates/RNG and replay checks still pass.
Corrected-source-bindings.json binds the combined final source for neural02,
which exercises all59 admitted onchain test modules. Independent correction
review and that suite are in progress.

## Final verification

Combined neural02 completed all59 onchain modules:498passed/2CUDA skips in
326.39test seconds; guard328.903s, peak sampled
821239808bytes, child0, no memory-limit events,
cleanup verified. All five corrected source/test bindings match. The newly
prepared graph-validation-memory test module is excluded from this fixed
59-module command and has its own evidence.

Independent review found no unresolved critical issue in the final increment.
No frozen scientific configuration, empirical claim or financial result changed.
Full-size capacity, GPU parity and full paper coverage remain unestablished.
