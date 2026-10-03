# Independent local non-tail context03 review

Disposition: **ACCEPTED narrowly for the source correction of NTC4 and preservation of the reviewed local-preparation contracts**. No genuine authority, registration, transport, capacity, disposal or empirical execution is accepted.

Exact frozen candidate manifest `c94e977984bb9af15fd325eb45a6f4d53b9e6e13c135047189b5860c0377afc4` and source `7645b320badaa6827c1609b4d35e674c4e13e9fffc6097eaded9187004a75dad` were independently verified. All18 manifest entries were checked, including16 file bodies and two explicit retained synthetic symlink witnesses; five declared origin references match their hashes/lengths. The two unchanged accepted dependency bodies were independently rehashed. Author files, previous WITHHELD reviews and earlier harness failures remain unchanged.

## NTC4 reproduced and corrected

The exact original02 parent-rename→symlink interleaving was rerun in reviewer-owned fixtures. The actual02 bootstrap returns the bytes even though final canonical path differs, closing its one file descriptor. The same actual OS interleaving against03 raises ValueError and closes both distinct parent/file descriptors once. CHECK03.log retains both results and both witnesses. Neither witness is a valid source capsule or authority; the symlinks are explicitly listed in this review manifest.

The corrected bootstrap obtains the original parent stat and a no-follow directory descriptor, checks parent FD/path/canonical equality, opens the child relative to that held descriptor with no-follow/nonblocking flags, and checks the original child FD/relative-path/absolute-path signatures. Before returning, it rejoins both file identities and the original parent descriptor/path and final canonical paths. Bytes remain bounded by the original regular single-link file's1MiB stat extent, with at most64KiB reads and the one-byte growth check. Dependency SHA and execution of the captured source bytes remain unchanged.

Independent real tiny-file tests additionally reject regular parent replacement, ancestor/subdirectory replacement, file replacement with identical bytes but a different inode, symlink and hardlink source files, oversize before any read and missing child after acquiring the parent. Missing-child failure closes the parent exactly once. Growth refusal and source-read MemoryError with later ordinary close failures preserve the original fatal and close both distinct descriptors. Ordinary close uncertainty yields BootstrapCleanupFailure; a later first actual SystemExit outranks an earlier ordinary close error; a first actual fatal survives a second fatal while both closes are attempted. EDGES03.log retains all four named edge-test groups and their subcases. No new defect was found in these bounded checks.

## Preservation and local controls

Replacing only03's `bootstrap_read` with02's body reconstructs the entire02 module byte-for-byte and AST-for-AST. All import, loader, reservation, context, reader/recovery and activation behavior outside that function is unchanged. Both dependency pins remain exact. No broader module refactor, budget mutation or accepted-source replacement was performed by this review.

NTC1 fatal/growth, NTC2 creator-thread/reentrancy and NTC3 shared-alias revocation were independently rerun against03. Foreign-thread reservations refuse before committing counters and revoke the budget. A swallowed nested same-thread refusal still blocks the outer commit. Original reservations remain spent. Reader birth, body error, clean-body reader-close uncertainty and body fatal with later close uncertainty revoke all shared aliases; subsequent reservations refuse. Normal sequential shared-budget use is not redefined as a failed context.

Complete local original/recovered controls pass for score-batches (four members), raw-f32 MCM output (two members) and graph-artifact content including its NPY companion (three members). Original metadata/header/member bytes are retained. These are synthetic byte fixtures from the accepted format tests, not empirical arrays or live Owner outputs. Independent part accounting matches the unchanged floor-plus-one32KiB rule; a32768-byte proposal reserves65536. Local original/recovery counters are not actual command/framing/wire spend. Positive activation still raises NotImplementedError.

No new test failure occurred. The previous review's CHECK02 contextmanager-harness interpretation failure and all historical failed candidate evidence remain preserved in their original directories; they are not rewritten or relabeled by this acceptance.

## Scope and remaining requirements

Only unadmitted local source behavior is accepted. LocalContent metadata is not a genuine Binding/Owner/held/cold capability. No ResearchRun, claim, native unit, admission, source integration, network, actual SSH command, financial fit, retirement or deletion occurred. No numerical packages were imported and no empirical array values were decoded. This review does not activate the separate durable context, grant raw-f32/NPY held authority or resolve its paging/transport limitations.

The genuine selected durable source closure/Git anchor/runtime, finite registered population/policy/cumulative allowance, current native guard and one-use launcher, full byte transport and remote recovery, failure-retention and explicit disposition authority remain root requirements. Zero bytes are freed. Full55,439,818,752-byte payload and9,239,969,792-byte nontail scope remain unchanged, with capacity and numerical/model/gradient/checkpoint evidence still pending.
