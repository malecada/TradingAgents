# Independent continuation04 prelaunch review

Disposition: no blocking correctness finding. One new04 finite `all-bulk`
continuation is cleared after a released object binds the exact reviewed
contract, candidate and this report, and the preparation is committed before
launch. No predecessor identity may be relaunched. This report does not claim
that04 has started or completed.

Exact reviewed identities:

- Contract: `7e5b5ed24d87be8da0560cbbcf6960d744e3a35d126767ea8f985e956ea70bda`.
- Transfer source: `f4a7105d80e29b90b51ac1716ddc174b298fb2996571283125ba40e0a24c6470`.
- Prepared candidate: `cfef8655a498378ef807467c0ccb57c648ce8101ab9fcdb6768f91c2699c7151`.
- Reconciliation: `773f92fd66c61a11474a6fabd576a49f90ae9a2ae192ec0aaa10edf7213057ce`.
- Verification: `faa2bced84de18b374c3e44acbfea3079a186859ce07c8ef7972eefad91edea2`.

The operative instructions and current review brief were read. Actual04 source
was compared with frozen03. All contract source/input hashes and all test/source
bindings matched their current files. Review used independent metadata
reconstruction instead of accepting the author's prefix totals.

Pilot02 batch0 and all33 complete03 batch receipts/manifests cover exactly global
indices0 through33. Their individual completion, manifest, recovered-manifest,
completion-payload and recovered-complete identities were checked. Every manifest
row and numeric archive member matches its exact position in the frozen full
inventory. Receipt flags, start offsets, member counts, byte counts and archive
identities agree. These34 completed batches cover5,832 files /18,052,844,567 raw
bytes. The remaining161 batches34 through194 cover53,251 files /85,471,644,476
bytes, bringing the total to59,083 files /103,524,489,043 bytes without overlap.
Batch33 is correctly reused even though its enclosing phase failed later.

Parent03 is terminal FAILED after two complete phases. Its third guard records
`RuntimeError: disk floor breached`, cleanup verified, and sampled free bytes
21,473,370,112 below the21,474,836,480 floor. The retained child exit is-15.
The owned cgroup and observed PIDs14574,305961,305966,326654 are absent. Every
other reconciled predecessor guard is terminal with cleanup verified and its
cgroup absent. The current boot independently matches reconciliation and differs
from parent03's boot. Prior jobs and diagnostic outcomes remain closed.

Failed03 batch34 has no complete marker. Its local536,811,520-byte bundle,
482,181,120-byte recovered partial and95,061-byte manifest remain present; the
manifest hash is
`7c237f098b4fb4b89aeb035966ccd0465499f1b185708c49bfb1a7379a24c1a1`.
These are preserved failure artifacts, not completed backup credit. Starting
batch34 under04 is a new reconciled identity; it neither resumes nor overwrites
the failed03 object. No raw body or tar payload was read by this review.

The new reused_prefix path requires the exact1..33 prefix, validates each bound
completion receipt, checks all preservation/source/readback flags as actual true
values, and compares counts/offsets/bytes to the fixed batch plan. Both controller
and guarded worker execute this admission. All reused receipt and manifest
metadata is bound by the contract. The eleven new phase ranges cover34..194
exactly once; ten phases contain16 batches and the last contains one. The full
plan remains byte-identical to03. Pilot0 and completed03 batches are excluded
from new uploads and included once in the terminal whole-inventory count.

Existing exclusive lock/controller/phase/batch identities, strict SSH identity,
bounded receiver, source hashing, recovered-member checks and failure retention
remain unchanged. No retry loop was added. Generated tar copies alone may be
removed after verified completion; original stores and predecessor partials are
outside that cleanup path. Final success requires the whole retained inventory
count, not only surviving phases.

The new preflight requires20GiB free-space floor plus2GiB packing/readback scratch
before each phase and before worker transfer operations. The guard retains its
20GiB runtime floor,256/192MiB memory caps, zero swap,4GiB startup and3GiB runtime
reserves, inherited two-CPU affinity, <=8h per phase and <=48h controller window.
Reconciliation observes39,765,774,336 free bytes and5,670,674,432 available RAM
bytes. These observations are not guarantees; execution still rechecks limits.
No concurrent synthetic test is permitted after launch.

The phase payload ceilings sum203GiB, within the205GiB new04 ceiling. Prior
backup reservations remain249GiB; diagnostic contracts add1.25GiB and0.375GiB,
so the conservative combined ceiling is455.625GiB. No previous allocation was
silently reset. Eight predecessor guards sum13,141.744918814009 elapsed seconds;
adding172,800 prospective04 seconds gives185,941.74491881402. This is measured
prior execution plus a prospective bound, not the sum of old reservations or a
wall-clock promise. Payload reservations exclude SSH overhead explicitly.

The current XML records36 passes and zero errors, failures or skips. XML and all
source/test hashes match verification.json. The thirteen new tests cover valid
prefix reuse, duplicate/gap/overlap/hash/status/count/offset/byte/verification-flag
refusal and scratch-floor admission. Existing8 pilot-reuse and15 preservation
checks remain included. Tests were inspected, not rerun by this review.

Not tested or claimed: present remote contents of every completed03 archive;
independent second recovery of raw bodies; original-source size/mtime scan
repetition;04 transfer success or sustained throughput; graph/MCM/scratch backup;
financial outcomes, paper numerical agreement or strategy validity. Existing
production round-trip/member verification receipts are reused after exact
metadata reconstruction. Root's all59,083-file source-stat scan remains a
separately attributed check. Independent terminal review must reconcile every
new04 completed/failed batch with the reused02/03 prefix. No unresolved
correctness question requires a higher-effort escalation.
