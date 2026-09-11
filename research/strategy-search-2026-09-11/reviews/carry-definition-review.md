# Independent review — carry definition diagnostic

Disposition: **pass for the narrow saved-index definition diagnostic**. No
material error was found in the new diagnostic. No financial experiment was
rerun, no raw data were collected, and no gate or run output was changed.

The [standalone checker](check_definition.py) reads the four registered saved
inputs directly without importing the runner. Reconstruction uses 60-digit
Decimal arithmetic, direct multiplication for compounded indices, the central
second moment for sample variance, and the logarithm of the final product for
the convention diagnostic. The [machine-readable review](carry-definition-review.json)
retains reconstructed values, hashes, scope and limitations.

## Verified evidence

- All four input hashes match their registration and committed bytes at source
  `d3ba86924bd8711704fc80fd771a0e717cc9bb51`. Registered source, charter and
  lifecycle runtime hashes also match that commit.
- The immutable claim, completion receipt and diagnostic output hashes agree.
  The official independent receipt verifier separately passed. These are
  identity and structural checks, not proof of investment validity.
- Exactly six distinct registered cells are complete, with zero unavailable:
  BTC, ETH and their fixed 50/50 sleeve in each of two windows. Both date grids
  are complete and end-exclusive: 1,239 development days through March 30, 2025,
  and 456 spent-holdout days through June 30, 2026. March 31, 2025 is not inserted
  into either window. The blend is dependent on its components, not a third
  independent sample.
- 1,795 numeric comparisons passed at absolute tolerance 1e-12 or relative
  tolerance 1e-10. Maximum absolute discrepancy was 8.88e-16. All additive sums,
  means, sample standard deviations, historical sqrt(252) Sharpes, compounded
  indices, convention diagnostics and sign classifications reconcile.
- Adding the saved daily charge, 0.000058228478649816985 per target notional,
  increases each sum by the number of days times that charge. Restored sleeve
  Sharpes equal the previously saved `plus_rebalance` waterfall values in both
  windows. The 252-day convention is preserved for reconciliation; it is not a
  newly justified annual forecast or cash benchmark.

| Sleeve window | Additive stressed index | Additive index after add-back | Historical Sharpe before → after | Compounded index before → after |
|---|---:|---:|---:|---:|
| Development | 0.127758002 | 0.199903087 | 3.750366 → 5.868202 | 1.136136519 → 1.221120707 |
| Spent holdout | -0.011496706 | 0.015055481 | -1.476787 → 1.933923 | 0.988552461 → 1.015152166 |

These units are legacy per-target-notional indices. They are not cash returns on
1,000 or 10,000 capital. The positive add-back result was already visible in the
historical waterfall; reconstruction confirms an interpretation correction,
not an independent discovery or a reversal of the original NO-GO.

## Actionable inherited limitations

1. [carry_sleeve.py:190](../../../tradingagents/strategies/carry_sleeve.py#L190)
   computes separate percentage returns and then zero-fills missing differences.
   [Funding aggregation:42](../../../tradingagents/strategies/carry_sleeve.py#L42)
   sums available events without proving the expected settlement denominator.
   The new finite daily CSV check cannot detect previously hidden missing inputs.
   **Impact:** neither cash completeness nor timing validity follows from this
   reconstruction. Admit original prices and all expected funding events before
   computing new economics; retain missing cells as unavailable.
2. [carry_audit_costs.py:124](../../../scripts/carry_audit_costs.py#L124) compounds
   short equity to determine drift. For identical spot and perpetual prices
   100 → 105 → 100, matched fixed quantities have zero terminal price profit and
   return to their starting notionals, while the legacy short-equity proxy is
   `(1 - 0.05) × (1 + 1/21) = 0.995238095`. It invents final drift of 0.004761905.
   **Impact:** restoring an opportunity-cost charge does not turn this proxy
   into a signed-quantity cash book. Any replacement requires its own frozen
   registration and retained correction ancestry.

## Next justified step and untested claims

Proceed with one separately registered, bounded input-admission investigation
for an explicit quantity book. Require complete funding-event marks, spot
prices, event amounts, quantity/rebalance rules, spot principal and collateral
before new economics. Distinguish a conditional price proxy from an exact event
mark. If essential inputs cannot be admitted affordably, retain the unavailable
denominator and move to the next family.

Not tested here: actual event completeness, execution timing and achievable
fills, fees appropriate to the user's account, cash profit or full-capital
returns at either capital level, margin/liquidation paths, BTC/ETH beta,
prospective sample freshness, product/account eligibility, concurrency fault
injection, or independent external proof that the commit was pushed before the
run. No higher effort is needed for the completed algebra question; cash-book
input sufficiency is the specific unresolved question.
