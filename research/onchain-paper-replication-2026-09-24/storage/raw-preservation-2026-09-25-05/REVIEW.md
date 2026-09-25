# Independent continuation05 prelaunch review

Disposition: no blocking correctness finding. One fresh05 finite `all-bulk`
controller is cleared after the owner freezes a released object binding this
report and the exact reviewed contract/candidate, then commits preparation before
launch. Prior identities remain terminal; no same-identity retry is admitted.
The original04 transport failure is not diagnosed or claimed fixed.

Exact identities reviewed:

- Contract: `cc08af31f9a7090b7ac13881d7c3c5c3424d3061ab3957f8fc86acdc7c21929b`.
- Transfer source: `c07745682d5d4879a801d02934a4040719ae26f18bcdfde614eb8877099a2d82`.
- Prepared candidate: `d24a6ef9fc144edd3be4fc89f0a57ba18b7bd0c397565b23b3b2cd0b1d3cce2e`.
- Reconciliation: `3e5749a924b191225df9bb1f168a69560818cecc3b9e813ca3631dd61d021f3b`.
- Verification: `0242395ee6e7e69f51960f8b52bbb4e5624531030b5ea9c302b40b9e323d971b`.

All contract-bound source/input hashes and verification-bound source/test/XML
hashes match. The shared preservation/resource/lifecycle/provenance sources are
unchanged. The actual05 script diff against04 was reviewed; the changes add
receiver diagnostics and bounded error-tail reporting without changing admitted
sources, prefix ownership, transfer denominators, upload rate, concurrency or
retry policy.

Independent04 closure inspection finds a failed controller with zero completed
phases and zero new completed batch markers. Its guard elapsed971.043705532s,
peak201,830,400 sampled bytes, child exit1 and cleanup verified. The cgroup,
monitor41712 and workload PID recorded by child_exit.json are absent. Memory
OOM counters are zero; disk and host memory floors were not the recorded cause.
The actual traceback identifies a nonzero download process exit. Because the old
receiver discarded stderr, its underlying SSH/readback cause remains unknown.

Failed04 batch34 retains a536,811,520-byte local bundle,212,402,176-byte recovered
partial,95,061-byte manifest and failed receipt, with no complete marker. No
partial is counted as preservation. The new05 output root is separate; neither
03 nor04 partials are overwritten or deleted by05. The previously independently
reconstructed pilot02/03 prefix remains bound by unchanged exact metadata hashes:
indices0..33,5,832 files /18,052,844,567 raw bytes. Eleven05 phases cover exactly
indices34..194,161 batches /53,251 files /85,471,644,476 raw bytes. The complete
inventory remains59,083 files /103,524,489,043 bytes. No verified prefix is
transferred again.

The new receiver drains stdout and stderr through nonblocking descriptors and
select, retaining at most16KiB of stderr bytes as a tail. Its stdout byte bound is
checked before disk write, and the original absolute transfer deadline, pacing,
exact-size completion requirement and nonzero-exit refusal remain. Partial
downloads receive exclusive transport receipts with observed byte counts, return
code, elapsed time and bounded diagnostics. The subprocess is killed/waited on
error or timeout. No shell execution or command/credential dump was added. JSON
encoding/replacement characters can make the serialized diagnostic larger than
the retained raw16KiB tail; memory and disk use remain bounded. These diagnostics
improve evidence on a subsequent failure, not the known cause of04's failure.

Exclusive controller/phase/batch identities and per-operation payload reservation
remain intact. Runtime controls remain256/192MiB cgroup caps, zero swap,4GiB
startup and3GiB host runtime reserves,20GiB local disk floor plus2GiB preflight
scratch, one batch at a time,8MiB/s transfer cap, <=8h per phase and <=48h
controller execution. Phase payload caps sum203GiB within205GiB. Prior455.625GiB
conservative allocations remain recorded, producing660.625GiB including05. Prior
actual guards total14,112.788624346009s, exactly04's prior total plus971.043705532s;
adding172,800 prospective seconds gives186,912.78862434602s. Prior reservations
and failed exposure remain retained rather than reset. SSH overhead stays
explicitly excluded from payload accounting.

The root's read-only SSH capacity receipt returned0 in0.812s. The latest
admission-only receipt reports38,948,515,840 free disk bytes,8,664,018,944 available
memory bytes and no05 controller. These point observations support admission;
ongoing capacity and transport success remain subject to execution checks.

The source-bound XML records42 passes, zero failures/errors/skips,1.258s. Six new
real-subprocess cases exercise exact/short/excess stdout,200KB stderr draining
without deadlock, retained nonzero exit, timeout and child cleanup, and pacing/
exclusive destination behavior. Existing36 checks remain included. Test execution
was inspected and not duplicated by this reviewer.

Not tested or claimed: repair of the original SSH failure, independent new remote
raw readback, remaining source-body identity,05 completion or sustained throughput,
full storage recovery, graph/MCM/scratch backup, empirical predictions or paper
numerical agreement. No financial experiment, raw-body read, transfer, predecessor
rerun or ledger mutation was performed by this review. Terminal05 evidence still
requires independent reconciliation with the reused02/03 prefix. No unresolved
source correctness question requires higher-effort escalation.
