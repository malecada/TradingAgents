# Fresh closed-array offload caller candidate

Exact selection:30 original arrays from six COMPLETE modern graph jobs04/05/06/07/
08/10,3,021,553,488logical bytes and3,021,758,464allocated bytes. Maximum individual
full-recovery scratch387,431,648B plus16MiB headroom above the unchanged10GiB floor.
The sealed metadata preparer joined original claim/terminal/index/manifest/component/
guard/owner and accepted producer reviews, without reading array bodies. Its seal
is807dc0fda2716370cf09a17b2ccc97db76fb0782a9fb810df2b0c749a38ab064.

Candidate worker is fixed to new `closed-array-pilot-offload-2026-10-05-01` and
refuses execution outside that fresh storage directory. It authenticates the sealed
selection, reviewed config/source commit/bodies and actual existing guard lease.
Before every row it rechecks metadata pins, closed producer/PID/cgroup status,
protected roots, active claim references, Git tracked status and complete-recovery
scratch. It calls unchanged reviewed `cold-offload-2026-09-29-03.offload_one` and
`finish` with the accepted latest transport. Existing historical workers are not
repurposed: their fixed identities/file counts remain unchanged. No new supervisor
or transport implementation is introduced.

Generic offload_one rechecks source identity/hash, uploads, performs a fresh full
get and hash, roundtrips restoration metadata, publishes verification+sidecar,
then unlinks only that source; failure retains original/failed scratch. Candidate
adds attempted/failed/skipped receipts and stops after first failed row without
retry. Successful rows remain independently recoverable. Root owns launch and
outer terminal reconciliation; the candidate has only an explicit guarded-worker
entry, no automatic launcher.

Protected metadata binds Jan3 dictionary graph manifestbc3bf9a6 and original
claim/source-index, June13 graph and July25 graph; original canonical input bundle
is protected as a root. Root confirmed the original dictionary's sole training
graph67ffff78… is Jan3. No dictionary numerical body was inspected. Fresh config
still has dictionary_sources_reviewed=false, null source_commit and empty source
closure: these deliberate refusal states require Root's final exact review/binding.
Other than opaque hashes of compact metadata/source, no raw/array data or credential
contents were read. No transfer, native job, claim or retirement occurred.

Four focused offline tests pass: per-row verification ordering; failure stops,
retains attempted/failed and skips remaining rows; invalid selection refusal; and
receipt-error handling preserves the original fatal exception. No resource/capacity
claim follows. Proposed existing native envelope is256MiB/high192MiB/swap0,
3GiB reserve/3.5GiB startup/14,400s/twoCPU; Root must freeze actual guard/source
closure and review the installed entry before any external action.
