# Triangle stream actual independent review

September11,2026. **Measurement defect; retained arithmetic/source receipts otherwise reconcile.**
Independent checker `check_triangle_stream_actual.py` imports neither the stream
collector, replay, wallet helper nor statistics implementation. It reconstructs
all retained quotes and currency flows from literal raw payloads with Fraction
arithmetic. No network, rerun, output/gate/ledger mutation or new selection occurred.

## Material finding: delayed termination clock admits unsupported bins

`triangle_stream.py:182` records exception-handling elapsed time after the last
chunk flush; `:304` uses that clock as the replay cutoff. The first dropped
inbound frame was already observed at407.778372831seconds. Its137-byte payload
is retained only as digest `4b26928dfa16cb107dbac91c31d102749f0862b5d52294ada39d244ea45c23ff`.
The source recorded termination at408.441994777seconds,0.663621946seconds later.
Consequently the407.8,407.9,408.0 and408.1second grid points retained admitted
quotes after an unknown omitted update. These are32unsupported bin/case subslots.
The next three grid points were already unavailable as stale, but their source
history is likewise incomplete. The dropped payload's symbol cannot be recovered
from its digest, so all three quote states must lose evidential support from
the earliest dropped arrival.

The immutable registered result remains2,357calculable/3,043unavailable bins per
case. A conservative **forensic source-support audit**, not a replacement run,
leaves2,353supportable/3,047unavailable bins per case:18,824/24,376of43,200subslots.
All four affected admitted points were unqualified in every case. Exact positive
counts and longest qualifying streaks are unchanged; only the quote-admitted
frequency denominator changes. The original denominator and this qualification
must both accompany claims. A future version should distinguish earliest source
loss from later socket/finalization time and test a slow last-chunk flush. Do
not patch this frozen run or consume an unregistered replacement attempt.

## What the preserved observation supports

No10bp-per-acquired-asset case has a positive exact factor on the2,353supported
bins, even before visible-size screening. Maximum gross discrepancies are about
1.7616bp for BTC-first and0.4658bp for ETH-first, while the assumed three-leg
fees reduce the best supported factors to0.9971786275 and0.9970494395 respectively.
These are conditional synchronous-price-model factors on asynchronous locally
aged quotes, not realized returns or executable opportunities.

| Direction/capital | Zero-fee qualified bins | Longest sampled streak |10bp qualified bins |
|---|---:|---:|---:|
| BTC-first /1,000 |355|60bins,5.9s sampled span|0|
| BTC-first /10,000 |296|42bins,4.1s sampled span|0|
| ETH-first /1,000 |41|29bins,2.8s sampled span|0|
| ETH-first /10,000 |21|17bins,1.6s sampled span|0|

The full planned denominator remains5,400per case. Zero-fee positive factors
occurred in373BTC-first and41ETH-first supported states; visible quantity reduced
some qualification counts, especially at10,000. These counts are overlapping
sampled states, never summed trade profits. Streak span does not prove continuous
exchange availability or execution latency. Absence at the assumed fee does not
establish timeless absence, actual commission rates or a family-wide theorem.

## Receipt, timing and resource reconstruction

The32chunk cap bound first, before the20MiB payload or100,000frame limits.
There are41,536receipts:41,494complete text updates,20inbound pings,20outbound
control receipts and two handshake receipts. Updates per asset are24,133BTCUSDT,
16,052ETHUSDT and1,309ETHBTC. All raw lengths/hashes, unique contiguous receipt
sequences, nondecreasing monotonic arrival and UTC receipt clocks reconcile.
No actual duplicate/regression/conflict/malformed/shutdown was encountered;
27,477nonconsecutive ID jumps are not interpreted as missing messages.

Raw payload is6,037,633bytes; serialized raw chunks occupy22,218,107bytes, each
at most944,474bytes. Periodic30second flushes and conservative per-record size
accounting consume immutable chunk slots before their theoretical aggregate
capacity. All35outputs total30,528,519bytes, below64MiB. The first text arrives
at1.284200935s; the final retained text at407.776409399s. The registered reason
counts per case are20missing,1,707stale,1,316resource-tail and2,357calculable.
Under earliest-source-loss accounting, three stale points move to the tail in
addition to the four invalidated calculable points; no missing tail is dropped.

All20recorded pongs echo their paired ping payload; maximum recorded local
arrival-to-outgoing-receipt lag is0.000412283s. This verifies recorded protocol
handling, not server receipt or network latency. UTC creation time may lag a
frame's monotonic arrival by up to0.76157s during persistence; the replay uses
arrival clocks, not later receipt creation time. The approximately−3.2microsecond
minimum UTC/monotonic offset is consistent with separate clock reads and does
not reverse either recorded ordering. No exchange timestamp is inferred.

The retained allowed handshake-line/body bytes verify independently. The full
header-block hash cannot be independently recomputed because unallowlisted
header bytes were deliberately not retained; this remains a stated limitation.
The failed137-byte frame and a65,536-byte diagnostic have hashes only, not
reconstructible content. No unknown payload is guessed or promoted to evidence.

Source commit `71234f87d4221e8849f130dfb3e62824d700f0df`, gate
`ce6e02d9f789fac3cb289fa6371327c6d7403975ec1b32001ec27bd60be652cd`, all registered
source/input hashes, original metadata identity/schema and35output hashes
reconcile. Independent lifecycle structural verification passes9cells, with
transport unavailable and eight structurally complete series. Scientific timing
qualification above is additional to that structural check.

The600second/512MiB sampled guard exits0 after416.3385s, peak115,523,584bytes RSS.
It reports no resource-monitor rejection; the earlier stop is the collector's
registered chunk limit. Independent reconstruction makes299,403numeric checks,
maximum absolute difference4.77e-12, covering gross/net/simple/log-shadow/fees,
three exact sizes, quote ages/IDs and all case summaries. None of this converts
a source screen into a profitable strategy.

## Disposition and next justified work

Preserve this measurement defect, all original results and the conservative
support qualification. The fee-negative necessary-condition conclusion holds
on supported evidence; completing the missing minutes is not needed to claim
anything stronger. The third triangle allowance is spent. No repeat, cap increase
or new venue follows from this review. The already specified options entry
prerequisite is a distinct remaining bounded question. Expected profit, power,
confidence intervals, beta, annual relevance, fills, account access and strategy
graduation remain untested/unavailable. Zero validated strategies remains true.
