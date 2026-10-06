# Selected pair checkpoint scope — bounded follow-up

Completed matching pairs do not each store or spend a checkpoint. The selected max_total_checkpoints=160 is a per-graph checkpoint-generation ceiling, not a160-completed-pair ceiling. No unconditional finite pair counter was identified in the requested route that forces failure before65,536 successfully completed cells. This establishes compatibility of the counter semantics only; it does not admit the pilot or establish numerical success, capacity or speed.

The parent supplied the completed seven-graph metadata total12,999,004 nodes/415,968,128 node-motif pairs. Those counts and June6 completion are task inputs, not independently reread data. The previous scope report and pins are reused. The short coordination file still describes June6 as active; the later explicit parent task is the current scope instruction. No data/array/active-output bodies or credentials were read and no numerical package was imported or executed. Only this new child report directory was written.

All runtime paths below are under `tradingagents/research/onchain_replication/`. SOURCE_PINS01.json binds the exact inspected installed bodies; overlapping bodies are compared with prior source pins and accepted composition hashes. The actual pair engine reached here is `matching_checkpoint.py`, via `matching_pair.engine`, not a separately named pair_engine.py.

## Actual selected call chain

- `compact_matcher.py:125–147` requires a fresh log, validates max_checkpoints<=pair.max_publications, and initializes matcher.checkpoints=reserved_bytes=0. This matcher is newly constructed for each graph by `compact_mcm.py:286–311`, as authenticated by the prior event-scope report.
- Before a pair, `compact_matcher.py:262–278` checks pair numerical limits, event completion headroom and checkpoint headroom. It tests checkpoints+max_checkpoints<=max_total_checkpoints; this is a prospective check, not an increment. It then emits one log.begin and invokes retention.begin.
- `compact_matcher.py:279–301` calls engine.create, then up to10,000 engine.advance calls in the selected one-checkpoint schedule. When phase becomes done, it calls score_only, closes the engine, emits log.complete, optionally calls retention.complete and returns. The return precedes `_save` at line302.
- Only `_save` increments matcher.checkpoints (`compact_matcher.py:204–216`). In the selected retention route it first calls retention.checkpoint, then increments by1. With max_checkpoints=1, reaching `_save` is followed by CheckpointStop at line303. There is no automatic resume or silent incomplete-score acceptance.
- `matching_pair.py:15` aliases matching_checkpoint as engine. `matching_checkpoint.py:33–37` creates fresh per-pair state; `:62–78` advances annealing/hardening state; `:91–99` calculates a score only for done state; `:54–59` closes it. Durable checkpoint serialization is a separate save function at`:102–118`. The done branch above does not call save. The isolated matching_pair session's separate publications counter (`matching_pair.py:194–207`) is not constructed or used by CompactMatcher; it must not be mistaken for a workflow counter.
- `compact_pair_log.py:47–68,184–195` counts begin/completion as pair events, separately from progress records. `archive_pair_writer.py:111–118` appends those same events and seals completed chunks. Its `_terminal` at`:309–330` seals, verifies and closes; it does not create numerical checkpoints or charge pair publication counters.

Thus65,536 successful pair completions produce131,072 pair-log events, completed_pairs=65,536 and stored checkpoint generations=0. Any selected-schedule pair that reaches its checkpoint prevents this successful-prefix condition by stopping immediately. Millions of successful terminal pairs are compatible with the checkpoint-counter semantics, conditional on all other registered bounds and actual matching success.

## Other finite counters and their scope

| Counter | Increment and scope | Implication for first full batch |
|---|---|---|
| Pair max_publications=1 | Bounds checkpoints per individual pair in CompactMatcher constructor; no shared publications counter on done path. | Does not mean one completed pair per graph/workflow. |
| Matcher max_total_checkpoints=160 and max_total_checkpoint_bytes=62,914,560 | Matcher-local, recreated for each graph; increment only in `_save`. | Successful terminal pairs leave both at zero. |
| Retention max_generations=160/max_stores=160/max_replays=2 | New Controller per graph, initially zero (`stage_retention.py:97–105`). Generation/store reservation occurs only in checkpoint (`:212–232`). | No debit for every ordinary completed pair. |
| Retention inputs/completion controls | mcm_selection chooses only first and last pair (`stage_retention.py:55–72`). begin copies inputs only for those selected members (`:169–183`). complete reserves controls only if a store exists or the pair is selected (`:247–269`). | No65,536-times control charge for a checkpoint-free batch. The first selected input still must satisfy its actual shape/byte bounds. |
| Log max_pairs/max_events | Fresh per-graph log. begin checks started_pairs<max_pairs; every event checks max_events (`compact_pair_log.py:43–68`). Matcher also requires an extra possible progress event before each pair (`compact_matcher.py:263–264`). | Final common bound must cover full graph cells. Existing formula max_pairs=max(cells), max_events=2*max(cells)+160 covers the successful first batch when finalized; chunk_events49,152 rotates files, it is not a total event ceiling. |
| Archive max_chunks/transfer commands/bytes | Writer chunk accounting is per graph; shared dispatch reservations cover the whole workflow, as in prior report. | No checkpoint160 or publication1 debit per completed event/cell. Actual total transport admission remains separately required. |

Retention `_reserve` adds bounded control/cumulative reservations and checks all limits (`stage_retention.py:157–166`). Its prospective before_pair check compares actual generations against the original160 allowance (`:204–211`), without incrementing them. This distinguishes stored checkpoints and selected endpoint evidence from ordinary event-log completions.

Numerical policy checks can reject a particular pair independently of occurrence count: `matching_pair.py:87–98` checks its graph dimensions, checkpoint-size allowance and score buffer; `matching_checkpoint.py:20–25` checks state/ranking limits. The schedule can also stop a difficult pair after its finite calls. No actual local-pair dimensions or numerical outcomes were inspected, so this report neither rules those failures out nor claims they occur before a particular batch cell.

## Exact template limitation

The referenced `full_sources/real-data-pilot-selected-feature-protocol01-2026-10-06/draft07/templates/pair_policy.json` has max_publications1 and total_checkpoint_bytes1,048,576. The same directory's compact_policy.json has max_checkpoints1/max_total_checkpoints160, operations_per_call1,000,000/calls_per_checkpoint10,000, score_chunk_cells65,536 and the retention ceilings above. Its log max_pairs/max_events/max_logical_bytes and workflow reservation remain null: this is an unbound template, not an admitted executable policy. Those nulls are missing preparation inputs, not a hidden160-pair cap.

No concrete pair-count/cardinality contradiction was found and no cap change is proposed. The existing method and checkpoint/replay protocol remain intact. Final seven-count policy binding and exact registration remain Root's separate preparation responsibility; this source-only finding grants no execution authority.
