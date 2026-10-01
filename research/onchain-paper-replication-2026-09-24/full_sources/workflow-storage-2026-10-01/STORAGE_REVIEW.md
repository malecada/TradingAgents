# Independent sampled-storage component review

Accepted for sampled, non-atomic accounting of an explicitly owned directory
tree. No material defect was found within that stated scope. This acceptance
does not integrate or release a runner, impose a hard filesystem quota, or bound
growth between observations.

The implementation accounts `st_blocks * 512` for regular files and directories,
while separately summing logical regular-file lengths so sparse files cannot
evade the logical limit. Entries count children, including nested directories;
the root is included in directory/block accounting but not the child-entry count.
Limits are strict positive integers, with depth at most 64 and scan-time setting
at most five seconds. A detected numeric, entry, depth or time breach raises
`StorageLimit` retaining the partial counters and reason.

The root is canonical and pinned by device/inode. Directory traversal is anchored
to open descriptors, uses no-follow relative stat/open calls and `O_DIRECTORY`,
compares child identity before/open/after traversal, and rechecks root identity
and canonicality at completion. Other devices, regular-file hardlinks, symlinks,
FIFOs and other special files are refused when observed. `O_DIRECTORY` prevents
a raced FIFO from being treated as an opened directory. Regular-file bodies are
never opened or read. Descriptor cleanup is protected by nested `finally` blocks
and scandir context managers, including refusal paths.

The time limit at `workflow_storage.py:44` is checked cooperatively between
metadata operations. It can detect a slow scan after an operation returns but
cannot preempt one blocked filesystem syscall. A future guard hook must not call
this a hard five-second watchdog or assume it guarantees the outer monitor's
sampling cadence. Outer wall-time supervision and bounded writes remain separate
requirements. Non-atomic traversal may observe concurrent growth/deletion at
different times; neither exact simultaneous totals nor protection against
inter-sample growth is established.

Saved `check01.log` reports eight methods passing in 0.012 seconds. Source review
confirms coverage of exact directory-inclusive allocated bytes, repeated growth,
sparse logical limits, an empty-directory allocation breach, symlink/hardlink/
FIFO refusal, entry/depth limits, replaced root, time-limit descriptor cleanup,
and malformed limits. Cross-device entries and directory replacement during the
stat/open/return sequence are guarded in source but do not have dedicated cases
in this suite. `red01.log` remains the missing-module failure evidence. No tests,
historical jobs or numerical-body reads were executed by the reviewer.

Independently calculated SHA-256 values:

- `workflow_storage.py`: `a0b1bd5e3f73f22f3c5922740a8bddde0437c3c635ea372a6853d4d504e7751f`
- `test_storage.py`: `745364ab569415c1df836b09497e0d2cf7bd8ee1192997a75f93c9f344513400`
- `check01.log`: `9aa6cf2c94a5ffa7c761137bc3b945b62707ace2ea13f0fbbe1edc38a7c8adce`
- `red01.log`: `5a0e34ad869dba6dfeb9bd3e4eb9b417263f97cc3488bb0c924f34dcfcd9595a`

Integration must select the actual owned roots, retain observed failures and
cleanup evidence, combine this observation with registered write/checkpoint/event
reservations and the free-disk guard, and distinguish logical bytes from physical
allocation. Process RSS, physical hard quotas, capacity of a retained graph job,
financial outcomes and empirical admission are not proved here.
