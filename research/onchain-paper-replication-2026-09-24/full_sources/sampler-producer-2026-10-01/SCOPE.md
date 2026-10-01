# Registered first-attempt resident sampler producer

This isolated producer joins the actual admitted OwnedJournal/Route and empty
first-owner FeatureJournal. The selected job and producer must name the same
registered sampler and artifact-read inputs. Direct producer, core, component
writer and artifact reader source bytes are registered and checked at the import
checkout and admitted run root. Historical sampler continuation is refused.
Actual parent hashes are checked before drawing; the workload validates the final
induced sample population and configuration before publication.

The attempt directory is fixed by workflow and actual experiment under a separate
onchain_sampler_workflows root. Existing attempts (partial, failed or complete)
are never redrawn. An exclusive mkdir reserves the identity; durable start and
per-draw metadata preserve the exact owner, source/policy bindings, configuration,
PCG64 state and draw chain. Failure preserves every existing file and attempts a
failed.json marker; if even that write fails, the partial reservation remains and
still refuses relaunch. This is not automatic rollback or a resume implementation.

The unchanged leased sampler core provides per-draw checks. The array-backed
payload uses native float64/int64 arrays. Publication precomputes NPY-v1 headers,
array bytes and component-manifest encoding; fixed-width placeholder hashes have
the same encoded length as the real SHA256 values. Both encoded artifact and
manifest caps are checked before FeatureJournal.__call__, together with the
strict reader's two-copy numeric allowance. Original sample arrays are released
after their durable publication and before reloading, so they do not coexist as
a third payload with loaded arrays and immutable AttributedGraph copies.

The completion proof binds the actual claim/owner, reserved start/source record,
all draw-file references, initial/final RNG states, sample identity/training hashes,
registered sampler/read policies and exact feature event/component hashes. A final
lease follows proof publication. A failure after complete.json exists preserves
failed.json too; such conflicting markers must be refused by future proof
admission, never treated as a successful artifact merely because complete exists.

## Reservation and operational limits

The logical encoded-byte reservation is (sample_count+4)*metadata_cap plus
artifact_cap. It covers bounded sampler start, per-draw, complete and failed
metadata, the separate FeatureJournal event and the numerical component allowance.
Event size uses the actual lifecycle._encode pretty JSON/newline encoding and
must fit both its metadata allowance and the artifact reader event limit before
FeatureJournal writes anything. Pre-existing owner/start/claim and pair-journal files are not new
sampler writes. Encoded-byte caps are not filesystem allocated-block quotas,
whole-workflow physical accounting, process RSS or a duration measurement.
NumPy choice scratch, parent inputs and Python metadata still require the outer
guard. The existing mapped-weight 20GiB policy and scientific caps are unchanged.

Actual kernel guard observations are mocked in the synthetic fixtures. This
producer does not grant empirical admission, mapped full-fold feasibility or a
new research attempt. Partial work cannot yet be resumed from exact retained
weights/RNG/sample state. Existing sample-artifact admission does not inspect the
sampler completion proof; a separate provenance-aware consumer must require and
revalidate that proof, including terminal conflicts, sources, policies and chain.
Dictionary/MCM publication and complete representation reuse remain separate work.

## Evidence

red01 retained six cases with seven missing-implementation failures (one subtest)
in0.002s. check01 closed six passes/59.614s. Independent INITIAL_REVIEW withheld
for SP1 original-array overlap during reload, SP2 absent lease after completion
publication, and SP3 stale lease before exclusive attempt creation. Original
source/tests remain retained. red02 reproduced all three intended failures in
25.917s. Corrections release originals before reload, recheck ownership immediately
before reservation, and check again after the completion proof is written.
check02 CLOSED: nine passes/86.166s. Review then identified the separate event
was absent from the reservation. red03 reproduced that missing allowance before
draw: one intended failure/7.520s. The producer now reserves its event allowance
and preflights event encoding too. check03 CLOSED with nine passes and one
expected-byte assertion failure/92.330s: canonical JSON predicted1112bytes versus
1256bytes actually written by lifecycle._encode. The exact source/tests are
retained. Event sizing now uses that registered writer encoding. check04
CLOSED exit0/session60639: ten passes/93.262s. Tests use actual temporary registration/ResearchRun,
FeatureJournal and pair owner with three synthetic sampled neighborhoods. They
check exact maintained-sampler identity/records, proof references/RNG, actual
encoded component bytes, refusal of existing/partial/failed attempts, pre-write
capacity rejection, source-policy routing, and preservation on draw/lease failure.
The pre-reservation and post-completion lease regressions redirect the live journal;
they do not simulate actual kernel guard death. Weak references test original-array
release before the reader is entered. No empirical source data or fit is executed.

Sampler metadata files currently have a hard64KiB ceiling. SCALING_CHECK.json
records deterministic metadata arithmetic: even a one-character experiment name
requires 138753bytes for512absolute draw references at this checkout,
before the rest of the completion proof. Thus this format cannot publish a full
512-draw proof under that ceiling. It fails explicitly and retains the attempt;
this is not permission to reduce the scientific sample count. Compact exact
references or a prospectively reviewed larger bounded metadata policy are required
before full-fold sampling. The arithmetic reads no empirical data and draws no
samples. Resource feasibility and proof-admission work remain mandatory.
