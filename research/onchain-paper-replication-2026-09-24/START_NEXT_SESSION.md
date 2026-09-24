# Start the paper-replication work in a separate session

Status: handoff prepared September 24, 2026. **No implementation, new capture,
model fit, research claim, recurring monitor or separate task has been started.**

## Prompt to paste into the execution session

> Implement the paper-faithful transaction-graph replication plan at
> `/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/superpowers/plans/2026-09-24-onchain-paper-replication.md`.
> Read its linked `REPLICATION_SPEC.md` and the applicable repository instructions
> first. The objective is to implement and evaluate what Çelik and Sefer describe
> as closely as available evidence permits, including the full architecture and
> the planned broader paper coverage. The first ETH experiment is an intermediate
> milestone, not completion of the task.
>
> Begin with Task 1: audit the paper and public author artifacts, resolve or
> explicitly document every missing design choice, and freeze the concrete
> protocol/configuration before empirical outcomes. Continue through the plan's
> implementation, tests, resource pilot, admitted experiments and independent
> verification. Prepare the necessary new registrations and cumulative budget
> amendments; the previous 17/17 allowance is consumed. Preserve all old results,
> source stores, failed attempts and exposed samples. Do not rerun old jobs.
>
> Use C01–C18 as the completion criteria and report the separate implementation,
> paper-scope and numerical-agreement outcomes. Do not substitute fixed temporal
> motif summaries or a tree model for the published neural architecture. Do not
> skip the architecture because the earlier screen or a price baseline is
> negative, and do not tune against test results to reach the published accuracy.
> Every material assumption/deviation needs an evidence trail.
>
> Proceed with ordinary reversible implementation decisions and preparation
> without repeated permission questions. Register and independently review each
> empirical stage before running it. Author/provider contact, paid data/compute,
> trading/deployment and resources outside available capacity require a concrete
> separately authorized action. If a dependency blocks one scope, continue
> independent work and report the specific unresolved requirement; never silently
> reduce scope or label a partial result fully complete.
>
> Keep `research/onchain-paper-replication-2026-09-24/STATE.md` current at durable
> checkpoints, with exact evidence references and the next safe action. Treat
> resource interruptions as recoverable work with preserved lineage, not a reason
> to duplicate an active process or restart a terminal claim.

Pasting this prompt is the later execution instruction. Its presence in a saved
file does not activate it in this planning session. No specific execution agent
layout or cloud resource is assumed.

## First-session orientation

1. Work in `/home/malecada/master_thesis/TradingAgents-audit-fixes`. Read its
   `AGENTS.md`, `docs/RESEARCH_START.md`, and the current study state below; inspect
   actual branch/status. The parent workspace is not a Git repository.
2. Read the [specification](REPLICATION_SPEC.md) and
   [13-task implementation plan](../../docs/superpowers/plans/2026-09-24-onchain-paper-replication.md).
   Apply the relevant local skills. No copied historical launch command is a
   current instruction.
3. Inspect the [closed previous study](../onchain-graph-2026-09-16/STATE.md),
   [negative screen](../onchain-graph-2026-09-16/comparison/evaluation-20260924/RESULT.md),
   [raw/evidence preservation](../onchain-graph-2026-09-16/fullpanel_resume2/CLOSURE.md),
   and [admission mechanism](../../docs/research/README.md). Preserve them unchanged.
4. Read the [publisher article](https://link.springer.com/article/10.1007/s10614-025-10940-1)
   and inspect the [author repository lead](https://github.com/nebipeker/Analyzing-Transaction-Graphs-for-Price-Prediction-of-Bitcoin).
   The latter is not yet confirmed to contain the published implementation.
5. Produce Task 1's artifact/configuration audit first. Its acceptance gate is
   explicit executable choices with evidence/assumption labels, not model output.

## Critical context that must survive the handoff

- The previous model was LightGBM using fixed daily temporal-motif summaries.
  Its negative screen does not test the requested architecture. A separate
  paper-replication objective is allowed without rewriting that old result.
- Existing ETH raw history is valuable, but required attributes, weekly
  boundaries and precise transfer semantics need fresh source admission.
  Stored transfer values are double precision, not exact wei.
- Prior reconstruction admitted 1,094 feature days from 1,096 source days and
  checked 1,221,389,903 distinct transaction identities. Do not redo that closed
  computation; new graph transforms receive new identities and output paths.
- The original data source vintage and historical publication are uncertain.
  Existing 2022–2024 outcomes are exposed; they are not a fresh holdout.
- The new study covers a full model, comparators, both assets and the broader
  paper experiments. It distinguishes M1 software, M2 initial ETH, M3 main study,
  and M4 complete paper scope. Exact reproduction depends on recovering original
  data/configurations; independent assumptions remain visible.
- Full raw-data off-device backup remains unverified. The Data partition is on
  the same physical NVMe as the workspace. A manifest is not a backup.
- No old monitor needs restarting. A new recurring monitor is a separate choice,
  not a prerequisite for finite guarded jobs and checkpointing.
- Resource compatibility and duration have not been benchmarked for this model.
  Do not assume a previous 6/8 GiB feature job proves neural-pipeline feasibility.

