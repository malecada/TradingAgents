# Independent review

Accepted for exclusive durable metadata publication from an actual current compact closure receipt. No material blocker was identified in the inspected source and terminal evidence. The maintained module was independently compared with the reviewed draft and is byte-identical. Review comprised source, test, log and hash inspection; no tests, empirical jobs or historical numerical artifacts were rerun.

The publisher requires an actual `compact_closure.Receipt`, acquires the same owner transition lock, and rechecks its full current dictionary/calendar/graph/stage closure. Both selected plan and job must name the same registered publication policy. The attempt reservation covers four metadata files, including possible failure evidence, and the exact start/binding/completion/failure bytes must each fit the registered per-file cap before namespace creation.

Expected binding and receipt bytes are serialized before writing. Every exclusive write follows a fresh closure lease and callback-free full closure/owner check, root identity check, exact current inventory and readback of all already-written bodies. Final admission repeats closure/owner checks after the final Published callback and requires the exact three successful files and byte-for-byte expected contents. It does not adopt a post-write hash as a substitute for the prebound expected bytes.

Namespace conflicts refuse republication; errors after claim poison the owner and preserve partial or complete-plus-failed evidence. Failure marking is joined to the original attempt inode. The final owned descriptor close follows the fatal one-shot cleanup convention, with failure marking through a fresh descriptor and guaranteed transition-lock release. This is a source review of that path, not exhaustive fault injection of every inherited I/O failure.

## Evidence

The saved `check01.log` reports **3 passed in 417.98 seconds**. The inspected cases reject an arbitrary caller object; publish an actual two-required-graph, 20-day synthetic closure, check exact saved binding bytes and refusal after saved metadata mutation/republication; and revoke the owner specifically after the final Published lease delegates successfully, requiring refusal while both complete and failed records remain and another publication attempt refuses.

The missing-module red run remains infrastructure evidence only. This fresh synthetic chain uses actual registration and ownership with mocked guard surfaces. The suite does not separately exercise every policy-cap refusal, write syscall fault, metadata member corruption, failed-marker write failure or final descriptor-close failure. Those invariants were assessed in source and the relevant inherited helper evidence; no claim of comprehensive final fault coverage is made.

## Scope limits

The owner remains active and unsealed. This adds neither old-format FeatureJournal events nor ResearchRun outputs and grants no cold/historical reuse, native dispatch or empirical fitting. The bound closure retains its explicit unverified price-exclusion/label reconstruction limitations. The reservation is a logical encoded-byte allowance, not a hard filesystem quota, process-memory bound or proof of full-workflow performance/resource feasibility. Future terminal handoff must preserve exact complete/failed conflicts and re-establish its own terminal receipt contract rather than reuse active-owner leases after sealing.

## Final direct bindings

Direct reviewed-file hashes follow; they do not constitute a complete transitive execution-source manifest.

- `compact_publication.py`: `a620e5f84c2ec5095ae1715aae4a7962e64180075d139e424c671a2d486e935a`
- `test_compact_publication.py`: `413a5da987ecc2a78dd209ed2bb84b3f539903217d4ac373a5e6f6aa1bd8719a`
- `check01.log`: `86a40b244f8bfe5f3975e0a76df42991b7cb3287116e0517598ec9f59f07563f`
