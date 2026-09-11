# Funding-carry input admission — frozen contract

Experiment `carry-inputs-20260911`, child of `carry-definition-20260911` within
the same funding-carry family. Development/exploratory data measurement, no PnL
or financial trial. Second of at most three new investigations in this family's
initial allowance. Earlier search remains known-incomplete; no reset or fresh
confirmation. The first diagnostic separated opportunity cost from a legacy
index but established no cash book. Local funding caches omit event marks.

Question: can a single bounded public acquisition supply authentic funding-event
marks plus matched spot/perpetual/mark daily bars for a fixed existing quarter?
Prediction: the documented fields and complete overlapping clock exist for both
majors. Competing explanation: fields, endpoints or event/bar coverage are
unavailable. Failure means unavailable measurement, not negative economics.

## Inputs and fixed scope

Use only the exact committed request-spec JSON. BTCUSDT and ETHUSDT are fixed
by earlier carry ancestry, never by outcomes. Historical interval:
[2026-04-01T00:00:00Z,2026-07-01T00:00:00Z), the last complete quarter within
the spent old holdout. It is exposed development, even if a field is newly
downloaded. No historical configuration tuning or fresh return claim.

Ten cells, with one attempted request each unless a prior host denial suppresses
it: `btc-funding`, `eth-funding`, `btc-spot`, `eth-spot`, `btc-perp`, `eth-perp`,
`btc-mark`, `eth-mark`, `exchange-info`, `server-time`. Funding requests use
`/fapi/v1/fundingRate`; bar requests use REST `klines` or `markPriceKlines`,
interval1d, limit1000, fixed start and inclusive end = registered end minus1ms.
Current exchangeInfo/time qualify identity/clocks only, not historical terms.

Allowed public hosts: `api.binance.com` spot klines and `fapi.binance.com` named
futures market endpoints only. No credentials, auth, proxy fallback, redirect,
alternate domain, repeat query, replacement window or paid source. HTTP
403/418/429/451 stops remaining requests to that host; all suppressed cells
remain unavailable. Twenty-second hard per-request deadline, max ten requests,
5MiB per response, max50MiB bodies, total300seconds, one CPU,256MiB memory.
No market requests may occur before committed source/gate and pushed freeze.

Retain each response immediately in its declared immutable `<cell>-receipt.json`
before attempting the next request or parsing its payload. Retain exact raw bytes
as base64 there and in aggregate capture.json, SHA256, request URL,
parameters, UTC request/retrieval times, status, error and allowlisted Date and
Content-Type headers. Truncation/timeouts remain explicit. No retries. The
capture will be committed and pushed in full, not merely its manifest. The
12 declared outputs include ten raw receipts plus capture.json/admission.json.
Maximum on-disk output allowance150MiB accounts for duplicated base64 bodies;
maximum acquired raw bytes remains50MiB. Earlier receipts survive later failures.

## Semantic admission and interpretation

Funding: correct symbol, ascending unique timestamps within window, finite rate,
positive associated mark. Check three events/day at00/08/16UTC with at most
five-second timestamp tolerance; compare expected/observed/missing/unexpected
identities. This is an explicit conditional calendar diagnostic, not independent
proof of historical funding schedule or unannounced adjustment. No zero fill,
mark interpolation, rate-only substitution or omitted unavailability.

Bars:91 complete unique ascending UTC daily open timestamps in REST milliseconds,
end-of-day close timestamp, finite positive OHLC and low<=open/close<=high.
Reject silent millisecond/microsecond conversions. Current exchange metadata
must identify the two conventional USDT perpetuals; current terms do not prove
historical terms or the user's account eligibility. Current server clock must
be plausible against retrieval metadata; discrepancies remain explicit.

Each failed source/admission cell remains unavailable with reason. A complete
lifecycle receipt certifies a fully recorded measurement, not an admitted
strategy. All sources must be independently reconstructed/checked before any
derived cashflow test. Coverage alone never establishes executable prices.

No numerical economic, beta, risk, significance, power or cash benchmark result
is computed in this run. Their values are unavailable, not zero. Funding sign
is retained as source data only. No convention swap applies to a non-PnL source
admission; a subsequent financial charter must supply cashflow convention
forensics, nulls, stress/costs and capital/risk measures before outcomes.

## Decision and continuation

If both symbols' sources are admissible, register exactly one fixed conditional
quantity-book development investigation within the remaining family allowance.
Daily bars remain execution proxies and intraday margin cannot be validated by
them. Actual account/lot/fee evidence and genuine future confirmation remain
later prerequisites. A funding schedule mismatch or absent fields must be
diagnosed before any PnL; no automatic schedule relaxation or refetch.

If core sources are unavailable, defer this cash-book route with exact missing
fields/host status and switch to the next highest-value eligible family. A
denial is not proof that the venue is unavailable to the user. Continue
independent dated/calendar/options/source work while account details are pending.
Independent reviewer checks raw hashes/clock/schema/denominator and absence of
economic inference; source code synthetic tests include denial suppression,
malformed/missing/duplicate fields and truncated bodies.
