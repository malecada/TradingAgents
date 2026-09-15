# Independent financial source-policy engineering review

## Disposition

**PASS for the bounded transport/policy helpers after the fixes below.** This is
not admission of a collector, financial recipe, source inventory or live request.
The exact source-specific charter, ownership manifest, gate, resource reservation
and detached execution root remain to be reviewed before execution.

Final reviewed SHA256 values:

- `financial_transport.py`:
  `d18be860cd607e2e0916664ae664acd1fb5eb72913d7b0b8817abb53563e4256`
- `financial_source_policy.py`:
  `de440376850ff321214bcadb5cafa03a360f2d71661f3cddb1c0e64d9d255def`

Only this new review file was written. No network, empirical source/price data,
active F2 root or process, account, wallet or financial experiment was accessed.
All responses, balances of request counters and clocks used below were invented.

## Initial findings and resolution

The initial policy SHA256 was
`641511d74916e5696d63abbce3c2f037b920ee5d76c4cf1a6f4998e90cbcd949`;
transport SHA256 was
`47569156f6135da71895196b4d959ba6d048730b56f31a858cd4525c48047880`.

1. Initial policy lines46–54/101–113 gave transient HTTP503 priority over response
   meaning. Independently injected plaintext `rate limit exceeded`, RPC−32601
   `Method not found`, and certificate-verification text each consumed all three
   sends. This contradicted the no-throttle/no-RPC-error/no-certificate retry
   contract. Final lines61–86/121–127/149–171 check raw text, denial/throttle and
   nontransient RPC errors before selecting a retry. The specific−32011 backend
   outage envelope is the declared exception under transient HTTP502/503/504;
   it is not a successful source result. The reproduced cases now send once;
   throttle/TLS/access cases also stop later logical requests.

2. The initial constructor accepted an empty denial list and weakened throttle
   rules. An invented HTTP429 then allowed a second logical send. Final
   lines39–51 copy the design and require the mandatory five-code denial set,
   fixed throttle policy and positive exact integer reservations. HTTP401 is
   included. Caller mutation cannot erase the stop policy. Fractional or Boolean
   request budgets are rejected before sending.

3. Retry-After was initially discarded. Final transport line62 retains it.
   Policy lines129–145 accept integer seconds or a timezone-qualified HTTP date,
   wait at least that delay up to300seconds, and stop the endpoint for malformed
   or longer values. The delay also applies to the next logical request after a
   successful response. This prevents the fixed15/60second retry schedule from
   disregarding a longer provider instruction. All waits are performed in
   at-most-five-second chunks.

The implementation owner applied the fixes; this reviewer did not modify code.

## Independent checks

The final named policy test file passes12/12. Additional independent injected
checks verified:

- HTTP503 plaintext throttling and TLS failure send once and suppress the next
  logical request; method-error RPC sends once without being treated as a
  successful response; HTTP401 stops the endpoint.
- Failure to persist the first intent causes zero sends. Failure to persist the
  first receipt after a transient response causes one send and immediately
  propagates the persistence error; it does not retry. The first intent and the
  in-memory attempt/raw counters survive that latter case. The future lifecycle
  must close it as partial/uncertain, not claim all receipts were persisted.
- A successful response with Retry-After120 delays the next logical request to
  the120second point, rather than five seconds.
- The header rule accepts timestamp equal to the target or one second earlier;
  it rejects later/earlier clocks, the wrong block height and a zero hash. It
  preserves the explicit false nearest/adjacent-bracket proof flag.

The actual transport was separately exercised with an invented opener/response,
without a socket: complete body, oversized body, timeout after a prefix,
IncompleteRead with additional partial bytes, and premature Content-Length EOF.
The exact retained prefixes and incomplete flags were correct. The connection
timeout was30seconds; proxy configuration was empty; SIGALRM handler and timer
were restored after every case. These tests inspect the real transport control
flow, not only a fake fetcher's expected policy answers.

## Accounting, timing and preservation limits

There are three explicit physical slots per logical key. Successful, failed and
suppressed slots each produce their declared intent/receipt pair in normal
operation. Attempts count sends, including retry sends; raw bytes count retained
body prefixes. Required budget checks precede a send. The scalar/header/code
prefix caps are16,384/262,144/65,536bytes. The outer gate must reserve the complete
method-specific three-slot maximum plus already spent phase resources; unused
slots cannot enlarge the financial/hypothesis grant.

Oversize detection reads one sentinel byte beyond the retained cap. The invented
scalar test read16,385bytes and retained16,384 with an explicit oversize error.
Thus these caps describe **retained raw prefixes**, not exact total network bytes
received. Any future report claiming all received bytes or a strict wire-byte
ceiling must account for that sentinel and transport framing separately. No
oversized prefix qualifies as a complete observation.

The30second request alarm bounds connection and body reading together and is
main-thread Linux behavior. It is not an experiment duration limit. The helper
does not introduce a background process, provider change, proxy, authentication,
redirect follow or hidden RPC batch. Pacing is measured from receipt completion:
at least five seconds for a new request,15/60seconds for the corresponding retry,
or the longer admitted provider delay. There is no guarantee that those delays
are acceptable to a provider; any recognized limit still stops the endpoint.

Durability depends on the supplied publish callback and outer lifecycle. A
storage failure or process termination can leave an intent without a receipt;
such a send is uncertain and remains spent/excluded. The helper must not be
described as guaranteeing completed receipts after arbitrary storage/process
failure. A source-specific collector must retain unattempted denominators and
partial receipts when closing such a failure, without restarting the key.

## Required collector/gate review

The helper rejects inherited or duplicate **literal normalized-JSON keys** for
new sends. This is necessary, but does not prove absence of semantically
equivalent aliases: changing hex/address case, block-tag representation, or
packing a failed field in a new getter vector can change the literal key.
The source-specific ownership manifest must enforce canonical parameters and
exclude previously attempted/uncertain overlapping observations, including
failures. It must separately prove which suppressed keys were never sent and
became eligible for prospective ownership after terminal F2 closure.

This generic helper also does not select or enforce individual contract addresses,
selectors, ABI types, immutable historical block tags or eligible dates. Those
belong in the frozen collector. Its allowed read methods alone do not establish
the scientific scope of an eth_call. Exact registration must forbid unintended
account methods, alternative providers, retry aliases and source backfills.

Single ownership depends on the ordinary run claim and detached fixedHEAD
execution root. This helper is not a cross-process lock or concurrent scheduler.
Do not run multiple owners, mutate an active root's HEAD or infer that importing
an old parser admits an old experiment. Imports were reviewed as definitions;
no old main was run.

The actual-clock model establishes only the selected provider-reported block and
its offset in[target−1second,target]. It does not prove a nearest block, adjacent
canonical bracket, exact midnight execution, executable oracle price or unchanged
protocol behavior. Failed F2 bracketing remains failed. No F2 result is repaired
or recalculated by this review, and no new financial/confirmation budget is
created.
