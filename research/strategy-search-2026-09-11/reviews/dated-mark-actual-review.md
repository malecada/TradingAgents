# Dated daily marks: independent actual source review

September 11, 2026. **PASS for the registered source question.** Independent
reconstruction starts from each saved base64 response, without importing the
collector, transport or any financial implementation. No network request,
experiment rerun, ledger mutation or financial calculation was performed.
Executable evidence is in check_dated_mark_actual.py and its JSON report.

Both BTCUSDT_260626 and ETHUSDT_260626 responses contain exactly 56 unique,
ascending daily rows from May 1 00:00 through June 25 23:59:59.999 UTC, 2026.
All 112 rows have exactly 12 fields, integral expected open/close milliseconds,
bounded finite positive decimal OHLC literals and consistent high/low ranges.
No missing, duplicate, unexpected or malformed row was found. Every reconstructed
slot, row index and literal price matches the saved normalized admission. The
two source cells and all 112 subordinate slots are complete.

Raw BTC and ETH bodies are 6,945 and 6,721 bytes, respectively, with SHA256
`c4a69b60ed295673f431f47bbb0ce9bcc343d2e8160c464dab40265fb0dc95d4`
and `a43fd0b6206f1ce47780c44256eb89507f5a28c772d2aad29bf6f97c30ef1409`.
Both retained receipts report attempted, complete HTTP 200 responses to the exact
fixed symbol/interval/window/limit URLs. Raw hashes, lengths, receipt-reference
hashes, input specification, four output hashes and terminal denominators match.
Total raw bytes are 13,666; total output bytes are 57,348, below the 4MiB cap.

Fields 5, 7, 9, 10 and 11 are the literal string "0" in every row. Field 8 is
an integer in every row. These fields retain their registered ignored status;
neither zero values nor nonzero integer values establish trading activity or
intraday completeness. Only the declared daily mark schema is admitted.

The BTC request/retrieval interval is 11:15:53.439386–11:15:53.762306 UTC and
ETH is 11:15:58.256047–11:15:58.556060 UTC on September 11. Requests are sequential,
their local elapsed durations reconcile, and both precede capture closure at
11:16:02.984653 UTC and terminal completion. Historical row clocks remain
distinct from current observation times. Source commit
`5cf5dd843131da489a4695623b81009a244ab49f`, its gate hash, source pins and retained
working-tree bytes reconcile. Remote equality before execution is the
coordinator's recorded operational evidence; this review did not access the
network to independently repeat that check.

The unchanged resource guard reports exit zero, no limit reason, 32.694867 seconds
elapsed and 67,661,824 bytes peak sampled aggregate RSS. This is within its
120-second and 512MiB limits; sampling qualifications remain unchanged. A short
HTTP request duration is not the full lifecycle duration.

The new independent verifier reconstructs the current certificate and all live
same-mechanism predecessors. The original family still records cap4/prior1.
Five visible program claims plus historical1 now consume effective6, including
both preserved failed attempts. The exact source-only extension is consumed and
provides no remaining grant. The completed v1 repair separately passes the
closed-inventory historical verifier. Calling the frozen v1 live-ledger verifier
now fails with the expected reason, "amendment inventory or original budget
differs". That refusal is retained and disclosed rather than patched or reported
as a frozen-verifier pass. Current and historical verification have different
inventory boundaries.

The missing daily valuation input is now available for the two fixed symbols
and window. This supports preparing a separately specified long-dated/short-
perpetual accounting question. It does not authorize a financial run, another
extension, an inverse direction, parameter selection or confirmation. A further
information-value decision must explicitly weigh that narrow question against
remaining affordable alternatives and preserve its algebraic relationship to
the already inspected spot books. Daily marks do not establish actual account
access, margin brackets, intraday liquidation, historical costs, fills or positive
expected returns. None of those claims was tested here.
