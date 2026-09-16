# Interpreting the remaining lending and LP questions

Prepared while F1 remains active and F3 remains unadmitted. This note derives
illustrative identities from the frozen recipes, using invented prices and no
new market observations. It changes no gate, allocation, benchmark, request
budget or confirmation rule. Exact integer books and their registered costs
remain authoritative; the approximations below are not experimental results.

## Lending: account return depends on both allocation and interest

For capital C, a lending fraction w, unchanged dollar token prices and an
effective holding-period interest return y, gross account interest is Cwy.
With the fixed w=70%, reaching 10% on the whole account requires y of at least
14.2857% before gas, routing and rounding. The initial idle day matters when
converting an annual rate to this actual holding-period return. The registered
native gas reserve slightly reduces the amount actually supplied. A displayed
10% lending yield would therefore be insufficient for the account target even
if fully earned. An APR quote is not a realized holding-period return.

Against otherwise identical zero-yield wallet cash, the additional $200 hurdle
requires lending revenue less incremental costs of at least $200. On an ideal
$7,000 deposit this is 2.8571%, a different and weaker condition than the absolute
$1,000 target. Actual available cash yield and all other fixed risk-eligible
comparators still matter; an unavailable comparator cannot pass by omission.

The combined authored 50% lending impairment and 20% USDC depeg gives inception
wealth C[0.3+0.7(1−0.5)](1−0.2)=0.52C before gas and execution costs: a 48%
loss. This is close to the 50% limit. Interest changes the later allocation,
and the exact book stresses every funded state. This simple inception identity
does not establish a risk pass. Complete protocol or wallet loss remains a
separate affected-position tail.

The competing explanation for interest revenue is compensation for credit,
liquidity, stablecoin and contract risks. A positive income-index change alone
does not establish net dollar profit, withdrawal feasibility or benchmark value.
The fixed endpoint opportunity ceiling can reject the absolute opportunity
without a complete daily book only when its generous upper bound is below
$1,000. A higher ceiling proves none of the remaining requirements.

## LP: trading fees must pay for changing inventory

For intuition only, approximate the very wide fixed range by an infinite
constant-product range, equal dollar entry inventory, zero costs and a constant
USDC dollar price. Ignore the small native gas reserve. With half the account
in this LP and half in cash, let r be the ETH price ratio relative to entry.
Before fees, account wealth is approximately C[0.5+0.5√r]. The matched initial
inventory held without LP has wealth C[0.75+0.25r]. The LP's inventory difference
is therefore −0.25C(√r−1)². This difference is already present when inventory
is valued; it must not be charged a second time as “impermanent loss.”

The table shows invented price scenarios at C=$10,000. “Extra revenue” means
terminal-dollar fee revenue before deducting additional costs. These are two
separate hurdles, not alternative metrics from which to choose.

| Invented ETH ratio r | Extra revenue needed for $1,000 absolute profit, before costs | Extra revenue needed for $200 over matched holdings, before incremental costs |
| --- | ---: | ---: |
| 0.2 | $3,763.93 | $963.93 |
| 0.5 | $2,464.47 | $414.47 |
| 1.0 | $1,000.00 | $200.00 |
| 2.0 | −$1,071.07 | $628.93 |

The negative absolute requirement in the last row means price appreciation
alone exceeds the absolute target in this idealization. It does not establish
LP value: the same starting tokens would appreciate more when held. Conversely,
beating matched holdings in a falling market can coexist with an absolute loss.
Actual primary-cost accounting and every fixed eligible comparison decide the
experiment. All fees remain marked token claims until modeled liquidation.

For an illustrative simultaneous ETH price ratio r and USDC dollar ratio s,
the same idealization has wealth C[0.5s+0.5√(rs)]. At r=0.1 and s=0.8, loss is
45.8579% before frictions. Finite ticks, funded gas, accrued fee inventory,
execution and later-state weights affect the actual stress book. This is no
bound on losses or probability statement. Pool and wallet failure are separate
tails; a locked exit does not deliver spendable dollars on the target date.

The economic mechanism is compensation for supplying inventory to swappers.
The competing explanation is that fees merely pay for adverse selection,
inventory divergence and operating costs. Historical fee-growth counters can
measure conditional attribution on an observed path, but added liquidity changes
fee shares and may change that path. A numerical pass would still require
counterfactual execution, capacity and fresh confirmation evidence.

## When greater capital could help

For C>0 and F>0, let a strategy have pre-fixed-cost net account return g, fixed dollar cost F and
target t=10%, its simplified net return is g−F/C. Increasing capital can cross
the target only when g>t, with C≥F/(g−t). If g≤t, increasing capital cannot
solve the percentage target through fixed-cost dilution. With F=0 there is no
fixed cost to dilute, and g≥t directly satisfies this simplified target. The benchmark hurdle
also remains 2% of capital, rather than a constant $200 at every account size.

This algebra is a diagnostic, not permission for a capital sweep. Variable
execution costs, fee dilution, protocol caps and liquidity can worsen at size.
Any actual larger-capital case must first identify an evidenced fixed-cost or
minimum-size blocker and receive an exact successor registration. The current
$10,000 F1/F3 recipes remain unchanged.

## Classification after the frozen runs

- **Economic failure:** sufficient qualified evidence places primary net profit
  or incremental value below its required minimum, or drawdown/stress loss above
  its permitted maximum. Name the failed
  recipe and criterion; do not generalize to every protocol strategy.
- **Source unavailable:** required observations or witnesses are missing. Retain
  affected cells and any separately qualified bounds; missing is not zero return.
- **Insufficient evidence:** conditional numbers exist but implementability,
  comparable cash terms or untouched confirmation is unproved. A conditional
  numerical pass is not an implementable strategy.
- **Measurement failure:** accounting, source identity or execution provenance is
  defective. Preserve partial records and the actual failure; do not disguise it
  as an economic verdict or silently repeat a spent attempt.

The primary rule requires all specified hurdles together. Neither a favorable
year, a high fee total, a frictionless result nor an unavailable comparison
replaces that rule. No strategy is currently validated.
