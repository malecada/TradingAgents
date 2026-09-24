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
