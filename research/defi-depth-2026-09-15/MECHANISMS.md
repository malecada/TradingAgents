# Mechanism-level investigation requirements

These are accounting identities and analytic thought experiments, not financial
outcomes, inferred investment preferences or return forecasts. Each actual book
needs a committed protocol/source/cost/benchmark contract before execution.

## Unlevered lending: who pays, and when is accrual cash?

Borrower demand supplies the interest. Token-denominated gross claim growth is
approximately the normalized reserve-index ratio for a fixed scaled balance;
the exact integer rounding and protocol implementation govern actual balances.
Use changes in the actual claim and realizable underlying balance, not an
advertised instantaneous APR multiplied by365. Rewards in another token require
a causal accrued quantity and an executable price; unobserved rewards stay
unavailable, not a convenient extra yield or assumed zero actual entitlement.

Reconcile three separate ledgers: stablecoin quantity, stablecoin/USD value and
funding/withdrawal/gas cashflows. With initial committed C and total realized
cost K, a full-investment idealization needs net asset growth at least
0.10 + K/C to reach the annual absolute target. It also needs incremental
benefit over accessible cash; a positive interest payment alone does not prove
benchmark value. All idle balances and native gas tokens remain in C.

A public underlying balance is only one condition for exit. Reserve flags,
liabilities, bad debt, pause/freeze behavior, caps, queue or transaction execution
may prevent realization. Contract failure is a separate affected-position tail;
depeg, ordinary liquidity loss and unavailable exits still enter market stress
and actual NAV. A lower-risk cash sleeve can be useful evidence even if its
absolute annual profit falls below the full-account target; it is not labeled
an adopted10% strategy.

## Staking: separate additional token quantity from directional return

For a wrapper quantity q, protocol conversion r, market conversion discount d
and ETH/USD price p, liquidation value before exit charges is q*r*d*p. The
protocol conversion rate is not a promise that ETH can be received immediately
at that rate. Queue waiting, foregone rewards, slashing/claim changes and wrapper
bid/ask must be accounted for along the selected exit route.

A staking-versus-ETH comparison asks whether additional realized reward units
exceed all differential fees and exit risk. A staking/cash portfolio-versus-cash
comparison is a second, broader claim with substantial ETH exposure. Preserve
both. An unhedged book is distinct from the retained WBETH fixed market-value
hedge only in its economic exposure and cashflows; earlier staking, funding,
relative-value and sample-selection history still applies.

Exposure constrains the annual target mechanically. In an illustrative portfolio
with25% risky exposure and75% zero-yield cash, a40% risky-asset gain is needed
for a10% portfolio gain before costs. At a hypothetical4% cash yield the required
risky return becomes28% before costs. These are algebraic examples, not expected
yields or a proposed parameter change. Raising committed capital does not fix
this exposure arithmetic; it changes fixed-cost drag and potentially execution.

## Static LP: reconstruct inventory before judging fees

A position receives fees while its range is active and holds a changing mixture
of the two assets. For a fixed v3 liquidity amount L, claimable token fees depend
on the appropriate inside-range fee-growth change, modulo2^256, multiplied by L
and divided by2^128 with contract rounding. Tick boundary initialization and
crossing, position mutations and fee collection must be reconstructed. Global
counters cannot replace inside-range growth for an arbitrary range.

Final wealth is remaining token0 inventory + token1 inventory + collectible
fees/rewards, each at a realizable liquidation price, minus complete entry/exit
costs. Compare holding the exact starting token quantities. Once the actual
inventories have been marked, subtracting a separate 'impermanent loss' number
again would double-count their divergence.

As an idealized zero-fee constant-product example, starting equal dollar values
and a token price ratio r produce LP value2*sqrt(r) and held-token value1+r in
units of one initial half-portfolio. The relative divergence is
2*sqrt(r)/(1+r)-1. If price halves, a$100 initial LP becomes about$70.71 and
identical holdings become$75: fees must first cover$4.29 plus differential costs
before LP adds cash value. This infinite-range illustration is not an exact
finite-tick v3 simulation or measured result. Full-range v3 still uses finite
usable ticks and integer token amounts.

Adding a hypothetical$10,000 position to historical liquidity can change the
fee share and price path. An unchanged historical fee-growth path is a
price-taking approximation; its participation/capacity error must be bounded
or the book labeled unavailable/conditional. A larger account can make that
approximation worse. Active range adjustment, fee-tier choice and incentive
selection are extra variants, not automatic repairs after a static LP loses.

## Small tokens: a causal universe is part of the strategy

The trading universe must exist at each decision, including assets that later
failed, migrated, became illiquid or could not be sold. A present-day list or
current safety flag cannot be projected backward. Circulating capitalization
requires contemporaneous circulating supply; total supply or fully diluted value
is a different field. Chain/address and pool/version identify instruments.

An adoption signal must have an observable economic channel and an availability
clock. Addresses, wallets and swap counts can be manipulated and may track
common crypto demand. The cheapest informative test establishes recoverable
historical universe/signal/exit fields before ranking tokens or selecting a
threshold. Net alpha then needs source-complete failed cases, realistic two-way
execution, common-exposure controls and independent future confirmation. The
retained NLST/SMW/T7 searches constrain novelty and cumulative selection.

## Carry and information: deepen the failed explanation

For retained carry, separate gross premium, hedge drift, funding, capital held
idle, fees, terminal settlement and unavailable contract lifetime. A failed
particular book can reveal an actual cost/capital blocker or only a snapshot
that lacks information value today. An external changed condition must be
established before reopening an exhausted mechanism. The22 settlement-blocked
cases remain explicitly deferred; no paid recovery or provider contact.

For information strategies, establish source vintages and event availability
before considering model complexity. LLM training exposure, article revision,
future normalization and cohort selection can invalidate an apparently causal
signal. Additional time is useful for reconstructing those dependencies and
cash accounting; it does not turn another feature/sign/window search into
independent evidence.

## Source basis

Protocol interfaces and units are documented in
[SOURCE-ORIENTATION.md](SOURCE-ORIENTATION.md), with raw official address-book
snapshots retained in documents/. Contract/version data at actual historical
blocks still requires the registered source checks. The numeric examples above
are derived illustrations and never enter measured strategy profitability.
