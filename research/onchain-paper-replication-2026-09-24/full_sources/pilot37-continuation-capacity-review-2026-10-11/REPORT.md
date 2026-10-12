# Independent prospective whole37 capacity review

Disposition: accepted static prospective arithmetic only. No P1/P2 defect found in the changed growth calculation. No whole37 capacity declaration, admission or release follows. Review author: independent reviewer `/root/pilot_efficiency_integration_review`.

`check01.py` independently derives cells from each public graph's row count times32, joins the original seven graph cardinalities, calculates batches/groups by integer ceilings, and aggregates full-group plus trailing-group tar extents independently of the author's batch loop. It authenticates every source/input pin in the candidate and checks preserved/recovered byte, operation/chunk, marker, origin and summary caps. `CHECK01.json` preserves the exact input/source hashes and results; `CHECK01.log` preserves the passing execution. Only standard-library metadata arithmetic ran, with no project imports.

| Quantity | Independently reconstructed |
|---|---:|
| Whole graph cells | 415,968,128 |
| Batches / groups | 101,559 / 6,352 |
| Persistent prefix marker cap | 415,985,664 bytes / 101,559 entries |
| Conservative added logical/allocated bytes | 416,083,968 |
| Projected logical bytes | 16,987,319,366 |
| Projected allocated bytes | 19,129,360,989 |
| Projected entries | 769,715 |
| Remaining logical / allocated / entry margin | 192,549,818 / 2,345,475,491 / 230,285 |

The public typed allowances exactly cover recomputed preserve and twice-recover payloads, two operations and three chunks per group. Every full archive remains within3,645,440 bytes and the inherited4MiB scratch slot. The current35 and36 declaration growth, directory, other-writer and entry terms are identical; no unreviewed downward credit is needed.

The relevant lifetimes were checked in the actual source:

- `batched_continuation.py:54` writes one marker after numeric/score closure; `batched_journal.py:59` creates it directly, without a second temporary marker. `grouped_offload_semantics.py:37` selects only the original three score files. All seven graphs' prefix markers therefore remain local. Null manifest/empty graph-specific inputs select no parent recovery copy.
- `compact_mcm_batched.py:664` flushes each16-batch group synchronously; `typed_payload_operations.py:232` recovers and authenticates before retiring originals. **Original and semantic-recovery journal trees coexist.** The candidate's single98,304-byte live delta is not itself a complete description of this overlap. However, the inherited capacity01 aggregate already reserves seven original journal groups (24,553,536 bytes), plus one3,507,648-byte recovery journal. The actual serial two-tree peak under the new cap is7,211,904 bytes, below that28,061,184-byte inherited envelope. `real_pilot_import_caller.py:601` completes each graph before advancing; failures abort. Thus the overlap is covered without another addition or hidden deletion credit. Any future parallel graph execution must revisit this argument.
- `batched_numeric_execution.py:150` retains one8192-byte-capped summary per batch and9-byte origins per cell. Added phase/policy fields consume the existing cap. Provisional occurrence receipts are hashed, not emitted as new files. Fixed-size closure tokens, group anchors and summary counts are unchanged.
- Typed claims and group result schemas retain the same bounded fields. Increased payload sizes fit the inherited19-digit numeric envelopes. Transport counts do not change; the2,599,854,080-byte additional cumulative payload is not retained filesystem growth. Existing bounded lifecycle/stage metadata covers the new scalar policy/timing/continuation fields; exceeding a body cap refuses rather than silently growing it.
- With4096-byte allocation rounding, both1024- and4096-byte pending/complete bodies occupy one block. The script independently obtains3,670,016 allocated bytes for either full journal group. The candidate deliberately adds98,304 allocated bytes anyway. Markers each reserve a full4096-byte block; directory allocation is a separate pending term, not included by pretending directory entries are free.

Before a concrete37 entry, Root must use its fresh baseline including all retained36 results and later preparation metadata; independently accept the expanded101,559-marker directory/inode population against the inherited2,147,549,184-byte directory allowance; bind actual free-space/floor and other-writer conditions; retain inherited path/ASCII/integer and failure/checkpoint restrictions; and produce a separate whole37 declaration/review. The192,549,818-byte logical margin is dated arithmetic, not current available space. Existing guards are sampled checks, not hard quotas or writer exclusion. Current36 inputs still select the mandatory preparation stop and cannot be treated as a whole37 execution selection.

No arrays, numerical execution, native process, claim, budget, runtime import, source edit, Git action, network, credentials or storage transport was used. No empirical result, timing/throughput, memory sufficiency, current remote availability, parent-prefix reuse, successful36 outcome or full37 feasibility was tested. No marker packing or deletion credit is assumed. No higher-effort correctness investigation is required for this narrow static increment; the remaining conditions require concrete entry evidence.
