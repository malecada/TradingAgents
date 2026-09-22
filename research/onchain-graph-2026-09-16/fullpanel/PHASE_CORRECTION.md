# Final-checker phase serialization correction

The live full-history extraction remains fixed at
`fdb33cf27ca97b8d32926f046be422d8b8b45b6f`. Startup review found a serialization
reconstruction defect in its final checker after the first three independently
checked source days and first two graph days were published. The compute, daily
checker, outputs, numerical definitions and 14/14 claim remain unchanged.
STARTUP_REVIEW.md and startup-review.json preserve the original failing and
restored hashes. The original final checker has not been executed; this is not
a failed full-calendar review or a second empirical extraction attempt.

Fresh-source degree histograms have integer keys when the producer first writes
phase.json using sorted JSON. The runner subsequently reads that JSON, making
the keys strings, and retains it in the immutable daily output. Reconstructing
phase.json from that output needs the original numeric key order; lexical order
changes its SHA256 despite identical values and byte length. Pilot source reuse
already reads old JSON, so those histograms instead require lexical string order.
The initial synthetic case used only a single-digit key and missed this distinction.

check_final_phase_v2.py binds and loads the original checker bytes, preserving
its original file identity and every source, terminal, day, array-manifest,
resource and exact-global-hash check. Only its phase serialization helper is
replaced. A copy of the phase restores the two known fresh-source histogram maps
to validated canonical nonnegative integer keys when source_reused is false.
Reused source retains canonical string keys and lexical sorting. Counts, values,
annotations, timing, references and all other maps stay unchanged. The resulting
bytes must still match both the original daily audit's exact phase SHA256 and
the deleted phase's retained manifest SHA256 and length. No checksum comparison
is removed and no source output is edited.

The separate correction contract binds the wrapper, launcher, synthetic tests,
this explanation, independent review/approval and focused verification. The
launcher accepts an explicit full committed correction SHA and verifies its
contract and files against that commit; later coordinator commits are allowed
only while the correction bytes remain unchanged and the correction commit is
an ancestor. It also binds the original execution HEAD, claim and core inputs.
The check runs against the fixed Data checkout, with its PYTHONPATH, under the
same two-CPU/8 GiB sampled guard, after the compute terminal and guard receipt.
There is no additional acquisition, financial experiment, compute replay or
fresh family allowance.

## Superseding closure command

Do not run the original fullpanel/launch.py --review for this extraction; the
known ordering defect prevents that checker from verifying fresh-source days.
Use the committed correction SHA recorded in STATUS.md with the pinned interpreter
from the coordinator:

```bash
PYTHONPATH=/home/malecada/master_thesis/TradingAgents-audit-fixes \
/home/malecada/master_thesis/TradingAgents-audit-fixes/.venv/bin/python -B \
research/onchain-graph-2026-09-16/fullpanel/launch_phase_v2.py \
--source <full-correction-commit>
```

First confirm the compute process exited, there is exactly one terminal, the
resource receipt is valid JSON, and no corrected review is already running or
attempted. Preserve a new review launch observation and log. Outputs are new
Data fullpanel/independent-report-v2.json and independent-resource-v2.json;
never replay or replace either. The report attributes the original checker and
actual wrapper; the resource receipt identifies the correction commit/contract.
The final numerical conclusion still requires full-calendar global uniqueness,
all daily checks, the two exact boundary exceptions and clean guard exits.

The frozen compute's named offline result (2422 tests plus 97 subtests) remains
unchanged. The correction has its own focused synthetic regression and launcher
contract evidence; that focused result is not described as another broad run.
Independent read-only verification of already published compact day evidence
must reproduce original hashes. Full-calendar review remains pending until
compute completes. RUNBOOK.md retention/import/closure rules otherwise apply;
raw backup and historical publication limitations are unchanged.
