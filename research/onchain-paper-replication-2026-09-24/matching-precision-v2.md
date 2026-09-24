# Pre-result precision amendment v2

The independent Task4 reviewer found a tie-free two-node/three-node fixture where
float32 annealing changed Eq1 score0.0503767954 to0.0462317504 and changed the
assignment. Independent70-digit Decimal recurrence confirmed the float64 reference.
The fixture is retained in test_iterative_roundoff_does_not_change_tie_free_assignment;
it failed before this amendment. No empirical data or fitted outcomes were used.

Retain config/matching.json and protocol-freeze.json unchanged as version1. The
active matching configuration is config/matching-stable.json: affinities,48-step
annealing and hardening use float64; reported similarity/soft matrices convert to
float32 after solving. C05/C06 tolerances are unchanged. This is a declared numerical
implementation difference with higher memory/compute cost to measure in Task8.
Native float32 iteration is not claimed parity-verified. GPU verification remains
pending because no CUDA device is available. The mathematical objective is unchanged.
