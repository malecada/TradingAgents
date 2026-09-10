# Research Codex setup

Use **Astra High for coordination and review, Medium for bounded workers** as a
provisional starting policy. The [paired synthetic comparison](../readiness-2026-09-10/agent-evaluation/REVIEW.md)
found no material correctness difference in four responses. All four proposed
implementations passed 12 independent functional checks. Minor omissions occurred
at both efforts; total latency, per-agent usage and savings were not measured.
This does not establish equivalence for difficult research or justify a model
change. Extra High/Max remains available for a specific unresolved accounting or
inference question; Ultra fits substantial independent parallel investigations.

## Saved configuration and actual activation

- Tracked `.codex/config.toml` supplies Astra High, Astra Medium worker defaults,
  and a limit of three concurrent workers in addition to the coordinator.
- Three tracked `.codex/agents/*.toml` files define an investigator, implementation
  worker and independent reviewer with explicit model/effort and bounded duties.
- The non-Git parent workspace has the same configuration and a relative link to
  those role files. Its default High/Medium settings were verified through a fresh
  local Codex `config/read` request.
- A selectable personal `crypto-research.config.toml` profile carries the same
  settings. This is useful when opening this worktree directly: Codex 0.153.4
  resolves its trust to the main `TradingAgents` checkout, which is not currently
  marked trusted, so its project configuration is ignored. Trust settings were
  not changed. The named profile is accepted by CLI runtime commands and its
  instruction filtering was verified by rendering a prompt without a model call.
- The personal base model remains Astra Ultra. A running task and an explicit
  app model-picker override can retain their selected effort. Start the next
  desktop task at the workspace root and select **Astra High** if the picker
  retains Ultra. Saving a file does not retroactively change this task.

For a direct CLI start in this checkout:

```bash
codex --profile crypto-research -C /home/malecada/master_thesis/TradingAgents-audit-fixes
```

On a new computer or after plugin updates, render/recreate the scoped settings:

```bash
.venv/bin/python scripts/configure_research_codex.py
.venv/bin/python scripts/configure_research_codex.py --apply --profile
```

Add `--workspace-root` only in the intended parent workspace. The renderer
preserves unmanaged existing configs and never changes trust, permissions,
personal base config or vendor caches. It resolves locally installed skill
paths; committed paths describe this machine and should be regenerated elsewhere.
Fresh clones still need the normal trusted-project choice before Codex uses
project configuration. Custom role files are installed/schema-checked; no
existing task was silently switched to one of them.

## Skills and connectors

Three tracked domain skills are enabled: governance, data provenance and research
cycle. Workspace skill links resolve to those same tracked sources. Their syntax
validators passed. Targeted debugging, review and verification tools remain usable.

Four overlapping workflows were disabled: `superpowers:using-superpowers`,
`superpowers:brainstorming`, `caveman:caveman`, and `claude-mem:learn-codebase`.
In this client, project exclusions alone did not filter the rendered catalogue.
The named profile did; the four exclusions were therefore also applied through
Codex's `skills/config/write` API to personal settings for desktop use. **These
four personal exclusions apply across projects.** A fresh skill inventory verifies
all four disabled and all three domain skills enabled. No entire plugin was
removed: the 20 prior plugin entries remain, and no connector was installed.

To reverse the personal exclusions, enable those four skills in Codex or set
their matching personal `skills.config` entries to `enabled = true`, preserving
unrelated configuration. The research profile's exclusions remain separately
scoped. Original root instructions/skills are preserved in the local hashed
backup documented in the data catalogue.

Existing public HTTP, web/PDF, local code/data and Git capabilities are sufficient
for the next phase. Reconsider a connector only for a named missing field or
workflow. Context7 is installed; callable availability should be checked when it
is needed. This setup does not establish exchange-account eligibility or fill
missing historical settlement data.

Configuration layering and effort guidance follow the official
[configuration documentation](https://learn.chatgpt.com/docs/config-file/config-basic),
[subagent schema](https://learn.chatgpt.com/docs/agent-configuration/subagents), and
[model guidance](https://learn.chatgpt.com/docs/models). The observed activation
limits above come from the local client, not assumptions based on those pages.
Allowlisted receipts are retained under `docs/readiness-2026-09-10/`; no credential
values or full personal configuration were saved in the repository.
