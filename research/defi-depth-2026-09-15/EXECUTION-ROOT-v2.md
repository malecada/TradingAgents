# Authoritative R1 execution route, v2

The sole root remains /home/malecada/master_thesis/TradingAgents-defi-depth.
No R1 claim was created from the original09ef89a packet. Its two failed interface/
metadata checks are retained in reviews/r1-metadata-preflight-history.json.

Move the clean detached worktree to the reviewed v2 commit, then use the original
pinned Python with PYTHONPATH set to this isolated root. Metadata admission is
`tradingagents.research_defi_repair.admit` (Python API), exact registration
research/defi-depth-2026-09-15/gates-r1-v2.json and experimentdefi-depth-r1-20260915.
The sole actual runner is research/defi-depth-2026-09-15/r1_source_v2.py.

Existing source/inputs/oldrecords are byte-identical; only the separately reviewed
historical-verification compatibility layer and corresponding bindings differ.
Keep one owner and one launch. Do not run R1 in the original checkout. Import
exact receipts and source history before later admissions elsewhere. Isolated
runtime/output paths and the actual session/commit are recorded after start.
