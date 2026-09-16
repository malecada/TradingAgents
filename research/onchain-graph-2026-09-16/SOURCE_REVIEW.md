# Independent source admission review — September 16, 2026

Reviewer: independent `onchain_review` research-reviewer agent, read-only; no implementation ownership. Review base: `06c7a82ed2a0041e94b86329bfc799bb6b1b9f19`. No archive objects or financial outcomes were inspected during review.

Verdict: no remaining material blocker to the single source-only capture, conditional on committing the reviewed bytes, passing the named offline target and lifecycle admission, and using the pinned launcher. No financial experiment, complete chain history or historical point-in-time dataset is admitted.

Resolved findings: default proxy discovery was replaced by explicit `ProxyHandler({})`; request intents now precede I/O with unknown/nonrepeatable treatment for missing response receipts; `launch_source.py` applies explicit 360-second/2-GiB limits rather than the old guard CLI's defaults.

Independent verification used separately constructed synthetic block/transaction tables, real Parquet serialization and fake S3 responses. It reconciled six listings, four ranges, two downloads and eight cells; checked ambient proxy rejection and interrupted-request intent retention; and recomputed charter/source hashes. This was synthetic engineering verification only. The official AWS registry confirmed the anonymous public bucket/region/prefix documentation.

History review supports three consumed MAP-row-8 questions plus one new source-only question under the latest user instruction. Wallet/NLST/SMW history and unknown broader multiplicity remain. The document-only lifecycle input window cannot make inspected sentinel dates or future model samples fresh. Later development must inherit these observations explicitly.

Reviewed SHA-256 values:

| File | SHA-256 |
|---|---|
| CHARTER.md | `e1c2a228099d7ef683139676831ce637e36a4d331e0be2ccc0aaa61085394e20` |
| request-spec.json | `3bf065e1551da9718ce76e935e00a24ab9ad64f072f226bba2bd60cba9bf9b04` |
| source_probe.py | `9d24c2ca33c5779fa75135eb17d6c50a5d567f7df3738036ef56b6a2ebc7cdbf` |
| launch_source.py | `2fef68d720c6eef73e803e561dae63a6b185d1e458d465438c7254b5787f4225` |
| gates-source.json | `07298058a769bb0f5edc0ce56fab2a892d405ec0330f0dc53cf573b926f9bb24` |
| test_onchain_graph_source.py | `17e36ec329fee4258b546fe2ba63213c2baa16482fc02a664a05a07ed012500a` |

Unresolved empirical questions: archive availability, canonicality, coverage, historical publication, amount precision, graph computation, forecast quality and economics. They are not supplied by this review.
