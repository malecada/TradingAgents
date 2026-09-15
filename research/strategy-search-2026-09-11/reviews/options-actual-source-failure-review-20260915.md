# Independent actual options source failure and closure review

September 15, 2026. **Approve failure-only closure of
`options-episode-20260911` after binding the independently reviewed external
quiescence evidence.** All eight registered cells are unavailable because entry
source admission failed. No financial analysis intent, economic output,
performance evaluation, replacement entry or replacement claim is justified.
The effective fifth options allowance is consumed. This is a source-operability
failure, not an economic rejection of option selling or either asset.

## Exact reviewed evidence

Claim SHA256 remains
`9755f008355cbffdef9c0b561e3806ed39a1c2d874fb7a0f285def2ebab9dd78`;
assignment SHA256 remains
`8349daecd93b39ed2e41e48194b58790706edaf209cf2a3b24ba62b0b430eccf`.
Frozen source is commit `ebc21e931541e7e03e139e48f7d2069a8426742f`.
The returned tree is
`/home/malecada/master_thesis/research-deployment/options-20260915/actual-return-0901`,
with subordinate package `release-ebc21e9`, raw `data` and the original launch log.

| Retained report | Independently checked SHA256 |
| --- | --- |
| options-actual-return-20260915.json | 1b3e4ce2b6b30134a07d1fdc486b6aaf02ebc29c4fba174986573aa007435aa1 |
| options-actual-quiescence-vps-20260915.json | 26eef0c1db2120ee38e932ae099a3f645a0f5f9ffa8d204767535d59897324f3 |
| options-actual-remote-inventory-20260915.json | 138658f815810125ed44d82bac512417ab3fb6cad37f6db18434b3deea207317 |

The complete authenticated remote inventory records 93 regular package/data/log
members, 7,893,176 bytes. Independent local reconstruction hashed every returned
member and reproduced that exact remote inventory, without missing or additional
members. The archive has 103 entries including directories; it is not a competing
regular-file count. All 82 raw data-member hashes remained unchanged across the
read-only source review. Raw retained inventory SHA256 is
`4cff8859a4797b47fa69a6bf9ce207faa8a5fbaa7e6ef257f3aa0273647de5f6`.
No decoded economic price, option premium, Greek, book or PnL value was extracted
or displayed. The review decoded only venue and event timestamps needed for the
observed source refusal and checked raw bytes/receipt metadata structurally.

## Cause independently reconstructed from timestamps

The frozen nominal entry is `T = 1789462800000`, September 15 at 09:00 UTC.
`adapter.py:90–97` maps each provider event to a local interval using the
corresponding venue-time receipt. It tests maximum age at the fixed action
`T+5000 ms`, not merely age when the response arrives. Algebraically, its first
condition requires mapped earliest event time to be at least T. Its second
condition rejects a mapped latest event more than 1,000 ms beyond that source's
controller receipt.

The independently recomputed venue offset intervals are options `[-131,153] ms`
and futures `[-130,130] ms`. All eight known receipts pass the adapter's exact
HTTP/body/raw-clock/deadline reconstruction. That transport success does not
establish freshness of the economic event described by the response.

| Source | Provider event minus T (ms) | Mapped local interval minus T (ms) | Maximum age at T+5s (ms) | Frozen freshness result |
| --- | ---: | --- | ---: | --- |
| BTC index | -1000 | [-1153,-869] | 6153 | unavailable |
| ETH index | -1001 | [-1154,-870] | 6154 | unavailable |
| BTC perpetual depth | 320 | [190,450] | 4810 | passes this check |
| ETH perpetual depth | 343 | [213,473] | 4787 | passes this check |
| BTC perpetual mark | 2 | [-128,132] | 5128 | unavailable |
| ETH perpetual mark | 2 | [-128,132] | 5128 | unavailable |

The first failed source for both assets is the index, because
`adapter.py:120–124` checks index before perpetual depth and mark. The index
responses arrived at T+512 ms and T+518 ms, but describe events about one second
before T. Their maximum age at the frozen modeled action exceeds five seconds.
The independently inspected mark timestamps would also fail the same conservative
bound because clock uncertainty extends their local event interval before T.
Neither failure arises from the future-chronology side of the predicate. Passing
depth timestamps do not rescue the missing complete entry source set.

