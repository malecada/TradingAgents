# Independent prelaunch review

September 25, 2026. Disposition: **no blocking finding for the exact bounded
transport diagnostic below**, conditional on committing the reviewed objects and
publishing a release tied to their contract before its sole invocation. This is
not approval to change the active preservation controller or its concurrency.

Reviewed identities:

| Object | SHA-256 |
| --- | --- |
| probe.py | 332382290567fd104bcd618cf0d98bb3aeeadc43e21fb0ea88d6538020ba5581 |
| contract.json | 6b04a8f3587661b984b0fb6942eaa607736c6c21834d699fce120d20ca714692 |
| CHARTER.md | 33900e77454781b243862cc3668a87ab432f3b436aab8411c7f0ed5ab8c9985f |

All seven entries in `source_sha256` independently matched the current files.
The imported preservation transport and guard source were inspected statically;
neither was executed by this review. No network call, test, data decoding, large
artifact read, private credential read or financial claim was performed.

## Budget and containment reconstruction

- `probe.py:23–29,91–103` executes one upload/download pair, two concurrent pairs,
  then one pair, with no retry. There are exactly four 128 MiB uploads and four
  bounded downloads. Each download reserves 128 MiB plus one 32 KiB `dd` block.
  Conservative payload allocation is therefore **1,073,872,896 bytes**, below
  the **1,342,177,280-byte** (1.25 GiB) allowance. The allowance is application
  payload; SSH/TCP framing is not measured network traffic.
- Each per-file transport reserves at most 256 MiB plus 32 KiB against its
  384 MiB cap. There are at most two simultaneous probe transport connections.
  Upload and download stages are sequential. The active backup contributes its
  separately bounded connection; it is neither stopped nor relaunched.
- Two source payloads occupy 256 MiB. The parallel downloaded copies add at most
  256 MiB, giving **512 MiB** maximum generated file payload, plus small receipts
  and logs. Completed downloads are deleted between stages only after their
  hashes match. Sources remain until all stages finish; incomplete copies remain
  on ordinary errors.
- `probe.py:134–140` exclusively reserves a new local run directory and uses the
  existing guard with 512/384 MiB max/high, zero swap, 4 GiB runtime reserve,
  4.5 GiB startup reserve, 20 GiB disk floor and 900-second limit. Guard source
  confirms two-CPU affinity, unique control-group identity, descendant cleanup
  and readback before release. The 4.5 GiB threshold equals cap plus reserve.
- Upload subprocesses have a 180-second local timeout. Inherited download code
  has a longer timeout, but remains inside the 900-second outer guarded job.
  A timeout/error does not authorize another invocation under this identity.

## Integrity, control and limitations

`probe.py:80–87` exclusively writes two random payloads and hashes them.
`parent_transport` reuses the backup transport code and verifies the backup's
frozen contract inputs before extracting connection metadata. It does not call
the backup's controller or worker. The probe overrides only its own transport
instances' rate and upload timeout. The reviewed subclass also explicitly sets
`ControlMaster=no`, `ControlPath=none` and `Compression=no` on its SSH/SCP command
options (`:47–51`), preventing connection multiplexing and compression from
silently changing the diagnostic comparison. These options do not alter the
existing backup's transport instances. Exact source and charter hashes are checked
in both the launcher and guarded worker. The final reviewed increment adds
read-only active-backup guard/process snapshots before upload, between directions
and after download; no snapshot invokes or signals a backup process.

The remote probe directory is created exclusively (`:89`); every upload path is
derived from that directory and the fixed three-stage schedule. The inherited
transport validates remote paths, uses strict host-key checking and batch public
key authentication, reserves bytes before transfer, and refuses excess or short
download bytes. `:105–114` records each stage only after every downloaded SHA-256
matches its source. `:120–123` deletes only these four generated remote payloads
and the generated local source files after successful measurement. The empty
remote directory and compact receipts remain. No research/raw backup path is
selected for deletion.

One nonblocking reporting caution applies: `probe.py:117–127` publishes
measurement completion before cleanup. A cleanup error can leave verified probe
files behind or, for a local unlink failure, leave both completion and failure
records. Final reporting must inspect the guard terminal, child exit, cleanup
receipt and failure record together; the presence of `complete.json` alone must
not mean full clean completion. Never relaunch the probe to tidy such a failure.

The single-before/parallel/single-after sequence provides a useful bounded
comparison, but each stage has one observation. Report before/after drift and
individual parallel-transfer times; do not claim statistical variance or a
stable isolated ISP link speed. Active backup traffic, common CPU affinity,
encryption/setup overhead, server behavior and time effects are confounded.
No measured result yet establishes that concurrency will improve preservation
throughput. Any subsequent preservation-rate/concurrency change needs its own
prospective boundary, budget and independent review.

The claimed original 249 GiB allowance and current host headroom are supplied
by the parent task's separate cumulative reconciliation/startup observation;
this narrow review establishes the additional probe allocation and source/control
behavior, not a fresh reconstruction of the entire historical transfer ledger.

## Pre-release review correction

The initial review message bound probe
`707ff09e6c671a512eb64c51b519590f55aae270c40ddc1a379c32758711a09a`
and contract `266af8af51cc665347aa4834637cf74775f1af2b8321501f0528be92e53b91c7`.
Before any release or transfer, the explicit independent-connection SSH options
were added and independently inspected. That provisional review identity is
superseded by the exact final hashes in the table above. No earlier probe version
was launched as part of this review, and no runtime result is implied.
