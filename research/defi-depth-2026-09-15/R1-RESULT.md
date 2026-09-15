# R1 closed for provider throttling

Source aa926ef5c3ce3c0125af6bfc43d4b84bec80acfa. The sole worker was gracefully
interrupted after repeated provider limiting was independently verified. Its
failed terminal ended2026-09-15T18:00:02.839873UTC with KeyboardInterrupt.
This was not an elapsed-time stop or an economic rejection. No worker remains;
tool session95225 is terminal exit130. Do not restart this spent claim.

The frozen collector recognized HTTP denials but treated HTTP200 JSON-RPC errors
as individual unavailable members. That behavior followed its literal contract.
Independent review found repeated explicit RPC−32016 “over rate limit” responses;
continuing requests would disregard the provider's observed limiting. The exact
own PID2491461 was stopped with SIGINT without changing source, pacing, batching,
inputs, outputs or the old policies. failed.json is unchanged; this separate
report supplies the documented operational reason.

## Retained evidence and complete denominator

All620published outputs and the terminal claim hash verify. There are266durable
intent/receipt pairs:264attempted HTTP requests plus two suppressed state chunks.
All1,496attempted RPCsubcalls are charged.263HTTPresponses were200; one attempted
header request failed with errno99 “Cannot assign requested address”. Raw bytes
total499,548. No attempted intent lacks a receipt. The raw bodies contain468RPC
throttle errors and78execution reverts. A reversion or missing deployment-like
state is not automatically the same cause as throttling; errno99 does not identify
the underlying network/VPN cause.

| Frozen cell classification | Count |
| --- | ---: |
| Published complete, including chain |605|
| Published unavailable |1,063|
| November28 raw evidence retained, parsed cells not published |19|
| Unattempted after provider-limit stop, including later cohort summaries |19,203|
| Total original denominator |20,890|

The87published daily vectors cover September2–November27,2023. November28's
header and state raw receipts exist, but the interruption occurred during the
source check before results.json publication. No missing parsed result is
manufactured. The complete sidecar r1-closure-audit.json enumerates every original
cell's closure category without replacing lifecycle outputs. The terminal
structural verifier correctly reports zero completed terminal cells for a failed
run; that does not erase the1,668published partial classifications.

No complete365day source cohort, lending/LP cash book, return estimate or
executable route has been established. Unacquired dates are untested, not failed
strategies. The earlier batch-shape defect was repaired, but this separate
provider-rate limitation prevented the planned history from completing.

## Budget and justified continuation

Q1,Q2 and R1 consume three successor claims; source questions2/6, shared repair1/1,
financial recipes0/4. The narrow source family is exhausted at its reviewed
effective4, including the old imported DEX predecessor. No second repair or
same-claim restart follows. Original allocation188/189 and44related overlapping
DeFi history remain unchanged.

Actual cumulative new acquisition charges are129 +168 +1,496 =1,793RPCsubcalls
of25,000, leaving23,207before another reservation. Known raw bytes are637,835,
plus the conservative262,144reservation for Q2's one unreceipted intent. R1's
unspent resource reservation is released; it grants no extra experiment slot.

Continue the independently justified staking question under its own exact gate.
Previously unattempted headers from November29onward can support that distinct
question. Exclude every previously attempted header from new requests, including
failed October22 and acquired November28; qualify and reuse retained receipts
without rewriting R1. Q3 must not acquire Aave income or LP fees as a disguised
repair. Freeze single requests, fixed conservative pacing and immediate endpoint
stop on recognized RPC throttling as well as HTTP denials. Five-second pacing,
if selected, is authored and does not prove a safe rate. No retry, provider
substitution or VPN change is permitted.

The exact Q3 registration, request-key exclusions, complete denominators,
ancestry and resource reservation need independent review before capture.
Q4/Q6 source forensics and reviewed protocol accounting preparation remain
available. No additional go-ahead is required for justified authorized work.
The broader phase is not exhausted. No orders, paid resources, account/wallet
actions, production changes or options-work inspection occurred.