The saved selection records both assets as unavailable with null selection and
`source age or chronology`. `worker.py:205–229` preserves those facts, refuses a
replacement entry, and seals the source as failed. Its all-or-none behavior is
consistent with the frozen policy. The review does not revise the five-second
age threshold, shift the entry, narrow measured clock uncertainty or seek another
quote. A different prospective design would require a new justified allowance;
this review grants none.

The earlier 65,536-byte fundingInfo truncation remains retained. It is not the
entry failure's cause: the selector requires initial option rules and the eight
known roles, while financial funding coverage uses prospective hourly
nextFundingTime and finalized daily/final funding histories. No fundingInfo
omission is treated as an implicit eight-hour calendar or zero cashflow.

## Complete failure denominator

Each instantiated journal was opened read-only against its exact frozen source
specification, claim and resource limits. Receipt/prefix hashes, intent identity,
sealed inventory and suppressed-slot commitments validate.

| Journal or conditional set | Received | Suppressed | Unresolved selected | Total |
| --- | ---: | ---: | ---: | ---: |
| Bootstrap | 3 | 0 | 0 | 3 |
| Known hourly roles | 8 | 8448 | 0 | 8456 |
| Daily | 0 | 225 | 0 | 225 |
| Final funding | 0 | 4 | 0 | 4 |
| Conditional selected roles | 0 | 0 | 8456 | 8456 |
| **Total** | **11** | **8677** | **8456** | **17144** |

Received is a journal transport state; it includes the incomplete fundingInfo
body and is not equivalent to financially admitted source. No selected journal
or fabricated contract was created. Independent reconstruction of all 8,456
conditional selected role IDs matches the source seal's ordered hash
`e5670721bafeff0ab9782c82d3a717d2af8f7a6c4721ed66e43e7b56b4fa0f36`.
Together the instantiated journals and that unresolved commitment preserve the
entire 17,144-slot denominator.

The retained return report enumerates each of BTC/ETH × 1,000/10,000 × base/stress
as unavailable. It provides no evaluation arguments. That eight-cell source
classification is appropriate without running the financial engine. At review,
the authoritative local claim's control and output directories were empty; no
analysis intent or economic output existed. A failed terminal may reference the
retained review/source evidence without inventing `books.json` or booking zero
returns.

## External quiescence and closure conditions

The source seal reports failure at 09:00:00.805 UTC. Its hash is
`aecf7ac0245054e1a8c4859d7844b55a034265bc04fd5d00ef60f39e579e0595`.
The supervisor records child exit code 2 at 09:00:00.916 UTC, after the source seal;
its exact hash is
`30ea30be12acb7f60c997102e24ea1b4f59f85b54c87ac05da3b1923255f34cb`.
Both hashes and assignment identity match the returned raw files independently.

The separately retained authenticated SSH observation at 09:02:29.620603 UTC
finds the exact tmux server absent, supervisor PID 683626 and worker PID 685966
absent, and both persistent worker/supervisor locks available to exclusive
read-only acquisition. It also binds the matching seal and supervisor exit.
This combination supports stopped-worker quiescence under the reviewed
cooperative-filesystem/host assumption. This reviewer inspected and independently
bound that external observation rather than issuing another remote command.
The worker's own `quiescent_ms` alone would not suffice.

Bind committed quiescence and source/stop evidence to the unchanged claim, retain
the entire raw tree and unavailable-cell report, then close **failed** using the
actual protocol and independently verify the terminal. The subsequent closure
clock must be after the external quiescence observation. No analysis intent,
financial outputs, new query, cap increase, retry or source replacement is part
of this approval. The completed terminal itself was not yet present or verified
by this pre-closure review. All nineteen predecessors and four original runtimes
remain protected by their existing hashes and lifecycle checks.

This source failure provides information about the frozen entry clock and public
response behavior. It supplies no option-selling profitability, account access,
margin, fill, true-delta or tail-risk evidence. Zero strategies are validated.
