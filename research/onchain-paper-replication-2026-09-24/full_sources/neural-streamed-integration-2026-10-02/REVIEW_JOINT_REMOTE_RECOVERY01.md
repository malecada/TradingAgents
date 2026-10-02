# Independent joint remote recovery review01

Disposition: **accepted for the exact21 selected evidence blobs and complete five archived owned trees**. This is recovery verification, not another experiment, numerical replay, broader source recovery or a change to any closed outcome.

The reviewed recovery report `JOINT_REMOTE_RECOVERY01.json` has SHA256 `6e50ef6c18238beec80cd6b2c6973334def8ada819801b7fa79332252bbb4e17`; the recovery program `recover_evidence01.py` has SHA256 `67c8f1cba4626ebeea7d0f09ccf89320660909d5a9238cadb77ff28307443f9f`. Fixed source is `3c4b5f86b679b013d8243cfc4a930c4e1a9cf040`, which equals the fresh bare repository's FETCH_HEAD. Review did not assume current HEAD remained that source.

Independent read-only reconstruction compared every downloaded selected body with its report byte count/hash, the same fixed-commit blob in the bare recovery repository, the fixed-commit blob in the engineering repository, and the retained local original. All21 agree. Git reads used `GIT_NO_LAZY_FETCH=1` and `GIT_TERMINAL_PROMPT=0`; there was no fetch, network verification, recovery-program rerun or new namespace creation by this review.

Every tar member was streamed independently. Exact unique membership, type and mode were checked against its recovered manifest; all359 regular bodies were read completely and independently SHA256-hashed; all three symbolic-link target strings and their byte counts/hashes were checked without following them. No hardlink entry was treated as a regular body, and no unexpected/duplicate/missing member was accepted. Archives were not extracted. Checkpoint bytes were hashed, never deserialized or executed.

| Case | Files | Directories including root | Links | Members | Regular bytes | Original allocated bytes |
|---|---:|---:|---:|---:|---:|---:|
| diagnostic01 |10|5|0|15|175,021|225,280|
| GREEN02 |10|5|0|15|32,406|81,920|
| cleanup01 |11|4|0|15|17,767|65,536|
| adapter01 |135|42|3|180|72,046|745,472|
| adapter02 |193|59|0|252|605,418|1,536,000|
| Total |359|115|3|477|902,658|2,654,208|

The three adapter01 link targets contribute another744 bytes. All per-entry allocated-byte records sum to the reported per-case allocation, including directory blocks. These allocation values describe the original host; tar bodies cannot recreate or prove equal allocation on recovery media. The compressed archive sizes are likewise separate from original logical and allocated sizes.

The recovery program source verifies local committed bodies before creating its new bare namespace; it compares actual remote branch HEAD with source, fetches that source into the fresh bare repository, and then reads each selected blob into exclusive output files before publishing its report. Its completed execution is the coordinator's recorded external-recovery evidence. This independent review verifies the downloaded objects and source/control flow; a bare repository or configured remote by itself would not prove a network transfer. No new assertion about current remote availability or all repository blobs is made.

## Preserved dispositions and scope

The recovered originals and independent execution reviews retain the following distinctions:

- Diagnostic01: all four arms observed; worker0, parent1 under the original strict stop-return rule. No parent-pass promotion or rerun.
- GREEN02: all13 finite numerical/memory checks passed in the child; parent1 from the current-caller monitor-PID cleanup mistake. Later cleanup work does not rewrite that terminal.
- Cleanup01: successful finite stdlib native-owner smoke; this is not a numerical or capacity result.
- Adapter01: storage-link rejection and failed parent remain. The original result's incorrect absence-of-child-receipt wording is preserved together with `CLOSURE_RECEIPT_ADDENDUM01.json` (`46a0f4bb4137256b0bb3126f66102bc577b945f777d8ff97d6c9565aa9188d4d`). The already-archived child receipt reports125/signal; the four-test report is absent. Three pytest current-link targets remain in the archive as strings.
- Adapter02: its separately reviewed finite four-test/twelve-phase engineering pass and native closure remain. This does not establish a genuine full-size empirical producer, model capacity or paper agreement.

The21 selected blobs comprise five archives, five inventories, five execution results, five independent execution reviews and the adapter01 correction. Other outer references, registrations, all selected source/runtime files, original graph data, prior historical evidence and a complete runnable environment were not separately recovered by this operation. All archived members are covered, but this is not an all-source or whole-study disaster-recovery claim.

No discrepancy requiring correction was found within that limited recovery claim. No numerical import, test/job/claim, checkpoint replay, ledger/registration mutation, evidence deletion, budget refund or historical identity reuse occurred. Only this new review document was written.
