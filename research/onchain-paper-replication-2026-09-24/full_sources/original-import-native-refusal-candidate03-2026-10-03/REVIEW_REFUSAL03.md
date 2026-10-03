# Independent review — refusal candidate 03

**Disposition: parser/suite acceptance WITHHELD for one material evidence defect. The separate compact MCM cleanup-order delta is narrowly ACCEPTED as source. No execution is released and none of the 27 genuine refusal variants is discharged.**

## Finding

**P1 — Matching events are not joined to the registered target/motif purpose or ordered pair.** At `refusal_stage.py:70`, the purpose and ordered-pair identity need only be nonzero. At `refusal_stage.py:73`, the completion must repeat its begin identities; at `refusal_stage.py:89`, the tail must repeat the completion's purpose. These are internally consistent chains, but no check reconstructs either identity from the registered target neighborhood, selected motif, center index, motif index, typed graph identities, matching configuration and current context.

An independent tiny-file counterexample is retained in `review-counterexample03.py` and `review-counterexample03.log`. The actual candidate parser first accepts its qualified fabricated `wrong-ack` control. Replacing both binary events' purpose with byte `0x98` repeated 32 times and pair identity with byte `0x76` repeated 32 times, then recomputing only the matching event chain and terminal digest, is still accepted with one completed matching pair. Registered inputs, original import receipt, graph/motif/workload identities and all other evidence remain unchanged. The candidate's own positive `stage_fixture03.py:20` already generates purpose hashes from `SHA256(str(i))` and a constant pair identity rather than the actual scientific purpose.

Impact: unrelated or corrupted matching work with the expected event counts can discharge a numerical refusal. The report's claim that purpose identities are checked is stronger than the actual semantic join. A whole-tree recovery hash establishes which bytes were recovered, not that those events correspond to the declared computation. The supplied parser tests cover broken hashes and missing evidence but miss coherent resealing of unrelated purposes.

Required correction: reconstruct the expected per-cell purpose and ordered-pair identity from authenticated tiny target inputs and the ordered original motifs, using the selected source's exact encodings. Join each begin/completion to that expected pair before accepting the tail. Preserve finite bounds and no numerical execution in the verifier. Add negative tests with coherently resealed wrong purposes, wrong pair identities and wrong center/motif order, plus a positive fixture derived from the actual metadata identity rules rather than arbitrary hashes. If this join is delegated to a distinct outer verifier, make its exact authenticated proof mandatory here and review that source before claiming numerical-stage acceptance.

## Narrow cleanup acceptance

The selected `compact_mcm.py` SHA256 is `05c7d5dfd53fd537cc2b2033427b4f496887c13ada9ff33310606dd2fa7c509d`. At `compact_mcm.py:312`, the only change moves Owner poisoning from before the cleanup actions into an unconditional `finally` around the existing cleanup reducer. The stream close, actual `PairLog.fail`, log close and failed producer marker are all still independent cleanup actions. This lets a still-valid actual Owner lease publish a truthful matching failure terminal before revocation. A failed terminal write is not replaced with synthetic evidence.

The whole-module AST is identical to candidate02 after substituting only that exception-handler body. Numerical loops, matching callbacks, stage/publication rules, preflight and all other methods are unchanged. The supplied actual extracted `PairLog._check/_terminal/fail` test passes with its explicitly qualified IO/lease objects. It proves the ordering in that source fragment, not a genuine Owner/OS run.

Independent `review-cleanup-original03.py` combines the actual selected producer handler with the actual accepted `owned_io._cleanup` reducer. Four cases pass: ordinary failure preserves its original exception; the first actual fatal survives a later close error; a later fatal outranks an ordinary primary; and an uncertain ordinary close produces the actual `CleanupFailure` retaining both causes. Every independent action runs and Owner poisoning occurs afterward in all four cases. These checks are stdlib fragments with qualified resource sentinels, not a lifecycle or numerical attempt.

Root may compose this narrow cleanup delta with its separately reviewed metadata source-reference correction. That composition and its exact source/input/runtime/release joins require their own checks. This acceptance does not include the refusal parser or grant a retry, budget change, identity reuse or numerical launch.

## Evidence and verified corrections

Manifest `0f3bb9c12cdb0b64f76d12057bfbcdb54ffa55ada297ff269c07a7fd042674cb` matched all 36 owned bodies and four dependencies. Source inventory `3fb8fe3af80006960207d5f371875ee079251c09916fbb2750a42969631b0303` matched all 161 source bodies, including the declared 144 package sources. Installation delta `69afda3e677f49d9c5c3f45df616acd052bc6dfeeb7b1ec651ec6456502fe422` remains source preparation only.

The pinned interpreter ran the named 20-method corpus successfully; independent output is retained in `review-corpus03.log`. This includes whole-module handler parity, original validator-prefix parity, source-format checks, missing/truncated stage evidence, numeric record corruption and preceding review regressions. Passing those methods does not resolve the new counterexample.

The new full original semantic parser was additionally applied, read-only, to all eleven byte/hash-joined original JSON bodies retained in the genuine closed primary capsule. It authenticated dictionary identity `48832eeb9774ef6ca13915364c17d1ac89f5c67165636de5811ebf82ad6ad726`, 32 ordered motifs and 11,136 numeric bytes. This independently supports the correction of the prior len-only original-import numeric metadata weakness. It did not materialize arrays, resample, recluster or rerun the historical parent. The original completed dictionary component remains distinct from its failed enclosing historical attempt.

The parser now requires actual stage intent, matching start/failed terminal and the selected stream/tail/batch evidence, with fixed per-class counts. Empty numerical stage evidence and the originally reported missing/corrupt original fields are refused. This is useful progress but remains insufficient while event purposes and ordered pairs lack their semantic join.

An initial independent manifest-inspection command incorrectly prefixed paths that were already repository-relative, producing `FileNotFoundError` before reading a source body or changing anything. The corrected inspection verified the entire manifest/inventory. This harness path mistake is not a candidate defect or empirical attempt.

## Untested and preserved boundaries

No numerical package or tradingagents package was imported by the review checks; no array, actual Binding/Owner, guard, lifecycle claim, registration or ledger was created. No live source, candidate implementation, old evidence, STATE, registration or committed source was edited. Only this review and its bounded independent source/log files were written.

The 27 real variants / 16 classes remain unexecuted, with four preclaim refusals, at most 23 claims, 17 compact Owners and 19 journal groups. Actual process-death behavior, cross-Owner/process reuse, current runtime/source/native guard authentication, hard limits, cleanup, publication failures, full numerical comparison and external outcome recovery are not tested. The parser remains a supplement to a separately required exact outer verifier. Existing terminal identities and historical scientific jobs must remain closed. No higher-effort escalation is needed for the confirmed question; the concrete metadata reconstruction and resealing refusal tests are the next source correction.
