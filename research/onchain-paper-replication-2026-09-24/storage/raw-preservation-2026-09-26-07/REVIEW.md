# Independent continuation07 prelaunch review

Disposition: no blocking correctness finding. One fresh07 finite `all-bulk`
controller is cleared after its release binds the exact reviewed contract,
candidate and this report, and preparation is committed before launch. No
predecessor identity is reopened, and no future transfer success is claimed.

Exact reviewed identities:

- Contract: `97470dbfcecbbc4919b92f590b813e6098928ccb66d8d0ab32122b63ac12b7fe`.
- Transfer source: `c07745682d5d4879a801d02934a4040719ae26f18bcdfde614eb8877099a2d82`.
- Candidate: `171725eb07ee65a9662f7e52ae1ec500203cbbae6f3eba5dcfd443108f303e79`.
- Reconciliation: `6892a9ca8397e44da9698415364db33fece801a747373fde1a54543979c6e746`.
- Verification: `c6ca6b776ef91ed6e6abf143ba89f651122ea0ed4a213befa76a9cc430ab53ea`.

All source/input bindings matched actual files. The07 script is byte-identical
to06 and the reviewed05 implementation. Its dynamic HERE resolves07 paths;
shared helpers and the complete batch plan are unchanged. Inherited source,
verification and XML hashes matched05 artifacts, including42 passes and zero
failures/errors/skips. This is inherited source evidence, not a new test run.

Independent reconstruction checked every completed manifest and receipt from
pilot02,03,05 and06 against the frozen metadata inventory. All source rows,
member names, offsets, counts, raw bytes, archive identities, preservation flags
and recovered manifest/completion-marker hashes agree. The exact completed
prefix0..44 covers7,943 files /23,907,703,265 raw bytes. New06 batches42..44
contribute634 files /1,593,323,300 bytes. The parent phase failure does not discard
these durable per-batch completions.

Ten07 phases cover45..194 exactly once:150 batches /51,140 files /79,616,785,778
raw bytes. Nine phases have16 batches, the last6. Reused and pending totals equal
the full59,083-file /103,524,489,043-byte inventory. No completed batch is repeated.

Parent06 is terminal FAILED. Guard SHA256
`c8fb5e19bf4acbacac5b510e3b01a617a92a0b5c1f1a0e57cec2b12478089118`
records2,022.1096230760013 seconds,202,878,976 peak sampled bytes, child exit1
and verified cleanup. The actual guard log records SCP exit1 with stderr
`lost connection` during batch45 archive upload. This supports transport-loss
classification; the specific physical network cause was not independently
established. No memory/disk floor breach or kernel OOM is recorded. Independent
checks found the cgroup and recorded PIDs521764,521768,521774,558352,558353 absent.

Failed06 batch45 retains535,347,200-byte bundle.tar,110,871-byte manifest.json
and112-byte failed.json. There is no recovered archive or complete marker, so
it receives no preservation credit. Any remote partial remains under06;
07 uses an exclusive new remote root. No local partial was read as raw data,
modified or deleted by this review.

The unchanged source retains exclusive controller/phase/batch identities,
no automatic retries, full source/recovered-member verification and bounded
transport diagnostics. Controls remain one batch at a time,256/192MiB memory
caps, zero swap,4GiB startup/3GiB runtime host reserve,20GiB local floor plus2GiB
scratch preflight,8MiB/s rate, <=8h per phase and <=48h controller execution.
The latest root admission receipt observes7,562,100,736 available memory bytes
and34,818,895,872 free disk bytes, with no07 controller. The read-only SSH
capacity receipt returned0 in0.768s. These point observations do not guarantee
sustained connectivity or host capacity.

Phase payload ceilings sum200GiB within205GiB new07. Prior865.625GiB
conservative allocations remain recorded, giving1,070.625GiB combined.
Prior measured guards total22,870.31174160801s, exactly the preceding total
plus the full failed06 duration. Adding172,800 prospective seconds gives
195,670.31174160802s. Prior reservations are not reset or relabeled as measured
spend. SSH overhead/control traffic and idle preparation remain excluded from
file-payload/guard totals; read-only preflights are separately retained.

Not tested or claimed: a second raw-body recovery, present remote bytes of all
completed archives, future connectivity/host stability,07 completion/throughput,
graph/MCM/scratch backup, financial results or paper numerical agreement. Review
performed no network request, raw-body read, test rerun, predecessor restart,
empirical job or ledger mutation. Terminal07 still requires independent
whole-inventory reconciliation. No unresolved source correctness question
requires higher-effort escalation.
