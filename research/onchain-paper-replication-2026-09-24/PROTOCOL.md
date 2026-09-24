# Independent paper reconstruction protocol v1

This protocol freezes implementation choices before empirical fitting. It does
not itself admit a run. Exact stage source/input hashes, resource readback and an
independent release review must precede each lifecycle claim. The user authorized
all13 tasks on September24,2026; earlier planning-only wording describes history.

The eight `config/*.json` files are the executable numerical specification.
`fidelity.json` distinguishes assumptions, deviations and blocked source identities.
All sizes and hyperparameters absent from the target paper are independent choices.
The architecture remains dictionary→motif similarities→MLP→GAT→graph pooling→
price/graph sequence→LSTM→additive attention→separate task head. No MCM/GAT block
may be detached to make a resource limit pass.

## Graph and source contract

One directed sparse attributed graph per complete Monday UTC week. Retained ETH
source schema contains identity/block metadata, sender, recipient, float64 wei and
receipt_status. Successful positive native top-level transfers are included;
failed/zero/null-recipient events have separate exclusion counters. Duplicate
identities fail, including duplicates that would otherwise be filtered. Contract
creation with unknown recipient, token logs and internal transfers are excluded.
Every raw identity contributes exactly once to admitted or excluded accounting.
No exact-wei claim follows from float64 conversion.

Aggregate ordered pairs, retaining count and approximate native amount. For
A→B3ETH and A→B2ETH, count2/value5; A→A1ETH adds one self-edge and both incoming
and outgoing volume1 for A. Node features are log1p incoming/outgoing counts and
native volumes; edges log1p count and native volume. No cross-week fitted feature
statistics. GAT self-neighbor added exactly once regardless of observed self-edge.

BTC resolves every previous output before projection. Inputs A6,B4 and outputs
C7,A2 (all amounts in satoshis for this example) yield rational edges A→C4.2,
A→A1.2,B→C2.8,B→A0.8; sum9, fee1. Rational values are a modeling allocation,
not observed bilateral payments. Merge repeated input addresses; retain change;
coinbase excluded/count recorded; unresolved prevouts are unavailable; any script
without a unique admitted address excludes the whole transaction. Never round
projection contributions to fabricated integer satoshis.

## Mathematical path

Interpret E=edge agreement, V=node agreement. On standardized-by-definition
log features, E and V are exp(-mean squared difference); absent edges have E=0.
Eq1 is [sum M_ui*M_vj*E_uvij/(2sqrt(l1*l2)) + alpha*sum M_ui*V_ui/sqrt(n1*n2)]
/(1+alpha), alpha1. If either l is0, the edge contribution is defined0; no empty
node graph is admitted. Directed identical-edge scores need not1.

Algorithm1 transcription by displayed line:3 beta=beta0;4 M=V;5 while beta<=beta_f;
7 Q_ui=.5 sum_vj E_uvij*M_vj + alpha V_ui;8 exponentiate betaQ;
10 normalize rows;11 normalize columns;12 beta*=1+beta_rate;14 greedy hardening.
Compute normalization in log space for stability. No additional fixed-point loop,
no slack padding, no derivative correction. beta0=1,final30,rate.075,cap50.
Hardening repeatedly chooses global maximum, row-major ties, removing its row and
column; exactly min(n1,n2) matches. Rectangular soft matrices need not be doubly
stochastic. Tie-free relabeling and tied-score feasibility have separate tests.

Sample512 weak1-hop induced neighborhoods from training graphs, preserving centers.
Halve remaining centers' probability weights when inside the just-selected
neighborhood; normalize weights at each draw. Average-linkage cluster to32 groups,
choose medoids, and retain all sample/probability/RNG provenance. Symmetric
clustering distance is1−mean(S(A,B),S(B,A)). No assumed symmetry of approximate
rectangular matching. Fewer than32 eligible samples is unavailable. No hub cap
silently changes a graph: node/matrix limits produce explicit capacity failures.

