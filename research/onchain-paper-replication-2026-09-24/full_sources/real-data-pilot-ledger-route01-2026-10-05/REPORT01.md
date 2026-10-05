# Authoritative Main-ledger route

**Use Main as the execution root. Existing CAP code cannot run against Main's ledger merely by changing `--root`, `execution_workspace`, cwd or PYTHONPATH.** The narrow route requires no new ledger abstraction: retain Main's ledger and integrate the required reviewed package changes into Main before the import/MCM/training job. The first graph can use Main's already existing `graphs` route without waiting for that integration.

Observed roots: Main HEAD `7d400380810c2aefd79e82ed2a8eabbe44119e89`; CAP HEAD `5a6169f6101dd6524325fc22643d6415dbc283ff`. Actual CAP150 package hashes match the integration record. Compared with Main:101 identical,15 absent,34 different; Main also has8 additional package bodies. The full preserved union is158. `SOURCE_ROUTE01.json` records exact names and both current hashes, not an instruction to overwrite divergent bodies. Accepted allocation review is reused:19 actual current claims +17 prior =36spent; proposed71 is allocation-only and does not authorize execution. No historical claim bodies were recopied or recounted here.

Concrete refusal points:

- `tradingagents/research/admission.py:235`: source must equal the chosen root's actual HEAD; registration and every declared source body must match that root's committed/current bytes (`:107`,`:294`). CAP5a6169f is not Main's HEAD. Even importing that Git object into Main does not change this condition.
- CAP `tradingagents/research/onchain_replication/job.py:140`: executed job.__file__ must resolve to admitted.root/tradingagents/research/onchain_replication/job.py. A CAP import with Main root is refused even if bytes happen to match. The candidate independently imposes its own same-root source location at `real_pilot_import_caller.py:110`; imported preparation imposes the same admitted-root/source-pin rule.
- CAP `job.py:105` workspace_binding describes root/research_runs, root/research_artifacts and that root's Git common directory. It validates paths; it offers no ledger override. `_command` (`:149`) repeats one root/source and uses `-m`; monitor/worker use cwd=args.root. There is no independent code-root/ledger-root contract.
- `admission.py:188` discovers claims only under root/research_runs; `:316–338` computes the same-family denominator there plus prior_attempts. `lifecycle.py:76` locks that same directory, `:94` places the new run there, and `:99` re-admits under the lock. Running with CAP root therefore uses CAP history, not the authoritative Main paper ledger. Copying claims, adjusting prior_attempts, redirecting symlinks or resetting a family is not a valid remedy.
- CAP `matching_owner.py:142` requires the current whole package source closure and every numerical-anchor body to match the admitted source. A merged158-body closure cannot reuse the old150-body5a6169f map as if unchanged. Main `admission.local_path` (`:39`) also refuses registered paths resolving outside Main; a symlink to the external CAP package is not a supported source bridge.

For the imported pilot, the bounded integration seam is the15 missing module bodies and34 divergent bodies listed in SOURCE_ROUTE01, preserving the101 identical bodies and all8 Main-only bodies. Key coupled changes are job dispatch/native limits, resources' genuine native guard, matching_owner/resource_binding, original_dictionary/preparation/stage/Target, compact_owner/stage/MCM/publication/retention, and FeatureJournal. The accepted caller/helper are installed into this same package. Divergent modules require a merge, not CAP replacement: Main's resources includes the accepted kernel-peak telemetry; graph_production includes the legacy coverage bridge; population_assembly includes checked projection/observer/treatment handling; model_registry/evaluation/training include existing financial execution contracts. Those features must remain intact. This is a source integration requirement, not a need to change admission, lifecycle, the old ledger, or family accounting.

After integration, Root commits the actual Main package and derives its complete required_sources map, then binds the pair policy to that exact committed package anchor. The eventual gate source is the actual Main HEAD containing the new gate/policies and unchanged source bytes. execution_workspace must describe Main. Existing launch/monitor/worker all use Main root and the new source; genuine ResearchRun.start then accounts against the original Main history. Pilot-specific real native/storage limits still need separate review: inherited3GiB/1800s/4MiB-file/1GiB-root constraints remain execution blockers, especially on Main's whole workspace. This investigation does not change them.

**Concrete next action for Root:** after the actual storage closure is independently accepted, run the already written metadata-only builder from Main:

```sh
cd /home/malecada/master_thesis/TradingAgents-audit-fixes
.venv/bin/python -B research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-first-graph01-2026-10-05/prepare_registration01.py
```

That script checks the actual storage closure/restoration/native cleanup, preserves the original family, uses Main's current required_sources, and creates only the exact first-graph gate. Do not rerun if its exclusive gate/namespace already exists. Once Root has committed that gate and its reviewed inputs, the existing read-only admission command is:

```sh
.venv/bin/python -B -m tradingagents.research check \
  --root /home/malecada/master_thesis/TradingAgents-audit-fixes \
  --registration research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-first-graph01-2026-10-05/gate01.json \
  --experiment eth-paper-real-pilot-graph-20220502-20261005-01 \
  --source "$(git rev-parse HEAD)"
```

Neither command is a native launch; the first was not executed in this investigation. A successful metadata check still needs the existing separate final source/input/resource/entry review. There is no `job --mode preflight`; its launch/monitor/worker modes must not be used for a metadata probe. Main remains frozen while the currently recorded storage unit owns its source.

Validation here was bounded source inspection, exact150-body code/hash comparison, static path/command/ledger reconstruction, and reuse of accepted allocation evidence. No Admission, ResearchRun.start, numerical imports, arrays, Owner, network, native activity, live source or registration mutation occurred. Runtime behavior of the eventual merged package and real-data capacity remain untested. Investigation stops at this route decision.
