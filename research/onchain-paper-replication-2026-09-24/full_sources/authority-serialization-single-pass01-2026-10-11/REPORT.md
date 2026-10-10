# Single-pass authority metadata serialization candidate

Status: uninstalled, synthetic checks passed; independent source/entry review pending.

The copied `candidate.py` removes exactly six explicit `thaw(...)` wrappers:
`inputs`, `sources`, and `runtime` in `Lease.__init__` and `Lease._finger`.
`canonical_bytes` still performs a fresh recursive thaw and JSON serialization
on each invocation. All other bytes, including imports, remain unchanged.
`PATCH.diff` and `INVERSE.diff` record the literal change. Baseline and candidate
SHA-256 values are in `RESULT.json` and `MANIFEST.json`.

The complete source AST differs only by those six call removals. No guard,
comparison, callback, scheduler, currentness check, public return shape or
cache changes. `compact_owner.configuration` and `binding_value` remain untouched.

## Type and evaluation boundary

`provenance.py:10` calls `thaw` before JSON encoding; `thaw` at line 65 recursively
turns mappings into dicts and tuples/lists into lists. On finite acyclic ordinary
JSON metadata and recursively frozen dict/tuple equivalents, applying it twice
has the same resulting values as applying it once. Serialization options stay
identical, including sorted keys and rejection of nonfinite floats.

The production construction path supports that domain: `admission.py:247`
loads registration JSON; its source roster is part of that experiment dict,
and lines 387–413 construct inputs as ordinary dict copies of JSON metadata.
`matching_owner.py:412` creates context as a plain string-valued dict;
`Binding.__init__` at lines 172–175 applies `freeze`, whose implementation in
`provenance.py:72` builds mapping proxies and tuples recursively. No empirical
input, live authority object or claim was used in these checks.

The equivalence does not extend to arbitrary custom mappings, objects with
side-effectful attribute access or iteration, cyclic structures, or concurrent
mutation during a serialization. The old expression traverses each selected
field while evaluating dictionary values; the new expression resolves all
field references before the single recursive traversal. Thus the timing of
reads and exceptions can differ in those out-of-domain cases. This change does
not make either expression an atomic snapshot and does not add any such claim.
Mutation between invocations is freshly serialized and remains detectable.
If independent entry review finds the admitted path permits side-effectful
custom metadata or concurrent mutation relied upon for currentness, this
candidate must be refused rather than weakening that contract.

## Finite verification

Command: `.venv/bin/python -B research/onchain-paper-replication-2026-09-24/full_sources/authority-serialization-single-pass01-2026-10-11/check.py`.
Python 3.13.13, exit 0. Limits: CPU 15 seconds, wall alarm 20 seconds,
address space 512 MiB, maximum individual output file 4 MiB.

The script parses complete old/new source but executes only extracted stdlib
`thaw`/`canonical_bytes` bodies and their serializer expressions projected onto
explicit synthetic field dictionaries. It does not import the authority module
or instantiate Owner, Binding, Admission or Lease. It compiles candidate source
without executing it. The 104 equality/error/fresh-mutation assertions passed,
covering both expression sites, ordinary nested mappings/lists/tuples, mapping
proxies, Unicode, unsupported bytes/sets, mixed keys and nonfinite floats.
Nested mutation and mutation through a mapping-proxy backing dict between calls
change the output equally in both expressions. Baseline current-source bytes
were rechecked after the run. No failed engineering execution occurred.

Tiny paired timing uses four alternating-order samples per expression and
roster size, 12 calls each; all fields are synthetic metadata, without real
labels or data. Raw nanoseconds are retained in `RESULT.json`. At 16 entries,
old batches took 4.366–4.485 ms and new batches 2.544–2.646 ms; at 128 entries,
old batches took 34.130–37.838 ms and new batches 19.074–20.113 ms. These are
serializer microtimings only, with no full-pilot saving or performance claim.

The actual pilot29 remains failed/closed as communicated by the root task;
this preparation neither modifies its outcome nor authorizes or starts a run.
Only this new preparation directory was written. No integration, Git mutation,
registration, state change, numerical calculation, network access or production
change was performed. The complete original 32-motif/512-sample research scope
is unaffected.
