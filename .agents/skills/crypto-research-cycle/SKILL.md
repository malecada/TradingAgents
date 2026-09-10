---
name: crypto-research-cycle
description: Admit, resume and close registered crypto research cycles using this repository's durable state and run lifecycle. Use during authorized empirical research, not ordinary source edits or as authorization to launch a paused program.
---

# Research cycle and continuation

Read [current state](../../../docs/research/STATE.md), the relevant program
charter and its highest-priority eligible question. Resolve authorization,
experiment identity, stage, parent family, remaining budget, input hashes and
sample exposure before execution. The [governance skill](../crypto-research-governance/SKILL.md)
defines the claim; this skill handles durable run routing.

## Use the actual lifecycle

Read [the API/schema contract](../../../docs/research/README.md) for the new
program's committed registration and exact call arguments. From the repo root,
the admission-only command is:

```bash
.venv/bin/python -m tradingagents.research check --root . --registration <committed-json> --experiment <id> --source <full-HEAD>
```

This checks metadata/source/history; it neither opens empirical inputs nor
starts a run. Use `ResearchRun` for execution only within the authorized and
registered scope. It writes new `research_runs/<experiment-id>/` receipts;
historical dated runners and their financial ledgers remain separate.

Check existing status before any start. A completed or failed attempt is not
rerun under the same identity. A partial run requires the contract's permitted
recovery/closure procedure; do not delete its receipts, invent a fresh ID to
reset a budget, or repeat acquisition because the conversation was compacted.
Keep each mutable output under one owner. A synthetic `examples` demonstration
is an engineering check, not an empirical cycle.

## Decide, record, continue

After every bounded result, reconcile all attempted cells and independent
forensics. Record the finding, uncertainty, weakened competing explanations,
effect on other families and best justified next action. Update the program
map/backlog and current state with exact artifact/source references. Preserve
failed and unavailable cases; a terminal run receipt is not a passing verdict.

Follow an evidenced next question with a new registration, advance a frozen
candidate only when its gates permit, or close/defer that particular question.
Continue independent eligible work within the user's authorized program;
ordinary progress does not require another “continue.” A failed configuration
is not automatically family exhaustion, and cosmetic variants do not establish
breadth. Family budgets and inspected windows remain cumulative.

Before ending or checkpointing, retain results/reviews, record the exact next
action and any running job's safe status-check/resumption contract, and back up
reviewed branch changes as authorized. Do not create background jobs implicitly.
Declare exhaustion only for the documented feasible map after independent
coverage review. Runtime/context limits mean incomplete but resumable, not
exhausted. Production, paid resources and provider/account actions require their
separate authority; the lifecycle supplies none.
