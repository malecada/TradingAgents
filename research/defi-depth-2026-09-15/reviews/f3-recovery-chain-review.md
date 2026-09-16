# Independent F3 recovery-chain review

## Initial disposition

Changes required to bind the additional execution commit to its source/config
bytes. The review covers the new recovery-chain helper, invented tests and F3
source/preparer/charter integration. No active F1 scientific or recovery root,
empirical financial values, acquisition or actual context preparation was accessed.
Only this review file was written.

## Material finding

Initial `recovery_chain.verify` checks `recovery_source` only against a40-hex
regular expression. The supplied adapter, decision and initial investigation are
checked against the supplied config, but their bytes are not compared with Git
blobs at that asserted recovery commit. An independent invented counterexample
changed the recovery_source in both identical attachment/start records from the
fixture's b*40 to c*40. Verification passed with all source/config bytes unchanged.
Thus the helper currently preserves self-consistent records without establishing
the claimed second execution source.

Require exact committed-blob comparison for the adapter, decision, initial review
and recovery config at the recorded recovery commit. The preparation and F3 main
can use the coordination/future execution checkout's retained Git history; no
read of either active root or network lookup is needed. Require a full commit ID
and fail on missing/different blobs. Preserve hashes of the separately registered
original claim and terminal and all existing empty-state/budget/chronology rules.

## Positive checks and bounded interpretation

The helper links original claim hash to complete scientific terminal, requires
byte-identical shared attachment/start records, checks original experiment/source/
start time, unchanged recovery/no-new-claim flags and empty initial output scope,
then links external completion to the exact scientific terminal hash. Chronology
requires UTC-aware original-start/recovery-start/scientific-end/recovery-end in
order. No additional scientific claim or confidence inference arises.

The F3 builder registers attachment, start, completion, config, adapter, decision,
initial investigation and final adapter review alongside the original claim and
terminal. The main calls recovery verification before context use and capture,
and writes both source identities into history. The charter explicitly preserves
additional recovery provenance without resetting source retries, samples or
financial budgets. The scientific cell/output denominator is unchanged.

The verifier covers the supplied chain; the eventual actual closure must still
retain the complete operational recovery directory and shared marker, including
any failed/pending or contradictory operational receipt. Selecting only a valid
completion subset must not conceal an observed recovery error. A chain pass does
not by itself prove an absent competing worker, an unchanged runtime throughout
execution, source availability or economic correctness; those require the actual
closure evidence and independent review.

Initial source SHA256: `7ada511ff0944d0f2a2c3d8fc2782c510c8c390777afbdb494c00f39add3891e`.


## Committed-source correction disposition

**PASS for the corrected chain verifier and prospective F3 integration.**
`verify(inputs, root)` now reads the four fixed adapter/decision/investigation/
config blobs at the exact recorded40-hex recovery commit and requires equality
to the registered bytes. Missing commits and differing blobs refuse the chain.
Both the builder and F3 main pass their own retained Git root before capture;
no access to an active scientific or recovery root is required.

All13 named recovery-chain/context tests passed. An additional independent
real-Git fixture created a second valid commit containing a different adapter,
then changed the claimed recovery commit to that existing commit while retaining
the original registered source/config bytes. The verifier correctly rejected it
with the source/config-byte mismatch, covering a valid-but-wrong commit as well
as the suite's nonexistent all-zero commit. Previous findings above remain
preserved as review history. No actual chain or empirical run was read.

## Complete recovery-directory requirement at actual closure

The corrected verifier validates the supplied chain; it intentionally cannot
infer absence of other files from a subset of input bytes. Before actual F3
admission, the terminal recovery audit must enumerate the entire original
operational recovery directory, including hidden pending files, together with
the original-root shared attachment marker. Retain exact relative paths, file
types, lengths and hashes, and copy/hash every observed file rather than choosing
only started.json and complete.json. For an unambiguous successful event, the
external protocol receipt set is started.json plus complete.json, with a matching
shared marker. Any failed.json, pending publication, contradictory terminal or
unexpected recovery event must remain visible and receive an explicit disposition.
A completion subset must not silently override such evidence.

A small immutable closure inventory/manifest and its independent review, pinned
as F3 inputs, are sufficient; no new empirical query, financial claim or general
recovery framework is needed. The import should record original source paths
and source/adapter commits and verify copied bytes. A standard future F3 gate
must not treat this prospective chain PASS as the missing actual inventory audit.
If operational errors coexist with a valid original scientific completion,
classify the operational event honestly and assess it explicitly before allowing
source handoff. Do not manufacture replacement receipts or edit frozen outputs.

