# Charter C3-P — LLM pairwise duels on numeric PIT cards (`llm_c3p_pair_xs`)

**Registered:** 2026-08-17 (gates file `data/llm_pair_xs/gates.json`, frozen
pre-result). **Parent:** revival of dead charter C3
(`docs/superpowers/specs/2026-08-14-llm-c3-rank-xs-charter.md`, THESIS §64),
per the Aug-14 leads note. C3 died at P0: in-batch presentation shuffle
Spearman 0.633–0.876 (< 0.8 gate) with rerun Spearman 0.936–0.985 — the
list-ranking score was a prompt-position artifact, not sampling noise.
**Fix under test:** pairwise comparison with both presentation orders by
construction, so position bias cancels in aggregation instead of being
assumed away. **Discipline:** probe ladder, STOP-on-fail; any STOP = dead
this cycle; house rails per `master_thesis/RESEARCH_LOOP_GUIDE.md`.

## 1. Hypothesis

An LLM judging sampled pairwise duels between anonymized numeric PIT cards
("which asset has the higher expected 5-day forward return?"), aggregated
per week by Bradley-Terry, produces a score whose residual — after
neutralizing to vol-rank, 4w momentum, and size — has positive IC vs 5d
forward returns AND beats a GBDT twin trained on identical inputs. Null:
residual IC ≈ 0 or ≤ GBDT twin.

Confirmatory/exploratory declaration (methodology rail 9): the P2 primary
gate is a single frozen hypothesis registered before any result of this
family exists → confirmatory n_trials = 1; family-scope (≤10 ledgered
configs) and cumulative-ledger denominators are reported as declared
sensitivities, not gates.

## 2. Data and cards (inherited frozen from C3)

Panel `data/llm_rank_xs/cards.parquet` verbatim (287 Fridays × top-200 by
30d median dollar volume, monthly PIT refresh, 799-sym survivorship-safe
store; 15 card fields, t-1 discipline). No field additions or removals.
Anonymization: per-week random tags `ASSET_NNN`, 3-significant-digit
rounding. Named cards exist ONLY for the P1 memorization probe.

## 3. Duel construction (frozen)

- **Pair sampling:** per week, k = 10 seeded permutation-pairing rounds
  (each round: seeded permutation of the week's symbols, consecutive
  disjoint pairs; odd count → last symbol skips that round). Multigraph:
  repeated pairs allowed and keep their multiplicity (disclosed).
- **Order debiasing by construction:** every sampled pair is issued as TWO
  duel instances, (A,B) and (B,A), in disjoint prompts.
- **Prompting:** 20 duel instances per prompt (seeded shuffle then
  sequential chunking; the two orders of a pair are chunked from separate
  shuffled lists → never share a prompt). Model `gpt-5.4-mini`,
  temperature 0, JSON output `{"winners": [tag, ...]}`, one winner per
  duel in order, disk-cached. Malformed/length-mismatched responses mark
  their instances unresolved; weekly resolution rate < 0.95 = infra flag
  (fix plumbing, not prompt).
- **Aggregation:** each resolved instance = 1 win for its winner.
  Weekly score = log Bradley-Terry strength, MM algorithm, 200 iterations,
  pseudo-count prior α = 0.5 win+loss vs a fixed unit-strength virtual
  opponent, geometric-mean normalized. Deciles from scores.
- **No prompt, k, batch-size, α, or field changes after P0 runs.**

## 4. Windows

Dev: 2021-01-01 → 2025-03-31 (222 Fridays). Holdout: 2025-04-01 →
2026-07-01, SEALED, one-shot only if P3 passes. Disclosure: the holdout
window is shared with the dead C3 family, which never read it — it is
virgin for LLM-XS claims; predlab book claims on overlapping dates are a
separate family (disclosed, as in C3).

## 5. Probe ladder (STOP-on-fail, in order)

- **P0 order-swap kill-probe + stability (~$3–8):** 8 seeded dev weeks
  (fresh seed 20260817; base run = both orders of every pair, so the swap
  probe is computed from the base run itself).
  - **P0b order-swap (the C3 killer, evaluated first):** pooled
    swap-consistency (same winner under (A,B) and (B,A)) ≥ 0.60 AND
    per-week ≥ 0.55 in ≥ 6/8 weeks AND pooled slot-1 pick rate in
    [0.35, 0.65]. Pure position-picking → consistency ≈ 0; pure noise →
    ≈ 0.5. STOP if failed.
  - **P0a determinism:** 3-week seeded subset, cache-bypassed identical
    rerun → instance-verdict agreement ≥ 0.90 AND weekly BT-score
    Spearman ≥ 0.90.
  - **P0c slot/grouping invariance:** 3-week seeded subset (disjoint
    draw), same instances re-shuffled + re-chunked into different prompts
    → instance-verdict agreement ≥ 0.80 AND weekly BT-score Spearman
    ≥ 0.80.
  - **P0d cost checkpoint (infra, not a result gate):** extrapolate
    P1+P2 spend from measured P0 tokens; if projected total > cap,
    surface to user BEFORE P2. Registered de-scope option, cost-driven
    only and blind to results: thin dev cadence to every 2nd Friday.
- **P1 anonymization kill-probe:** 26-week seeded dev subset run with
  named cards (identical pairs/orders). If named weekly Spearman IC (BT
  score vs 5d forward return) exceeds anonymous IC by > 50% relative →
  memorization STOP. Primary evaluation is ALWAYS anonymous.
- **P2 incremental IC + GBDT twin (compute + LLM spend):** full anonymous
  dev run. Weekly cross-sectional residualization of scores on {vol rank,
  4w momentum, size rank}; residual IC vs 5d forward returns (primary;
  10d, 21d reported). Gates: (a) mean residual IC > 0 with Newey-West
  t ≥ 2.0; (b) LightGBM twin trained walk-forward on identical card
  features with identical targets — LLM residual IC ≥ GBDT residual IC.
  STOP on either.
- **P3 decile LS dev gates (compute):** §43 XS harness verbatim, 5bp +
  funding: decile LS net SR ≥ 0.8; dual-family placebo p < 0.05; DSR
  > 0.5 at declared n (confirmatory n = 1 primary; family ≤ 10 and
  cumulative reported); ≥ 3/4 sub-periods non-negative.

## 6. Multiplicity, ledger, spend, stop rules

Ledger `data/llm_pair_xs/trial_ledger.jsonl`, append-only, ≤ 10 configs
(P0 ≤ 3, P1 ≤ 2, P2 ≤ 3 incl. GBDT twin, P3 ≤ 2). LLM spend cap **$150**
total this charter. No prompt/sampling/field/frequency changes after P0
runs; no holdout reads before a registered one-shot; any STOP = dead this
cycle, revival needs a new registered cycle. Commit producing code before
logging trials (rail 14).
