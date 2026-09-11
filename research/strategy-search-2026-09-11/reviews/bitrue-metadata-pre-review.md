# Bitrue metadata independent pre-result review

September 11, 2026. Source/synthetic review only; no real endpoint or saved
market payload inspected. Implementation review passes. Final charter/gate
freeze remains pending the documentary ambiguity below.

Reviewed collector SHA256:
`daadd2532952fb06a2789c70423c28835eece7d6622aa4a8a4a2444e5a7efab7`.
Request-spec file SHA256:
`d04ba9b8dabeafb845707e9f23f829eebd846c7ccc770f145e98271061887810`.
Initially reviewed charter SHA256:
`d4b7e3172be47024d2183822ed99725a46f11e2bdd0860152297ba8f6fb0d612`.

Independent targeted synthetic run: **25 tests pass in 0.98 seconds**, using
the pinned `.venv/bin/python -B -m pytest -q` on
`tests/research/test_bitrue_metadata.py` and
`tests/research/test_bitrue_metadata_lifecycle.py`. The latter creates a
disposable Git/ResearchRun lifecycle and two invented 5 MiB responses under
the frozen v2 512 MiB/two-CPU/120-second guard. No real source or empirical
financial evaluation was used.

The canonical spec fixes two requests with no fallback; immediate per-source
receipts precede parsing and subsequent calls. Denial suppresses the second
same-host request while retaining both intended cells. Partial bodies/errors,
cooperative time exhaustion and recoverable parse errors preserve the two-cell
denominator. Abrupt resource failures remain failed claims with partial outputs.
Strict JSON rejects duplicate keys/nonfinite values and injected array-wrapper
fields. Rows preserve unknown identity/unit/type combinations, with no numeric
string coercion or account-permission inference. Duplicate/missing symbols make
the source unavailable rather than silently removing rows. Time objects retain
unknown clock semantics. Actual lifecycle-encoded admission/output sizes are
bounded; no compact-JSON proxy substitutes for persisted-byte accounting.

The exact E-BTC-USDT/E-ETH-USDT mapping is a conditional literal candidate rule,
not observed listing or sufficient proof of collateral/linear cashflows. Invalid
or unfamiliar rows remain preserved. No fees, funding rates, PnL, synchronized
cross-venue state or return confidence are inferred.

## Documentary condition before freeze

The official v2 public controller's displayed contracts request omits parameters
and shows an array response, while its parameter table calls `contractName`
required. The cheapest informative registration keeps the existing two calls
as an **unfiltered listing/version-availability question**, explicitly preserving
this conflict and prohibiting unregistered symbol-specific retries. Failure
does not establish absent BTC/ETH products. See
[bitrue-funding-history-source.md](bitrue-funding-history-source.md) for exact
source URL and denominator. The initially reviewed charter does not yet state
this conflict; coordinator clarification and final pinned gate review are
required before acquisition. No implementation change is necessary for this
conservative interpretation.

## Final charter and gate — PASS

The documentary condition is resolved in final charter SHA256
`c16f74b157344c6458f91332080c7fea278bbb9658c085d7be5dc49c57eec4fe`:
the contradictory required parameter is explicit, the unfiltered example is the
fixed availability question, and no fallback or absent-contract inference is
permitted. Collector and request-spec hashes above are unchanged; the prior
25-test synthetic verification still applies.

Final gate SHA256:
`c8325be306f6a4faa4af5df94f8764d741c9550a81409ae01117195b51dba51c`.
Every pinned source/helper/transport/guard/runtime/lockfile, charter and request-
spec digest matches local bytes. All ancestor family, dataset and experiment
objects match `gates-triangle-proxy.json` exactly. The new family has zero
**known exact** prior gates and a three-question administrative cap, explicitly
preserving broad funding/venue history and unknown statistical multiplicity.
Two source cells and four outputs match the fixed specification; parent is null
for this distinct source mechanism, not an erased history claim.

The pinned local document-observation marker and exposed input window both use
September 11, 09:12:21.519513–09:12:21.519683 UTC, and its request-spec digest
matches the input. This is existing request-definition bookkeeping only; it
does not establish live source availability or backdate future response clocks.

Copied synthetic preflight reports preserve two invented 5 MiB bodies,
27,966,493 actual output bytes, two CPUs, exit zero, 0.737 seconds and
125,845,504 bytes sampled aggregate RSS under the stated guard. No real source
request or financial computation was performed in this review. No remaining
pre-result blocker was identified. Coordinator commit, verified remote
preservation, guarded execution and independent post-capture source review
remain required lifecycle steps.
