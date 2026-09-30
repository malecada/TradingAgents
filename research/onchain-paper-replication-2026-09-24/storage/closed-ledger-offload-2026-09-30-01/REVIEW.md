# Independent closed-ledger preservation review

September 30, 2026. Source and compact evidence review with metadata/stat checks only. No source ledger, SQLite, graph-array or raw body was opened, and no test, transport or job was run. Only this review is written.

**Hold prospective execution pending T1.** The exact target and preservation ordering are otherwise consistent with the stated one-file scope.

## T1 — inherited per-transfer timeout is incompatible with the stated throughput plan

`offload.py:67–69` creates the unchanged retained `Transport`. Its `transfer.py:165–169` subprocess runner imposes a1,800-second upload timeout, and `transfer.py:186–191` imposes a1,800-second receive deadline. Raising only the outer guard to7,200 seconds does not extend either operation. The3,755,220,992-byte target requires approximately3,414 seconds per direction at the previously observed1.1MB/s, while a1,800-second transfer requires approximately2.09MB/s sustained. Thus the stated two-hour full-file plan can still fail halfway through a direction, leaving substantial partial remote/scratch evidence and freeing no space.

Provide an explicit preservation-local transport deadline compatible with the full-file plan and the finite outer guard, or substantiate another bounded transfer plan. Do not modify any active graph source or historical transport bytes. Preserve this initial source snapshot and add a synthetic deadline-forwarding check if the transport interface is changed. This is a feasibility/admission issue, not evidence that the failure path deletes the original.

## Checks and scope

All20 frozen bindings match. The exact source is the closed graph03 aggregation ledger,3,755,220,992 bytes, with expectedSHA `e82812887fd8c9757e52635761061abb4693593363a2fbd735a0c8ecdc3cf3a9` from the original closed artifact index. Its stat identity matches; no WAL/SHM/journal/remote sidecar exists. All five closure hashes match; old monitor/cgroup are absent. The manifest is scoped to one exact path and a new exclusive remote directory. Hash consistency joins terminal→claim/index and guard→owner; no original registration or artifact index is amended.

The retained helper verifies source hash/identity, locks its no-follow-opened descriptor, performs full body and restoration-metadata roundtrips, publishes fsynced verified receipt and original-path sidecar, then revalidates both path and descriptor before unlink. Failure before these steps retains the original; interruption after unlink can leave verified receipts/sidecar without an evicted or aggregate completion marker, requiring reconciliation rather than retry. Aggregate local completion occurs only after remote completion-metadata roundtrip. A receipt is not independently downloaded evidence from this review. Any future local-path verifier must restore the hash-verified cold body first.

The8GiB payload allowance accommodates the two3,755,220,992-byte body directions and bounded metadata/padding. The4GiB per-file scratch allowance is explicit; the worker requires10GiB floor plus exact file size plus16MiB before transfer. Numeric guard limits remain256MiB max/192MiB high/zero swap/3GiB reserve/3.5GiB startup/twoCPU/10GiB disk/7,200 seconds. Scratch and other concurrent disk growth share the same volume; guard admission does not reserve capacity. Fresh owner/resource checks remain necessary. During review the graph04 live receipt had advanced to phase complete; do not rely on its earlier active status, and reconcile its terminal/cleanup before assessing launch concurrency. No inference of graph04 content correctness is made here.

Eligibility rejects direct active input references, changed scope/stat/closure, tracked files, and SQLite transient sidecars. It is intentionally not an indirect dependency finder. The retained four new eligibility tests pass in0.019s, with the honest qualification that tests followed initial implementation. They do not exercise this larger transfer, new disk peak, timeout compatibility or real Storage Box execution. Prior helper tests/live preservation remain separate evidence.

Initial reviewed identities:

- New offload source: `034aa5627e03b06ea1e9d26dcc3eacf6d279bf2b75558e8f6eba3227bce393ad`
- Manifest: `774086f8b3e9d39ba9ddcc93c0a27730976f4b38e37b7d2daf36009d7e4012c7`
- Eligibility tests: `ee2faac1f1e2b6b80181c91913e634e479cbfd0a05737065e5a597f0ca052eee`
- Retained helper: `0d507711644d962e494e659987ba0a6d479304af7092ba15315630d0b68e1a84`
- Retained transport: `c07745682d5d4879a801d02934a4040719ae26f18bcdfde614eb8877099a2d82`

## T1 correction and conditional release

The corrected preservation-local subclass resolves T1. Inherited `put` calls the overridden subprocess runner with **5,400 seconds**, and overridden `get` passes **5,400 seconds** to the original bounded receiver. The new worker and outer guard both declare **14,400 seconds**. The original transport bytes, rate, payload reservations (including rounded receive allowance), destination refusal, diagnostics and no-retry semantics are retained. Source diff changes only the two outer/worker wall declarations; manifest diff changes only the transport path/hash. The initial candidate is preserved byte-exact.

The retained red log is a missing-module error, not a timed live counterexample. The two passing mocked tests in0.002s exercise actual inherited upload dispatch and overridden receive dispatch, assert the forwarded deadlines and exact byte charges. They do not measure throughput or guarantee completion. Two worst-case5,400-second body operations leave3,600 seconds for local hashing and metadata under the whole-job guard; other delays can still exhaust the finite run and must preserve failure evidence.

All **22 current bindings** match. The graph04 final now reports complete/cleanup true, and its exact monitor/cgroup are absent; the earlier concurrent-active concern is therefore superseded for this reviewed snapshot. Storage guard01 does not yet exist. The target remains only the closed graph03 ledger. No graph-body or source-ledger read was performed by this review.

**Accept one bounded preservation execution of the corrected exact candidate, conditional on fresh source/identity/host/disk checks and the registered guard.** Recheck the absence of any newly active dependent owner before eviction. Preserve terminal/partial identities and do not retry this one. The prior original-path restoration and evidence limitations remain; acceptance does not establish an external recoverable copy until the actual full roundtrip, durable per-file proofs, sidecar and completion sequence succeed.

Corrected identities:

- `offload.py`: `a754467fa639610c883afa9a7db44432b77a54bedeaa4f676e2af4e2bc74de39`
- `transport.py`: `ee551abbb81bec2b42355ce073c2a570d6ed0b37bd763b047b539f8c1148de16`
- `manifest.json`: `6c484cdafc0413c6971064157b9d809821d5c91264ab039fa7a8b80d7c1a281a`
- `bindings.json`: `98c909a530885cfe963934a7363ff531ba80776bf7aa5ba16ea4d0c4c4a23bbb`
- Deadline tests: `fdec910a8c1e9d91c7b824262d253649909edc9420e5e7377959b9de40b0e003`
- Deadline green log: `81b3a301c9d065d9ef8562b319743d675c26ac3b3d9b2aebddfb49c927ed9e37`

Throughput qualification: the prior3,584,497,664 relocated bytes divided by3,357.995 seconds measure about1.07MB/s of net relocated bytes across the complete roundtrip job, not observed one-way throughput. Earlier wording referring to an observed1.1MB/s direction is superseded:1.1MB/s is a conditional planning scenario only. T1 identifies the hidden per-operation deadline and its required minimum one-way rate; it does not prove that the old deadline would fail on this transfer. The corrected finite5,400/14,400-second plan and conditional acceptance remain appropriate without a guaranteed throughput claim.
