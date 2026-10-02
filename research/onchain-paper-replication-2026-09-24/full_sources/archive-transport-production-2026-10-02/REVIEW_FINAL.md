# Independent final transport correction review

Disposition: accepted for the bounded maintained transport extraction and the corrected direct cleanup boundaries. ATP1 and ATP2 from REVIEW_INITIAL.md are closed. The initial review and failed evidence remain unchanged. No reviewer tests, subprocess experiments, network operations or empirical work were run.

The initial review's labels are authoritative: ATP1 covered sequential receiver cleanup and raw upload closes; ATP2 covered completion before output close. REPORT_CORRECTION.md groups receiver/publication under ATP1 and upload cleanup under ATP2. This is a label difference, not an omitted correction.

## Source disposition

`archive_transport.receive_diagnostic` now retains the primary error and independently attempts process-group kill, bounded direct-child wait, bounded stderr drain, both pipe closes and output close through `score_batches._cleanup` (lines 129–137). That helper catches BaseException from each action, attempts the remaining actions once and raises shared fatal CleanupFailure. Receiver propagation chains cleanup uncertainty to the original primary when present (lines 154–159). No descriptor-close retry is introduced.

The receiver publishes its success/failure diagnostic only after those cleanup attempts (lines 139–149). An output-close error therefore cannot leave the prior complete-only acknowledgement. Diagnostic publication failure retains an existing receive/cleanup failure with an explanatory note; durable diagnostic availability cannot be guaranteed when its own filesystem publication fails. Upload directory and sealed-memfd closes now use primary-aware `io._release` at lines 240 and 261. Inspection of the shared helpers confirms the claimed one-shot fatal propagation for these direct owned resources.

The bounded upload snapshot, exact reservation, exclusive download destination, expected-extent detection, stderr tail and deadline behavior remain intact. The code now accurately distinguishes a process-group kill request and direct-child wait from full descendant cleanup verification by the outer guard.

## Independently inspected evidence

- `review-red02.log`: 15 failed, 24 deselected, 0.78 s. The new regressions reproduce five receiver cleanup targets with and without a primary oversize error, two upload close targets with and without primary errors, and diagnostic-publication primary loss against the preserved predecessor.
- `check03.log`: 44 passed, 1.28 s, session 94153 reported closed. This comprises 39 maintained-module cases and five predecessor cases. The raw terminal summary agrees with the report.
- The receiver regressions inject errors after real local operations, assert every listed cleanup action was attempted once, require failed diagnostics and no destination, and check the original ValueError cause. Upload injections likewise perform the real close first and assert a single injected close plus reservation retention. This proves propagation/ordering under reported uncertainty; it does not simulate every unresolved OS-resource state or every combination of simultaneous cleanup failures.

SHA256 bindings independently recomputed:

| Artifact | SHA256 |
|---|---|
| `archive_transport.py` | `ef0fdc052a354af5b83e487cbc2d2cf92170149d64f90117adcb5ee37e3b572d` |
| `test_archive_transport_production.py` | `ee4dc841d2187c1c7c9412bd9ae7f1467717f6d7bdf5c580f8868fd3239cba08` |
| `review-red02.log` | `2248c243b1b553bd6463efcd57e9a93869ff437dbbd8306ba7778cb90167b0b7` |
| `check03.log` | `ae91c820d8fe4c17fec9f17d4c63676b086adb4dbe82bb70250637e2fdfd203e` |

## Limits

Acceptance is not a redesign or exhaustive fault audit of the shared lifecycle diagnostic publisher. The diagnostic failure test injects an ordinary publication error; it does not establish all partial-publication or internal lifecycle-close failure behavior. Bounded stderr drain failure and simultaneous cleanup-failure combinations were inspected structurally, not independently executed.

The caller must serialize shared transport/budget access and supply trustworthy command configuration and current admission/guard leases. Snapshot preparation is outside the child deadline; forced direct-child cleanup has its separate ten-second wait. Payload reservations exclude framing, diagnostics and physical overhead. Linux memfd and `/proc` are required. Partial remote objects may remain after failures, without refund or automatic retry.

No actual SSH/SCP interoperability, new off-device recovery, remote capacity, concurrent shared-budget safety, full descendant termination, producer/owner integration, whole-workflow resource admission or financial/scientific claim is established. Historical evidence is preserved and is not reinterpreted by the new transport identity.
