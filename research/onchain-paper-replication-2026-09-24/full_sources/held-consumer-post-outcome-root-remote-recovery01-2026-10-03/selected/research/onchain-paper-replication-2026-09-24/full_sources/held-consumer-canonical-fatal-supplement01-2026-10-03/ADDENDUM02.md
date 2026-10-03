# Independent-control aids

The source remains exact `e05aa225b6bcf8f4e14a644d0a03f2a9aff6cb36ae4a5b02a3dded72d94580b9`.
Initial12-body MANIFEST01 `2724d3e13b2fcf3ecb416e03d7dc9c83e9ac9c4eace54df143617a6d282dcedb`
and all its bodies remain unchanged. MANIFEST02 includes that immutable manifest
and the added review aids. No independent acceptance is asserted by the author.

`exact_reducer02.py` wraps the actual reducer source in `select(primary,error,fatal)`;
only indentation and the surrounding function/return are added. The verbatim
original slice and line span are retained in `CALLBACK_RESULTS02.json`. The
predicate is a parameter so a reviewer can bind the actual pinned `_fatal`
without importing the numerical `score_batches` module.

`callback_controls02.py` extracts the actual method's action/postcheck statements
into a scalar pipeline. It explicitly renames two `self._check()` calls to an
opaque `check()` callback and supplies the actual extracted pure fatal predicate.
It excludes the real lock and cleanup; those are unchanged by the inverse and
their utility ordering is tested separately in regression01. This is a declared
test adaptation, not a real evidence capability or fake authority object.

Six passing controls cover original MemoryError followed by SystemExit and a
diagnostic KeyboardInterrupt; original SystemExit followed by ordinary recheck
and diagnostic MemoryError; ordinary action followed by first recheck fatal;
ordinary action/recheck followed by first diagnostic fatal; successful action
whose postcheck refuses; and result return after both checks pass. Every trace
is `check0, action, check1`, followed by one note attempt only in the applicable
diagnostic branch. Each selected exception is checked by identity. No callback
result is returned after a failing recheck.

These controls do not certify genuine check/lease/Binding/Owner behavior,
arbitrary callback side effects, allocation or call-count exception equivalence,
capacity, timeout resolution or run eligibility. No source was installed.
