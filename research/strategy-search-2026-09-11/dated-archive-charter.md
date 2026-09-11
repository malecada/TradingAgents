# Dated-contract archive admission

Experiment `dated-archive-20260911`. New investigation within the existing
dated-basis mechanism, following the fixed funding-carry diagnosis into the
next ranked family. No financial return or quote economics is computed here.
The prior September10 dated capture remains one negative measurement with
432 correlated terminal scenarios; no repeated current quote search. Initial
new allowance three investigations plus that prior measurement; variants and
follow-ups inherit it.

Question: do the official listed June2026 BTC/ETH USDT dated-contract archives
contain usable internally complete hourly observations and verifiable checksums
for a later historical basis/convergence question? Directory existence alone
does not establish data quality or profitability. Competing explanation: archives
are malformed, incomplete, mismatched or missing the needed lifetime boundary.

## Frozen source and denominator

Official directory metadata was inspected September11,2026 without downloading
price bodies. Both `BTCUSDT_260626` and `ETHUSDT_260626` have listed monthly1h
May/June2026 ZIPs and96-byte checksum objects. Listed ZIP byte counts:
31,906/26,843 for BTC May/June;32,688/27,378 for ETH. These are catalogue
observations, not source-integrity guarantees or size-selection criteria.
Daily file names span December26,2025 through June26,2026; exact listing/expiry
UTC hour remains unverified. LastModified describes the currently served version,
not guaranteed original publication.

Exactly four ZIPs and four paired CHECKSUMs, from:
`https://data.binance.vision/data/futures/um/monthly/klines/SYMBOL/1h/SYMBOL-1h-2026-MM.zip`
and identical URL plus`.CHECKSUM`, where SYMBOL and MM are precisely the two
symbols and05/06. Eight cells use `btc-2026-05-zip`, `btc-2026-05-checksum`, etc.
Committed request-spec is the sole input. Existing window:
[2026-05-01T00:00:00Z,2026-07-01T00:00:00Z). Conservatively exposed development;
underlying spot/perp history is spent and directory inspection is recorded.
No claim that a new archive field restores freshness.

Use the already reviewed public transport with one20-second request per cell,
no retries/auth/proxies/redirect/fallback. Same-host403/418/429/451 suppresses
remaining calls with unavailable receipts. Each response is published before
the next request. Max5MiB body per request,40MiB aggregate acquired raw bytes,
150MiB duplicate/base64 output allowance,300seconds,256MiB memory,one CPU.
Retain eight raw receipts plus archive-capture.json/archive-admission.json.
No archive is extracted to the filesystem and no original store is altered.

## Exact admission

Verify companion SHA256 and expected ZIP basename. A ZIP must contain exactly
one member named the same stem plus`.csv`; reject extra members/path traversal,
uncompressed size over2MiB or compression ratio over100. Twelve CSV fields,
with either no header or exactly the frozen standard header:
`open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore`.
An unknown header is unavailable, never silently adapted after observation.

Require hourly millisecond open times, unique and ascending in the named month,
closeTime=openTime+3,600,000-1, positive finite OHLC with valid ordering; volume,
quote volume, taker volumes and trade counts nonnegative and finite. Trade
counts must be integral. Retain zero-volume bars and report their count; their
presence does not establish executability. No returns, spreads or PnL calculation.

May must contain all744calendar hours. June has720calendar hours in the complete
month, but this expiring instrument is not expected to trade through all of
them. Preserve every missing calendar slot; distinguish an observed contiguous
prefix and missing tail from internal missing hours. Do not fill the tail or
call it complete-month coverage. Conditional June archive admission permits a
contiguous prefix beginning June1; exact terminal lifetime/settlement admission
remains unavailable regardless of how plausible the last timestamp looks.
Any checksum/schema/internal-clock error or incomplete May is unavailable.
All eight request/admission cells and failed reasons remain in the denominator.

This is deterministic data admission. Economic relevance, BTC/ETH beta, capital
feasibility, costs, confidence/power and convention-swap PnL are not measured.
No p-value or profitability judgment applies. Independent review decodes raw
bytes, verifies checksums/member/schema/clock and reconciles every cell without
importing the collector. Synthetic corruption, truncated bodies, ZIP boundaries,
clock gaps, zero-volume bars and denial tests precede source/gate commitment.

## Decision

Usable May observations can justify one fixed, separately registered historical
basis question with matched spot inputs and fees, even if exact expiry settlement
remains unknown. Any holding period must avoid an unestablished terminal event
or admit it independently. June tail unavailability must never be hidden in an
outcome. Unavailable archive fields get a precise dependency and no replacement
fetch. Re-rank options/public triangles/relative-value alternatives afterward;
no broad data collector, paid source, repeat quote refresh or familywide
no-opportunity claim follows from this bounded result.
