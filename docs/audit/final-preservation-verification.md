# Final preservation verification

Checked at **2026-09-09 15:27:01 UTC**, with the correction checkout at `cc6801e81e25f05cdfbae77d560b59fa43e16dd9`. Exact paths, expected/current hashes, statuses, and comparison results are retained in [verification/final-preservation-checks.json](verification/final-preservation-checks.json).

**The three original research worktrees match their recorded audit state. All existing gate entries and the available original source/data evidence hashes are preserved. The final offline log confirms 779 passed and 2 deselected. Authorized workspace-document and thesis changes are explicit exceptions.**

## Original worktrees

`git status --porcelain=v1 --untracked-files=all` was compared line-for-line with `/home/malecada/master_thesis/data/audit_2026-09-09/verification.json`. HEAD and branch were also compared with `workspace_inventory.json` from the same audit directory.

| Original worktree | Recorded and current HEAD | Branch | Status comparison |
| --- | --- | --- | --- |
| `TradingAgents` | `017986777996647a71b7c3097845b3c6ac53883c` | `feature/llm-event-xs` | Identical: modified `uv.lock`; untracked `scripts/trend_mult_robustness.py`. |
| `TradingAgents-predlab` | `c5f1a4452aa3ba1124595bcf6a222422af8fb16e` | `research/prediction-lab` | Identical: one deleted local loop file, four modified evidence files, and one untracked champion script. Exact six status lines are retained in the JSON. |
| `TradingAgents-monitor-nav` | `ed5e22f63d9e2d8ab4bf163103f40b0029eb0e7b` | `main` | Identical: modified `CLAUDE.md`. |

Existing dirty files were preserved; this check does not describe these worktrees as clean. The audit checkout and intentionally revised thesis are separate from this preservation comparison.

## Gate preservation

Every tracked `gates.json` file in the correction checkout was compared with integration commit `b7dff69e8d4922f053cf7b5d3ce9a61ffe87d48b`. Parsed JSON values were compared recursively for every existing top-level entry, so nested criteria, windows, cells, and thresholds are included. The current tracked gate-file set is the same five-file set present at integration.

| File | Original entries | Current entries | Existing entries changed or removed |
| --- | ---: | ---: | ---: |
| `data/llm_event_xs/gates.json` | 1 | 1 | 0 |
| `data/llm_pair_xs/gates.json` | 2 | 2 | 0 |
| `data/llm_rank_xs/gates.json` | 1 | 1 | 0 |
| `data/predlab/gates.json` | 30 | 31 | 0 |
| `data/rebuild/gates.json` | 21 | 21 | 0 |

All **55 existing entries are unchanged**. The sole addition is `audit_correction_2026_09_09` in the predlab gate file. This is a semantic preservation check; harmless JSON formatting differences are not treated as criteria changes.

## Recorded evidence hashes

The existing audit inventories were read as manifests. Files named by those manifests were hashed without interpreting market or strategy outcomes.

- `workspace_inventory.json`: 16 non-thesis paths checked. Fourteen hashes match, including the original predlab gates, ledger, selected source files, superseded equity image, prior audit reports, and assignment text. The two nonmatching paths are the authorized root documentation exceptions described below.
- `data_probe_results.json`: all five recorded data-manifest SHA-256 hashes match: predlab 5-minute klines, OI, and Bybit manifests, plus xsect klines and funding manifests.
- `gates_inventory.json`: original predlab gate and ledger SHA-256 hashes both match. The already-dirty original ledger remains byte-identical to the audit snapshot.
- `engine_branch_matrix.json`: all 45 recorded source-presence/hash checks match across the three original worktrees. This comprises 23 existing files whose recorded 16-hex-character SHA-256 prefixes match and 22 files that remain absent as recorded.

The original predlab gate hash remains `4225cc9965940d226bd8d77e9633b3995cc7dc7935527bbd352a2750a828f85e`; the original ledger hash remains `d4aa4a780caa03f945d0d9d2743950dce8002a0b36885ca667939ebdd78ebda8`.

The root `AGENTS.md` and `CLAUDE.md` deliberately differ from their initial workspace-inventory hashes. The coordinating repair confirmed that they were updated to identify the consolidated correction checkout, withdraw stale resumptions, and reconcile correction status. Their old/current hashes are retained in the JSON rather than hidden by the preservation claim. `RESEARCH_LOOP_GUIDE.md` was also deliberately updated for audited governance; it has no hash in the initial workspace inventory. Versioned copies of these workspace documents are held under `docs/audit/workspace-*`. Five thesis paths in the original inventory were intentionally excluded because thesis evidence reconciliation and rebuilding were authorized.

## Final offline test log

The correction-checkout log and its copy in the original audit directory are byte-identical:

```text
docs/audit/verification/integrated-offline-final.log
/home/malecada/master_thesis/data/audit_2026-09-09/integrated-offline-final.log
SHA-256: 9f93c8ed93d72a1e45c417eb803413e877a4407c4fd506872fe5bd2dbe3cb059

779 passed, 2 deselected, 3502 warnings in 223.37s (0:03:43)
```

The log reaches 100% and contains no failure summary. Its warnings comprise 3,501 scikit-learn feature-name warnings and one pandas deprecation warning. The execution plan separately records that two historical parity/marker tests were deselected and a three-test physical-data coverage file was excluded because the raw stores remain in the preserved source worktree. The log verifies the reported counts; it has no command header that independently identifies the selection arguments. No new suite execution or backtest was performed for this preservation review.

## Limits

Matching Git status alone cannot prove that an already-modified or untracked file has identical bytes; the independent recorded hashes provide that assurance only for the paths they cover. Matching a data manifest proves preservation of that manifest, not of every underlying raw row. The initial audit did not provide a complete cryptographic snapshot of every workspace file or data shard. Source checks in the branch matrix retain their original 64-bit hash-prefix precision. No claim of complete raw-store equality beyond the recorded manifests/hashes is made.

The check is a point-in-time preservation record, not a certification of subsequent edits, VPS state, holdout outcomes, or strategy validity. No original worktree, original input, gate, ledger, implementation file, or historical result was changed by this verification; only this report and its JSON evidence were written in the correction checkout.
