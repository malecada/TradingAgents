# Physical persistence-file requirements correction

All predecessor01 files and its manifest remain byte-identical. This successor changes capacity.py by one insertion only; inverse deletion is byte-identical to01. No kernel, Main, limits, scientific behavior, registration or empirical artifact changed. No real bodies or numerical imports were used. Original motif dimensions supplied separately to Root are not read or inferred here.

Named requirements now compare max_file_bytes against the largest possible score-tail records.bin (80*min(stage cells,score_chunk_cells)), float64 score-data .bin (8*min(stage cells,score_chunk_cells)), and event .bin (168*min(2*stage cells+global checkpoint-generation budget,log_chunk_events)). The global generation budget is conservatively available to each individual stage when forming a universal file envelope; it is not spent repeatedly in aggregate accounting. Partial final/only chunks use their possible record counts. JSON metadata is stored separately and retains its own8192-byte file allowance check.

Source derivation: score_tail.py:20-21 declares80-byte records comprising the48-byte <Qd32s frame plus32-byte chain; records.bin has no additional header. compact_pair_log.py:19-20 and145-170 append136-byte <QB7xQdQ32s32s32s frames plus32-byte chain, without a file header. score_batches.py:178-196 serializes contiguous <f8 values directly with tobytes() into .bin and writes the header separately to .json. compact_policy.py:77 retains the80*cells<=8MiB chunk-contract check; that8MiB internal bound does not imply a4MiB physical file bound.

For the stated current chunk settings, full tail=65536*80=5242880B, score-data=65536*8=524288B, events=49152*168=8257536B. Against4194304B, tail and event files refuse independently of checkpoints and selected inputs; score-data fits. No cap increase or chunk-policy change is performed.

Focused successor-only tests pass: exact source record widths; the three named full-file sizes; both added4MiB refusals; equality passes and one-byte deficit refuses for each named requirement; partial chunks; full source compile; and byte-identical inverse. Predecessor manifests were verified without rerunning its matrix. Existing component-accounting limitations and execution_admitted=False/complete_resource_envelope_proven=False remain unchanged. This is not complete filesystem accounting or admission.

Run `.venv/bin/python -B research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-complete-neighborhood-capacity-preparation01-2026-10-08/successor02/check02.py`.
