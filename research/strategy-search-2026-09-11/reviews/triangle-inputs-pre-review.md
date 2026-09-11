# Triangle input source pre-review

September 11, 2026. Final disposition: **PASS for the exact source-only gate
and guarded launch below**. No network, real quote or financial
calculation occurred. Only `tests/research/test_triangle_capture.py` was run:
27 synthetic tests passed in 1.65 seconds, including the disposable actual
ResearchRun with six padded 5 MiB invented responses under resource guard v2.
Neither the collector nor its tests were edited by this reviewer.

Reviewed collector SHA256:
`45daa3485959c455b09ea36d793a7e9aed13ce6331206be9957618a2f67fc5dc`;
test SHA256:
`909824b7d4087b563b922a2b3554c86a26befb4967826ae521379ccfd5b13586`.

## Blocking finding

`triangle_capture.py:44` wraps the raw bookTicker body inside
`{"items": ...}` and then selects `items`. This does not prove the raw body is
valid standalone JSON: an invented body containing a valid three-row array
followed by `,"injected":true` fails `json.loads(raw)` but the collector accepts
it as a complete ticker response. The wrapper absorbs the trailing field into
its own root, and the extra key is silently ignored. This violates the frozen
strict-JSON source-admission rule.

Require that the parsed wrapper contain exactly one `items` key, with no other
keys, or use a strict decoder that directly permits an array root and rejects
trailing content. Retain existing duplicate/nonfinite guards. Add a synthetic
regression that makes this cell unavailable and preserves the six-cell capture
denominator; no source fetch or financial run is needed to resolve the issue.

## Otherwise aligned checks

The canonical request hash fixes six URLs and order: exchangeInfo, server time,
three-symbol batch ticker, then BTCUSDT/ETHUSDT/ETHBTC depth20. It rejects mutated
specs before transport. The reused frozen public_get supplies 20-second/5 MiB
request bounds with no retry/auth/proxy/redirect, and same-host denial suppresses
remaining attempts. Receipts preserve exact received prefixes and hashes before
parsing and before the next request. Known failures and recoverable parser
exceptions retain all six identities; the 90-second cooperative budget admits
only requests with 20 seconds remaining. Abrupt failure's partial-output/intended
denominator contract is explicit and does not permit a silent rerun.

The full synthetic lifecycle writes eight real JSON outputs under the reviewed
512 MiB/two-CPU/120-second v2 guard with 30 MiB raw bodies. Encoding uses the
actual lifecycle pretty serializer, including nested normalization allowance,
and enforces the 100 MiB combined output limit. The final execution must use
that pinned guard path; direct collector main alone does not enforce global
RSS/wall bounds. Ordinary source import is not a live request.

Exchange metadata requires exactly three unique symbols, precise base/quote
identities, literal TRADING and boolean true spot permission. Filters/raw rules
are retained while personal access and lot/notional interpretation remain
unavailable. The ticker requires finite positive bid/ask prices and sizes and
uncrossed quotes. Depth requires nonnegative integer update ID, 1–20 levels per
side, positive prices/sizes, strict distinct price ordering and uncrossed best
levels. Server time requires positive integer milliseconds. Raw timestamps and
update IDs are not silently converted into simultaneous observations.

No economics, interpolation, fee deduction, full-book claim or actual fill is
computed here. Quote positivity and structural source completeness cannot
establish executable arbitrage. The later fixed both-directions/two-capitals
bound remains a separate registration; one negative snapshot can close only
that measured conditional proxy, not all future triangles.

## Ancestry and pending gate

`prior_attempts=0` is supportable only as the exact explicitly defined static
three-currency conversion mechanism's known administrative count. Saved evidence
does not establish an earlier exact triangle gate. It must not be described as
zero historical liquidity research or a complete statistical trial count.
OFLOW/passive/fade histories and unknown selection remain inherited. The charter
also charges these new investigations against map row 5's three-investigation
new-work umbrella; keep that aggregate cap visible so a new mechanism label
cannot reset old variants or multiply the allowance silently.

Final gate review must verify the source fix, imported options_metadata helpers,
public transport, guard, runtime/lockfile, charter/spec hashes, six exact cells,
eight outputs and input-definition observation marker. The latter records only
the local static-document observation; future live metadata availability begins
at its actual request/retrieval clocks. No backdated fresh-confirmation label is
admitted. The 22 settlement-dependent cases remain deferred.

## JSON defect resolution

The coordinator's fix requires the strict wrapper's key set to be exactly
`{"items"}` before extracting its array. Trailing injected fields now fail,
while duplicate-key rejection remains inherited from strict_json. The new
six-cell capture regression injects the original malformed raw body; only the
ticker cell becomes unavailable and the other five source cells remain complete.
No valid response is substituted or retried.

Independent rerun: **28 synthetic tests pass in 6.11 seconds**, including the
full padded-body guarded lifecycle. Final reviewed collector SHA256:
`348a4f0f5515359e2f4359c764bbfa37deb81a03605c03c2c374770992d05c3d`;
test SHA256:
`7ada4a46f543c61d27f76b79f46ac26ff27c71cbc1ff1f929d1861d02a85f65c`.
The sole implementation blocker is resolved. Final gate, source-definition
marker, pinned imports/resources and exact cells/outputs remain to be checked
before acquisition. No source request or financial computation was performed.

## Final gate review — PASS

`gates-triangle-inputs.json` SHA256:
`fcf50aa82ba0947d4858945edae0d897b3c927faa89b086a43a05c6819e8560a`.
Charter SHA256:
`c447bf15f50102bc4617aafc535970e7d7bebed4ab073aecb7cd93ea5b538d29`.
Every pinned collector, imported options helper, public transport, guard v2,
definition marker, uv.lock, charter/spec and runtime hash matches actual bytes.
All ancestor experiment/family/dataset objects match `gates-options-eoh.json`
exactly, including its separately registered, unrun EOHSummary child. This
triangle capture has parent null, six exact source cells and eight outputs.

The new family preserves prior_attempts zero solely for the known exact static
conversion mechanism, cap three, and explicitly charges the same new questions
to map row 5's allowance while retaining OFLOW/passive histories and unknown
broader statistical multiplicity. No old family object is reset.

The marked existing-input interval September 11, 08:59:38.166552–08:59:38.166591
UTC is a local observation of request-definition bytes only. It is not a live
quote event, first market availability or confirmatory sample. Actual acquired
responses must retain their later request/retrieval clocks.

The charter describes a possible later optimistic unit-factor/full-notional
proxy, not an upper bound on actual wallet wealth. It preserves both directions,
both capitals, fee scenarios and asynchronous-only qualifications, and requires
a separate registration before any economic calculation. This pre-review admits
only source acquisition under the pinned v2 guard. Source commit/push and remote
equality remain coordinator steps, and post-result source reconstruction remains
necessary. No remaining pre-result blocker was identified.
