# Evidence required before terminal accounting can be admitted

This document translates the existing consumers into data requirements. It does not implement an event engine, run a strategy or change a gate. Source inspection is from the preserved reviewed implementation at `a87b67b97cd88ed3bbe83e2dd03eca99a5082d33`.

## Fields and economic meaning

| Required field | Admission condition | Insufficient substitute |
|---|---|---|
| Contract identity | Venue, linear/inverse type, collateral, original identifier and termination event are explicit | Token symbol, spot swap or successor price |
| Terminal timestamp | UTC time and boundary semantics for completed settlement or applicable official scheduled procedure | First missing daily bar |
| Terminal price | Actual settlement record, or historically applicable rule with complete authentic required observations and rounding | Last trade close, estimated-settlement field, final minute close or average of minute closes |
| Settlement fee | Historical fee basis and rate/tier/discount applicability, or a separately registered explicit model with appropriate qualifications | Current VIP schedule assumed unchanged, a quarterly-delivery fee applied to perpetual delisting, or automatic duplicate application of ordinary trading cost |
| Final funding | Event timestamps, realized rate, applicable valuation basis and position existence at each event; any special closure adjustment is explicit | Summing all published daily rates after a mid-day termination |
| Restrictions and ordering | Announced opening/reduce-only restrictions and ordering where orders/funding/closure share a timestamp | Treating an unchanged weight fraction as an unchanged quantity |
| Provenance | Raw response, source URL/parameters, retrieval UTC, content hash and historical applicability evidence | A screenshot or copied number without identifiable event/source |

The price field and its effective time are distinct. A current public endpoint retaining a delisted symbol or a historical price series continuing after cessation does not establish that a position could still be traded or charged funding.

## How the existing books consume these fields

`tradingagents/accounting.py` stores signed notional at the preceding mark and marks fixed units with simple returns between target decisions. Opening trades and fees precede the bar's return. This is not an intrabar settlement interface. A terminated instrument requires explicit final valuation, fee and removal of its quantity, followed by rejection of new positions in that original contract. It cannot be repaired by inserting an ordinary synthetic close into a continuing price series.

The weekly momentum wrapper uses this engine with no supplied funding series. The liquidation-fade registration also explicitly excludes funding and remains qualified on that basis. Recovering a settlement price would not silently convert either construction into an all-in economic backtest. Adding funding would be a separate declared change, rather than an undocumented adjustment to reproduce an old result.

The carry wrapper passes the sum of a UTC day's funding rates to the engine. The engine multiplies that sum by the opening signed notional. That existing approximation cannot represent an exact intraday forced settlement: funding requires the held quantity and applicable valuation at each funding event, and a rate published after closure cannot be charged to a terminated position. An event-aware carry correction therefore requires preserving individual funding records, not just an adjusted daily total. No claim that funding has already been reconstructed exactly is made.

For a USDT-linear position with signed base quantity `q`, preceding mark `P`, and established terminal price `S`, the terminal change in value is `q × (S − P)`. Settlement commission is deducted once under its admitted basis/rate, and quantity becomes zero. Where the applicable funding convention is signed quantity times funding-event mark times rate, its cashflow is `−q × M × f` while the position exists. These expressions specify what evidence is required; no historical value for `S`, `M`, or the fee is supplied by them. Fee rounding, contract multipliers and event-time ordering must follow the admitted historical contract.

Future synthetic verification must cover long/short symmetry; initial and drifted quantities; fee charged once; funding immediately before versus after closure; exact and intrabar boundary events; target-flat transitions without a fictitious exit; restriction periods; successor separation; and complete calendar retention. A verified price alone would not certify every contract lifecycle in the frozen universe, every placebo schedule or the original cohort's subsequent requirements.

## Exact values and bounds

If a historically applicable settlement rule is an arithmetic mean of authenticated second-level index observations, complete observations plus the documented rounding establish a reproducible value. Minute OHLC bars ordinarily do not identify that exact mean.

They can sometimes bound it: if every required observation is proven to belong to a covered minute with low `L_m` and high `H_m`, and the rule uses `n_m` equally weighted observations from that minute, then the mean lies between `sum(n_m × L_m) / sum(n_m)` and `sum(n_m × H_m) / sum(n_m)`, before admitted rounding. This is a conditional mathematical statement. Missing minutes, different observation fields, protection overrides, unknown sampling/weights or unestablished rule applicability prevent admission as a bound on the actual settlement. A midpoint is not an observed settlement price.

A future analysis of outcomes under admissible bounds would require separate preregistration, complete event/cell denominators and a justified treatment of NAV-dependent position sizes and later rebalances. Sharpe is not generally monotone in a single cashflow, so substituting a favorable endpoint does not automatically provide an upper bound on strategy Sharpe. No bounded portfolio inference is performed in this documentary cycle.
