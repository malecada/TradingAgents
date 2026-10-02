# Independent integration review

Accepted as tiny synthetic integration evidence for the actual CompactMatcher and the previously reviewed fresh archive-backed PairLog. No material defect was found within that bounded claim. Source, test assertions and saved logs were inspected; no checks or remote operations were rerun by the reviewer.

Both parametrized cases execute the unchanged checkpoint matching engine for two distinct ordered purposes on the same pair of synthetic two-node graphs. Each returned score must equal `match_reference` exactly. An independently assembled `<Qd32s` digest binds ordinal, reference float64 score and purpose hash, and must equal the archived replay's score digest. This is two occurrences of one numerical graph pair, not broad numerical coverage or an independent economic oracle.

The no-checkpoint case explicitly requires one three-record remote chunk and one one-record final chunk after four begin/completion records; the latest-event acknowledgement remains compatible with the matcher's existing local readback. Both cases require no remaining local `.bin` payloads under the matching namespace. The progress case uses operations_per_call=10 and calls_per_checkpoint=1, requires at least one real progress event and eventual completion, then directly decodes retained synthetic remote frames. Each progress reference is passed to the existing `compact_stage.checkpoint` validator, which joins the wrapper and intent to the log start, event, pair/purpose/identity, registered pair policy and cumulative reservation ordinal, and hashes the actual nested checkpoint files. The independently ordered event/reference digest must match archive replay, with checkpoint directory count equal to progress count. The digest assembly is independent; the checkpoint-tree validator itself is an existing shared implementation, not a second independent checkpoint decoder.

Initial check01 reports **1 failed, 1 passed in0.57s**. Its failing progress fixture requested32 checkpoints while omitting the corresponding pair-policy max_publications allowance; it failed constructor admission before that case executed. The preserved test documents this. The corrected fixture explicitly sets max_publications32 and closes the log if matcher construction fails. Corrected check02 reports **2 passed in0.58s**. No production source change is attributed to this test correction.

This establishes actual matching and checkpoint-tree compatibility across archived chunk rotation using an in-process synthetic filesystem transport and no-op caller leases. It does not establish checkpoint resume/continuation, a cold archive-manifest reader, a full generic archived-stage seal, score-stream joins, registered current-owner or scientific admission, real network transport, operating-system guard behavior, concurrency, measured resource capacity or empirical source eviction. The temporary fixture bodies are not claimed as durable archived research artifacts. Failure/adversarial coverage belongs to the separately retained primitive suites; these two integration cases are successful compositions, not new fault-injection evidence.

Inspected SHA-256:

- test_archive_matcher_integration.py: `9830123e05e941445f24cfa9c437679491c196a5f2aaeb35d08d8bb85655dabf`
- compact_matcher.py: `645925483675e5fb8bc0aad4c662fcff963db24125610928b532bb13f1b1b650`
- archive_pair_writer.py: `c714c350f372be1b4e3c7840b5187deb7f72ee80549edfed4e48450e2d0ca052`
- compact_stage.py: `fe96c774ec784cd2899747db8f9736ff6655a369a0113de001e3b60c782ad83f`
- archived_pair_log.py: `50ff9d9deaf665f5953bd0a82de6c48dbf84bace0ee8bc2dde86cb3581ed3c12`
- test-check01.py: `cd3515a8982118b2fa8e11fc96507c05d9f98b302fa1a0dc348c62c6173ce046`
- check01.log: `b9ffc3e7d29a01f704dca12ea29e894e81a2784b92f486cc31da579c352ae324`
- check02.log: `58d793cef6bdeb229f9f394f5165532a11de34e02e472f40294a73e4117c390d`
