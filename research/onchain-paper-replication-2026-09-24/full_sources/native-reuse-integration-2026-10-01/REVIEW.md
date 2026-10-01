# Independent native-reuse integration review — acceptance withheld

This initial source review identifies two historical lease defects. The saved
integration log was still active at review time: the repeated-batch/guard-loss
method had passed and the normal two-fit executor method had not yet reported a
terminal result. No completed integration result or launch release is claimed.

## NR1 — validation-to-inventory capture accepts new foreign entries

`native_reuse.py:114–126` enumerates historical directories after the science
inspection and uses every observed name as the future allowed inventory. Only
pending and failed-marker names are refused at capture. If an otherwise foreign
entry appears in a graph attempt, representation publication or other strictly
validated directory after science inspection returns but before this capture,
the entry becomes part of the accepted baseline. Later `_output_inventory`
calls compare against that enlarged baseline and no longer reject it.

The transition from the validated historical inspection into the current
consumer's retained lease must preserve the admitted inventory. Derive expected
names from the verified proof/component declarations, or bracket capture with
exact predecessor inventory checks and require equality before installing the
baseline. Keep streaming count bounds. Add a regression injecting a foreign
entry specifically after the scientific inspection and before capture; an entry
present before inspection only tests the predecessor's existing refusal.

## NR2 — late broken lifecycle failure marker is invisible

`native_reuse.py:134` checks only `failed.json.exists()` for the historical
lifecycle. A broken `failed.json` symlink introduced after initial history
inspection has `exists() == False`, so the current consumer lease accepts it.
The historical `research_runs/<experiment>` directory itself is not part of the
captured inventories, only its outputs directory is. The initial history reader
already treats broken terminal links as conflicts; the retained consumer lease
must preserve that rule with an `exists() or is_symlink()` refusal. Add a late
broken-link case at a batch/verification boundary.

## Source and interface observations

The new route is explicitly selected from the actual current ResearchRun's
registered execution job. It uses a separate reuse reference, source-transition
input, native batch policy and binding output. Current owner metadata is pinned,
the maintained guard boundary joins the actual current command, policy, monitor
identity and liveness, and the historical root must appear in its disk paths.
The source transition retains all historical library files, allows replacement
only of the job-payload bridge, requires exact before/after hashes, registers
new reader dependencies, and compares historical/current/runtime checkout source
bytes. This is an explicit source transition, not a claim that the entire old
execution identity remains unchanged.

The dispatch branch passes real examples/scaler through the accepted scientific
inspection and returns the existing native FixedFeatureMap/PreparedFeatures
interface. It publishes the binding through the normal current ResearchRun path.
No source path reopens the old producer or historical journal. Current source,
input and owner checks surround map operations; the inherited numeric allowance
continues to exclude model state, aliases/autograd storage beyond tracked tensor
wrappers, Python overhead and process RSS.

Reviewed source SHA-256 values:

- `tradingagents/research/onchain_replication/native_reuse.py`: `ddd83e9c1542c0759f772684aee16ecc87c6a3f5a18c87ced54b3b2e8c5f4fad`
- `tradingagents/research/onchain_replication/job_payload.py`: `5863fdcf5bfc1b4dfcdb68839d16a23f7182467c9045024889fe5a9cf0819c3b`
- `test_reuse.py`: `e2ea0fb99d03596b5d50a6d6b30994fd3ad01b3d18ff79139e44aba131a8d634`

No test, job, fit or numerical-array inspection was executed by the reviewer.
The active fixture mocks the OS guard boundary while using an actual temporary
ResearchRun; it cannot establish real kernel admission or resource feasibility.
Final corrected-source review, terminal integration evidence and a separately
reviewed actual guarded consumer remain required. No empirical release follows
from this note.