Thus no code/provenance blocker remains in the reviewed correction itself.
Actual recovery termination, full inventory, copy integrity, final gate/input
binding and scientific/source closure remain prerequisites; this review does
not claim they have occurred or authorize another attachment.

Corrected reviewed SHA256 values:

- `recovery_chain.py`: `f02b3dec7d4a17a5f6f50fafe09a7114c283c1f79650bc871a4320f7264bae3d`
- `f3_source.py`: `83e47145f31658093a952ded392539f9d1d613b673dbad133a6bf8ddd8cd1334`
- `prepare_f3.py`: `1b3ecccc99f2b36501f5c7b226711c1e106e8a309dab6585b94c678662bd1d23`
- `f3-charter.md`: `0ffc900d8004dcc93cd6d16b911ac3bcb43f53cb9a4ca3fd4d3ef2cc596a3f67`


## Imported-directory exactness re-review

**PASS for the added imported-directory guard.** The helper now requires the
complete imported event directory to contain exactly attachment.json, started.json
and complete.json; each must be a regular nonsymlink file with bytes equal to its
registered input. It rejects a symlink event directory and extra failed, pending
or unlisted records. This prevents F3 from ignoring contradictory records that
are present in its own imported directory.

All17 named chain/context tests passed. Independent same-byte receipt-symlink and
event-directory-symlink fixtures were both rejected. The original findings and
commit-binding correction above remain preserved. No active root or actual
recovery state was accessed.

The guard proves the imported directory's exactness, not completeness of the
copy from the original recovery root. The proposed separate registered
`f1-recovery-import.json` is the appropriate remaining link: record the entire
original relative inventory, types, byte lengths and SHA256 values; identify the
separate original-root shared marker and its attachment.json destination; bind
source/recovery identities and the terminal capture time. Require exact path/hash
agreement with the imported three files and the registered chain inputs. The
actual closure reviewer must inspect the original directory and marker after
terminal publication and confirm byte-exact copying. Do not inspect an active
root or create that actual manifest early merely to satisfy the schema.

The current prospective code pass does not claim that this original-to-import
manifest exists or has been verified. Once implemented, its binding and actual
terminal evidence remain part of exact F3 admission; no new experiment or source
query is necessary to establish this metadata chain.

Reviewed directory-guard source SHA256: `efc8091f75d167f971b0807bf501840932c516ea7fe35f875bcc97ba5b374004`.
Reviewed updated F3 charter SHA256: `4eb7dfd4fe469dd9232c09e47ae61e5890f4cfe995d44fb3b7b5bb38c936018e`.


## Registered import-manifest binding — final prospective disposition

**PASS for the additional required `recovery_import` input.** The verifier now
requires the manifest's original directory path to match the retained recovery
start record, its complete source member/hash map to equal started.json and
complete.json, the separate attachment source path/hash to match the original
claim-root marker, and the destination directory/member/hash map to equal all
three registered imported records. Main input enumeration and the builder now
include the manifest, and history records its SHA256. The builder also pins this
independent chain review. All previously reviewed commit, receipt, directory,
empty-state, budget and chronology checks remain.

All18 named chain/context tests passed. Four additional independent invented
checks altered source directory, original marker path, destination directory and
marker hash; each was rejected. The extra-source failed-record fixture is also
rejected. No actual manifest, origin directory or active root was opened.

The remaining requirement is evidential, not another code change: at terminal
closure independently enumerate and inspect the actual original recovery
namespace and marker, retain their observed types and bytes, and create the
immutable manifest from that complete inspection. Hash-map equality cannot
prove that an unobserved original file was not omitted when authoring a manifest.
The actual source inspection and copy verification remain necessary before the
future gate is frozen/admitted. This prospective pass does not authorize early
manifest creation, active-root reads or renewed recovery/source attempts.

Final prospective source hashes:

- `recovery_chain.py`: `96e9b8e4580123935efde4b05d175b8637e28ae9958dd85003d6da95a52dbb55`
- `prepare_f3.py`: `c1d2e1371de16e6a7936efb7f72483988ac566c206038dd24c781e66ee2a629f`
- `f3_source.py`: `83e47145f31658093a952ded392539f9d1d613b673dbad133a6bf8ddd8cd1334`
