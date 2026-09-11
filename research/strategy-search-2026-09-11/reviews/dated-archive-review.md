# Independent dated-archive evidence review

Verdict: PASS for the frozen archive-admission claim. The independently written
`check_dated_archive.py` imports no collector code and makes no network requests.
It decodes each saved receipt, verifies SHA256 companions and ZIP CRC/member
identity, checks exact URLs, schema and hourly clocks with decimal arithmetic,
and compares its reconstructed coverage against the recorded admission.
The retained machine result is `dated-archive-review.json`.

All eight raw receipts agree with the aggregate capture; all eight admission
identities are present. The four expected ZIPs and four checksums reconcile.
Both May archives contain all 744 hourly bars, with no zero-volume hours.
Both June archives contain 609 contiguous hours from June 1 at 00:00 UTC
through the hour opening June 26 at 08:00 UTC. Each June archive has one
zero-volume and zero-trade hour, precisely that final observed hour. All 111
subsequent missing calendar hours per asset remain recorded as an unverified
tail. No internal or leading gaps were found.

## Proposed later window

The fixed hypothetical May 1 opening through June 25 closing window has 1,344
contiguous hourly trade bars per asset, including each daily opening and closing
observation. None of those selected bars has zero volume or zero trades. It
ends before the observed final zero-volume bar and the missing calendar tail.
This supports conditional historical trade-price input admission for a later
registered development question. It does not prove executable opening/closing
fills, historical bid/ask spreads, mark-price margin survival or exact contract
expiry. The last observed timestamp must not be promoted to legal expiry proof.

Matched spot inputs, historical execution and fee assumptions, instrument lot
limits, collateral and account applicability require their own admission. In
particular, hourly traded high/low prices are not established margin marks.
A later book may be a qualified trade-bar scenario while those fields remain
unavailable; it cannot claim complete executable economics or pathwise survival.
May/June history remains exposed development, never fresh confirmation.

Verification command: `.venv/bin/python -B
research/strategy-search-2026-09-11/reviews/check_dated_archive.py`.
Result: PASS, eight receipts and eight admission cells, no financial computation.
Source commit/remote equality is outside this evidence review; the coordinator
reported execution source `69c844c30e57d4d3ba6aa065eeff54cabf65652e`.
