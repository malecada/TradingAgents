# Fixed WBETH market-value hedge cash diagnostic

Experiment wbeth-book-20260911, child of wbeth-inputs-20260911. Development only,
second of three new WBETH linked-value questions, also charged to map rows 3/8.
The observed current WBETH source and already spent ETH/BTC quarter remain
exposed. Prior PRX/DEX/funding history and incomplete multiplicity are inherited;
no fresh confirmation, pair selection, threshold sweep or parameter rescue.

## Economic prediction and limits

WBETH's documented claim on staked ETH provides a relationship and potential
validator-reward component different from plain ETH spot carry. A fixed WBETH
spot long with an ETH perpetual short may retain that relative appreciation
while reducing broad crypto-price exposure. Competing explanations include
staking accrual, market basis/depeg and demand, funding, costs, residual market
exposure and capital immobilization. Market-price cashflows cannot separate
these sources into pure validator yield. No redemption cashflow is modeled.

Question: does the fixed one-quarter market-value approximation earn positive,
economically relevant net cash under both cost scenarios and have acceptable
measured conditional exposure? The registered source interval is April 1–July 1,
2026 exclusive, 91 daily observations, first open to last close. This is one
holding episode, not 91 independent strategy trials. No alternative dates,
asset, ratio, capital allocation, cost or hedge will be selected after results.

Four primary cases: capital 1,000/10,000 USDT × base/stress costs. Four paired
zero-funding counterfactuals retain exactly each primary's quantities/costs;
their funding source is still validated and observed amounts retained. They
remove one modeled cashflow, not identify pure staking returns. Eight declared
cells remain, including all unavailable cases; capital scales and
counterfactuals are not independent discoveries.

## Exact signed-quantity and wallet convention

Use the hash-pinned WBETH capture/admission and carry capture/admission. Require
91 complete WBETH/ETH spot, ETH perpetual and ETH mark days plus all 273
registered conditional ETH funding records; entry-coincident funding is excluded,
leaving 272 after entry through exit. Use authentic event marks, not zero-filled
funding or an index adjustment. BTC spot supports descriptive beta only; its
unavailability cannot silently invent a benchmark or erase an otherwise valid
cash book. Source identity, raw hashes, normalized admission and coverage are
revalidated. Positive activity is required at entry/exit; other zero activity
remains visible. Current filter values are not historical rule proof.

Define r = raw WBETH spot entry open / raw ETH spot entry open. This is a
market-value hedge approximation, not a contractual ETH conversion ratio.
Let Wask and Fbid be the adversely slipped WBETH spot and ETH perpetual entry
prices. With spot/futures fee rates fs,ff and capital C, choose conservatively:

qW = floor((0.40*C / (Wask*(1+fs) + r*Fbid*ff)) / 0.0001) * 0.0001
qE = floor(qW*r / 0.001) * 0.001

Hold +qW WBETH and −qE ETH perpetual. Both must be positive. This analytic
quantity choice is conservative, not an optimized largest feasible portfolio.
Actual WBETH principal plus BOTH entry fees must fit 40% of C; retain 50% of C
as separate futures collateral and at least 10% idle cash. Assumed lot sizes
0.0001 WBETH and 0.001 ETH perpetual remain conditional on historical/execution
applicability. There is no short-sale notional cash inflow or additional capital.

Base spot/futures commissions are 0.001/0.0005 and adverse per-side slippage
0.0002. Stress doubles all three. Entry buys WBETH at first open plus slippage
and sells ETH perpetual at first open minus slippage; exit sells WBETH at last
close minus slippage and buys ETH perpetual at last close plus slippage. Fees
are assumed USDT. No maker rebate, discount, borrow, redemption or unstated
transfer leg. Quantities remain fixed throughout, with no ratio refit/rebalance.

Funding to the ETH short is qE × actual event mark × signed settled rate. Report
spot purchase/sale principal, signed perpetual price cashflow, every commission,
funding, idle cash and released collateral. Terminal wallet cash must reconcile
to explicit price PnL + funding − fees within absolute 1e-8 USDT tolerance.
Same-quantity frictionless price PnL and slippage/fee decomposition stay separate;
no higher-financed counterfactual replaces the actual primary quantities.

## Risk and inference

Daily NAV uses WBETH spot close, ETH perpetual mark and observed settled funding,
with terminal wallets flattened and principal/collateral released. Keep valid
simple daily NAV returns, full-capital terminal cash return, drawdown from initial
capital, net/gross MARKET-VALUE notionals, residual market-value mismatch and
mark-high reserve diagnostics. Actual liquidation rules and true WBETH ETH delta
remain unavailable. Consequently the program's realized net-base-delta ≤1% of
NAV gate is unavailable; market-value mismatch is not substituted for that gate. Report common underlying half/double scenarios and isolated
WBETH −10%/−50% depeg scenarios separately; they are chosen stress illustrations,
not bounds on every loss or proof of collateral survival. Counterparty/redemption
risk cannot disappear because exit is modeled through a spot bar.

Cash benchmarks 0/3/5% × C × 91/365 remain separate and are not deducted from
cash profit. The log1p NAV-return sum times C is an invalid arithmetic-PnL shadow
retained only for the convention forensic; actual wallet cash governs.

Necessary historical economic screen: positive cash and descriptive simple
annualization ≥3% on ALL capital in both base and stress primary cases. This
is the existing provisional relevance assumption, not an annual forecast.
Descriptive exposure screen: joint BTC/ETH OLS of 91 valid simple NAV returns,
intercept, HAC7, 97.5% individual beta intervals (within-book 95% Bonferroni).
Each absolute point beta ≤0.1 and interval within [−0.2,0.2]; observed drawdown
≤10%. First benchmark return references the first spot open. These are diagnostic
screens, not cross-search confirmation or a fitted trading hedge. Singular,
nonfinite or nonpositive-NAV cases remain unavailable.

Expected-profit confidence interval and power remain unavailable: one fixed
holding episode does not supply independent repeat-trade outcomes. Do not
bootstrap endpoint fees into a future-strategy-profit claim. Actual fills,
fee/lot/account applicability, margin/liquidation and stablecoin-dollar risk
remain unvalidated. No case graduates, even if all necessary historical screens
pass. A positive result would justify separately frozen execution/dependence and
untouched/prospective evidence, not paper or real orders automatically.

## Resources, review and continuation

One foreground run, eight cells, books.json and summary.json capped at 20 MiB
combined actual lifecycle encoding, no network, two CPUs, 512 MiB sampled
aggregate RSS and 120 seconds under resource_guard_v2.py. Pure synthetic tests
must prove principal/wallet release, two distinct quantities, cost/funding signs,
zero-funding fixed quantity, planted relative movement, common-price cancellation,
rounding mismatch, missing source, nonpositive NAV and depeg scenarios. A guarded
full lifecycle using invented inputs and real HAC calculations must pass.

Independent implementation/input/charter review precedes committed source/gate
and verified remote freeze. Independently reconstruct actual cashflows and
statistical descriptions afterward, retain all cases and receipt verification,
write a decision and back up state. Diagnose costs versus price/funding/exposure;
do not tune the same episode to pass. Choose a distinctly justified remaining
question or switch families. This experiment cannot establish research exhaustion
or a validated strategy by itself.
