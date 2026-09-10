# Repository and Codex readiness review — September 10, 2026

**A bounded preparation pass is justified before sustained research. Preserve the corrected accounting and historical evidence; improve the default workflow, research admission and instruction setup. Astra High is a reasonable research default to evaluate, with Medium for routine work and Ultra for suitably large parallel investigations. No additional connector is currently a demonstrated prerequisite.**

This is a review and proposed preparation sequence. No source refactor, experiment, full test suite, model-setting change, plugin installation/removal, account access or production operation was performed. The reviewed repository was clean at `a75932c`. Three independent reviews covered structure, testing/admission and skills/context. Codex CLI reports version `0.153.4`. Model recommendations are informed judgments, not a measured performance comparison on this repository.

## Repository preparation

### 1. Make the default verification command safe and complete

The standard-suite [V2 regression test](../tests/regression/test_v2_unchanged.py#L30) launches the historical `baseline_strategy_v2.py` when two saved prediction files exist. Its subprocess points at the real `data/multi_2coins_v2` directory; [lines 49–74](../tests/regression/test_v2_unchanged.py#L49) explain that metrics are written into that directory. It has neither an empirical opt-in marker nor a `slow` marker. [Pytest defaults](../pyproject.toml#L79) exclude only `slow`. The two triggering CSVs are absent in the reviewed checkout, so the test would currently skip; the problematic behavior becomes reachable when those data are restored. No historical overwrite was observed or induced by this review.

Independent saved-evidence checker tests also live under `docs/`, outside a typical `pytest tests/` invocation. Collecting the diagnostics and risk-policy files both named `test_verify_preservation.py` produces an import-file-mismatch error. The same two-file collection with `--import-mode=importlib` successfully collects 22 tests. Collection only was performed; no test bodies or financial runs executed.

**Prepare:** provide one named offline engineering/checker command, classify empirical/network/account tests explicitly and keep them opt-in, move historical-data regression inputs to temporary copies when explicitly invoked, and use collision-safe collection. Add a small CI job for that safe target; no `.github` workflow currently exists. Test collection must not quietly turn into a strategy replay or write into retained evidence.

**Acceptance:** the default target is deterministic, needs no credentials or market requests, does not mutate historical stores, includes relevant independent verifier tests, and runs successfully in a clean research environment.

### 2. Establish one truthful, portable starting point

The [README](../README.md#L62) still directs readers to clone TauricResearch upstream, and [its usage section](../README.md#L112) emphasizes the original LLM CLI. [CHAMPION_SYSTEM.md](CHAMPION_SYSTEM.md#L5) still opens with the invalidated +1.89 Sharpe/+409% claim, while the [correction register](audit/corrections.jsonl#L3) withdraws it. A fresh agent or reader can encounter the obsolete claim before its correction.

Root `AGENTS.md` and `CLAUDE.md` contain approximately 16KB each, with the same state narrative except for an empty memory-injection block. Checkout `CLAUDE.md` adds about 8KB of overlapping history. These are byte counts, not measured token costs, and Codex does not automatically load every file named CLAUDE.md. The duplication matters when agents follow the reading instructions and when status copies drift.

The active Git checkout has no operative tracked `AGENTS.md`, `.agents/skills` or `.codex` setup. The two useful crypto skills reside in the non-Git workspace root. A new clone does not reproduce those local instructions. Codex's documented discovery starts at the project root and recognizes AGENTS.md or configured fallback names; an unrelated parent-workspace file or unconfigured CLAUDE.md is not a portable substitute. [Official instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

**Prepare:** version concise repo instructions and the domain skills; keep root/Claude entry points as short pointers to the canonical version. Put active status and the next action in one linked state file. Add a current research landing page and a supersession index for historical documents, while retaining original evidence bytes and pinned snapshots. Conspicuous withdrawal notices can be placed in mutable landing pages or companion records when the original document is an immutable artifact.

**Acceptance:** a new clone/worktree can find the active program, correct environment, permitted commands, zero-validated-strategy status, constraints and current evidence without relying on this conversation or private memory files.

### 3. Give new research explicit sample-exposure and run admission

The preserved [predlab registry](../tradingagents/predlab/registry.py#L20) encodes an April 1, 2025 holdout boundary and an `allow_holdout` boolean. That historical guard cannot by itself represent which family inspected or spent a window, a new prospective sample, adaptive development ancestry or a cumulative attempt budget. This is a limitation for the next program, not a new invalidation of the recently reviewed runs, whose dated guards supplied additional checks.

**Prepare:** add a small new-program register linking family/parent hypothesis, experiment, dataset/window identity, exposure state, research stage, selection freeze and cumulative budget. Admission should check these records before a new empirical run accesses its registered inputs or produces outcomes. Ordinary read-only evidence recovery is not a new empirical run. Older gate objects, window constants and outcomes remain unchanged. An explicit correction or new development experiment must remain distinguishable from a confirmatory test.

**Acceptance:** synthetic admission checks reject spent-as-fresh windows, unregistered outputs, reset family budgets and unauthorized repeat runs, while accepting valid new development and prospective cases.

### 4. Reuse common run plumbing without rewriting old experiments

There are 252 Python scripts and 225 package Python modules in the reviewed tree. Size alone is not a defect. The useful extraction boundary is repeated run/evidence handling: [RunContext](../scripts/audit_reeval_common.py#L51), the [dated collector preflight](../scripts/capture_dated_carry_2026_09_10.py#L37), and the [risk-policy ledger writer](../scripts/audit_factor_risk_policy_2026_09_10.py#L140). They already implement stronger controls than the generic [ledger append](../tradingagents/predlab/registry.py#L119), but each is tied to a particular cycle.

**Prepare:** a narrow new-run helper/template covering registration and source checks, exclusive run ownership, declared inputs, immutable outputs, complete denominators, serialized once-only ledger completion, failure receipts and independent verification. Build from the proven patterns and use it for new work. Keep independent cashflow reconstruction independent of the implementation under test.

Do not mechanically migrate every dated runner or combine the simple-return [holdings engine](../tradingagents/accounting.py), [event-accounting contract](../tradingagents/event_accounting.py) and [Decimal carry calculator](../scripts/carry_feasibility_math_2026_09_10.py). Their instrument, fee, wallet and event semantics differ. Document when each is admissible; extend one only for a concrete research need.

**Acceptance:** two small synthetic example runs can use the common lifecycle; tests cover duplicate starts, concurrent completion, partial failure, source mismatch and denominator loss. No old financial run is recomputed to prove the refactor.

### 5. Make runtime and evidence locations reproducible

The active checkout has no `.venv`; recent checks deliberately use the sibling predlab interpreter. [conftest.py](../conftest.py#L3) documents the editable-install source-path ambiguity and works around it for pytest. A lockfile exists, but the declared Python range, research instructions and [Dockerfile](../Dockerfile#L1) do not describe the same research runtime. Foundation-model packages, UI, on-chain and LLM dependencies also share the [base dependency list](../pyproject.toml#L11).

**Prepare now:** one pinned research interpreter and locked environment in the active checkout, with an import-origin/runtime receipt. Do not mix this with dependency upgrades. Separate optional heavyweight dependency groups only after a reproducible baseline and an actual need are established.

Some registered inputs intentionally reside in sibling worktrees; [forecast diagnostics](../scripts/audit_saved_forecast_inference_2026_09_10.py#L116) depend on them. The broad `data/` and `*.log` [ignore rules](../.gitignore#L224) coexist with explicitly tracked evidence. Add a logical dataset/artifact catalogue and a manifest-aware backup check. Preserve physical paths/hashes initially; neither mass-moving data nor blanket-unignoring all data is useful preparation.

## Codex configuration and model effort

The reviewed allowlisted settings in `/home/malecada/.codex/config.toml` are `model = "gpt-6-astra"` and `model_reasoning_effort = "ultra"` at lines 1–2. There are 20 enabled plugin entries and four configured MCP servers: node_repl, fetch, pdf-mcp and playwright. No explicit model/effort agent defaults, custom-agent directories or project `.codex/config.toml` were found at the checked workspace/checkout paths. This is configured state; it does not prove every plugin/server is healthy or exposed in every session. Credentials, environment values and authentication headers were not included in the inspection output.

Ultra has a specific product meaning: it uses automatic subagent delegation. Higher effort can increase latency and token use, while parallelizable work can benefit from Ultra's delegation. OpenAI recommends selecting the lowest effort that delivers adequate results; most tasks do not require Max or Ultra. [Official model guidance](https://learn.chatgpt.com/docs/models).

The following is a starting policy to evaluate, not an asserted optimum:

| Work | Proposed setting | Reason |
|---|---|---|
| Research coordinator, experiment design, synthesis | Astra High | Retain a strong model and enough depth for interacting economic/statistical constraints. |
| Bounded implementation, source inventory, known test fixes, documentation | Astra Medium | These tasks often have a clear contract and executable checks. |
| Difficult accounting/inference dispute or single deep review | Astra Extra High or Max | Spend extra reasoning on a specific unresolved correctness question. |
| Broad audit or research synthesis with independent substantial subtasks | Astra Ultra | Automatic delegation fits this workload; use the output only after coordinator reconciliation. |
| Routine high-volume bounded work, later optimization | Evaluate Terra or Luna against Astra Medium | Change model only after comparable quality is demonstrated on the actual tasks. |

Keep the first comparison simple: lower Astra's effort before changing the model too. A small fixed evaluation packet can cover a known accounting bug, an availability/leakage check, a bounded code change and source-backed synthesis. Use identical inputs, hidden expected findings, no production data mutation, and an independent reviewer. Compare missed material defects, regression results, wall time, actual usage where available and follow-up repair work. Repeat enough to avoid treating a single lucky answer as proof. This is an agent-workflow check, not another trading strategy test. No speed, usage-saving percentage or superiority was measured here, and API prices are not a reliable substitute for this account's Codex usage accounting.

For agents, retain a coordinator plus at most three concurrent bounded workers initially: data/source investigator, implementation owner and independent reviewer. Use short task briefs and named artifacts rather than passing the entire history to every worker. Current full-history forks inherit the parent model/effort; a cheaper label does not make them cheaper. Verify actual settings when introducing role defaults or fresh-context workers. Official custom-agent support allows per-role model and effort, and global subagent defaults, but runtime overrides and the selected client must be checked. [Official subagent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents).

A project-local research configuration and role files would make this reproducible; start with the app's model/effort selector for the immediate choice. Trusted project config and client/session overrides affect what takes effect. Do not edit the global config and assume an already-running task changed. [Official configuration layering](https://learn.chatgpt.com/docs/config-file/config-basic). No configuration change was made during this review.

## Skills and connectors

**Keep and improve the two domain skills.** [Governance](/home/malecada/master_thesis/.agents/skills/crypto-research-governance/SKILL.md) and [provenance](/home/malecada/master_thesis/.agents/skills/crypto-market-data-provenance/SKILL.md) fit the task. Make registry routing explicit for financial experiments, corrections, engineering checks and quote measurements; allow validated signed-quantity/cashflow accounting as well as simple returns. Clarify historical program closure versus a new authorized phase. A small research-cycle skill should call the reusable admission/checkpoint tools, not repeat the approximately 1,800-word launch prompt as more prose.

**Reduce competing workflow instructions.** The installed Superpowers [brainstorming](/home/malecada/.codex/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/brainstorming/SKILL.md) and [using-superpowers](/home/malecada/.codex/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/using-superpowers/SKILL.md) skills contain broad compulsory invocation and fresh-approval rules; these can pull against continuous work already authorized by the user. [Caveman](/home/malecada/.codex/plugins/cache/caveman/caveman/local/skills/caveman/SKILL.md) instructs dropping hedging and progress narration, which risks losing qualifications; it also includes clarity rules intended to preserve substance. Broad whole-codebase-reading workflows work poorly with preserved research history. Higher-priority user/developer instructions govern conflicts, but removing needless ambiguity is useful. Scope or disable those particular skills for the research workflow while retaining targeted debugging, review and verification tools. Do not patch vendor cache files as the durable fix or uninstall entire useful plugins indiscriminately.

This is not a claim that 20 enabled plugins insert all their skill bodies on every turn: Codex normally advertises metadata and loads full instructions when a skill is selected. The concern is overlapping activation and behavior, plus repeated document reads. [Official skill loading](https://learn.chatgpt.com/docs/build-skills). Astra's guidance specifically recommends auditing skills and instruction files because the model responds strongly to their instructions. [Official Astra guidance](https://developers.openai.com/api/docs/guides/latest-model).

**No new connector is needed to begin the preparation phase.** Current tools already support web research, public HTTP access, local code/data, PDFs and Git; the recent 16-request Binance public capture succeeded without a Binance account connector.

| Capability | Recommendation |
|---|---|
| Official/library documentation | Keep OpenAI Docs and the existing Context7 installation; verify Context7 tool availability when it is actually needed. It is enabled locally but not present in this turn's exposed tool catalogue. |
| Papers and research discovery | Existing web/PDF tools and installed research skills suffice initially. A specialist literature connector is optional only if a measured discovery/retrieval limitation appears; papers still need source review. |
| Binance | Defer an account connector until a specific read-only account fee/product/position requirement exists and its fields are verified. Do not assume it resolves missing historical settlement evidence. |
| GitHub | Optional convenience for hosted issue/PR workflows. Git operations already work and `gh` is installed; it is not a prerequisite for local research. |
| Market-data or generic trading assistants | Add only for a named missing field with adequate historical coverage, publication timing, raw export and reproducibility. Current headline data or recommendations are not a substitute for audited inputs. |
| Browser/automation overlap | Review the existing browser, unified-computer-use, Chrome and Playwright capabilities before adding another. Keep the route that actually works for each surface; no removal was performed. |

The available plugin directory/search surface was inspected, but no callable general plugin-catalog search was exposed in this session. Connector observations therefore use the current tool inventory, local enabled configuration and supplied recommended-plugin list; they are not an exhaustive marketplace comparison or a claim that an untested connector lacks a feature.

## Proposed bounded preparation sequence

1. **Safe tests and portable instructions:** classify empirical tests, expose the offline target, fix checker collection, add a current research landing route and version the concise agent instructions/domain skills.
2. **Reproducible runtime and minimal CI:** create the locked research environment, verify imported source, run the safe target and record how to reproduce it. Preserve the original environments.
3. **New-program admission and reusable run lifecycle:** add exposure/budget status and the narrow immutable-run helper using synthetic fixtures. Provide script/data/engine indexes instead of mass moves.
4. **Codex workflow simplification:** choose the research skill set, evaluate Astra High/Medium on the fixed work packet, and only then save verified role/model settings. Use Ultra when a task benefits from substantial parallel work.
5. **Launch the research program:** use the saved launch prompt once the preparation acceptance checks pass. Do not turn preparation into an open-ended framework rewrite.

The completed reviews found practical preparation work, not a need to rebuild the trading system. The corrected financial evidence, frozen runners, old gates and production setup remain untouched. This review neither starts the new research phase nor promises that better tooling will create an economic edge.