MCM output N×32 feeds learned MLP32→64→32. Two GAT layers use4×16 concatenated
heads then1×32, incoming neighbors/self, LeakyReLU.2, ELU then identity. Mean
pooling after GAT gives32 coordinates. Each daily step concatenates one scaled
price, yielding33 inputs. LSTM64 with28-step lookback; additive attention32 uses
last valid state query and tanh keys, zero attention on padding. Output is one
regression scalar or two classification logits. All neural blocks train jointly.

## Chronology and fitting

For UTC price bar[d,d+1), Close[d] is assumed available at d+1 midnight. Forecast
Close[d+1] then; upward class is Close[d+1]>Close[d], ties0. A weekly graph ending
Monday January8 is available Tuesday January9 under the declared one-day lag,
never during its own week. Each sequence step uses its then-available complete
week. A missing expected week invalidates the example, not an indefinite carry.
Historical source vintage remains unverified; these are retrospective assumptions.

Tests are decision dates in2018,…,2024; each fold trains on preceding two calendar
years with labels ending strictly before test_start. Test label_end must not exceed
test_end. Initial training warmup excludes insufficient28-day/graph context;
all exclusions and exact common mask freeze before outcomes. Initial ETH uses2022–
2023 training/2024 testing. No pre2016 source is invented. Both requested timing
lanes currently have identical explicit rules, so a separate causal-audit fit is
not created; historical availability is not thereby proved.

Five seeds11,23,37,51,71, no search/selection. Adam.001,100 fixed epochs,batch16,
no validation/early stopping, norm clip1. Price normalization uses training only;
regression metrics inverse-scale to USD. Classification is directly trained cross
entropy. Any unavailable arm remains in the denominator, never removes test dates.

HLSTM uses shared lower128 LSTM on four seven-day chunks and upper128 LSTM on
chunk vectors (declared adaptation of Hou, not a stacked LSTM). Other price and
graph arms are fully specified in baselines.json. Learned coordinate embeddings
require declared historical-only alignment; reference parity precedes accelerators.
SVC sigmoid margin is an uncalibrated score; the classifier decision is margin>0.

Whale example: directed A→B9,B→C1 gives incident volumes A9,B10,C1; threshold9;
only B is removed (strict greater), removing both edges. Self transfers contribute
twice. Threshold uses only its weekly graph; rebuild attributes after removal.
Fund filter software uses an induced admitted-address graph; actual cohort absent.

Primary direction metrics use up-positive binary counts and equal-weight annual
averages, with pooled/macro/weighted alternatives labeled. Report each seed and
fold;2,000 paired14-day moving-block resamples within years, seed20260924. Missing
consecutive dates make this interval unavailable until a pre-result gap-aware rule.
No result triggers tuning. Numerical closeness≤2 percentage points is descriptive
only and unavailable when data/labels/folds are incomparable. No PnL is computed.

## Resources, budget and preservation

The6GiB/twoCPU/zero-swap limits,3GiB host reserve and20GiB volume floor are hard
startup requirements, verified through cgroup readback. No GPU is currently usable;
GPU parity remains a separate requirement. Checkpoint each graph and every≤10min
safe training interval, retaining model/optimizer/cursor/all RNG/provenance. Immutable
cell identities prohibit duplicate live workers or terminal relaunch. Full-size pilot
uses frozen weeks plus largest training week by label-free metadata, synthetic labels.

`history.json` retains17 consumed claims. `budget-amendment.proposed.json` proposes
34 additional claims (18 source,1 pilot,1 initial,14 full-fold batches), cumulative51;
1,420 unique one-lane fits maximum. Source/engineering counts are not model fits.
This is a reviewed-policy proposal to bind at each release, not a new registry or
permission to launch incomplete cells. Failures consume allowance; no retries or
second lane allowance exists. Future refinements must be explicit and before the
affected outcomes. Preserve all original raw stores and closed jobs without rerun.
