# DeFi and self-custody extension — September 15, 2026

Status: **authorized consideration and source preparation; no DeFi financial
experiment, wallet connection, signature, transfer or order**. This is an
additive branch of the broader program. Original options gates, results, raw
stores, spent samples and exhausted allowances remain unchanged.

## Accepted scope and numerical assumptions

The user requests wallet-held assets, decentralized exchange trading including
Uniswap, and consideration of low-cap coins. Uniswap is a DEX. Ethereum mainnet,
Base and Arbitrum One are the accepted three-chain comparison set. This broadens
the earlier Binance-only implementation preference: Binance remains a baseline;
a wallet is an alternative location, not a second independently funded account.
No chain, token, pool, allocation or profitable strategy has been selected.
The first source comparison proposes Uniswap v3 major-asset routes consistently
across the three chains. Historical v2 evidence remains ancestry; v4 hooks are
deferred. Exact contract addresses and available versions must be frozen in the
source registration, with no substitution after failed acquisition.

The accepted objective remains $10,000 total committed capital, a documented
larger amount only if capital is the blocker, at least 10% annual net profit,
30% maximum drawdown, and 50% market/stablecoin stress loss. USD is the reporting
currency. The proposed operating assumptions remain 365 days, pre-personal-tax
net reporting, no borrowing/leverage and a 2%-of-capital incremental benefit over
eligible benchmarks. These are research assumptions, not additional personal
preferences. At baseline the annual hurdles are $1,000 absolute and $200
incremental, reported separately.

The user explicitly accepts separate reporting of wallet compromise,
smart-contract exploits and token failures as potential total losses of affected
positions, alongside total Binance failure. Losses are still recorded in actual
net wealth and observed drawdown; an exception to the deterministic stress gate
cannot erase an observed loss. Preclassify tail events before outcomes: ordinary
price crashes, depegs, poor liquidity, slippage and failed exits remain in the
market/stablecoin book even if a token approaches zero. Contract theft, malicious
transfer restrictions or demonstrated token/protocol failure may additionally
enter the separate tail register. Ambiguous cases remain in both reports, with
no post-result relabeling to obtain a pass.

For a later low-cap financial contract, proposed additional market scenarios are
a90% and99% small-token decline, simultaneous80% ETH/BTC decline and20% stablecoin
depeg, plus a seven-day exit outage followed by the same price shock and fivefold
execution frictions. Apply them to the whole committed account at each state;
use measured exit capacity or mark it unavailable. These scenario choices must
be frozen before outcomes. They are not a quantified worst-case loss bound, and
no small-token allocation weight is selected here.

Report affected dollars and percentage of total NAV at each state, not only the
initial weight. Include correlated failures: a compromised signing key or shared
approval can affect several assets; a protocol, bridge, stablecoin issuer or
chain incident can affect several pools. A wallet containing the whole account
can lose the whole account. Do not assign unsupported probabilities or assume
independent tail events. Protocol-deposited assets are exposed to contracts even
when the receipt token is held in a self-custody wallet.

## Finite ranked economic questions

D0 is a prerequisite, not an alpha claim. D1–D4 are the finite DeFi mechanism map;
none adds an initial financial recipe to H2–H5. Ranking favors low turnover and
existing cash-account infrastructure, before new outcomes.

