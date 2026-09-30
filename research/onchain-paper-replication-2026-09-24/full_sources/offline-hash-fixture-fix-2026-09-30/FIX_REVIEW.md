# Independent synthetic disk-fixture correction review

Accepted for the five maintained synthetic test-module corrections. The completed admitted focused run reports112passes in87.06seconds. No production or historical resource policy was changed, and no remaining material blocker was identified in this test-only diff. This is not a new broad-suite pass or empirical release. Only this review was written; no tests/jobs, source edits or commits were performed by the reviewer.

## Root cause and preservation

The original failed offline01 retains35 standard and18 neural failures. The35 standard traces share the historical hash-audit20GiB-plus-margin refusal. The neural failure inventory exactly matches all18 original failed node IDs:17 traces expose sampling's20GiB-plus-reserved-bytes refusal, including the expected-capacity mismatch, and one forwarding test ends in missing representation `proposed-11`. The retained `neural-keyerror-underlying-failure.json` is byte-identical to the still-present output of that exact temporary fixture and records `ValueError: weight workspace breaches disk reserve` for `proposed-11`. This resolves the previously open downstream symptom without relabeling the original test as passed. Receipt SHA-256 is `a1e1601ce458b3356a92bd2fa987d3ea71bb341a600b9008f31e6a1ca401b91c`.

All five `.original` snapshots match their respective bytes at committed failed-run source `f6aa6d006f026e2d994181fe8beef9b14ea7b6b3`. Each `.red02` snapshot adds its isolation regression but contains no autouse capacity fixture. The admitted `red02.log` records five genuine failures in2.40seconds, SHA-256 `760efd2ed7746235927da23650ea0a2657d18178c9acaf1b871fa72aab1b64a9`. The earlier isolated-copy red01 remains a collection-admission usage error and is not counted as regression execution. Historical hash-audit/comparison/union modules and maintained sampling_weights.py remain byte-identical to the failed-run commit.

## Inspected correction

The diff changes only five test modules, adding one function-scoped autouse fixture and one sentinel regression to each. Fullpanel fixtures replace the dynamically loaded audit module's shutil namespace, providing its unchanged floor plus unchanged margin plus1GiB of synthetic spare capacity. The three sampling fixtures replace only sampling_weights.shutil, providing32GiB. Every replacement is a fresh local namespace under pytest monkeypatch's per-test restoration; process-wide shutil is not used to supply positive capacity, and no `_space`, reserve formula, writer, mapper or numerical function is bypassed.

Existing assertions are unchanged. The fullpanel low-space check still overrides the local namespace to the historical floor and requires refusal before intent creation. Resume union still proves refusal before buffer allocation. Mapped sampling's low-space test still sets one free byte and requires no workspace creation. Allocation-granularity/budget checks, partial-allocation and flush failures, closed mappings and preserved failed attempts remain exercised by their original code. Original hash/duplicate detection, complete graph-manifest comparisons, sampling probabilities/RNG states and policy/checkpoint identities also remain intact.

Each new regression first requires the module namespace to differ from real shutil, then temporarily makes real shutil.disk_usage raise if consulted and exercises real append/audit or MappedWeights creation/terminal publication. This scoped negative sentinel proves isolation rather than supplying ambient capacity. Cleanup restores both the module namespace and sentinel after each test, preventing the synthetic observation from becoming a process-wide resource override.

The final existing focused invocation completed all five admitted modules:112passed in87.06seconds, with the reviewed-profile notice that26 encountered files were withheld. The notice is not a failure or an assertion that the entire legacy tree ran. This run covers the prior failing cases plus the new isolation regressions; no reviewer rerun occurred. It does not replace a new independently released broad verification.

Focused `green01.log` SHA-256: `54dd8497660b82284487c8f7015874c8fc4ea97764568b438dd22b1473db409f`.
Neural failure inventory SHA-256: `22fdb8d6685de59abcfbcfd438fac80bc2887f2f5b7f7be994c3ce4d377d11d7`.

## Reviewed maintained test hashes

| Test module | SHA-256 |
|---|---|
| `test_onchain_fullpanel_hash_audit.py` | `0077fe762f14c8605e7b726e661973a212449565ec4757607ddab1d884715273` |
| `test_onchain_fullpanel_resume_hash.py` | `bc51196ee51b167dd317cfdcd716a18fa42c55b98d937d06394ce2a80ac33b52` |
| `test_mapped_sampling.py` | `57cd4ca3aee1d0d68c67025c1a65a70fe49bc262383e5b7b1909b6c81f455166` |
| `test_neighborhood_policy.py` | `6bb72d5f4400e74ecd1fdfe8f01103feb921f844d0feb12a5b10be6e7bd3a031` |
| `test_sampling_policy.py` | `f14eb893bed5702f03748440db437a57a5935031ada3ddf7baa82bcb2f0e9dbf` |

The previous run's freeze was independently released only after its failed guard, owner and cgroup closed. These test edits do not alter that closure or authorize reuse of offline01. A future broad attempt still requires its own reviewed bindings/launcher, commit/push, fresh resources and owner checks, unused identity and source freeze. No actual disk-capacity adequacy, financial result or empirical allowance is established by simulated fixture space.
