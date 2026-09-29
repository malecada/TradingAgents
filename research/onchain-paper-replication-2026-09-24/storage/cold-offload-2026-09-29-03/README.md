# Cold-file preservation continuation 03

Continuation 02 failed at inner worker admission before any network or eviction:
the outer 10 GiB floor conflicted with the worker's hardcoded 20 GiB minimum.
Its terminal receipt, original source and every historical failure are retained.
Continuation 01's partial remote upload remains unchanged. No body has yet been
verified remotely and all nine originals remain local.

This new local/remote identity explicitly requests the 10 GiB worker contract
added in the reviewed resource-guard correction. The existing default stays
20 GiB for every other caller. All retention and byte verification logic is
unchanged; the same nine files total 3,584,497,664 bytes. The wall limit is 7200
seconds; memory remains 256/192 MiB, zero swap, 3 GiB host reserve and 3.5 GiB
startup. One-file recovery scratch remains at most 512 MiB, transfer allowance
8 GiB and rate ceiling 32 MiB/s. Earlier traffic/partial bytes remain spent.

Read ../cold-offload-2026-09-29-01/README.md for exact restoration and interruption
handling. No original is removed before full body and restoration-metadata
round-trip plus durable local receipt/sidecar. Refuse any prior per-file result
that requires reconciliation. Eleven bindings include the corrected guard,
unchanged transport, declared disk policy and exact failed predecessor receipt.
Eight synthetic per-file preservation tests pass for this copy. A ninth test
(red01 then green02) checks that the bound disk policy is validated before the
reduced worker contract is supplied; all nine checks pass. Compact bindings and
policy checks precede worker admission, with all body/transport work after it. The tiny real
worker-disk-policy probe separately validates actual 10 GiB guard/worker admission.
No empirical claim, raw-source acquisition or financial fit is authorized here.
