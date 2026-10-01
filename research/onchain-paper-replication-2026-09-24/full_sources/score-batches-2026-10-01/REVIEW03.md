# Independent completed-score primitive review 03

Accepted for the bounded storage-primitive scope. The residual SB2 content boundary is addressed by the new second content pass; the earlier withheld reviews remain historical evidence. No adapter, numerical reuse or empirical release is accepted here.

The delta adds a constant-space aggregate of hashes binding each filename to its actual read content, alongside the existing signature/count aggregate. After the last external lease, the final streamed inventory validates allowed names and bounded count, then rereads every metadata/payload file through the same nofollow/nonblocking bounded reader. Final count, signature aggregate and content aggregate must match the first pass. Thus a prior payload changed during the final lease is no longer accepted merely because its stat signature remains equal. Root identity is rechecked before return. No per-cell or per-chunk list is introduced, and working memory remains O(chunk_bytes); the final binary-read cap is the explicit 8 MiB ceiling, while metadata retains its 8 KiB cap.

The precise qualification is appropriate: every retained score byte is read twice, and changes after an entry's last read cannot be excluded by this non-atomic procedure. The sole-writer/source-freeze contract remains mandatory. These are bounded content observations, not a filesystem snapshot or prevention of continuous mutation.

The saved `red03.log` shows the new unchanged-timestamp simulation failing as intended: one failed, 16 deselected, in 0.19 seconds. The test performs a real equal-length payload rewrite during the last lease and mocks only the modification/change timestamp fields in signatures; real inode/type/size/link/block information remains. It therefore distinguishes content rechecking from the signature-only predecessor. Saved `check03.log` closes with **17 passes in 0.27 seconds**, including all earlier checks. The preserved `check02-source.py` exactly matches the source reviewed in FINAL_REVIEW. No test or job was rerun by this reviewer.

SB1's post-write lease/root/readback checks and parent-directory synchronization remain unchanged. Publication errors retain files and refuse success; a terminal already written before a failed final check must not be retried or treated as externally admitted merely by observing its hash.

The conditional logical accounting remains eight bytes per cell plus one 8 KiB allowance per chunk and two fixed metadata allowances. It excludes filesystem overhead, matching scratch, input/copy/validation memory, logs and other workflow artifacts. It does not remove old PairSession journals or reservations. Whole-chunk publication does not make an unflushed individual callback result durable; exact per-score return/checkpoint semantics, no-redraw behavior after interruption, actual workload/owner membership, score-domain validation, successor admission and full-workflow capacity still require the separate adapter. In particular, this generic finite-float64 primitive does not enforce [0,1].

Exact reviewed SHA-256:

| Artifact | SHA-256 |
|---|---|
| `score_batches.py` | `079571b425e1fd04ecf46d8b34aa6fb5352ca2a2bdfda1d9f45982a1ced1f531` |
| `test_score_batches.py` | `b9ad1e1d576ef103b4276f3175025fcfe26b4c44db358ebff011c099ea6e9ed2` |
| `check03.log` | `07aab0014e9882758575aba6adf1bc4b50a155b1cc4e770c59ee4e6ae2f659f6` |
| `red03.log` | `489669567df883c32ea1f778c6581478a55397ce6f4dfcf1e943122c8a275b00` |
| `check02-source.py` | `01471f1ccd1420602bf66ab7f44ec98f0be8ad6bac31239797cf72bf559c58d6` |

No financial timing, returns, fees, funding, empirical denominator, real registered execution, cold/successor admission or numerical matcher correctness was tested by this review.
