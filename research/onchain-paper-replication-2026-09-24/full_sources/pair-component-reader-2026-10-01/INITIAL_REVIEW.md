# Initial independent component review

Acceptance is withheld for three bounded-I/O defects. This review covers the
initial reader preserved as `reader.py.original`, not an eventual corrected
reader. Source and saved synthetic evidence were inspected without executing
tests, opening empirical arrays, changing source or launching a job.

1. **CR1 — hashing can consume an unbounded concurrent append.**
   `reader.py.original:57–62`, called at lines 173 and 215, reads until EOF
   despite an admitted exact file size. A growing regular file can exceed the
   registered read bound before the final signature check refuses it. The
   author identified this independently. Saved `red02.log` reproduces the
   defect: 1,000,176 bytes consumed for an admitted 176-byte file, exceeding
   the 177-byte extent-plus-sentinel ceiling. Hash exactly the expected
   extent with bounded requests, refuse early EOF, then read at most one
   trailing byte. Apply this to both admission and final rehash.
2. **CR2 — nonregular files can block before type validation.**
   `reader.py.original:39–43` opens with blocking `O_RDONLY` before `fstat`
   checks `S_ISREG`. A FIFO substituted for a declared member or manifest
   waits for a writer, preventing refusal and subsequent lease checks.
   Open with `O_NONBLOCK` as well as the existing no-follow/close-on-exec
   flags, then reject nonregular descriptors and close them. A preliminary
   `lstat` alone does not close the substitution window. Add a controlled
   synthetic boundary test that cannot hang when the flag is absent.
3. **CR3 — unexpected directory entries bypass the metadata-memory bound.**
   `reader.py.original:143,211` materializes the entire directory iterator
   into a set before comparing against expected files. Manifest limits bound
   registered names, but do not bound arbitrarily many foreign entries.
   Enumerate incrementally with a context-managed directory iterator and
   refuse on the first unexpected or duplicate name; also verify missing
   members after enumeration. Test early refusal with an iterator that must
   not be consumed past the first foreign entry.

The remaining inspected structure supports the proposed narrow contract:
manifest/tree/declared aggregate caps precede array allocation; array members
must occur exactly once; headers are length-bounded before their body is read;
numeric dtype, shape and exact payload extent are joined to each declaration;
materialization hashes the loaded bytes and preserves C/F ordering. File
descriptors are context-managed, and signatures, inventory and lease are
rechecked before return. These observations do not resolve the three defects.

Saved `check01.log` reports eight passing tests in 0.086 seconds. The initial
tests cover ordinary numeric/F-order/empty-array round trips, aggregate refusal,
a late malformed member, disguised NPZ refusal, links/inventory, repeated and
omitted tree members, lease loss and late-file mutation with handle closure.
Saved `red02.log` reports three cases in 0.040 seconds: growing-file failure,
with endian and oversized-header tests passing. No independent execution is
claimed. FIFO refusal and bounded enumeration were not established by these
saved tests. Source and tests may be under correction by their assigned owner.

Evidence SHA256:

- `reader.py.original`: `182dfcf353cab910b37bf75dbdb23d0de3fa5c0032a8e2de5df8343e3ff71632`
- `test_reader.py.original`: `1da4737518554ac28b0df41f9ee59eed314da08786955dbbdf6cb13738f7268f`
- `check01.log`: `82ddf33145538deb9eb3b944c344c8002022c9e7031c023873033377f7abb07a`
- `red02.log`: `609b8e266daf8da78c6f5f83f642f9fd727010e5b84d62eb3b1291e590ad955d`

This is a generic resident numeric reader review. Registered owner/event/sample
joins, provenance of a sampler draw, physical/process memory accounting,
complete source closure and empirical admission remain outside this scope.
