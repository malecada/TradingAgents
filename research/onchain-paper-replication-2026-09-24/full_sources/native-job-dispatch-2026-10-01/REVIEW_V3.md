# Independent corrected native dispatch review

Accept the inspected source corrections for the bounded synthetic native dispatch, conditional on successful closure of the still-running regression03 and preservation of its exact source/evidence. This is not final regression closure, actual-guard execution or empirical release. INITIAL_REVIEW.md and all failed identities remain unchanged.

All798 files in candidate03-sources.json independently match. Manifest SHA-256: `11c5d61eff9eb848628c92b5a69cf740543694ede7bcd5a64f0c59ab94a89268`. The source changes were reviewed against the actual maintained files and saved tests; no test or job was rerun by the reviewer.

## Findings closed in source

ND1 is closed: graph_store._resident_array captures the NPY magic, length prefix and bounded header once, parses that captured BytesIO and allocates only the admitted shape/dtype/order. It does not call np.load or reread the live header for allocation. The payload is filled through bounded readinto chunks, and the hash covers the exact captured header plus loaded payload. Extent, trailing-byte, open-file signature and final path-content checks reject drift.

ND2 is closed: the version-specific two/four-byte header length is checked against10000 bytes and the admitted file extent before header bytes are read. The NumPy parser subsequently sees only the bounded captured header. The new tests forbid generic np.load, reject an oversized length before the header parser and inject payload mutation during allocation. The first test proves absence of live-header reparsing; it does not itself rewrite the live header. header03.log closes six tests in0.300s.

This reader change bounds its header/payload allocation; it does not claim an atomic filesystem snapshot, complete RSS accounting, or new hardening of every inherited common path/hash operation. Node-ID conversion, GraphSnapshot validation and Python overhead still require the outer resource contract. The historical default mapped-loading route remains unchanged.

The pair-construction failure is fatal in the native caller even if the constructor never returns its handle. Its exact namespace is retained, no rollback/retry occurs, and job_payload propagates NativeProducerCleanupError. Native selection rejects existing or redirected pair/representation namespaces before graph allocation. First-owner creation rejects redirected ancestry and noncanonical required sets before mutation; construction/rebinding failures preserve partial bytes. The new fatal exception wrapping is now restricted to first-owner mode, preserving the prior successor exception contract. Ordinary sampler failure closes available pair and feature handles; a failed lease/cleanup escalates rather than being presented as a normal unavailable result.

The composition's actual keyword arguments and return shapes remain compatible through sampler, dictionary, MCM, native graph publication and terminal preparation. The shared import chain retains concrete ownership/ticket class identities. The returned `(PreparedFeatures, terminal)` matches eager-loader unpacking and the maintained batch executor.

## Git anchor retrieval

The optimization replaces87 per-file Git processes with one fresh cat-file batch per full source check. Current implementation hashes, registered/numerical mapping equality, exact required source set and every returned blob's SHA-256 remain checked. Binary-safe framing validates object type, hash syntax, exact expected size and delimiters; missing/truncated/trailing responses refuse. The generator is exhausted by strict zip, including its final trailing-data check. Subprocess failure propagates and no cross-call cache is introduced.

anchor03.log closes four tests in0.188s, including exact87-object byte parity against individual git show reads, binary/newline payloads, malformed/missing frames and process failure. Its measured0.134048s versus0.007769s applies to that synthetic Git fixture only, not whole-pipeline performance. The response extent check occurs after communicate captures stdout; this is not a new bounded-subprocess-memory guarantee. The trusted committed source closure and outer guard remain required.

## Evidence and release limits

dispatch02.log closes one complete native payload/executor integration in287.881s, with both synthetic fits complete and duplicate refusal passing. failure02.log closes two methods in113.608s, including the three partial pair-construction subcases and sampler-failure preservation. These runs precede the subsequent bounded-reader/anchor changes; their results are not relabeled as executions of candidate03. The header and anchor suites directly cover those changes. regression02's prior successor exception failure remains preserved; regression03 is the fresh check of its correction and was nonterminal at review.

The integration uses real temporary registration, graph stores, fresh journals, numerical producers, terminal native features and maintained execute_fit_payload/execute_batch, with mocked kernel guard admission. No actual guarded launch, complete paper-sized batch capacity, physical whole-workflow quota, financial-data fit, continuation, cold/mapped reuse, or external checkpoint recoverability is established. Temporary fixture blobs are not represented as retained production artifacts. All original resource and financial denominators remain outstanding as previously recorded.

The separately prepared native-guarded-dispatch attempt has its own conditional ADMISSION_REVIEW.md. It must use the exact retained committed checkout and real launcher/monitor/worker after successful regression closure and fresh preflight. This review alone does not assert that those conditions have occurred.
