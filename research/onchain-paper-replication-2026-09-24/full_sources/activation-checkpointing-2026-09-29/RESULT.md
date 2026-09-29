# Graph activation checkpointing

Implemented and independently reviewed. An optional strict boolean configuration
field, `graph_activation_checkpointing`, defaults to false. During training it
recomputes each unique graph encoder during backward while preserving the full
joint gradient path. All graph tensors are positional inputs to Torch checkpoint
for device/RNG discovery. Inference retains the ordinary path.

The fixed CPU fixture retained1,444,104 tensor-reference bytes ordinarily and
220,890 with checkpointing. Predictions, gradients, optimizer updates and RNG
agree; saved-model/optimizer replay is exact. These are synthetic reference-byte
counts, not process-memory measurements or proof that large graphs fit. Three
inherited graph comparators are covered. CUDA comparison is skipped on this host.

The initial independent device/RNG finding, its failing regression, corrected
source and review closure are retained. Initial neural01 was deliberately stopped
and cleaned up; it is not a successful verification. Enabling this option in an
empirical configuration requires prospective registration/review.

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
