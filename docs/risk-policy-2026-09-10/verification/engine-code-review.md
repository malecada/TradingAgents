# Independent engine/controller review

Verdict: no material blocker found in the reviewed optional hook and controller under registration `67eb720305ccddff266df396e61d03dc2fa1985e`. This is a source and synthetic-test review before empirical execution; no saved strategy observations were evaluated.

Reviewed identities:

| File | SHA-256 |
|---|---|
| `scripts/baseline_strategy_v2.py` | `2113a2e9b94b19aeee7e63190188290b0fb7991326a53caafbb42e1a8f2f6f05` |
| `tradingagents/strategies/factor_risk_policy.py` | `72ca71e41c7a2f3a65f2695d775546470ebc11b3a487d1cb83d0dfbb9b98b72a` |
| `tests/test_factor_risk_policy.py` | `963fd940239d2f2b32c57c9fd213cf97d33a78d1c2c1733151afb5e5c6974e45` |

The only existing executable change is the optional `target_policy` argument, its decision call before accounting, its notification after an executed price-stop close, and extra trace fields. The `None` branch retains the original target expression, accounting stages and original trace schema. Synthetic tests compare both default and explicit A00 behavior with the exact archived engine across long/short directions and all four cost cases; these worker tests were inspected rather than redundantly executed.

The controller's sigma uses the original twenty-return sample standard deviation and sqrt252 annualization on `[Close[0], Close[:-1]]`. The original factor correction's `build_targets` also computed volatility after slicing to the same development clock, so this reproduces its estimator warmup rather than discarding hidden preceding volatility history. Daily sizing uses the registered `min(3, 0.15/sigma)`, preserves raw direction, and has no new daily percentile exit. Only an admitted nonzero daily request requires a finite positive sigma; unavailable sigma cannot silently become zero exposure or retained holdings.

The state transition uses the saved raw target, not a controller-generated zero or a latent signal. After an executed price stop, same-sign requests remain blocked despite magnitude changes; a later raw zero releases while flat, and a later opposite request may enter and set its own block if stopped. The permanent halt takes precedence over every release and resizing decision. Stop notification occurs after the charged exit, including when trace collection is disabled. Same-sign resizing does not alter the original price anchor; a fresh entry or sign flip does. Funding, drifted-holding maintenance trades, both exit charges and pre-/post-exit drawdown checks stay in the existing engine.

The inspected test cases cover future-close perturbation, exact one-period sigma alignment, clipped long/short sizes, invalid required sigma, raw-target episode transitions, controller reuse/order failures, fresh controller isolation, long/short anchor preservation, funding-sign and charged-turnover identities, post-exit-fee halts, and a planted trade-off that does not presume an improvement. The hook rejects nonfinite targets, attempts to release permanent halts and metadata collisions with accounting fields.

Limits: the original threshold/gap-fill convention and constant daily funding approximation remain as preregistered; this review does not make them executable-price evidence. End-to-end committed runner admission, full saved A00 control parity before alternatives, all-denominator preservation and post-run arithmetic remain separate requirements. The exact archived engine and all old empirical outputs remain immutable.
