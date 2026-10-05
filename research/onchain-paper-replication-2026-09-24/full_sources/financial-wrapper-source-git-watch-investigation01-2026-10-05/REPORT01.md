# Actual source-receiver watch refusal: bounded investigation

Only this new report is written. No live source, Main, CAP, Parent, Git, registration, STATE, claim or existing outcome is changed. No network, Git command, empirical run or numerical import was performed.

Inspected receiver: `full_sources/financial-wrapper-serialized-storage-source-remote01-2026-10-05/`. Its recover01.py SHA is db66bc857b0ac61ff94a57cb3d3a7b02200049e7a19842adcb55965a9ff2603c; watch01.py SHA bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18; FAILED01.json SHA c258db8301da5f16f3069826d12c320bfc9ba6eb4f37e49d2b6d89854cbcc0fb; ACTUAL_ROOT_EXIT01.json SHA cc46fcfd636e6a957df026a2e094dcaa3510618fa91e563343e73d82ba90c7a1.

## Actual evidence and limits of attribution

FAILED01 records30 Git operations. First9 are remote, ls-remote, init, remote, config, config, fetch, rev-parse, ls-tree, all exit/reaped0. Calls10–30 are selected-object fetches. The last is pid102284, code null, actual_reaped_exit -9,1.515953860seconds,115stderr bytes,0stdout, no cleanup failures. Its actual child hard and soft RLIMIT_FSIZE readback was [4194304,4194304]. The preceding selected fetches completed normally. Calls preserve operation names, counts, hashes and cleanup, not full argv or stderr bodies; the precise selected OID is not available from that receipt alone.

The failed error is ordinary ValueError `owned per-file/hardlink bound`, produced only by watch01.py:19's combined `s.st_nlink==1 and s.st_size<=POLICY['file']`. The exact path, st_nlink and st_size were not retained. It is therefore impossible to distinguish the two conditions as a historical fact. A temporary Git hardlink is a plausible interpretation of the active-publication timing and settled compliant census supplied by Root; it is not proved. The settled largest pack2,760,012B and no current violations do not disprove a disappeared historical excess.

468 successful complete observations were retained. The last three show100/103/103members,3,547,136/3,563,520/3,567,616allocated bytes and3,309,858/3,311,868/3,312,003logical bytes; all one attempt/no recorded extent changes. Failed partial observations are not successful census data. Root receipt explicitly says FAILED_NO_RELAUNCH, actualRootexit1, session83538, selected_bodies_present=false, native_or_lifecycle_claim=false. No complete recovery is established.

## Concrete cause in observation scheduling

recover01.py:98 watches before Git. Its:100–113 installs and verifies native4MiBhard/soft FSIZE. While owned Git runs, :119 calls the same strict full-tree census before each stream-poll iteration; :132 repeats after Git exit and :151 after owned group kill/reap/pipe/selector cleanup. The owned Git process can publish object names during that active census.

watch01.py:56–73 already allows ChangingTree/FileNotFoundError to discard the entire partial scan and retry at most three times under one5s budget, using existing two100ms waits. However a non-single-link observation at:19 or:41 is ValueError and never reaches this publication retry. The error therefore terminates the owned group even if the link would disappear as publication completes. This is an error-classification seam, not evidence that the numeric budgets are too small.

## Minimal correction in a prospectively reviewed fresh receiver

Keep every active complete-tree scan. Do not remove recover01.py:119, ignore objects/tmp/pack names, accept partial counters, deduplicate away links, or increase any cap/retry/deadline. The Git process has no separate full-tree guard, unlike the numerical Parent/native-guard case, so merely moving scans before/after Git would remove the current active aggregate enforcement.

Split the combined predicate at watch01.py:19 and:41:

1. Check size <=4MiB first, unconditionally; any observed excess remains immediately terminal.
2. A regular file with nlink==1 follows the existing code unchanged.
3. nlink>1 may raise a dedicated subclass of ChangingTree ONLY when the caller is inside a currently live, owned fetch for the exact newly owned bare repository, and the canonical path is within that repository's objects/ subtree on the already checked device. This is a discarded observation, never accepted link ownership or accepted accounting. nlink0, links outside that precise subtree, and any hardlink in strict mode remain terminal. No broad catch of ValueError is added.
4. Retain bounded relative path, dev/inode, nlink, size, phase and partial counts in the observation history and terminal failure. Reuse existing ChangingTree three-attempt/five-second retry exactly. A persistent link exhausts and refuses; a successful sample still has nlink1 at both endpoint observations for EVERY regular file.

Caller seam: extend watch/census with an explicit optional active-object-root context. Default is strict. Supply it only at recover01.py:119 after the genuine FSIZE readback and after verifying `args[0]=='fetch'`, cwd equals the exact fresh repository, and child.poll() is None. Before-call:98, post-exit:132, final post-cleanup:151, write:61/82, and final acceptance:244 all remain strict. Do not infer active publication from filename, catch-all error text or a caller Boolean disconnected from the actual owned child. If the child exits while the bounded active census is in progress, its later required strict post-exit and post-drain checks still gate acceptance.

This is the smallest concrete candidate correction for the supported transient-link hypothesis. It cannot promise that every future Git publication will settle inside three attempts; unresolved publication still fails closed. It also does not relabel an actual size excess as transient.

All original4MiBFSIZE,64MiBlogical,96MiBallocated,32768members,depth32,10GiBfloor,5s/sample,8192samples,60s/operation,600s/global,1024operations and pipe/output bounds remain byte-identical. Existing owned group stop/reap, cleanup precedence, fixed selection and remote-commit checks remain unchanged.

## Focused stdlib verification required

Use one deterministic local publication fixture with genuine os.link followed by unlink of the temporary name between bounded census attempts. Require that active-owned-fetch mode discards the linked sample and accepts only the later complete nlink1 census with exact membership/bytes. Run strict pre/post modes on the same linked tree and require immediate refusal. A link that persists for all three attempts must refuse within the existing common budget. A >4MiB file, including one also linked, must refuse immediately rather than enter publication retry. A link outside the exact owned objects root must refuse. One aggregate logical or allocated breach after publication must remain terminal. No network, matrix expansion or source-recovery run is necessary to establish those local semantics.

## Body identity remains separately sealed

A whole-tree metadata census does not authenticate recovered content. Existing recover01.py:232–239 remains necessary: Git cat-file size equals frozen size, decoded body length/SHA256 match, Git blob OID recomputation matches, original body joins, and exclusive saved-byte readback. That already supplies a body seal independently of transient internal object publication. No different body-seal primitive is required for this correction. If an actual Git pack needs >4MiB, retries cannot solve it; the unchanged native FSIZE must refuse and a separately bounded selected-body transport would be required. No evidence from this failed call establishes that need.

The original failed receiver remains frozen. This report is a source-level correction proposal and evidence assessment, not an implemented/tested correction, new attempt, network authorization or recovery acceptance.
