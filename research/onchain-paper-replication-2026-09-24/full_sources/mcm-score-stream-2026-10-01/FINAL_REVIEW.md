# Independent corrected MCM score-stream review

Accepted for the bounded synthetic MCM callback/storage composition. MS1 and the float64 evidence gap are addressed. The initial withheld review and original source remain preserved; no numerical admission or resource release follows from this acceptance.

After publishing a seal link and executing its external lease, `_seal_check` performs callback-free validation of the pinned stream start, exact link hash and ordinal/count, complete retained tail under its terminal hash, exact tail destination, destination start/header hashes and identical float64 payload bytes. A late link-publication callback therefore cannot return a successful completed-chunk reply with the destination mutation described in MS1.

After the final completion callback, `_history_check` verifies the completed ScoreBatches terminal/content, walks all retained tails and seal links, checks their hash-chain predecessors and terminal head, enforces exact bounded stream/tail inventories and rereads the exact completion bytes. It performs no matcher calls and uses no further external lease callback. The first-pass link hashes are not an unbound observed baseline: their predecessor chain must end at the prebound in-memory head already recorded in completion. Working memory remains bounded by chunk/tail size; total verification I/O grows with all retained scores. These checks remain sampled and non-atomic after individual files' final reads.

Saved red02 evidence contains three expected failures for late completion payload/link mutations and a late seal-link callback mutation. Saved check02 closes with **6 passes in 0.85 seconds**. The positive test uses the actual frozen array MCM kernel, retains 14 scalar results over four chunks, compares exact purpose order, and now compares little-endian float64 bytes against independently computed `expected_calls.saved` values before separately checking the final 7×2 float32 matrix. This closes the previous float32-only evidence qualification. No closed tests were rerun by the reviewer.

The failure case still injects an ordinary callback RuntimeError labeled cleanup. It demonstrates propagation, retained empty tail and refusal of further compute; it does not execute actual PairSession cleanup or establish cleanup-failure classification. The compute callback remains responsible for matcher convergence, checkpointing and cleanup. Wrapping existing Serial does not eliminate its per-pair journals, reservation overhead or scratch, and the adapter has no automatic replay/reopen/successor admission.

Caller-supplied scope/owner/lease remain prerequisites. The adapter checks actual sequential MCM occurrence and identities supplied through the kernel, but does not itself admit the registered run, independently reconstruct induced graphs, enforce full workflow storage quotas or establish process RSS/runtime feasibility. Retained 80-byte tail records, batch float64 copies, links, metadata and all existing matcher artifacts must be counted together. No financial data, returns, fitting experiment, historical job or production dispatch was performed by this review.

Exact reviewed SHA-256:

| Artifact | SHA-256 |
|---|---|
| `mcm_score_stream.py` | `73daf274e788c0c46df6c1bd2a6ea203f1704b843458bb96632292432ef856d2` |
| `test_mcm_score_stream.py` | `88bcc07354e7bdda5391d61d28d37ffcba5e6a3a183c9bc23a9f2d731c9b1037` |
| `check02.log` | `05e730fedae8233e94b8d7b1676dd2ed3da2b55707cfb14106e3eb9f306c67dd` |
| `red02.log` | `03f1bab93b0cb14328300b3f945657a313480b74cf0a4d38ce82ddb32c96481e` |
| preserved `check01-source.py` | `cd6ade1794f2fe00cf0c4dab5f89f64b6e2ceb18876b5aea25ded6cfb2779873` |