| Rank | Mechanism and competing explanation | Prior evidence / ancestry | Data and cheapest informative test | Current disposition |
| --- | --- | --- | --- | --- |
| D0 Wallet-held major-asset spot | Custody/access or execution route might improve implementation of an existing exposure. Alternative: gas, transfer costs and additional dependencies make the route worse. Venue choice alone is not return alpha. | Inherits H1 allocation, passive holdings, execution and custody history. Chain-specific route admission is distinct from the old futures/proxy books. | One comparable ETH/stablecoin funding-to-exit route per chain; official deployment/asset identity, raw pool state, fee and gas provenance, exit availability and source limits. Audit fields before measuring prices. | First DeFi admission question. WETH and any BTC wrapper have separate identities and wrapper risk; never substitute a wrapper for BTC silently. |
| D1 Low-turnover small-token adoption/attention | Sustained observable adoption or delayed attention might predict subsequent demand beyond broad crypto exposure. Alternative: beta, thin markets, supply dilution, manipulation and survivor selection explain gains. Low capitalization alone is not a signal. | Inherits new-listing, DEX-ratio, wallet-signal, momentum and H8 information-selection histories; exact crosswalk is required before admission. No current low-cap strategy is validated. | Point-in-time token/pool universe including failed tokens; contemporaneous circulating supply and unlocks; causal signal timestamps; historical buy AND sell state. Cheapest test is whether those fields and a reproducible universe exist, before any token return ranking. | Consideration only. Proposed later universe definition: circulating cap $10m–$250m and token age at least 90 days, monthly decisions, no launch sniping. These thresholds are explicit draft definitions, not admitted cutoffs or a sweep; missing circulating cap is unavailable, not FDV substitution. |
| D2 Low-maintenance liquidity provision | Swap fees might compensate for supplying inventory over a broad fixed range. Alternative: informed trading, inventory loss versus holding, incentives dilution and gas consume fee income. | Inherits execution/carry and common crypto exposure. No prior literal LP cash-book experiment is established by absence of an LP name; ancestry review remains required. | Pool swaps, ticks/liquidity, fee growth, position changes and all underlying token cashflows. Cheapest test checks reconstructability and derives a conservative fee break-even bound against holding the identical underlying inventory. | Deferred after D0/D1 source feasibility. Full-range or broad fixed-range first; active range optimization, v4 hooks and leverage must earn a separate question. No advertised APR backtest. |
| D3 Unlevered stablecoin lending | Borrower demand may pay interest on idle capital. Alternative: reward subsidies, depeg, bad debt, utilization and withdrawal restrictions account for yield. | Related to accessible-cash and carry history; Binance cash or staking evidence does not establish a lending protocol return. | Point-in-time interest indices, real rewards, caps, reserves/utilization, withdrawal and loss history; specific protocol/market eligibility. Cheapest test is whether realized net accrual and exit constraints are observable without paid data. | Deferred; no named lending protocol selected. No recursive borrowing, looping or reward-token valuation at an unrealisable headline price. |
| D4 On-chain ETH staking exposure | ETH-denominated protocol accrual may improve holding ETH after costs. Alternative: slashing, wrapper discount, delays and dilution explain the premium. | Direct H6/WBETH ancestry, including the two retained claims. Changed venue or unhedged exposure does not restore the old allowance. | Conversion/reward indices, wrapper liquidity, redemption queue, depeg and contract dependencies. Reuse existing audit first; source gap check precedes a new cash book. | Deferred; no extra inherited staking/carry trial granted. |

New-listing sniping, wallet copying, frequent rotation, cross-chain arbitrage,
leveraged yield farming and discretionary token picking are not extra fallback
recipes. They require an evidenced distinct question and explicit budget review.

## Three-chain comparison, before outcomes

Official Uniswap deployment documentation lists Ethereum, Base and Arbitrum.
That establishes documented deployments, not current executable liquidity or
this user's interface/account access. See [Uniswap deployments](https://developers.uniswap.org/docs/protocols/v3/deployments).

| Chain | Distinct implementation question | Must establish; no current cost ranking asserted |
| --- | --- | --- |
| Ethereum mainnet | Does infrequent trading leave enough cash benefit after L1 transaction costs? | Exact router/pool version, gas at intended actions, funding and terminal exit, reliable historical state, token identity. |
| Base | Does the route reduce total implementation cost after L2 and funding/exit dependencies? | Execution and data-related fees, sequencer/finality/outage behavior, native versus bridged token identity, withdrawal route and historical RPC availability. |
| Arbitrum One | Does the route offer an implementable alternative for the same frozen exposure? | Execution/data fee evidence, ordering/finality, withdrawal route, token identity, complete historical pool state and source availability. |

Compare the same total capital and exposure. First choose an admissible route by
coverage, conservative total round-trip cost and operational constraints, with a
predeclared tie-break; do not choose the chain with the best subsequent return.
If chains, pools or tokens later become selectable financial variants, include
every tried variant and unavailable case in the selection denominator. A missing
route cannot become a zero-fee route. Extra capital can worsen pool impact and
exit capacity, so it may impose an upper capacity bound rather than fix costs.

## Source and execution admission

Use chain ID plus contract address for tokens; chain ID plus pool address/version
and fee/tick/range identifiers for liquidity. Record decimals, native/wrapped and
bridged identities, creation block, administrative powers and available contract
code. No ticker-only joins. Retain all universe entrants and reasons for exclusion
at each decision, including dead, rugged, migrated, illiquid and unsellable tokens.
Current listings, market caps, safety scores or wallet labels cannot be projected
backward without an availability witness. Unknown historic supply or circulating
cap stays unknown; fully diluted value is a different measure.

A registered source check must specify endpoints, exact request limits, block
range and finality policy; preserve request/receipt timestamps, block numbers AND
hashes, raw bytes, provider versions and failures. Reorg handling creates a new
version with lineage. An archive RPC, indexer or token warning is not proof of
complete point-in-time coverage. Public documentation reviewed here is source
orientation only, not captured market evidence.

Before any DEX return test, establish two-way sellability, executable depth at the
proposed size, transfer taxes/rebases/blacklists/max-wallet restrictions, approvals,
quote age, slippage controls, reverts and ordering/MEV assumptions. A successful
read-only simulation does not guarantee a later sale. Keep unknown terminal
proceeds unavailable; report documented worthless/unsellable holdings consistently
rather than deleting them or using the last quoted price as liquidation wealth.

