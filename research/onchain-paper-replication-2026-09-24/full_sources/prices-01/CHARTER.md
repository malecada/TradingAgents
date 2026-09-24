# Frozen Yahoo daily price source capture

Two distinct source claims acquire BTC-USD and ETH-USD unadjusted daily Close
under the already frozen calendar. Each asset uses one public HTTPS chart
request covering 2016-01-01 through 2025-01-01 exclusive, with a 30-second
timeout, 8 MiB response limit, no redirect, proxy, credentials or retry.
No alternate provider or adjusted price field is substituted. HTTP denial,
malformed schema, missing bars and null closes remain explicit unavailable
cells. Every one of the 3,288 calendar dates per asset is retained alongside
the capture cell. Bar timestamps must be integer UTC midnights; USD instrument,
UTC exchange timezone, explicit daily response granularity, unique quote/result arrays and positive finite numeric
Close values are validated. The exact retained response byte buffer is hashed and parsed. Missing dates are never filled.

The raw request intent, response bytes, selected headers, UTC capture times,
hashes, daily dispositions and parsed panel are immutable. Current retrospective
provider vintage is explicitly qualified: original publication availability is
assumed rather than verified. Source acquisition does not admit a predictive fit
or shrink the registered financial comparison population. Sample history remains
exploratory, including previously spent ETH2022–2024 windows.

The cumulative ceiling stays 51: 17 preserved historical claims and 34 new claims.
The reviewed successor allocation retains two resource pilots, 17 source claims
(one metadata, fourteen missing-body batches and these two price batches), one
initial ETH experiment and fourteen remaining asset-fold claims. These captures
consume the two existing price allocations; no retry or additional lane is added.
All 88,776 source-field cells and 1,420 unique predictive fits remain in scope.

Run assets sequentially only after independent registration review, a committed
gate, live admission and resource preflight. Each has a separate exclusive
owner, nonce, monitor, cgroup, guard directory and experiment identity. Bounds:
512 MiB memory maximum, 384 MiB high watermark, zero swap, two CPUs, 3 GiB host
reserve, 3.5 GiB startup availability, 20 GiB free-disk floor and 300-second wall
limit. Outer supervision proves cgroup death and retains every missing cell
before failure closure. A terminal or claimed identity is never relaunched.
No transaction pages, fitting, provider contact, paid resources or trading occur.
