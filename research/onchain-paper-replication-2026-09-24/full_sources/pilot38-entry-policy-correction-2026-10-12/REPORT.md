# Compact MCM entry policy correction

Status: source candidate tested, uninstalled; no registration, authority, admission or execution release. Failed36 remains terminal and spent. The genuine post-entry qualifier stop is still unproved.

The exact failed36 source was `998d353d86d683e8a095ebffb4e539a5c849ca68`. `CAUSE01.json` joins the original claim/failed claim hash, selected policy and producer-plan hashes, original source hash and failed-output hashes. `STACK_EXCERPT01.txt` preserves the actual route: `produce_imported` → `compact_mcm_batched.produce` → `compact_mcm._prepare:146`. The failure occurred before the selected preparation-only stop.

Every conjunct of the failing generic predicate was evaluated from actual metadata:

| Predicate | Actual evidence | Result |
|---|---|---|
| Exact top-level keys | Extra `entry_qualification`; no missing keys | **False** |
| Integer supported schema | 6 | True |
| Integer positive cell allowance | 56,584,576 ≤72,495,392 <2^63 | True |
| Integer metadata allowance | 172,032 | True |
| Required metadata coverage | 3×8192×(8−1)=172,032 | True |

The eight stages follow the registered seven-graph descriptor plus dictionary import. The first graph's56,584,576 cells join the actual failed pilot summary (1,768,268 nodes ×32 original motifs). No arrays were read, generated, sampled or reclustered.

`compact_mcm_batched.validate` already explicitly accepts and validates `entry_qualification`. The later generic `_prepare` allowed-key equality omitted it. The candidate changes one expression: the batched branch adds that optional key to its allowed set. Legacy and durability branches remain unchanged. Invalid selector schemas, nonserial selection, format case, malformed/uppercase graph hashes and extra fields still fail the actual batched validator. A syntactically valid different graph hash is deliberately not rejected by parsing; actual target/experiment matching remains the genuine stop boundary's responsibility.

`compact_mcm.py` is the candidate, `ORIGINAL_compact_mcm.py` the byte-exact original. `PATCH01.diff` and `INVERSE01.diff` record the single expression change. Literal inversion reconstructs the original hash. No live source, gate, Git or STATE was modified.

## Focused verification

Root confirmed original36 supervisor/worker/monitor closure before execution. `TEST01.log` retains the initial repository pytest refusal of the new evidence-path module before collection. No profile rule was changed. The explicitly authorized new engineering fixture was then run as a finite standalone unittest harness; the existing admitted qualifier tests used normal repository pytest.

- `TEST02.log`:21 synthetic tests passed; enclosing2.76s, maximum RSS810,720KiB, exit0. The same actual `_prepare` function body is compiled from original/candidate source with synthetic boundary objects; the actual current batched and durability validators are used. Original36 policy reproduces the exact failure on original code (RED); the candidate reaches the immediately following kernel-selection sentinel (GREEN). Both original and candidate preserve absent-qualifier schema1, durability2, batched5 and grouped6 routes. Negative scalar/route controls retain cell, metadata, integer/schema and selected-input checks. No numerical kernel or writer is entered.
- `TEST03.log`:existing `test_entry_preparation_stop.py`11passed in1.96s; enclosing3.35s, maximum RSS827,392KiB, exit0. Existing parsing, genuine-target refusal and AST stop-order checks are reused.

The synthetic objects are not ResearchRun/Owner authority and never enter publication, source restoration, native execution or empirical production. The fixture proves this control-flow correction through the next kernel boundary; it does not prove full `_prepare` completion, genuine imported-target currentness, fresh lease validity, the actual qualifier stop, throughput, or future38 success. Future integration and any corrected experiment identity require Root's separate decision and evidence.
