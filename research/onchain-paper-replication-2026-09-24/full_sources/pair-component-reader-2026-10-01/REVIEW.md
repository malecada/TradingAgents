# Independent corrected component review

Accepted for the bounded resident numeric component-reader scope in SCOPE.md.
The initial findings and subsequent return-boundary finding are resolved in the
reviewed source. No remaining material blocker was found within that scope.
This acceptance does not admit an empirical execution or a registered sample
artifact. Only this new review file was written; no test, job or numerical data
read was executed by the reviewer.

The corrected source, test fixtures, retained snapshots and saved logs were
inspected independently. All 24 entries in bindings.json match current bytes;
its SHA256 is
`68846d7d07cda31d6f6c041546e3b0b42d0208aeff7cc8906df6bdf2712e3a76`.
This is the declared direct-file set, not a complete source/runtime closure.

The defect closures are concrete:

- CR1: `reader.py:57` hashes exactly the admitted extent with bounded requests,
  refuses early EOF and checks one trailing byte. Both full-file hash sites
  supply the saved extent. The red02 growing-file case retains the original
  1,000,176-versus-177-byte failure.
- CR2: `reader.py:39` adds O_NONBLOCK before fstat and retains O_NOFOLLOW and
  O_CLOEXEC. Nonregular descriptors are refused and closed. The saved FIFO
  regression exercises a real tiny FIFO in a forked child with a one-second
  parent deadline and kill/wait cleanup on the old blocking behavior.
- CR3: `reader.py:70` uses context-managed scandir, rejects the first foreign or
  repeated name and verifies exact coverage. red03's missing DirEntry.path is
  retained as a test-double error, not evidence of this defect; corrected red04
  demonstrates the intended excessive-enumeration failure.
- Return boundary: `reader.py:234–237` checks exact inventory and every saved
  path signature after the final digest loop and tree reconstruction, before
  the final lease. The only source change from reader.py.check02 is this
  compact check. red05 reproduces both a foreign entry added during the final
  manifest hash and an earlier member changed while the last member is hashed.
  Both cases now refuse in saved check03.

The reader joins exact member coverage, manifest/context hash, supported numeric
NPY headers, dtype/shape, file extent and hash before the first np.empty call.
Declared aggregate encoded bytes include the manifest and NPY headers;
resident payload bytes count each array once because repeated references are
rejected. Loaded bytes, including their exact header, are hashed before they
are returned. C/F reshaping does not duplicate payloads. The inspected code
uses context-managed ordinary file descriptors and does not invoke np.load,
memory maps, archive readers or pickle.

Saved check03 reports 15 passing synthetic tests in 0.176 seconds. The tests
cover the four defect groups plus aggregate refusal before allocation, a bad
late member, disguised NPZ, links, member omission/reuse, endian bytes, ordinary
C/F and empty-array round trips, lease loss and descriptor closure. The prior
eight-test and thirteen-test passes remain qualified by their later findings;
red01–red05 and original/check02 snapshots remain preserved. Passing status is
reported from saved evidence, not an independent rerun.

Evidence SHA256:

- reader.py: `3f9ebf731b5027f3282e8d4c7ae8a66c8d25f4aa8a989e2a8cfbd44d3d27cc50`
- test_reader.py: `518a98b1edb6138734da502232efac341024db494e924a4facbf0eb9a40a6d7f`
- SCOPE.md: `88f5bdb3dc1a9ce4792b3c65008ff547037261ff2c105ff019674fb497bedad7`
- check03.log: `97e0c8dd8a3974ec8b6dac5136b8e15822b808beb89a79a68dfdd0463a6af2cc`
- red05.log: `b35e3ab4a2c4364ba4cc8b28121acb52338851ddcc7af1ec2f907e0d7fa4fbf8`

The observations do not establish an atomic snapshot against continuous external
mutation; immutable artifact ownership remains an outer prerequisite. Array
payload caps are not whole-process RAM, Python metadata, cumulative I/O or
physical workflow quotas. Actual guard admission, registered read-policy and
owner/event/sample joins, sampler provenance, historical artifact reuse,
dictionary/MCM publication, full representation reuse and empirical admission
were not tested by this component. Those qualifications in SCOPE.md are retained.
