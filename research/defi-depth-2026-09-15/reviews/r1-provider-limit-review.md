# Independent R1 provider-limit and terminal review

Reviewer: separate broader_design_review research-reviewer. No network,
financial calculation, other process/worker inspection or source mutation.

Initial scoped review independently decoded exact raw receipts for September14,
October20,October22 and November20:76cells,20complete/56unavailable;
53attempted RPCsubcalls in10HTTPattempts;21explicitRPC−32016rate-limit errors.
All raw hashes, lengths and request/response IDs reconciled. October22 had an
errno99header transport failure, not proved archive unavailability; dependent
state calls were suppressed. The HTTP200envelope does not negate throttling.

The frozen code mechanically continues on these RPC errors and stops only on
the named HTTP denial statuses, so prior retained observations are not invalid
merely because that occurred. Recommendation: gracefully stop the exact worker
for observed limiting. Do not change live pacing/batching or retry. A temporary
inspection pause grants no adaptive acquisition policy and should avoid an
in-flight request with an active deadline. No repair allowance remains.

After the stop, full independent terminal reconciliation passed: sourceaa926ef,
failed at18:00:02.839873UTC;620output hashes and claim hash match.266intent/receipt
pairs include264attempted HTTP and2suppressed requests;1,496attemptedRPCcalls;
263HTTP200and1transport failure;499,548rawbytes;468throttle errors and78reverts.
No unpaired intents.87daily vectors contain604complete/1,063unavailable cells,
plus complete chain.20,890frozen cells include1,668published classifications and
19,222unpublished; November28raw evidence is not completed normalization.
Preserve the failed receipt's literal interruption reason and document the
provider-limit reason separately.

Q3's distinct staking prerequisite may acquire only previously unattempted
headers from November29onward under a new frozen contract. It must exclude all
previously attempted headers, reuse/qualify retained evidence without rewriting
R1, acquire no Aave income/LP fees, use single requests with fixed pacing and
immediate HTTP/RPC throttle stops, and prohibit retry/provider substitution.
Five seconds is an authored setting, not an empirically safe rate. The separate
gate needs full denominators, resource reservation and inherited crosswalk.
This does not repair R1 or turn unused resources into another allowance.
