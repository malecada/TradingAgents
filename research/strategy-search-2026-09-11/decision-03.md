# Decision 03 — fixed quantity carry economics

Completed once as `carry-book-20260911`, using committed/pushed source
`7d704ca97606eea4ab953c29d7587e7e8af517f1`. All eight primary books and eight
zero-funding forensic books are retained: 16 complete cells, zero unavailable.
Independent reconstruction checks 1,456 daily NAV snapshots and 35,072 numeric
values, with maximum absolute discrepancy 2.91e-11. Raw/source/gate hashes and
the independent lifecycle verifier pass.

Every primary case has negative modeled cash profit in the fixed 91-day quarter.
No opportunity-cost benchmark is deducted in these amounts.

| Asset | Initial capital (USDT) | Base-cost cash profit | Doubled-cost cash profit | Conditional economic screen |
|---|---:|---:|---:|---|
| BTC | 1,000 | -0.4754 | -1.6808 | Fail |
| BTC | 10,000 | -5.5146 | -19.4976 | Fail |
| ETH | 1,000 | -0.5792 | -1.8367 | Fail |
| ETH | 10,000 | -6.0816 | -19.2857 | Fail |

The fixed relevance requirement and positive exploratory confidence lower bound
fail in all eight cases. Other conditional beta, drawdown, matched-base and
reserve/stress screens pass within the model. This separates a thin economic
mechanism from unwanted broad crypto-price exposure in this measured quarter.
It does not establish actual exchange margin safety or execution feasibility.

## Why the result is negative

At 1,000 capital under base costs, BTC receives 0.84893 in recorded funding,
loses 0.11890 from the raw price-basis change, pays 0.95167 in modeled fees and
loses 0.25376 to assumed slippage. ETH receives 0.75210, loses 0.07380 to basis,
pays 0.99278 in fees and loses 0.26472 to slippage. Fees alone exceed funding
after the basis movement. Larger capital changes lot rounding but does not
reverse these proportional negative economics. There is no basis for a
parameter or fee-discount search around this fixed quarter.

Uncertainty does not support a positive expected cash-mean claim: every interval
crosses zero. The block-bootstrap and HAC estimates are descriptive on spent
history; endpoint fee resampling, nonstationarity, finite tails and unknown
previous search multiplicity prevent fresh-confirmation interpretation. Small
possible effects are not disproved, and one quarter cannot represent all future
funding regimes. These findings neither relabel the original holdout NO-GO nor
prove every form of funding carry unprofitable.

Actual account/entity permission, historical lots/minimum notionals, commissions
and fee assets, funding-calendar proof, simultaneous fills, intraday liquidation
and stablecoin/counterparty risks remain unverified. Fees and slippage are
explicit scenarios; public bars are not fills. Positive synthetic cash examples
and a complete receipt are not strategy validation.

## Learning and next action

The definition diagnostic was worth resolving, but a correctly denominated
quantity book with actual event marks still finds insufficient economics for
this frozen quarter. The first three new investigations in the funding-carry
allowance are used. Do not create cosmetic variants or refresh the sample under
a new family name. A future extension needs evidence of a distinct information
gain, preserves all previous attempts, and cannot become old-sample confirmation.

Switch to the next ranked eligible mechanism: admit the four officially listed
May/June archives for BTCUSDT_260626 and ETHUSDT_260626, with eight one-shot
ZIP/checksum requests. This asks whether historical dated-basis work is possible,
not whether a new current quote happens to be positive. Exact expiry settlement
stays unknown; no terminal tail is filled. Options and public spot triangles
remain independent source-feasibility alternatives. The program is active and
incomplete; zero strategies validated.
