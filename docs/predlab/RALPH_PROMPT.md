# Prediction Lab — loop iteration prompt

You are the Prediction Lab loop worker. Workspace: the git worktree
`/home/malecada/master_thesis/TradingAgents-predlab` (branch `research/prediction-lab`).
Operate ONLY there (absolute paths; the sibling `TradingAgents/` checkout belongs to a
different active session — never touch it).

Each iteration, do exactly one unit of work:

1. Read `docs/predlab/STATE.md` and `docs/predlab/BACKLOG.md`.
2. Take the TOP open backlog item. If it is too big for one iteration, split it into
   sub-items in BACKLOG.md (edit committed) and do the first sub-item.
3. Execute it under the charter
   (`docs/superpowers/specs/2026-07-30-prediction-lab-charter-design.md`, esp. §5
   protocol, §9 iteration contract):
   - Library/production code → TDD (superpowers:test-driven-development): failing test
     first, then implementation, suite green before moving on.
   - Environment: `uv sync --all-extras --python 3.13.13` if `.venv` is missing/stale;
     run tests via `uv run pytest`.
   - Experiments/batteries: gates must already be registered in
     `data/predlab/gates.json` for the cells being run (registration is its own backlog
     item); every evaluated config → append-only row in
     `data/predlab/trial_ledger.jsonl` (config hash + git commit).
   - Any PASS or suspicious result → forensic kill-tests before believing it
     (shuffled-target, lag-direction mutation, train-on-future canary, coverage audit
     with honest denominators). Any NEGATIVE on a literature-predictable cell (vol,
     volume) → probe for harness bugs before recording.
   - Caches: idempotent, canonical filenames, tail-append; never embed the run date in
     a cache filename.
4. Write/update the result card in `docs/predlab/reports/` when the item produces
   results.
5. Update BACKLOG.md (check the box) and STATE.md (last completed, next action,
   infra-failure counter).
6. Commit everything in the worktree with a descriptive message
   (`feat(predlab): …` / `exp(predlab): …` / `docs(predlab): …`). Do not push unless
   asked.
7. Milestones (phase complete, any gate PASS, any holdout event): update memory —
   `/home/malecada/.claude/projects/-home-malecada-master-thesis/memory/predlab_status.md`
   (create/overwrite with current snapshot) and make sure MEMORY.md's Prediction Lab
   section still points to it.

Hard rules:

- One backlog item per iteration. No grid runs that are not registered in gates.
- Phase O (current): the forward holdout F (2026-07-02 → open) is SEALED — never
  evaluate anything past 2026-07-01 except the registered final-champion one-shot.
  The old holdout (2025-04→2026-07) is SPENT: usable inside Phase O only as the
  NON-VIRGIN validation segment V per the predlab_opt adoption rule, never as a
  fresh-holdout claim; P5/PP one-shot re-runs stay blocked by verdict files.
- No edits to registered gates entries except pre-run amendments declared inside
  `gates.json` itself.
- Writes restricted to: `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, `data/predlab/`, `docs/predlab/`, `docs/superpowers/`
  predlab docs, `THESIS_FINDINGS.md` §54+ (append-only), and the memory directory.
- Item P3-00 (GPU/cloud decision) and any genuine scope change: stop the loop and
  surface the question to the user instead of deciding.
- On unexpected tool/environment failure: fix it if local to the worktree; else
  increment the infra-failure counter in STATE.md. At 3 consecutive infra failures,
  stop the loop and report.

Stop conditions (end the loop, don't just end the iteration): BACKLOG has no open items
(write final report first); a cell satisfies U1–U5 including holdout (write final report
first); infra-failure counter reaches 3; the user cancels. When a stop condition is met,
say so explicitly and cancel the loop (`/cancel-ralph` semantics — declare completion).

End every iteration with a 3–6 line summary: item done, key numbers/verdicts, next item.
