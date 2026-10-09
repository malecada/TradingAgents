# Frozen owner integration02: source acceptance withheld

The original empty-checkpoint-directory omission is corrected: the independent exact old inventory function returns an unchanged digest after adding an empty directory, while successor02 changes its typed inventory. The successor also refuses a synthetic symlink. All eleven candidate and baseline manifest source hashes were checked against actual bodies.

A separate failure-cleanup defect blocks source acceptance. In `compact_mcm_batched._compute`, the actual BatchJournal is created before `closure-tokens.bin` is opened, but the cleanup try starts only after that open and its descriptor signature have completed. A token-open OSError (such as ENOSPC, EMFILE, or an exclusive-path collision) therefore escapes without `journal.close()`. The focused AST execution with the actual frozen journal confirms the same exception object propagates while `journal.closed` remains false and `os.fstat(journal.fd)` still succeeds. No pair or numerical callback runs. The reviewer then closed this synthetic leaked descriptor. The real caller poisons the Owner but has no reference to this locally stranded journal.

The same unprotected interval also includes the first token descriptor fstat: a failure there can strand both descriptors. Resource acquisition must enter a cleanup scope immediately after journal creation, track the token descriptor only after successful open, and preserve primary-error precedence. No candidate edit was made.

The review stops at this concrete blocker. Shared-class wiring, offload recovery, output-consumer and authority seams have not received complete independent acceptance in this review. Existing driver03/journal/numerical evidence remains unchanged and does not establish this adapter's cleanup. Genuine Owner/Binding/Target/View/transport execution remains untested; no installation, capacity, launch or empirical authority is granted.

The synthetic test ran with 256 MiB address-space and 4 MiB file-size limits, a 30-second alarm, CPUs 3 and 4, and nice 10. It imported no numerical modules and constructed no authority objects. Candidate and historical review files were not changed.