## Full-capital accounting and comparisons

Reuse the existing lifecycle, Decimal synthetic patterns and pooled cash-book
contract. Add a narrow chain-event adapter only when a source question demonstrates
need; do not build a separate trading platform. Signed quantities/cashflows govern
PnL, never log returns booked as cash. All initial capital includes Binance cash,
wallet balances, ETH for gas, idle stablecoins, assets in transit, protocol claims
and dust. Transfers between these locations are not new profit or external capital.

Charge initial funding/withdrawal or bridge costs, approval/revocation gas,
successful and included failed/reverted transaction gas, pool/interface/router
fees where applicable, token transfer taxes, price impact and adverse execution,
conversion, redemption, final exit and remaining liabilities. Do not charge
embedded price impact twice or assume gas sponsorship/free bridges. Freeze
primary and doubled-cost treatment for each item before outcomes. Report labor
and pre-personal-tax scope separately; unknown tax is not a zero-tax assertion.

For LP positions, reconstruct token inventories plus actual claimable fees and
rewards, net of all entry/exit and range-management costs. Compare terminal wealth
with holding the exact same starting underlying quantities; do not subtract an
impermanent-loss statistic a second time after marking the actual inventory.
For lending/staking, include withdrawal queues and realizable claim prices; an
accrual index alone is not liquid cash.

Retain the ten B0–B9 core benchmarks under their identities, costs, clocks and
risk/access rules. DeFi comparison adds route-matched stablecoin holding, ETH
holding and simple ETH/stablecoin allocation controls, plus identical-inventory
holding for LP or no-lending cash for lending. These are comparison requirements,
not newly executed books; wrapped BTC is not an automatic B2 equivalent. A future
DeFi financial registration must freeze exact new comparator identities and
update the joint multiplicity/power budget BEFORE outcomes. The current 88-test
reserve covers only the four core recipes and ten original benchmarks; it cannot
support an expanded DeFi superiority claim unchanged. No choosing APR, Sharpe,
drawdown or token-price appreciation after seeing which looks favorable.

## Finite allowance and next action

The original six admission slots remain six. The unused repair reserve is now
assigned to one bounded three-chain DEX source-admission question, advanced to
second place after custody. Remaining order: EEA spot source, cash/FX/transfer
terms, synthetic pooled-account engine, precision/selection. Failure consumes its
slot. This pre-outcome reordering adds zero claims to the 178 + 11 = 189 core
administrative limit. Aggregate resource ceilings remain unchanged: 100 public
requests, 500 MiB new data, eight local CPU hours; each acquisition at most 20
requests, with the source contract setting a smaller exact bound before capture.

This document review and history crosswalk are preparation, not market quote
collection. The three-chain admission question must get a separate committed
charter, exact six-or-fewer source field groups per chain, input/cell denominator,
resource limits and independent review before execution. Retain all three chains
when sources are unavailable; do not replace a missing chain with a fourth.

No DeFi financial recipe or extra confirmation episode is admitted. The initial
four H2–H5 financial slots are retained. If DeFi source evidence justifies a
replacement before development, register the replacement and preserve the displaced
recipe in selection history; do not reuse the 88-test reserve without review.
If it warrants an addition, record a separately justified finite budget amendment
and cumulative ancestry before any outcome. Neither route resets NLST, SMW,
staking, carry or other inherited limits. A useful source failure remains useful;
missing history or exit evidence is not proof that DeFi cannot be profitable.

## Primary-source orientation, accessed September 15, 2026

- [Uniswap AMM mechanics](https://developers.uniswap.org/docs/get-started/concepts/how-uniswap-works): pool reserves determine execution and trades large relative to depth create price impact. This motivates size-aware execution; it does not establish an edge.
- [Uniswap token warnings](https://support.uniswap.org/hc/en-us/articles/8723118437133-What-are-token-warnings): flags include honeypots, impersonation and extreme transfer fees; coverage and accuracy are not guaranteed. Absence of a flag is not a safety pass.
- [Ethereum gas](https://ethereum.org/developers/docs/gas/): gas must enter the cash book; numerical fees are not estimated from this documentation.
- [Base documentation](https://docs.base.org/get-started/base) and [configuration changes](https://docs.base.org/base-chain/network-information/configuration-changelog): chain parameters change; use witnessed versions instead of fixed timeless fees. An attempted open of the network-information parent page was unavailable in the web tool and supplied no evidence.
- [Arbitrum Nitro](https://docs.arbitrum.io/how-arbitrum-works/inside-arbitrum-nitro): transaction ordering, execution and finality require separate clocks. Documentation is not a guarantee of user execution or recovery.
