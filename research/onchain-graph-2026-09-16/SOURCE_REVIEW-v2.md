# Independent v2 source admission review — September 16, 2026

Reviewer: independent onchain_review research-reviewer, read-only. This review supersedes the incomplete history finding and elapsed-time guard described in SOURCE_REVIEW.md; that original record is preserved. No source capture was claimed under v1.

Verdict: eligible for exactly one source-only capture, conditional on the committed detached-checkout preflight and named offline verification passing. No financial evaluation is admitted.

Independent checks reconciled all 37 local claim hashes, available terminal hashes and history anchors; preserved overlapping grants and separately recorded active F1; checked unchanged original charter/gate bytes; confirmed v2 source hashes, durable request intents, no proxy discovery/redirects/retries and unavailable-cell retention. The launcher applies two-core affinity and sampled 2 GiB RSS without an overall elapsed/CPU kill. Structured setup-failure retention was checked independently after correction.

Before capture, retain a detached-root preflight that verifies all pinned inherited metadata, exact HEAD, isolated package import origin, runtime and lifecycle admission. Execution HEAD must remain fixed until terminal closure.

Focused synthetic checks: 14 passed. The named offline target was still running when this review was recorded; its terminal result must be retained before acquisition. Neither synthetic checks nor structural admission proves source availability, coverage, canonicality, historical publication, forecast quality or profitability.

| Reviewed file | SHA-256 |
|---|---|
| CHARTER-v2.md | `54c4135c95f8b39ff0f02c7d99a511a229570adbd29cd167b911881941eb1739` |
| gates-source-v2.json | `76160c7f6a139b0aa2834378fc54fc7c9e64846c0f38f0e999063b10f292654e` |
| history-snapshot.json | `1e7366f6752c36fdbac57bb85de0df24e2ce96c9c6e7b5429e3f1a41e49b6523` |
| request-spec.json | `3bf065e1551da9718ce76e935e00a24ab9ad64f072f226bba2bd60cba9bf9b04` |
| source_probe.py | `d4f7cf193f41635910ee24d671a69b3e68b466cd01186c40c8f21b3c636231c0` |
| launch_source.py | `e12859f78d99e327b537dd43b924e18eb7329441b317d6fd9fe18fc36058d2ec` |
| tests/research/test_onchain_graph_source.py | `eab47ca6a728023fb506463766fa56839010230e1bbbdb472404e5f93beec192` |
