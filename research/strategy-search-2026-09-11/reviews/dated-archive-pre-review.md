# Dated archive pre-result source review

Read-only source/admission review on September 11, 2026. The reviewer did not
implement this collector. Scope: `dated_archive.py`, its charter, synthetic
tests, and the reused `carry_capture.py::public_get` transport. No network,
market archive, quote or empirical outcome was read during this review.

## Finding requiring correction

The validation exception tuple in `dated_archive.capture` does not catch
`zlib.error`. An independently constructed ZIP with a matching SHA256 companion
and invalid deflate block raises `zlib.error: invalid block type` after all
eight raw receipts have been published. The capture then fails before returning
the complete admission denominator. This conflicts with retaining each malformed
archive as an unavailable admission cell. Catch decompression/parser failures
including `zlib.error` and `csv.Error`, with their reasons, and add the matching
synthetic regression before execution. Earlier receipt preservation works.

## Verified scope

- Frozen specification contains exactly four reviewed May/June BTC/ETH dated
  archive URLs and four paired checksum URLs. A changed specification is refused
  before transport.
- SHA256 pairing, exact basename/member, a single member, path exclusion,
  encrypted-member rejection, size and compression-ratio bounds are present.
- The collector reads members in memory and does not extract filesystem paths.
- Twelve-field parsing, exact optional header, millisecond hourly clocks,
  ascending uniqueness, positive ordered OHLC and nonnegative volumes/counts
  match the charter. Zero-volume and zero-trade hours are preserved and counted.
- May requires all 744 hours. June permits a contiguous prefix from June 1,
  preserves missing calendar slots, and explicitly leaves terminal lifetime
  unverified. This is conditional archive admission, not full-month coverage.
- Raw receipts publish before subsequent transport calls. Reviewed production
  transport bounds time/bytes, retains incomplete prefixes, and disables proxy,
  redirect and retry paths. Denial suppression retains all eight cell identities.
- No return, spread or profitability calculation is present.

Verification: `.venv/bin/python -B -m pytest -q
tests/research/test_dated_archive.py` completed with 23 passing synthetic tests
in 0.15 seconds. The separate invented malformed-deflate probe reproduced the
finding above; all eight receipts remained available.

## Resolution and final pre-result verdict

The implementer added explicit `zlib.error` and `csv.Error` handling. Final
collector SHA256 is
`631412c60dd411466db185b3ae2cfb0cc62d5423153c98432e9aa93db86efb3d`.
The 25 synthetic tests pass in 0.15 seconds, including malformed-deflate and CSV
field-limit cases. The reviewer independently repeated the original single-ZIP
deflate corruption: all eight receipts and cells are returned; the malformed
ZIP is unavailable, while its checksum-format cell remains complete. The
original finding above is resolved and retained as review history.

The prepared `gates-dated-archive.json` pins the final collector, transport,
charter and request-spec hashes correctly. Frozen input identity, eight cells
and ten declared outputs agree with source. The dated-basis family retains one
prior measurement and a total cap of four investigations; these are not
independent financial trials. Historical ancestor objects remain in the file.

Verdict: PASS within the reviewed pre-result source/admission scope, with no
unresolved blocker. Final committed-source binding, runtime receipt verification
and independent post-capture raw evidence review remain coordinator
responsibilities. This is not a financial review or economic endorsement.
