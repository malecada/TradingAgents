# Protocol-specific stress design requirements

Preparation only. The accepted30%drawdown and50%market/stablecoin stress limits
remain; catastrophic exchange, wallet, contract and token failures remain
separate total-loss scenarios for affected positions. The exact financial gate
must freeze numerical shocks, path, timing, exit policy and costs before outcomes.
This document identifies accounting requirements, not new observed losses or a
change in investment preferences.

## LP claims must change inventory under an admitted price path

Reusing the spot book's stress calculations while freezing an LP's underlying
token quantities can understate its loss. If arbitrage moves the pool through a
shock, a fixed LP position holds more of the falling asset and less of the other
asset. Recompute token inventories from the position's exact liquidity/range and
the modeled shocked pool square-root price. A separate inventory-divergence debit
would then double-count that change.

As a mathematical illustration only, an idealized infinite-range50/50position
with one asset halving and the other unchanged retains sqrt(0.5), about70.71%,
of its starting value before fees/costs. Holding the initial tokens retains75%.
Actual v3 finite ticks and integer rounding must use the admitted position math;
the illustration is not a source observation or a chosen capital allocation.

The shock contract must distinguish:

- Market price changes with an operating pool and arbitrage: inventory follows
  the specified pool-price path; no invented favorable fees are credited.
- Wallet, bridge or exchange access outage with an operating pool: the LP can
  continue changing composition while the investor cannot exit.
- Pool/protocol pause or absent liquidity: a frozen pool price does not make
  inventory sellable at that price. Mark the actual claim/exit constraint, with
  missing realizable value explicitly unavailable.
- ETH and USDC both move: their relative price sets pool composition, while
  their separate USD marks set account wealth. Holding USDC at$1 would miss the
  stablecoin loss and can also use the wrong inventory ratio.

Treat a seven-day access outage and a30day redemption lock as timing constraints,
including when they cross day365. Delayed access is distinct from an eventual
marked recovery. No source proxy establishes instantaneous liquidation during
the shock. The stress gate must define whether path-dependent arbitrage and
fees are modeled, bounded or left unavailable, rather than selecting the least
damaging treatment after seeing results.

## Staking wrapper and queue claims

ETH/USD moves, wrapper discounts, protocol conversion changes and queued claim
haircuts are different channels. Applying only the ETH shock misses the latter
three. A direct wrapper market mark already includes the conversion/discount;
do not apply them twice. A holder cannot claim both rewards while waiting and
the queue's fixed/capped redemption amount without protocol support.

Queue entry before horizon end sacrifices some holding-period accrual and may
still fail to release cash by day365. Queue entry on day365 does not create
instantaneous year-end dollars. The primary exit route and any pre-horizon exit
instruction must therefore be frozen, with an alternative route reported only
under its registered role.

## Lending and stablecoin cash

Unlevered lending removes the investor's margin liquidation but does not remove
stablecoin market loss, borrower/collateral shortfall or inability to withdraw.
A reserve index does not guarantee the entire underlying claim can be realized.
Ordinary market-driven credit/liquidity loss cannot be removed from the market
stress assessment merely by calling it a contract tail. Contract exploits and
other separately accepted catastrophic events are reported separately, while
all actual account losses still enter NAV.

The same stablecoin/USD shock applies to uninvested wallet/Binance USDC and to
USDC underlying a lending or LP claim, subject to their different redemption
constraints. Pending bridges, gas reserves and residual tokens remain part of
the committed account and receive their own shocks/marks.

## Matched comparisons and reporting

Use the same shock origin, horizon, USD marks and comparable access assumptions
for the candidate and each benchmark. Risk-ineligible benchmarks still retain
their absolute/relative results and stated reason; unknown eligibility is not
a basis for dropping a difficult comparator. Route-matched token holdings provide
the direct comparison for a staking or LP sleeve, alongside the original broader
cash/crypto panel.

Report loss from origin, drawdown from peak, dollar loss and delayed-access time
separately. A daily-mark drawdown remains a discrete observation, not a bound on
intraday loss. Deterministic scenarios do not estimate failure probabilities.
The minimum10%annual net profit and2%-capital incremental hurdle remain separate
from risk limits. No alternative risk statistic can rescue a failed frozen rule.
