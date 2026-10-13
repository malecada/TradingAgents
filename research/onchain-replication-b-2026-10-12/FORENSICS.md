# CP4 forensics — why the full model sits at chance

Run 2026-10-13 after `cli report` (RESULT.md), on retained predictions,
checkpoints and features only. No cell was refitted and no setting changed; the
2024 evaluation remains one-shot.

## Result being explained

Full-model 2024 direction accuracy 0.4899 (5 seeds, range 0.4877–0.4904,
95 % CI 0.4471–0.5354) against the paper's 0.804: −31.4 pp, not numerically
close. Every arm lies between 0.476 and 0.521. Full minus LSTM −0.6 pp,
CI [−2.8, +1.8]. The label-permutation chance control passes (0.4762, CI
contains the 0.5096 majority rate). No cell was excluded.

## Findings

1. **The full model collapsed to the training-majority class.** Share of 2024
   days predicted "up", seeds 11/23/37/51/71: 0.025, 0, 0, 0, 0. Training
   up-rate 2022–2023 is 0.4877, so "down" is the training majority; 2024 up-rate
   is 0.5096, so always-down scores 0.4904. Final training cross-entropy
   0.6907–0.6930 against the training-label entropy 0.6928: the joint model
   gained at most ~0.002 nats over a constant predictor on the training days
   themselves. The price-only LSTM partly collapsed too (up-shares 0.04–0.41);
   GRU, HLSTM and SVM did not.

2. **The pooled graph vector is almost constant across weeks.** MCM features
   are not degenerate (seed 11, 104 training weeks × 5,000 nodes × 32 motifs:
   mean 0.047, standard deviation 0.075; per-motif spread across nodes
   0.035–0.17). Averaging over 5,000 nodes removes that spread: the per-week
   mean of each motif feature varies by 0.003–0.017 across weeks, and the
   trained seed-11 encoder's 32-dimensional graph vector has mean absolute value
   0.016 and a standard deviation across weeks of 0.007 (largest dimension
   0.026). The graph input therefore carries little week-to-week information
   into the LSTM. This follows from the declared mean-pooling assumption (F11)
   applied to 5,000-node graphs, not from a code defect: encoder gradients were
   verified through `encode_weeks`, and the batched solver matches the reference.

3. **Price level is out of the training range in 2024.** The scaler (training
   windows only) has mean 1,870.6 USD and standard deviation 551.1; 2024 closes
   map to 0.61–4.0 standard deviations. Level inputs outside the training range
   explain the regression ordering: GRU MAE 77, HLSTM 121, LSTM 126, full 173,
   SVM 350 (RBF kernel extrapolating on levels).

## Reading

- The protocol as frozen yields no evidence that weekly motif-graph features
  predict next-day ETH direction in 2024; neither do the price-only arms. Next-day
  direction at 2024 base rates near 51 % is a hard target, and the result is
  consistent with no exploitable signal at this horizon.
- The gap to the paper's 80.4 % cannot be attributed by this run. Candidate
  sources, each already a declared assumption or deviation: graph scale and
  definition (F01b, density gap), pooling (F11), price provider (F03), fold and
  aggregation convention (F14, F20), and the unreported original timing of
  graph availability (U05).
- Not done here, and not permitted on the spent 2024 holdout: tuning, class
  re-weighting, alternative pooling or input differencing. Any such variant needs
  its own registration and an unused evaluation window.
