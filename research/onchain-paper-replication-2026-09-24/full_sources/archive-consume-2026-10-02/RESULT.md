# Bounded archive cache consumption

New archive_consume.consume accepts trusted receipt bytes/hash and exact scope,
retrieves and validates full member bytes, removes only its newly created cache
payload, and returns immutable bytes. Source/old-copy directories need not exist
and are never disposed. Success retains three metadata receipts. Failed attempts
cannot reopen. Late failures after deliberate cache disposal retain failure and
remote evidence; they do not recreate the disposed cache.

Evidence:
- red01:18absent-module failures0.18s.
- check01:53passed and1fixture assertion failure0.83s; symlink was correctly
  rejected by O_NOFOLLOW/OSError but fixture expected only ValueError/RuntimeError.
  Original test retained in test-check01.py; assertion corrected only.
- check02:54passed0.84s (18consumer plus36archive/transport cases).
- Independent ACC1 found final owned descriptor close uncertainty escaped the
  failure/fatal handler. Original source retained as consume-check02.py.
- cleanup-red01:both targeted cases failed0.26s, success body and primary in flight.
- check03:56passed0.87s after fatal closure/primary preservation/fresh inode-pinned
  cleanup evidence correction. REVIEW accepted
  9f8b048e81fc10168a55325e3e6ef7bdf1cfdbd658f66a9facc507501529352e.

The synchronous helper bounds one cache payload to8MiB. It does not bound
parallel calls, retained returned byte objects, cumulative metadata, transport
scratch or physical allocation. Caller owns those budgets and genuine guard/
finite transport enforcement. This is synthetic verification; no original-source
eviction, current-owner admission or new external operation occurred.
