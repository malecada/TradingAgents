# Decision 10 — static triangle discrepancy is erased by assumed fees

The frozen eight-case calculation completed once as triangle-proxy-20260911 from
b4fc9466196108f83a593396970df65651889914, pushed and remotely verified before
execution. Eight complete cells, zero unavailable, one immutable 63,130-byte
output; receipt verification passes. The independent cashflow reconstruction is
retained in reviews/triangle-proxy-review.md and its JSON report. Execution took
2.427 seconds with sampled peak tree RSS 56,909,824 bytes, within frozen bounds.

| Cycle | Initial USDT | Zero-fee cash proxy | With 0.1% received-asset fee on each leg |
|---|---:|---:|---:|
| USDT→BTC→ETH→USDT | 1,000 | +0.16037690 | −2.83710475 |
| USDT→BTC→ETH→USDT | 10,000 | +1.60376897 | −28.37104752 |
| USDT→ETH→BTC→USDT | 1,000 | −0.47687302 | −3.47244483 |
| USDT→ETH→BTC→USDT | 10,000 | −4.76873017 | −34.72444828 |

These are forced continuous full-notional static proxies, not filled-order PnL.
Both zero-fee and fee cases are retained; capital scales are correlated algebra,
not additional samples. All eight displayed-best-size flags pass. Three-fee
terminal-USDT equivalents for the 1,000 cases are 2.99748165 and 2.99557181;
fee accounting and signed currency wallets reconcile. No opportunity cost or
cash benchmark is deducted. The invalid log-factor PnL shadow stays forensic.

## Diagnosis and next action

One direction has a very small positive gross unit factor, while its reverse is
already negative. Under the frozen fee assumption both are negative. Fees erase
the modeled discrepancy before impact, latency, rounding or leg-failure costs
are considered. Displayed quantity is not the binding condition in this model;
actual simultaneous liquidity and fills remain unavailable. The observation may
reflect asynchronous quote updates rather than a tradable discrepancy.

This snapshot cannot establish expected profit, opportunity frequency, beta,
drawdown, power or annual economic relevance. These remain explicitly unavailable.
The full capital can become directional BTC/ETH inventory between idealized legs.
No universal wealth upper bound with abstention/partial sizing is claimed. No
strategy graduates, and this is not proof that every future triangle is negative.

Do not choose a lower fee, another snapshot or a maker fill model to rescue this
result. A further triangle investigation would require a separately justified
finite synchronization/execution design with realistic fee eligibility and
partial-fill risk. The present information value favors switching to the
already identified Binance–Bitrue metadata/history prerequisites rather than
using the third triangle allowance immediately. Two of three new triangle
investigations are now used, also charged to MAP row 5; old liquidity-search
history remains. Options semantic deferral and prior carry/dated verdicts remain
unchanged. Update the map, freeze the Bitrue metadata probe after synthetic and
independent review, and continue broader eligible mechanism work. The research
program remains active/incomplete, with zero validated strategies.
