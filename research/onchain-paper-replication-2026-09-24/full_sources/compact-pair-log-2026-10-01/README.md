# Compact matcher event history

`compact_pair_log.py` replaces a growing in-memory completed-pair map with an
append-only sequence of fixed 168-byte records in bounded files. A record binds
its event and pair occurrence ordinals, exact purpose and numerical identity,
score, convergence kind, iteration count, optional checkpoint manifest hash and
chained checksum. Start metadata binds owner/workflow/configuration/policy/context
and numerical-source hashes. Only one unmatched begin is allowed.

Every acknowledged record is fsynced and read back. An interrupted write poisons
the writer and remains retained. A terminal failure can preserve a pending pair
and up to one unacknowledged record. Directories never reopen under the same
identity; no suffix is truncated. Bounded replay retains one pending pair and
aggregate counters, rather than one Python object per completed comparison.
Two content/signature passes protect the sampled verification boundary under
the sole-writer contract; this is not an atomic filesystem snapshot or RSS limit.

The log does not independently derive occurrence uniqueness, inspect checkpoint
trees, establish convergence, grant successor admission or execute matching.
Those responsibilities belong to the caller. `checkpoint_path()` identifies a
prospective event-ordinal directory under an exclusively owned sibling checkpoint
namespace. No checkpoint files are produced by the log itself.

Evidence: `red01.log` contains ten expected missing-module failures;
`check01.log` records ten passes in 0.47 seconds. Synthetic cases cover ordered
completion/progress semantics, retained partial writes, invalid values, no replay,
lease loss, content/symlink/foreign-file corruption, late mutation and capacities.
Independent `REVIEW.md` accepts the bounded primitive, SHA
`f1d8b21fdb804dc845ed7396fa67dccb468fb262ad367aba4354adefa3ebdf5c`.
No research job or historical test identity was rerun.
