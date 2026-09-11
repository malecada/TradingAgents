# Independent raw-capture review — funding-carry inputs

Disposition: **pass conditional source admission**. All ten cells and twelve
outputs reconcile. The captured inputs are sufficient for a separately
registered conditional fixed-base-quantity book, with the limitations below.
No financial statistic or PnL was computed in this review.

Source: `8cac1b361ecc96e5bd6f2ab0fa43bf51b1524ec4`.
The [independent checker](check_capture.py) decodes the original bodies directly,
without importing the collector or accessing the network. The
[machine-readable review](capture-review.json) retains hashes, each cell's
coverage and the checks against source clocks.

## Verified evidence

- The committed registration, request specification, charter, collector source
  and lifecycle hashes agree with the immutable claim and source commit. The
  collector hash equals the version that passed pre-result review.
- Every individual raw-receipt JSON equals its duplicate inside `capture.json`.
  Every base64 body decodes strictly; decoded lengths and SHA256 hashes agree.
  The completion receipt hashes cover exactly twelve declared outputs. The
  official independent receipt verifier also passed.
- Ten distinct registered requests were attempted once and returned HTTP 200
  with complete bodies and no recorded transport errors. All ten cells are
  complete; none is unavailable. Total decoded raw bodies: **1,265,237 bytes**.
- Request URLs, hosts, paths, parameters and fixed start/end boundaries match
  the frozen specification. UTC request/retrieval timestamps are ordered within
  the run, consistent with monotonic elapsed times and source Date headers.
- BTC and ETH each contain **273 funding events**, all uniquely ordered within
  the registered quarter. All rates are finite and all associated event marks
  are positive. The conditional three-per-day schedule has no missing,
  unexpected or duplicate identities; maximum offset from its canonical slots
  is **16 milliseconds** for each asset.
- The six spot/perpetual/mark series each contain **91 complete daily bars**:
  546 bar rows total. UTC opening and closing stamps, finite positive OHLC,
  high/low ordering and cross-series day alignment all pass.
- All **546 funding-event marks** lie inside the same UTC day's mark-bar
  high/low range, using an absolute tolerance of 0.00000001 USDT per asset unit.
  This establishes consistency of the retained observations. It does not make
  daily extrema an independently verified continuous intraday margin path.
- Current exchange metadata identifies one active USDT perpetual each for BTC
  and ETH, with matching base, quote and margin assets. The current server clock
  lies inside the request/retrieval interval: 161 ms after local request time and
  119 ms before local retrieval time, both within the frozen five-second margin.

No material error was found in the captured evidence or its stated conditional
admission result. The earlier review's transport and retention fixes are present
in the executed source.

## Required qualifications before financial registration

1. **Funding boundary ownership must be frozen.** Observed event timestamps can
   trail a canonical midnight by a few milliseconds. A model entering at the
   first daily open must not collect the opening funding event merely because
   its recorded timestamp is slightly later. Excluding that opening canonical
   event is a defensible conservative convention. Freeze exit ownership too.
2. **Cash accounting must use matched base quantities.** Equal entry notionals
   at different spot/perpetual prices do not establish equal base quantities.
   Include spot principal, futures collateral, fees, funding and idle reserves
   in each 1,000/10,000 capital denominator. For a linear USDT perpetual, the
   conditional funding amount uses signed quantity, the associated event mark
   and its rate; a different price basis or daily-average rate changes the amount.
3. **The observed calendar remains conditional.** The three-event schedule
   agrees with these raw observations but has no independent historical rule
   reconstruction. Historical schedule changes and revisions were not tested.
   No missing funding cashflow may silently become zero.
4. **Prices are execution proxies.** Daily spot/perpetual bars do not establish
   synchronized fills, bid/ask, slippage, fee-asset behavior, transfer timing or
   achievable closing prices. Daily mark extrema and sampled funding marks do
   not prove maintenance-margin sufficiency or absence of intraday liquidation.
5. **Historical applicability is unverified.** Current metadata does not prove
   historical fee schedules, spot/perpetual lot limits, maintenance tiers,
   borrow/conversion costs, contract terms or the user's account eligibility.
   Assumed fees, quantity steps and collateral policies must be named assumptions
   in the next charter and output, with unavailable validation claims preserved.
6. **The quarter is exposed development.** Downloading new fields does not make
   the dates fresh confirmation. The capture records when historical data were
   retrieved, not when every field was first published or later revised.

The next justified step is exactly one frozen conditional quantity-book
investigation within the remaining family allowance, with independent cashflow
and convention checks. Positive results could justify further validation work;
they could not establish executable returns or advancement to use by themselves.

Not tested here: upstream authenticity independent of the retained official
endpoint evidence, historical revisions/calendar changes, actual fees or lot
applicability, funding amounts for real positions, executable fills, margin
paths, capital returns, beta or other economic statistics, external backup or
pre-result push timing, and crash/concurrency/maximum-resource fault injection.
No higher effort is needed for the completed raw identity and coverage checks.
