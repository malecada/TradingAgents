# Independent mechanism-interpretation review

## Scope and disposition

Bounded analytical review of `MECHANISM-INTERPRETATION.md`. No source observations, active execution roots, financial results, network or empirical calculations were opened or run. Only invented-number arithmetic was independently reconstructed. No financial registration, ledger, recipe or execution permission changes follow from this review.

**Disposition: numerical examples pass; correct the risk-threshold direction before using the classification section.** This is a documentation finding, not a defect found in the registered books.

## Findings

1. **Required correction — risk failure inequality is reversed in prose** (`MECHANISM-INTERPRETATION.md:98`). Net profitability and incremental value fail below their required minima, but maximum drawdown and stress loss fail above their permitted maxima. The current phrase “net, incremental or risk result below its fixed threshold” can classify acceptable low risk as economic failure. State both directions explicitly, retaining equality treatment from the frozen rule. The conclusion must name the fixed conditional recipe/assumptions and must not generalize a model failure into deployed-protocol evidence.
2. **Minor clarification — holding-period versus annual rate** (`MECHANISM-INTERPRETATION.md:12`). With `y` defined as an effective holding-period return, the idle day is already outside that earning interval. The ideal requirement remains `y >= 0.10/0.70`; the idle day raises the annual-rate equivalent rather than being a second deduction from `y`. Gas and costs genuinely raise the required earned return/reduce supplied capital. Separate those explanations.
3. **Minor domain clarification — fixed-cost threshold** (`MECHANISM-INTERPRETATION.md:84`). State `C > 0`, `F > 0`, and that `g` and `F` are held constant for the identity. Then `g - F/C >= t` is achievable at finite capital exactly when `g > t` and `C >= F/(g-t)`. When `F=0`, `g=t` already meets the target, so the strict-positive-cost premise should be explicit. The following caveats correctly reject extrapolating this identity to variable cost/capacity conditions.

## Independent mathematical reconstruction

- Lending: `C*w*y` requires holding-period `y >= 1/7 = 14.285714...%` for a 10% whole-account target at 70% allocation. A $200 incremental hurdle on a $7,000 ideal deposit is `1/35 = 2.857142...%`, before incremental costs. The stated rounded numbers agree.
- Combined credit/depeg shock: surviving lending principal is `0.7C*0.5`; the other `0.3C` and surviving lending claim are both exposed to the `0.8` USDC mark. Total `0.52C` means 48% loss. This inception simplification excludes native gas, costs, accrual and dynamic weights, as the note discloses; it is not a maximum-loss bound or risk pass.
- Infinite-range LP: for equal initial dollar inventories with constant product and no fees, marked sleeve wealth changes by `sqrt(r)`. A half-account sleeve plus half cash is `C*(0.5+0.5*sqrt(r))`. Matched holdings are `C*(0.75+0.25*r)`. Subtraction gives `-0.25*C*(sqrt(r)-1)^2`, which is already included in terminal inventory value and must not be debited again.
- Independent 70-digit Decimal calculations reproduce every table cell to the cent: at `r=0.2`, absolute/matched requirements are $3,763.93/$963.93; at `0.5`, $2,464.47/$414.47; at `1`, $1,000.00/$200.00; at `2`, -$1,071.07/$628.93. Negative absolute requirement describes excess appreciation over that hurdle, not negative fees or benchmark-relative success.
- If ETH and USDC dollar ratios are respectively `r` and `s`, invariant inventory value is proportional to `sqrt(r*s)` and idle USDC to `s`, yielding `C*(0.5*s+0.5*sqrt(r*s))`. At `r=0.1`, `s=0.8`, loss is `45.857864376269...%`, agreeing with 45.8579% after rounding.

## Interpretation limits retained

The document explicitly labels infinite-range, frictionless and inception assumptions as illustrative. Finite tick inventory, integer rounding, actual funded gas, entry clocks, costs, fee-token inventory, dynamic stress and locked exits remain governed by the exact registered books. LP fee-growth attribution on a retained historical path does not prove that added liquidity receives the same fee share or preserves the price path. The endpoint ceiling is a one-sided necessary-opportunity screen only; a higher ceiling does not rescue missing feasibility or confirmation. Absolute profitability and every required benchmark-relative comparison remain conjunctive. The note neither adds trials nor supports actual returns, capacity, access, deployment, or a validated strategy.

## Evidence

The calculations used only literals printed in the note, Python Decimal at 70-digit precision, and algebra independent of the strategy runners. No source-model fee, rate, price or profitability observation was consulted.

Reviewed document SHA-256: `bc0033148cf60b3d2b738ac610cfc518d8df2b1b73e5182dc4a43b0ae612964f`.

## Correction re-review — PASS

The three changed sections were re-read directly. Profit and incremental shortfalls now use lower bounds while drawdown/stress failures use upper bounds. The idle day is correctly described only as part of converting an annual rate into the earned holding-period return. The capital identity now states positive capital/fixed-cost premises and separately handles zero fixed cost. These changes resolve the findings above; no remaining substantive issue was identified within this analytical scope. The original findings remain retained as review history.

No financial calculations were rerun and no empirical data or active execution root was accessed. Corrected document SHA-256: `bc0033148cf60b3d2b738ac610cfc518d8df2b1b73e5182dc4a43b0ae612964f`.
