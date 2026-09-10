# Data locations and retention catalogue

This catalogue preserves the physical layout. It is an index of known inputs and
evidence anchors, not a new data collection, an exhaustive quality audit or a
declaration that all historical samples are available for fresh testing.

The machine-readable [artifact catalogue](artifact_catalog.json) records:

- **42 repository-relative anchors:** exact SHA-256, byte count, local presence
  and current Git tracking for ledgers, gate files, reports and manifests.
- **284 workspace-relative external files:** 14 root-document/manifest anchors
  freshly hashed while cataloguing, plus the 270 original input records pinned
  by the retained [risk-policy baseline manifest](../risk-policy-2026-09-10/verification/baseline-input-manifest.json).
  All 284 were locally present when catalogued. The 270 content hashes were
  copied from that prior verified manifest; their current sizes/presence were
  checked without materializing financial data. The retention checker performs
  any subsequent byte verification and reports its own result.
- **Known unavailable evidence:** exact historical settlement cashflows for
  BZRX/LUNA/BNX have no admitted dataset, path or hash. Recovery is deferred.

`artifacts[].path` is relative to this repository.
`external_inputs[].path` is relative to its parent workspace, historically
`/home/malecada/master_thesis`. A clean clone elsewhere may lack those inputs.
The catalogue does not silently redirect them or fetch replacements.

## Logical datasets and evidence

| Group | Physical location | Evidence/availability boundary |
|---|---|---|
| Financial registrations and outcomes | This checkout: `data/predlab/`, `data/rebuild/`, `data/llm_event_xs/`, `data/llm_pair_xs/`, `data/llm_rank_xs/` gate/ledger pairs | Tracked anchors record exact current bytes. Outcomes include historical invalidations and unavailable cases. Gate existence is not fresh-sample admission. |
| Corrected saved forecasts | This checkout: `data/predlab/audit_correction_2026_09_09/` | Sixteen corrected ENet vectors; fixed saved comparisons documented in the forecast charter and pinned gate. No model refit or new forecast-class validation. |
| Original saved forecasts | Sibling `TradingAgents-predlab/data/predlab/forecasts/predlab_p2_ml/` | Original model/baseline Parquets pinned in the 270-file external manifest. Current source still refers to these paths. Historical confirmation exposure remains spent. |
| Predlab raw five-minute data | Sibling `TradingAgents-predlab/data/predlab/klines_5m/` and `klines_5m_manifest.json` | Directory and manifest present. The manifest is indexed; the entire raw store was not rehashed or certified complete. No `klines_1h/` sibling directory was found at this particular path. |
| Xsect daily/hourly market stores | Sibling `TradingAgents/data/xsect/`; this checkout retains `data/xsect/*manifest.json` | Original hourly/daily files used by past corrections are in the external pinned-input list. Broader raw-store coverage is not certified by the presence of a manifest. Funding and lifetime admission remain instrument-specific. |
| Historical factor/reference streams | Sibling `TradingAgents/data/multi_2coins_v2/` and other exact original paths in the baseline manifest | Existing source/data worktrees are preserved. Proxy-price/assumed-funding constraints still apply. Do not run legacy baseline scripts on these directories as an engineering check. |
| Hourly recovery and identity evidence | This checkout: `data/recovery/2026-09-10/`; [recovery manifest](../data-recovery/verification/final-manifest.json) | Prior retained recovery covers admitted missing bars and explicit identity quarantine. Original inputs remain preserved. The [prior retention receipt](../data-recovery/verification/git-retention.json) reports its own checked scope, not the entire external store. |
| Settlement documents and receipts | This checkout: `data/settlement-evidence/2026-09-10/` and settlement recovery subdirectories | Documentary bodies and failed requests retained. Exact terminal prices/fees/final funding are not established merely by closure notices or minute candles. |
| Forecast/risk and policy results | This checkout: `data/diagnostics/2026-09-10/`, `docs/diagnostics-2026-09-10/`, `docs/risk-policy-2026-09-10/` | Completed registered diagnostics and fixed policy comparison. Dedicated forensic/result receipts do not authorize another run. |
| Dated BTC/ETH carry capture | This checkout: `data/carry-feasibility/2026-09-10/capture/` plus separate measurement ledger | 16 public requests, three snapshots, 48 entry cases and 432 terminal scenarios retained. The capture manifest's `files` map is explicitly declared for member verification; conditional fees/freshness/margin qualifications remain. |
| Carry official source documents | This checkout: `docs/carry-feasibility-2026-09-10/source-evidence/` | Manifest/raw source bodies preserved. Entry structure differs from a generic `path`/`sha256` member list; the original independent checker, not blind manifest recursion, defines member verification. |
| Prospective operational funding | This checkout: `data/operational_funding/2026-09-10/` | Retained public event captures are observed queries, not historical expected-calendar proof or permission for paper accumulation. See the funding-capture report. |
| Bybit, open-interest, cross-asset and fundamental manifests | This checkout: `data/predlab/bybit/manifest.json`, `data/predlab/oi_5m_manifest.json`, `data/xsect_futfx/manifest.json`, `data/xsect/fundamentals*manifest.json` | Indexed source/coverage anchors. Later causal-data, entity mapping and accounting qualifications govern use; manifest presence alone does not certify vintage or executability. |
| Article corpus | Workspace `News_fulltext/` | Directory present; no content inventory, publication-vintage audit or backup verification was performed in preparation. Future use needs its own manifest and point-in-time admission. |
| Canonical workspace reports | Parent workspace `AUDIT_*.md`, recovery/settlement/operations/funding reports and `RESEARCH_LOOP_GUIDE.md` | Selected exact hashes included as external anchors; tracked portable counterparts are linked in the evidence index. Some root-only historical reports need separate restoration in a clean clone. |

## What retention means here

Local file existence, content hash, Git tracking, an available local Git blob
and a remotely recoverable copy are different claims. `.gitignore` broadly
ignores data/logs while specific evidence is tracked. A tracked manifest with
ignored or absent raw members is not a complete backup.

The preparation retention checker verifies declared catalogue hashes and only
explicit member mappings. It must not open arbitrary paths embedded in unknown
manifest fields. Its receipt states the observed scope; a successful anchor
check does not certify every file mentioned in this table. Historical external
`git_blob` references in the 270-file manifest are recorded provenance, not a
fresh check that the current remote retains those blobs.

The original root instructions and skills were copied before simplification to
workspace `.readiness-backups/2026-09-10-instructions-173014102728/`, including a
SHA-256 manifest. This is a same-machine backup and is not tracked in the active
repo. Original raw stores were not moved, deleted, amended, refetched or newly
backed up by cataloguing. Keep new run outputs immutable and verify their actual
Git inclusion/backup separately before treating a checkpoint as recoverable.
