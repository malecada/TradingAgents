# Triangle proxy: independent completed-result review

**PASS for the registered arithmetic and evidence claims. The assumed-fee
profitability screen fails in both directions at both capital levels.** BTC-first
has a small positive zero-fee proxy that is erased by the three assumed fees;
ETH-first is negative before fees. This is one conditional static observation,
not measured filled-order PnL or a timeless rejection of triangular conversion.

The independent [checker](check_triangle_proxy.py) reconstructs all eight cases
from retained raw ticker strings with 75-digit Decimal arithmetic. It imports
neither producer engine nor runner and makes no network request. It also invokes
the separately written independent source checker for all six parent schemas.
The [JSON evidence](triangle-proxy-review.json) retains every reconstructed case,
fee conversion, size flag and comparison. No fee, direction or snapshot was
selected or varied beyond the frozen eight cells.

## Numerical result

All figures below are USDT cash proxies from the forced continuous full-notional
model, rounded to eight decimals.

| Direction | Initial USDT | Zero-fee profit | Profit after 0.1% received-asset fee on each of three legs |
|---|---:|---:|---:|
| USDT → BTC → ETH → USDT | 1,000 | +0.16037690 | −2.83710475 |
| USDT → BTC → ETH → USDT | 10,000 | +1.60376897 | −28.37104752 |
| USDT → ETH → BTC → USDT | 1,000 | −0.47687302 | −3.47244483 |
| USDT → ETH → BTC → USDT | 10,000 | −4.76873017 | −34.72444828 |

The BTC-first gross factor is about 1.00016037689733, declining to
0.997162895247611 after fees. The reverse factors are about 0.999523126983165
and 0.996527555172073. Both assumed-fee factors are below one. The two capitals
scale the same unit arithmetic; they are not independent opportunities.

At 1,000 USDT, the BTC-first fees have downstream USDT equivalents
1.00016037689733, 0.999160216520435 and 0.998161056303915, totaling
2.99748164972168. Subtracting that drag from the 0.160376897332543 zero-fee proxy
gives −2.83710475238914. The corresponding reverse-cycle fee drag is
2.99557181109167 on an already negative gross result. This decomposition uses
the actual fee in its received asset and later gross conversion rates; it neither
duplicates fees nor assumes every fee was initially paid in USDT.

## Independent reconstruction and forensics

All 576 numerical comparisons agree within **4.252e-12** in their respective
units, below the 1e-8 check tolerance. Purchases divide by ask, sales multiply by
bid, fees reduce the acquired asset before the next leg, and every signed
BTC/ETH/USDT wallet flow reconciles. Terminal BTC and ETH balances are zero in
the idealized model. Terminal USDT minus starting USDT matches simple cash profit.
The fee sum equals zero-fee terminal wealth minus fee-paying terminal wealth.

The product of the two gross route factors equals the product of the three
individual bid/ask ratios and is at most one, as required by uncrossed prices.
All 24 case/leg displayed-size checks pass for the modeled base quantities.
These checks use gross acquired base before fee on buys and spent base on sells;
they do not measure depth consumption, queue position or fills.

The log-factor shadow is independently reconstructed with Decimal logarithms
and remains separate from the cash ledger. At 1,000 USDT with fees it understates
cash profit by about 0.00403221 USDT for BTC-first and 0.00604293 USDT for
ETH-first. No log return was booked as arithmetic PnL.

## Source, receipt and scope checks

The completed run matches committed source
`b4fc9466196108f83a593396970df65651889914` and gate SHA256
`e5981da6917982c7d845e885ff552963f344a48cab3b67f815edce616a1b629b`.
Every ancestor gate object, financial/helper/runtime source hash and both parent
input hashes matches. Eight complete cells, zero unavailable and one 63,130-byte
output are retained. Output SHA256 is
`1a75f7cc8703aab237498cfa7dcdff26b774dfd610d69a2a101143eed054deef`.
The official structural verifier separately passes.

All six parent raw/schema outcomes and their literal capture clocks reconcile.
Only the fixed batch ticker supplies calculation prices. Its request interval,
September 11, 2026 09:10:26.744354–09:10:27.051204 UTC, is preserved. Neither the
batch nor later depth responses supplies cross-symbol event-clock proof. Optional
depth/time availability does not replace or align ticker prices. Exchange-info
establishes only conditional pair metadata, not account permission or filter
economics.

The resource report records no limit failure, 2.42654 seconds elapsed,
56,909,824-byte sampled peak and 28,864 KiB child `ru_maxrss`, within the declared
policy. External recoverable backup is not independently established by these
local artifacts.

Every case and the top-level output retain unavailable expected-return confidence,
power, market beta, execution frequency and annual economic relevance. Execution
and graduation remain unavailable/false. Full-notional cash is explicitly **not**
a universal wallet-wealth bound with abstention, partial sizing, rounding or idle
residual cash. Factor at or below one excludes positive cycle profit only under
the fixed synchronous-price and assumed-fee model. Actual observations remain
asynchronous and exposed.

## Decision and next action

Close this snapshot's assumed-fee claim as negative. The observed BTC-first
zero-fee discrepancy is explained by the declared fee drag within the model;
it does not establish a repeatable discrepancy or fee applicability to the user.
Do not replay the snapshot, select a friendlier fee or treat the passing size flags
as proof of execution. The original financial result and all eight cases remain.

The mechanism has used two of three new investigations, leaving one; broader
liquidity-search failures and unknown multiplicity are unchanged. Preserve that
allowance for a separately justified finite question about synchronized source
timing, applicable costs and executable opportunity persistence if other evidence
makes it worthwhile. Otherwise advance the next ranked eligible mechanism rather
than collecting unregistered favorable snapshots. No result here establishes
family-wide absence or overall research exhaustion.

Untested: actual fee assets/account rates, lot/dust/notional handling, synchronized
quotes, latency, fills/atomicity, failed-leg inventory and unwind risk, expected
returns, beta and annual opportunity frequency. Zero strategies are validated.
