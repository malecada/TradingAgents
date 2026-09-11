# Dated-mark source implementation: staged independent review

September11,2026. **PASS for source/schema design; final extension/gate/lifecycle
approval pending.** No historical payload or market endpoint was read. Only
source, tests and invented responses were evaluated; no empirical run or commit
was made. The exact successor lifecycle and final registration remain separate
requirements before acquisition.

Reviewed dated_mark.py SHA256
`2853d70b6f28fd653c96b4c1cd07eb5484e437f6ea61c2c392f966e65f3c1bf9`
and dated_mark_transport.py
`3639602d77274ec829360acd06561c4cadca28d0a07ea693f4e2d55c9fe7569a`.
No material source/schema blocker was identified. The fixed UTC epoch arithmetic
independently resolves to56days fromMay1 00:00 throughJune25 23:59:59.9992026.
ExactlyBTCUSDT_260626 andETHUSDT_260626 daily mark URLs are constructed. There
is no fallback source, symbol, interval, retry, proxy, redirect or financial
calculation. The new transport preserves reviewed ancestor behavior with the
new endpoint allowlist rather than changing frozen constants.

Independent checker `check_dated_mark_synthetic.py` passes22invented scenarios:
exact complete coverage, zero/arbitrary ignored fields, missing/duplicate/extra/
reversed days, fractional/string/Boolean clocks, one-millisecond close error,
zero/nonfinite/out-of-range prices, exact sub-float OHLC range violations,
maximum256KiB valid body, overflow prefix, denial suppression, deep JSON and
large malformed projection. Every run preserves2cells,112fixed daily identities
and4outputs; receipt lengths/hashes and bounded raw prefix bytes reconcile.
The result is recorded in dated-mark-synthetic-review.json. The root's26test
result, including partial HTTP Content-Length handling, is supporting evidence.

Complete individual slots do not imply global source admission: a reversed or
extra-row source may retain56well-formed day slots while its top-level cell
correctly remains unavailable. Duplicate days invalidate that date rather than
select a favored occurrence. Any source needed by a future book must satisfy
its separately registered top-level admission, not merely filter complete rows.
Malformed/oversized normalization remains unavailable with raw receipts retained.
Ignored fields5/7–11 cannot be used as trade-activity filters. Strict JSON still
rejects nonfinite JSON syntax, even inside otherwise ignored positions.

Both bounded raw receipts are persisted before schema parsing; denial, timeout,
cooperative45second capture-budget failure and overflow preserve the unattempted/
unavailable slot. The20second whole-request alarm and120second sampled-RSS guard
are distinct limits; only the exact final guarded target lifecycle can establish
its certificate-verification overhead and maximum-output behavior. Raw and
normalized serialization bounds are separate. No daily mark source can prove
intraday liquidation, real margin brackets, historical account access or fills.

The final independent package/closed-history certificate review, all source/input
pins, exact target gate and maximum-payload real-lifecycle synthetic preflight
remain pending. This source review alone grants no extension or acquisition.

## Exact lifecycle preflight addendum

The three full current-source CLI preflights now pass with the reviewed successor
and unchanged v2 guard. Independent comparison confirms all 19 runtime hashes and
both collector source hashes match the reviewed files. Full, same-host denial
and large-malformed cases each preserve four outputs, two cells and 112 daily
slots. Each actual fake response uses the 256KiB byte bound. The full case retains
large ignored string fields; the malformed case supplies 100,000 invalid rows,
exercising the bounded normalization failure path. The test patches only the
transport with invented responses and executes the actual collector main and
disposable ResearchRun lifecycle.

Actual output totals are 732,977 / 370,946 / 721,973 bytes for full / denial /
malformed. Maximum sampled aggregate RSS is 81,440,768 bytes and maximum elapsed
time 7.418 seconds, under 512MiB and 120 seconds with two CPU affinity slots.
All three guard reports have exit zero and no limit reason. The separate actual
closed-history hash check also passed and is documented in the successor review;
its outputs were not used as financial input or re-evaluated.

The draft gate without a certificate has 12 matching source pins and 19 matching
runtime hashes. Its source/schema/resource contract presents no remaining material
engineering blocker. Final exact target/change-manifest/certificate/approval
bindings are still pending; this addendum does not admit an empirical request.
