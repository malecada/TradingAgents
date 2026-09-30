# Conditional largest-hub matching work

The closed hub measurement reports 701,309 nodes and 712,125 induced directed
edges at center 447113. This memo combines that result with hypothetical opposite
graphs; it does not claim any listed graph is an actual dictionary motif.

For a six-node/five-edge opposite graph, the pair has 4,207,854 entries, already
above the original four-million-entry capacity. Three retained float64 matrices
alone require 100,988,496 bytes, excluding graph inputs, normalization temporaries,
validation, checkpoints, hardening and scoring. The literal edge accumulation
would contain 3,560,625 directed edge pairs per iteration, or 170,910,000 over
48 iterations. Feasibility depends on both retained workspace and computation;
a larger memory allowance alone does not establish throughput or checkpoint time.

The existing capacity remains enforced. Any change requires explicit scientific
versus execution-parameter lineage review and prospective identity binding.
Current checkpoint prototypes preserve scalar arithmetic and greedy choices in
synthetic tests but do not establish integrated full-size matching, bounded dense
normalization, durable output ownership, accelerated parity or numerical agreement
with the paper. Scenarios in arithmetic.json are planning arithmetic only.
