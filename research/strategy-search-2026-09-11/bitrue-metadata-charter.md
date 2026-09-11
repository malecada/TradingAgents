# Bitrue contract metadata prerequisite

Experiment bitrue-metadata-20260911. New venue-segmentation family mechanism:
opposite matched-underlying USDT perpetual legs across Binance and Bitrue might
receive different funding because demand and balance sheets are segmented.
This is a source-admission question, not a funding-profit test. Prior exact
cross-venue registered gates are not established; existing funding-carry and
cross-sectional/venue histories, including failed cases and unknown broader
multiplicity, remain in HISTORY.md. An initial maximum of three new questions
is an administrative cap, not independent-trial accounting. Do not reset an
existing carry strategy under this name or count current metadata as alpha.

## Documentation-version conflict and fixed choice

The older HTML describes an all-contracts array. The official v2 document at
https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/v2/PublicControllerApi.md
shows an unfiltered GET example and array response but marks contractName as a
required query parameter. This conflict is unresolved. The fixed request tests
the unfiltered example's present source availability, without presuming success.
An error, missing array or ambiguity remains unavailable; no symbol-specific
fallback is permitted. The result can narrow this exact request/version route,
not prove that Bitrue lacks the relevant contracts. Source-review denominator
and limits are in reviews/bitrue-funding-history-source.md.

## Fixed source question

Do the two exact public Bitrue contracts/time endpoints provide bounded,
well-formed literal metadata sufficient to identify conditional BTC/ETH USDT
forward perpetual contract units? The contracts documentation explains type E,
side 1, status 1 and a contract multiplier, but actual returned values have not
been admitted. The time documentation gives an arbitrary object, not a verified
clock-field schema. Preserve it literally; do not guess units from a field name.

Freeze bitrue-request-spec.json: exactly GET https://fapi.bitrue.com/fapi/v1/contracts
and GET https://fapi.bitrue.com/fapi/v1/time, once each. No credentials, index/rate/
price endpoints, retry, redirect, proxy, fallback host or account call. All source
rows and response bytes retained, including ambiguity and failed cells.

Contracts must be a strict standalone JSON array of objects, unique literal
symbol identifiers and documented field types where normalized. Preserve all
rows in the raw source and conservative metadata representation. Conditional
BTC/ETH target matching requires exact E-BTC-USDT/E-ETH-USDT names, type E,
numeric side/status 1 and matching BTC/ETH multiplierCoin, with positive finite
multiplier/minimum-volume and nonnegative valid minimum-money fields. Unknown
names/identity/unit combinations remain ambiguous, not silently inferred.
The identity test only concerns the naming/unit convention documented by this
source; it does not prove tradability, account eligibility, quote-asset cashflow
rules, margin requirements or historical contract continuity. Time requires a
strict literal object; clock semantics remain unavailable.

The saved Binance futures exchange-info receipt from carry-inputs-20260911 may
be independently compared for literal current contract asset/type/filter fields
at its original timestamp, with no new Binance acquisition and no synchronization
claim. This comparison never substitutes current rules for historical ones or
computes a funding/price differential. Capture output concerns Bitrue only;
any later numerical cross-venue book needs separately bound/admitted inputs.

## Denominator, limits and outcome handling

Two source cells: bitrue-contracts and bitrue-server-time. Four outputs: individual
source receipts, metadata-capture.json and metadata-admission.json. Both raw
receipts are saved immediately before parsing and subsequent requests. Each
response has a 20-second timeout and 5 MiB cap; raw total 10 MiB. Actual pretty
serialized normalized admission ≤10 MiB and total outputs ≤40 MiB. Cooperative
capture budget 60 seconds, only start a request if its 20-second allowance fits;
hard 120 seconds, two CPUs and 512 MiB sampled aggregate RSS under frozen v2
guard. No claims of strict instantaneous RSS enforcement. Synthetic maximum
payload/lifecycle and hostile JSON/type cases precede freeze and execution.

Denial suppresses later same-host requests, retained as unavailable. Body
prefixes and source errors remain explicit. Parse/schema/integrity failures
stay unavailable; a successful HTTP code is insufficient. Abrupt process failure
retains a failed claim and partial outputs, consumes the attempt and is not retried.
No financial parameter tuning, statistical test, expected-return CI, power,
beta, annual relevance or graduation can be evaluated from this metadata.

A conditional BTC/ETH identity/unit match justifies further source admission
of settled funding cashflows/marks, applicable fees and margin conventions. It
does not by itself justify a historical profit book. Absent/mismatched targets
narrow this exact product route; do not silently swap contracts. An unresolved
history dependency defers historical venue economics and invites comparison
with other affordable mechanisms or a separately frozen prospective source
question. Record a decision, independent raw/source review, structural receipt
verification and verified remote results backup, then continue the program.
