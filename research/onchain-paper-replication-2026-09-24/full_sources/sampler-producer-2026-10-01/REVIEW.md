# Independent corrected sampler-producer review

Accepted for the bounded first-attempt resident publication scope in SCOPE.md.
SP1–SP3 and the separate event-byte accounting issue are resolved in the inspected
source. No remaining blocker was found for that scope. Full-fold publication,
empirical execution, downstream provenance-proof admission and continuation are
not released by this review.

The final source, actual fixture code, retained failures/snapshots, scope and
metadata arithmetic were inspected independently. All 140 declared file hashes
match current bytes. bindings.json SHA256 is
`8cac94a5d0ce260b7d941f3144c5f135b6e754f5aaca76f16ee56a8254f37a3e`.
This is direct component/dependency evidence, not complete empirical source or
runtime closure. Only this review file was written. No tests, jobs or numerical
files were opened or executed by the reviewer.

The corrections address the concrete failure boundaries:

- SP1: compact training hashes are retained, then both samples and payload
  references are deleted before strict artifact reload. The weak-reference
  regression checks every original graph array is gone at the reload boundary,
  closing the third-copy overlap under the two-copy allowance.
- SP2: a full lease follows complete.json publication before success returns.
  The regression redirects the live journal during completion publication and
  requires refusal with both complete and failed markers preserved. A future
  proof consumer must reject that conflict; complete.json alone is insufficient.
- SP3: a fresh lease immediately precedes exclusive attempt mkdir after parent
  hashing/setup. The regression redirects the live journal after a parent hash
  and confirms no attempt directory is created. This is live-object drift, not
  an actual kernel-death test.
- Event bytes: the reservation includes an additional metadata allowance for
  FeatureJournal's event. Before writing, its size is computed using registered
  lifecycle._encode, including indentation and trailing newline, and checked
  against both metadata and event-read limits. The final positive test compares
  recorded event size and aggregate component size with actual saved file sizes.

The formula `(sample_count+4)*metadata_cap + artifact_cap` covers start, draws,
complete, failed and the separate feature event, plus component files. Existing
owner/claim/pair files are excluded as pre-existing state. NPY-header/payload and
canonical component-manifest sizes are computed before publication; fixed-width
hash placeholders preserve encoded length. These logical byte limits are not
filesystem block quotas or whole-process RAM limits.

The inspected producer joins actual registered owner, source bytes, both selected
policy routes and an empty first-owner feature journal. A fixed exclusive attempt
identity precedes sampling; any retained partial, failed or complete identity
refuses redraw. Durable draw records join the core's hash/RNG chain, and the proof
references the owner/start, draw files, policies, sample identity and exact event
and component hashes. Failure preserves existing evidence and attempts a failure
marker; if that write fails, the retained reservation still prevents redraw.

Saved check04 reports ten tests passing in 93.262 seconds. Earlier evidence is
preserved: check01's six passes were insufficient; red02 reproduced SP1–SP3;
check02 had nine passes; red03 reproduced the missing event allowance; check03
retains nine passes and its 1112-versus-1256-byte assertion failure. The final
encoding correction resolves that failure. The tests use real tiny temporary
registration/ResearchRun/journals and synthetic sampling; kernel guard observations
are mocked. No reviewer rerun is claimed.

Evidence SHA256:

- producer.py: `59f55292f2e440debc5eff8ca55fedd452ba0ad4f7822cc3ce6616b640795a56`
- test_producer.py: `6683649d7845d9549fa6f2ee6847e0da35b84c86bf89440578e3b5be40c4d8de`
- check04.log: `1620f5bd12caf5fc9b2e792964fe7a9918e8c04d0310d1351d12bb99dfb679bb`
- SCOPE.md: `a37ceee67f828172eefbc9d443fadf0d4882fb05a061774ed5c7efe8b8ac6a94`
- SCALING_CHECK.json: `88692fde62e015b04c242d6469abb5265152ca0158736b75b902339ebb12bd81`

The scaling arithmetic was independently reconstructed using only stdlib JSON
and synthetic path/hash strings: 512 absolute draw references alone occupy
138,753 bytes at this checkout with a one-character experiment name, exceeding
the 65,536-byte ceiling before other proof fields. Therefore this format cannot
complete a full 512-draw publication here. Compact references or a prospectively
reviewed larger bounded metadata policy are mandatory; reducing the scientific
sample count is not authorized. Measured resources, provenance-aware downstream
proof admission, historical reuse, exact resume, physical accounting, orphan
reconciliation, dictionary/MCM publication and empirical release remain separate.
