# Independent successor lifecycle review

Scope: source and invented disposable-repository lifecycles only. No empirical
input was evaluated, no real claim was started, and no frozen registration,
receipt, original runtime or worker implementation was edited by this review.

## Initial disposition: blocked pending one preservation fix

**Material finding: dataset identity and exposure history can change under the
same approved certificate.** At `tradingagents/research_amended/amendment.py:39`
and `:78`, the target hash and invariant comparison cover the experiment object,
whose dataset references are labels. They do not cover the definitions in
`spec.datasets`. The independent reconstruction has the same gap at
`verify_amendment.py:35` and `:79`.

An independent counterexample used the existing invented fixture in a disposable
Git repository. After constructing its certificate, only
`spec.datasets.sample` was changed to
`{"identity":"renamed-unexposed","history_reference":"reset","exposures":[]}`.
The certificate bytes and target experiment remained unchanged. After committing
that registration, amended start, registered input read, output publication,
completion and independent `verify_run` all succeeded. The completed claim
reported the renamed sample identity. Thus preservation of input hashes and
window labels alone does not establish preservation of sample identity/history.

Required correction: compare each dataset definition referenced by the preserved
experiment with the failed parent's committed registration, including identity,
history reference and exposure entries, before claiming. Reconstruct the same
comparison independently in the verifier. Add rejection checks for identity,
exposure and history edits. No financial execution is approved before this fix.

## Findings supported by source and synthetic checks

The initial focused suite passed 27 tests. Its checks cover one successful child,
failed and interrupted claims, original exhaustion, exact integer increment,
changed target/family/history/economic inputs, omitted or changed prior receipts,
review/preflight status rejection, repeat/chain rejection, concurrent starts,
source changes during operations, and structural accounting tampering. An actual
Git lifecycle is exercised under the v2 resource guard. These tests did not catch
the separate dataset-definition counterexample above.

The ordinary runtime has no working-tree diff. Its four copied core source hashes
match the preserved hashes documented in the successor README. Admission pins all
six successor Python modules and all six original modules, including the original
CLI and examples. The original verifier
independently checks every relevant prior terminal receipt. Inventory equality
retains failures, exact exhaustion precedes the +1, the parent must be the latest
failed attempt, and existing amended history rejects chaining. The shared lock
serializes claims and revalidation; read/write/finish also check the caller's
unchanged active claim. Terminal and output files use the original immutable
publication path.

The draft economic manifest preserves the hashes of `dated_book.py`,
`dated_book_run.py`, `dated_statistics.py`, `dated_archive.py`, `carry_book.py`,
`carry_capture.py` and `uv.lock`. The draft runner differs from the failed parent's
runner only in its descriptive module text, successor `ResearchRun` import and
registered target/gate identity. Financial input order, evaluate call, output
publication and self-RSS logic remain unchanged. The charter accurately states
that the first failed attempt computed books in memory and the second failed
before evaluation; no completed output is not proof of no prior computation.

## Explicit limits and pending admission

The runtime verifies committed attestations and source partitions. It cannot
infer whether a file classified as harness actually changes economics, whether a
reviewer is independent, or whether a report claiming a passing preflight tested
the complete intended command. The final source partition, target contract,
approval and actual preflight therefore require independent inspection. The
current draft partition is consistent with the inspected runner diff.

This review has not approved a real certificate or final gate: they were not yet
present. The exact amended CLI with invented full-shape data and real statistical
dependencies must pass under the frozen guard after the final runtime changes.
Final certificate inventory, all source hashes, approval/preflight references and
committed remote equality remain required before one financial execution.
Cashflow outcomes, historical risk, profitability, inference or graduation were
not tested in this engineering review.

## Dataset fix and full invented CLI addendum

The blocker is resolved in `amendment.py:75` and `verify_amendment.py:72`.
Both now load the failed parent's committed registration and preserve every
existing dataset definition, rejecting removal or any field change. An independent
repeat of the original unchanged-certificate counterexample rejects before creating
the amended claim. A second independent counterexample first completed the valid
invented run, then recommitted a changed dataset registration and updated the claim's
source, registration hash, exposure entries and window identity to be internally
consistent. `verify_claim` separately rejected the dataset-history change. No
production claim or registration was touched.

The current focused successor plus full dated-CLI suites passed **35 tests in
26.07 seconds**. The actual amended `main()` and argument parser ran in a disposable
checkout with invented full-shape input, three preserved synthetic failures,
committed certificate and source files, real statistical imports, the frozen v2
guard, original Git checks and successor verification. It completed all eight
cases, all eight exposure calculations and all three outputs; expected-return
confidence and power remained unavailable. The reviewed guard report recorded
9.93514 seconds, 434,868,224 bytes peak sampled aggregate RSS, two CPUs, no limit
reason and exit zero. The 512 MiB/120-second limits and sampled-RSS qualifications
remained explicit. Reports were inspected at
`/tmp/pytest-of-malecada/pytest-290/test_actual_dated_cli_real_hac0/`; durable copies
must be bound by the coordinator's final repair certificate.

Reviewed successor source hashes:

| Module | SHA-256 |
|---|---|
| `__init__.py` | `b34ced6fb4b6dd9dc1ae15645c40d62687ae7fa85f104ff77a6f1f49f874d2af` |
| `admission.py` | `dbb4ec5e0b81948a4d7e007306ffb72277e0a448ae2c5d65c82cd4ddf5ba1b78` |
| `amendment.py` | `516b82264fb9152f2135a036eb030feefb7f507221aa213b9509e6f424fe1bfd` |
| `lifecycle.py` | `a4681c16e441e41496c1de88017dbcc27b3ce4e30309023ac3ffe83d5f7a1b52` |
| `verify.py` | `ccc85b7b98c97e048a3c17a8335b4e735e220398604e05eb19dea96616b84666` |
| `verify_amendment.py` | `5b056e3c8f002f1e5391e851840a1d7aa90c0939a9b21a73726137380a2c8e13` |

Current engineering disposition: **pass, with final real certificate/gate review
still pending**. The real manifest should match the synthetic preflight by adding
all six successor modules to its target harness/source map as well as pinning the
runtime hashes; this establishes their committed source availability. The original
runtime remains unchanged. This addendum does not authorize a financial claim.
