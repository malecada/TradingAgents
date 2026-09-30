# Independent conditional preservation preparation review

Reviewed September 30, 2026. Accepted as conditional preparation for the exact closed graph04 ledger. No blocking discrepancy found. This is not evidence of remote preservation or permission to execute while graph05 is active.

The manifest selects only `research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-graph-resource-20260930-04/aggregation/ledger.sqlite`: 3,370,971,136 bytes, producer/index SHA-256 `926020b6171496b001ebf5fb9957469094ef1b2bc7b5251206441254ab9add38`. Independent compact reconciliation found the exact original artifact-index entry, terminal-to-claim/index hashes, successful guard child zero/cleanup and matching owner. The exact old monitor and cgroup are absent. Stat-only examination matches all five recorded identity fields, regular nonsymlink type and single link; the path is untracked, with no WAL, SHM, journal or restoration sidecar. No body hash or SQLite opening occurred. The expected content hash remains attributed to the closed producer until the guarded transfer independently verifies it.

All 22 bound compact/source hashes match. Source comparison with accepted preservation01 finds only the exact graph identity and descriptive graph03-to-graph04 substitutions in offload.py. The transport is byte-identical. The existing helper retains full source validation, exclusive file lock, upload/download length and hash agreement, restoration metadata roundtrip, fsynced verified receipt and original-path sidecar, final source/FD validation, then unlink/directory fsync. Aggregate complete is published only after completion metadata roundtrip. Failure after individual eviction can leave a failed aggregate while durable per-file restoration proof remains; recovery must reconcile those receipts, never retry this identity. Failed scratch and remote partials remain retained. Historical artifact-index bytes are not rewritten, so later ledger-body checks require verified restoration first.

Dependency review covered graph05's actual admitted plan and inputs and the graph producer's build path. Graph05 builds June 2023 from seven declared raw-source wrappers into its own exclusively created source directory and aggregation workspace; it neither resumes nor reuses graph04's aggregation ledger. None of its 42 compact input bodies contains the exact graph04 ledger path. Its preservation prerequisites concern the separate already-preserved graph03 ledger. Source-index ancestry and graph04 budget/history evidence are compact metadata dependencies, not instructions to reopen graph04's database. This supports the current specific dependency assessment; the direct-reference scan is not a universal transitive dependency resolver. Any later consumer or owner appearing before release requires fresh review.

Limits retain 256 MiB maximum / 192 MiB high / zero swap / two CPUs / 3 GiB host reserve / 3.5 GiB startup / 10 GiB disk floor / 14,400 seconds, with 5,400-second transport operation deadlines. Scratch preflight requires 14,125,166,592 free bytes (10 GiB plus exact ledger plus 16 MiB). The body fits the 4 GiB file allowance; upload plus rounded download charges total 6,741,946,368 bytes before small metadata, below the 8 GiB transfer ceiling. The shared transport still enforces that ceiling. These are finite bounds, not guaranteed completion time, throughput or absence of memory.high throttling.

Saved synthetic evidence reports four eligibility tests in 0.017 seconds and two mocked deadline/payload tests in 0.002 seconds. Test source covers exact-path admission, scope/journal/sidecar/tracked/stat drift refusal, active guard/direct claim refusal, closure drift and actual forwarded deadlines/charges. These tests were added to the adapted implementation and are not a fresh preimplementation red/green proof; they do not validate network recoverability or indirect dependency completeness. No tests were rerun here.

Release remains conditional: graph05 must first have an actual terminal, cleanup and independent reconciliation. Fresh disk must fail the reviewed graph06 requirement of 20,718,879,508 free bytes; if sufficient, leave this preparation unexecuted. Commit/push the reviewed preparation only after the active freeze ends, then recheck bound hashes, source eligibility, dependencies, exclusive local/remote identity, host/disk capacity and unchanged resource limits before one launch. The worker does not itself enforce the new graph05-terminal or graph06-shortfall conditions; they are mandatory external release checks, not guarantees supplied by eligibility(). No financial claim, new paid resource, raw eviction, graph-array eviction or graph05 ledger access is admitted.

At review, HEAD remains `9f7401158b3544deefbc4c1b9e995d565880ce50`; all active graph05 87 source and 42 input hashes match. Only this review file was written. No network, credential contents, archive/SQLite/array body reads, transfer, job or eviction occurred.

Reviewed SHA-256 identities:

| File | SHA-256 |
| --- | --- |
| bindings.json | 03e46485430c60f931668e00bcab8fd8972db7e28e603aeef04f88659a1a19c9 |
| manifest.json | bf5f2a8bc5bba1fc71a4ff1f3d8649f2d2a4d8dd8c197ee1a10cc0f2314ae048 |
| offload.py | 0f5f5789639a0074b4deb96d522117dcf47f71235c9a859f87dfe5f569125604 |
| transport.py | ee551abbb81bec2b42355ce073c2a570d6ed0b37bd763b047b539f8c1148de16 |
| README.md | 0f3edf142db83a6c6b84f7be9e4612cb9581654cce84cab2178b030255488f6d |
| eligibility-green01.log | 8443360320382c06e9b07ce94cd94708cbc355744bebe65cac31e8cf28a6fcfe |
| deadline-green01.log | 81b3a301c9d065d9ef8562b319743d675c26ac3b3d9b2aebddfb49c927ed9e37 |
