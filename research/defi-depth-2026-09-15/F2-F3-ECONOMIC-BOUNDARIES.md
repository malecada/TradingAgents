# Allocation arithmetic before financial outcomes

These are algebraic implications of proposed/frozen allocations, not backtests,
new return observations, or changes to the primary decision rule. The$10000
capital denominator includes cash and gas. Greater capital does not improve a
percentage-return mechanism unless fixed costs or execution granularity bind.

## Wrapped staking versus its ETH control

For a sleeve fraction w, an ETH gross price factor p and an additional wrapper
price factor q relative to ETH, the gross incremental whole-account value is
C*w*p*(q−1), before different entry/exit costs and residuals. It is not the full
wrapper price return, and does not identify whether q comes from staking,
oracle construction, bridge basis or discounts.

With the fixed approximate25%sleeve, the$200incremental hurdle requires
p*(q−1)≥0.08 before extra wrapper costs. At unchanged ETH prices, an illustrative
3%wrapper-over-ETH increment would contribute only about$75 to a$10000account.
That arithmetic makes the wrapper's additional costs and risk meaningful; the
actual panel is still needed to test the registered price-return question.
No observed or expected staking yield is claimed by this invented illustration.
The10%absolute account target at unchanged cash value requires about40%gross
sleeve return before costs at25%weight. Cash can lower loss exposure while also
reducing the contribution of sleeve gains.

## Fixed low-maintenance LP

A50%investable-capital LP sleeve needs approximately20%sleeve net return to make
10%on the whole account when the other half earns zero and ignoring gas reserve
and fixed costs. Fees must be added to the changing underlying inventory exactly
once. They are not the same as incremental LP value versus holding its initial
ETH/USDC quantities. In a falling ETH market, fee receipts can coexist with a
negative account return; in a rising market, positive LP return can coexist with
underperformance of its matched inventory control.

Daily active-liquidity observations cannot prove the minimum liquidity across
all swap steps. A fixed-flow fee participation bound needs that stronger input;
using the smallest daily snapshot instead would assert an unsupported lower
bound. A favorable historical fee attribution therefore does not by itself
establish the extra position's achievable fees or fill capacity. These limitations
must remain in F3's source and decision contract before any financial result.
