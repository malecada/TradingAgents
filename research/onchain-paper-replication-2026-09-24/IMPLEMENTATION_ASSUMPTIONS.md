# Implementation details clarified before empirical execution

- Node2Vec uses the same fixed, seed-generated walk corpus at every optimization
  epoch, node-index order within each of ten walks per node. Negative draws advance
  the recorded PCG64 state. These ordering choices were unspecified by the paper.
- GraphWave/Node2Vec/WatchYourStep require an explicit allocation ceiling derived
  from the resource contract. A generic4million-entry development default was
  removed before empirical use; it is not a scientific graph-size cutoff.
- Weekly graphs preserve original edge count/value aggregates alongside log
  attributes. Whale thresholding never reconstructs native volumes by exponentiating
  logs, which can change strict boundary membership. BTC requires exact rational
  incident volumes for its threshold. Retained cohort/non-whale vertices that become
  isolated remain in induced graphs and receive zero recomputed derived attributes.
  Origin source-event counters remain labeled as origin counters; variant edge/node
  removals are reported separately, not relabeled transaction exclusions.
- Exact BTC decimal conversion uses rational arithmetic, independent of ambient
  decimal precision. The public AWS schema documents input/output amounts as BTC
  doubles; these are not admitted as exact satoshis without a separate precision
  amendment and verification. Prevout/multiscript/coinbase distinctions remain.
- Graph encoding can be reused within one forward call for the same graph object;
  its autograd graph remains joint and fresh each call. No learned representation is
  cached across parameter updates. Sparse neighborhood indexing preserves the same
  directed induced graphs and original edge order; graph hashing streams canonical
  JSON to avoid large list copies without changing the identity formula.

- October 1 compact matcher execution is a prospective operational variant:
  `calls_per_checkpoint` groups a bounded number of unchanged checkpoint-engine
  `advance` calls before a retained progress snapshot. This changes the earlier
  Serial runner's checkpoint cadence, not the matching equations, temperature
  schedule, convergence criterion or hardening order. It must be registered
  explicitly before resource or financial execution. An operation bound does
  not bound the stable sort inside the annealing-to-hardening transition.
- The compact completion path records durable begin/completion/progress events
  instead of creating a PairSession owner and completion directory for every
  completed comparison. Completion retains exact score, convergence and iteration
  count, purpose and numerical identity. Progress/failure snapshots and old
  historical artifacts remain preserved. No successor/reuse permission follows
  from matching identities or an intact checksum. The new path has passed only
  tiny synthetic integration and is not yet selected by the registered native
  producer; it is not empirical resource-capacity or paper-agreement evidence.
- The prospective compact policy counts directional dictionary work and retained
  logical evidence before allocation. Its metadata-only capacity calculator
  refuses hierarchies exceeding 1024 levels and overflow at each reduction; it
  never truncates numerical samples or returns partial counts. This operational
  validator limit is explicit and requires review if a deeper hierarchy is
  requested. It does not establish available physical storage or admit a run.
