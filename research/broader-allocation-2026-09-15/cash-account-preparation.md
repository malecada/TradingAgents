# Cash and pooled-account preparation

Next admitted question: cash vehicle, USD valuation, applicable fees and
funding/exit terms. This file is engineering/design preparation, not a completed
admission claim or a financial experiment. No additional data request, portfolio
simulation or price sample has been run under it.

## Evidence now available

The two registered source checks identify three fixed native-USDC/WETH DEX
factory mappings and current public Binance BTCUSDC/ETHUSDC rules/depth. They do
not value USDC in USD, establish individual account commissions or prove
transfer/redemption access. The three chains and Binance are possible routes;
no route or income product is selected from those results. B1 remains unavailable
as an actual implemented yielding/low-risk cash vehicle.

The user specified USD reporting, Czech Binance account, stablecoin cash and
later wallet alternatives. A concise clarification asks whether the baseline
starts in USDC already on Binance or includes bringing new money in. Until an
answer, retain both as explicit input cases; neither is silently booked at zero
funding cost. Ordinary source and pure accounting preparation can continue.

Freeze the investment start boundary explicitly. For already-funded USDC, value
all starting balances in USD; historical acquisition fees before that boundary
are sunk costs and are not charged again. New conversion, transfer or exit costs
after the boundary remain in the book. For fresh money, the boundary precedes
entry conversion and transfer, so those charges reduce the same committed
capital. Report the basis alongside every comparison.

## Exact contracts needed before a financial book

| Field | Treatment while unresolved |
| --- | --- |
| Initial asset/location and amount | Parameterized: funded USDC or fresh money; all committed balances and initial conversion costs counted. No transfer action authorized. |
| Initial USD value | Value starting stablecoin quantities using an admitted USD mark/exit convention.10,000USDC is not automatically$10,000. |
| Fiat/account entry and terminal route | Preserve actual currency, conversion, fixed/percentage fees, delays and minimums. Existing-funded inventory and new-money cases differ. |
| Binance commissions and fee currency |10bp/side remains a conservative research proposal without discounts; do not label it this account's verified rate. Actual applicability is unknown. |
| Passive USDC cash yield | Zero nominal token accrual may be a declared holding control. No automatic Earn/lending yield. USD value still changes with the admitted stablecoin mark. |
| Funding/withdrawal/bridge/gas | Include charged amounts, native fee inventory, in-transit receivables, delay and terminal exit. Unknown charges remain unknown. |
| Redemption and account eligibility | Public documentation/reachability are insufficient for personal access. No credentials/account probes or assumed retail issuer redemption. |
| Cash and venue risk | Retain depeg/market stress and separate accepted affected-position total-loss tails, including correlated failures. Real losses remain in NAV/drawdown. |
| Tax/labor | Pre-personal-tax net figures, labor separately, under the disclosed research assumption. No implied zero tax. |

All cost/valuation assumptions must be frozen before financial outcomes. A
conditional scenario may be informative but cannot pass implementability using
unverified assumptions. The10% absolute hurdle and proposed2% incremental hurdle
apply to all initial committed USD capital, including idle cash and fee reserves.

## Reuse and narrow engineering boundary

Read-only inspection of docs/research/ENGINE_INDEX.md and the actual implementations
confirms that tradingagents/accounting.py is a signed-notional return book with
pretrade-NAV fees. It does not itself enforce individual spot-wallet purchase
cash or multi-location asset inventories. Reuse its accounting principles and
missing-held-value checks, not a futures/sleeve NAV as a funded spot-wallet book.

scripts/carry_feasibility_math_2026_09_10.py already contains Decimal quantity/rule,
ordered-depth and fee-currency examples. Reuse reviewed patterns or narrowly
pinned pure helpers where compatible, without invoking its hedge sizing or
terminal financial main on source snapshots. Original engines remain unchanged.

The next pooled-account adapter should retain signed asset deltas by location:
buys debit quote and credit net base; sells debit base and credit net quote;
fees debit their actual asset once; transfers relocate quantities and separate
fees, never create profit. Require available cash before buying and available
base before selling. No shorts/borrowed top-ups. Base-fee and quote-fee paths,
rounding/dust and fee-asset replenishment need independent literal checks.

USD liquidation NAV sums every sellable holding and cash claim under its admitted
exit mark and cost, including all locations. Pending transfers remain receivables
with explicit access/valuation status. Missing held valuation makes NAV unavailable;
a failed/rugged token cannot be deleted. Do not subtract LP inventory divergence
again after valuing actual LP token inventories. No LP/lending engine is added
before its separately reviewed question earns that scope.

Pure synthetic checks can be prepared without the funding answer: round-trip
cash conservation; full-capital phased entry; fee currencies; insufficient cash;
transfer delay/double counting; stablecoin depeg; dust; final exit; and missing
held values. A later registered financial measurement also retains the convention
swap diagnostic and independent book reconstruction. This design creates no
new strategy recipe or empirical attempt.

## Next finite admission contract

Freeze exact public/documentary sources or authored scenario inputs after the
funding basis is settled. Retain inherited179import/cap189 and parent source claim;
helper counts both actual source claims automatically. The next new claim uses
admission4/6, not a fresh family or replacement source attempt. Three admission
slots and78registered public requests remain; preserve unknown terms and stop
short of adoption if free evidence cannot establish them. Current quotes are
exposed source observations, not untouched confirmation or historical fills.
