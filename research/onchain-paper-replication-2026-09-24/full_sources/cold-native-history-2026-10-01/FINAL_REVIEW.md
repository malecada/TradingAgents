# Independent corrected-source review

Acceptance remains withheld for one residual bounded-I/O defect. The original
`REVIEW.md` remains unchanged. This review covers the completed-run certificate
only; it does not admit native features or a current research worker.

## CH1–CH3 correction assessment

The corrected reader now checks its local remaining byte allowance and retained
signature before opening, checks the opened descriptor before reading, reads at
most the admitted extent plus one byte, and pins the exact unique-file size for
subsequent reads. Aggregate accounting is based on admitted bytes. Output
enumeration now uses incremental `os.scandir`, stops at the first foreign entry,
and repeats after all compact-file rereads. Monitor/cgroup death is also repeated
at the final boundary. Unavailable cells require a nonempty string reason.
These changes address the specific CH1–CH3 cases in the original review.

The saved `check03.log` reports 12 tests passing in 0.095 seconds. Inspection of
the tests confirms coverage of static cap refusal before opening, growth between
stat and open before reading, exact unique-byte accounting and reread limits,
early and late foreign-output refusal, final monitor revival, and missing
unavailable reasons. Some semantic negatives inject decoded records through a
mocked metadata reader; they test the joins rather than fully rehashed malformed
on-disk chains. No test was rerun during this review.

## CH4 — blocking open precedes descriptor validation

`terminal.py:25` calls `os.open(path, O_RDONLY | O_NOFOLLOW)` after the regular-file
`lstat` check. A concurrent replacement of that regular file by a FIFO with no
writer blocks inside `open`; the subsequent `fstat` rejection is never reached.
`O_NOFOLLOW` prevents a final symlink traversal but does not prevent opening a
FIFO. Thus the new local reader does not yet provide the bounded refusal claimed
by this component, even though its regular-file read sizes are bounded.

Open with `O_NONBLOCK` before descriptor validation, retaining the existing type,
identity, extent and hash checks. The accepted strict component reader already
uses this pattern. Add a regression for substitution between the initial stat
and open, using an isolated child with a hard timeout and cleanup if exercising
an actual FIFO. A direct flag assertion can supplement that regression. This
finding follows from source inspection; no blocking probe was executed here.

## Evidence identities and limits

Independently calculated SHA-256 values:

- `terminal.py`: `089cb473103e7e7eef9e517e4e5860fd096486d8de6a79bf62bd9576edfb57a6`
- `test_terminal.py`: `c8c156347d2bfbb35fbe311d1ea84347b44422aea8a4c09e1714454490548af5`
- `check03.log`: `ceaf3457ae5afadae4f4dad4b1ee7e4e4d15ce25563071afb593cda091900f6b`
- Preserved `terminal.py.check02`: `4a4fdd4ca04a005896153ee27baf92e3fdfd8aa3119a3fa35c390d931c34d1ee`
- Preserved `test_terminal.py.check02`: `6e32e9ef9e08c01b150e05f7d4f3d294387bdb8d8f8bf05ffb9364c1f7f87895`
- Original `REVIEW.md`: `6c613d9ebe3e24d3aec0b12844873c935cb7aaebf54a6a19e59c253fd7cec230`
- `SCOPE.md`: `3d0fdcf471c0b97a0c57647638bc4d360ba5ffa462b9f2b893d08c00cd2642bc`

The explicit false current-run, native-feature, source-compatibility and array-read
flags correctly limit the certificate. This review does not establish scientific
denominator or seal/member joins, numerical array correctness, resource-policy
compatibility, a current guard, atomic snapshots under continuous mutation,
financial performance or empirical release. No source, test, registration,
ledger or historical result was modified.
