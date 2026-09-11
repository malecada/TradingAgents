# Research starting point

**Start with [current state](research/STATE.md). Zero strategies are validated.**
The completed preparation improves reproducibility and research admission.
The user launched the strategy-search phase on September 11, 2026; the active
program is linked from current state.

## Working sequence

1. Read [operative instructions](../AGENTS.md) and current state. Inspect the
   actual branch and working tree before editing; the directory name does not
   guarantee the active branch.
2. Read the [preparation result](readiness-2026-09-10/IMPLEMENTATION.md) and
   [Codex setup](research/CODEX_SETUP.md), then use the pinned environment and
   offline command below. The earlier review records the accepted scope.
3. For a specific question, consult the [evidence/supersession index](research/EVIDENCE_INDEX.md),
   [script map](research/SCRIPT_INDEX.md), [engine contracts](research/ENGINE_INDEX.md)
   and [data/retention catalogue](research/DATA_CATALOG.md). Avoid loading every
   historical report or source file.
4. Research can start under the user's separate launch instruction using the
   [saved phase prompt](PROMPT_STRATEGY_RESEARCH_PHASE_2026-09-10.md). That prompt
   calls for repeated learning, not one attempt. The historical closure and
   spent samples remain preserved when a new program is authorized.

## Environment and verification

The research interpreter is Python **3.13.13**. Use the repository lockfile and
local `.venv`; keep original sibling environments intact. Runtime installation
and checks are part of the bounded preparation, not dependency upgrades.

```bash
uv sync --locked --all-extras --python 3.13.13
.venv/bin/python -B scripts/research_runtime.py --check
.venv/bin/python -B scripts/verify_offline.py
```

For the reviewed inventory and limitations, read [offline testing](TESTING.md).
The new-run interface is documented in [research lifecycle](research/README.md).
The broad legacy `pytest tests/` command and experiment mains should not
substitute for the named offline target. Some old tests can become empirical
writers when historical files are restored.

The original LLM CLI, Docker execution and provider-key setup remain documented
in the [README's framework reference](../README.md#framework-reference).
They are not prerequisites for offline quantitative engineering.

## Evidence and portability

The consolidated source contains `tradingagents/predlab` and `tradingagents/xsect`.
Their coexistence does not validate a strategy. Historical `THESIS_FINDINGS.md`,
gate files and ledgers contain both earlier claims and subsequent corrections;
use the latest applicable evidence, not an isolated positive headline.

A clean clone contains tracked source and retained evidence, but does not
necessarily contain sibling raw stores, private workspace documents or their
backups. The data catalogue records those distinctions. Historical pinned
paths/hashes remain unchanged; a new location requires a declared mapping for a
new run. Never silently refetch or replace missing research inputs.
