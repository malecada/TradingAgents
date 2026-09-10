# Engine/controller implementation verification

Implemented after registration `67eb720`, using synthetic inputs only. No policy backtest on saved research observations, alternative-policy outcome calculation, original artifact modification, gate edit, ledger append or commit was performed by this implementation task. The registered empirical control-parity and alternative runs remain pending reviewed source commit and the root agent's execution.

## Scope and interface

The only existing executable changed is `scripts/baseline_strategy_v2.py`: a26-line diff (25 insertions, one replacement) adds the optional `target_policy=None` keyword and its decision/notification hooks. It preserves the default branch, original arithmetic, price-stop anchoring, funding/fee assumptions, peak ordering and original default trace fields. Policy metadata cannot overwrite accounting trace fields. Nonfinite, boolean, textual or complex policy outputs are rejected rather than reaching the old NaN/retain-holdings convention; a policy cannot release a permanent halt.

New `tradingagents/strategies/factor_risk_policy.py` exposes:

```python
causal_sigma(close) -> numpy.ndarray
FactorRiskPolicy(sizing="saved" | "daily",
                 reentry="immediate" | "new_target_episode",
                 sigma=full_target_clock_array)
```

`causal_sigma` invokes the existing `compute_realized_vol` with lookback20 on `[Close[0], Close[:-1]]`. It does not invoke the diagnostic analyzer, signal builder or position builder. The controller copies its sigma array and advances once over engine indices1 through N−1. A fresh instance is required for every sleeve, policy arm and cost scenario.

The engine calls `decide(i, raw_target, halted, date=dates[i])`, receiving a finite target and metadata. After an actually executed price-stop exit, it calls `on_price_stop(i, exposure)` whether or not tracing is requested. That notification first affects later decisions. Same-sign raw targets remain blocked until an observed raw zero or opposite direction; current executed zero, resized magnitude and model-signal changes do not clear the latch. A permanent halt takes precedence. Invalid/nonpositive sigma is unavailable only for an admitted nonzero daily target, while flat, waiting and permanently halted states request zero without inventing a valid sigma.

Policy trace additions, absent under default None:

| Field | Meaning |
| --- | --- |
| `raw_target` | Original saved target before policy or permanent-halt suppression |
| `requested_target` | Executable target selected for this bar |
| `sizing_sigma` | Current estimator observation; null when nonfinite |
| `blocked_before` | Direction latch entering the decision |
| `blocked_after_decision` | Latch after a raw zero/opposite release, before this bar's execution |
| `blocked_after` | End-of-bar latch, including any executed price-stop notification |
| `decision_blocked` | Nonzero raw request suppressed specifically by the re-entry latch |
| `block_release` | Null, `raw_flat`, or `raw_opposite` |
| `decision_reason` | `permanent_halt`, `raw_flat`, `waiting_same_direction`, `saved_target`, or `daily_resize` |
| `stopped_direction` | Actual direction reported by this bar's executed price-stop notification; zero otherwise |
| `policy_sizing`, `policy_reentry` | Fixed policy labels |

The existing `halted_before` field remains authoritative and unchanged. Policy stop updates preserve the difference between the decision state and post-execution state. The protocol and field meanings were supplied directly to the evaluator owner.

## TDD and final verification

- `engine-policy-red.txt`:32 expected failures before the new controller/hook existed.
- `engine-policy-green.txt`:32 passed after implementation.
- `engine-policy-admission-red.txt`:two expected failures for malformed string/complex callback outputs, with40 tests passing; these led to the narrow finite-real-output guard.
- `engine-policy-final-tests.txt`:84 passed in2.77s after that fix.

Final command:

```bash
PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -B -m pytest -p no:cacheprovider -q tests/test_factor_risk_policy.py tests/test_factor_v2_trace.py tests/test_factor_correction.py tests/test_factor_correction_failures.py tests/strategies/test_v2_sizing_golden.py tests/rebuild/test_factor_signals.py
```

The84 tests comprise42 new tests and42 existing factor/sizing regressions. New tests include exact archived-engine/default-None/A00 equity, metric and original-field trace parity across both directions and all four cost scenarios; long and short price anchors under same-sign resizing; exact volatility lag and future-perturbation invariance; clipping and invalid sigma; raw-direction block releases and repeated stops; independent controllers; traced/untraced parity; actual drifted-notional charges and both funding signs; ordinary and post-exit-fee permanent halts; exact blocked cash; metadata collisions; and a planted rebound/continuation example that demonstrates a trade-off rather than presuming improvement. `git diff --check` passed.

Full144-trace/72-return empirical A00 parity is intentionally not claimed here: it is the registered execution gate that must precede interpreting alternatives.

## Final identities

| Artifact | SHA-256 |
| --- | --- |
| `scripts/baseline_strategy_v2.py` | `2113a2e9b94b19aeee7e63190188290b0fb7991326a53caafbb42e1a8f2f6f05` |
| `tradingagents/strategies/factor_risk_policy.py` | `72ca71e41c7a2f3a65f2695d775546470ebc11b3a487d1cb83d0dfbb9b98b72a` |
| `tests/test_factor_risk_policy.py` | `963fd940239d2f2b32c57c9fd213cf97d33a78d1c2c1733151afb5e5c6974e45` |
| `engine-policy-final-tests.txt` | `9b1f08c3b37b4b1dfd801988dd48768bd4c1c0b9b33db590204d6296aca0a07c` |

No unresolved implementation concern was identified in the focused checks. Independent review in `engine-code-review.md` found no material blocker and verified these same executable/test hashes. Existing proxy-price, signed assumed daily-funding, threshold-fill, separate-sleeve and spent-history qualifications remain unchanged.
