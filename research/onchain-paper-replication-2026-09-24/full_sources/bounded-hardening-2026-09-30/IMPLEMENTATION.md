# Bounded graph matching prototypes

These isolated synthetic prototypes do not change the registered matching kernel,
scientific capacity, cache identity or empirical policy. Full iterative dense state
and checkpoint integration remain required.

`bounded_hardening.py` selects exact legacy float64 greedy row-major choices and
returns sparse pairs in selection order. Numeric reservation is
48*min(n,m)+64*min(chunk_entries,n*m), excluding input residency, Python/runtime
and mapped page cache. Eight focused tests pass, including integer rounding ties,
signed zero, strides, exact reservation boundaries and a mapped 2 by 2,000,001
matrix. Independent component review accepted. Scan complexity is unchanged;
no measured RSS, speed or intra-solver checkpoint claim is made.

`sparse_objective.py` reproduces literal scalar Eq1 nonzero terms in reference
order without allocating a dense hard assignment. The reference evaluates all
agreements before multiplying assignment zeros, which can raise on finite but
unrepresentable squared differences. Review finding S1 has a retained red
counterexample. The prototype now explicitly checks a conservative componentwise
extrema envelope for representable float64 squares and their sum. This is a
narrower accepted domain than general finite attributes and can conservatively
reject safe correlated extrema. It is not an unconditional behavior-equivalent
replacement or an adopted scientific restriction. Sparse-green02 passed six
tests in 0.027 seconds, including node/edge and sum overflow envelopes. Independent review accepted the explicitly restricted isolated component. The scalar path does not claim Torch reduction-order parity.

All red attempts remain. Neither prototype is an empirical measurement or a
resource-capacity override. Production integration must preserve registered
execution policy, admitted domains, exact source identity and failure accounting.
