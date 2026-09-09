# The Goal-Directed Research Loop — a reusable playbook

Distilled from the Prediction Lab's July2026 research process. Its initial
positive strategy claim was invalidated in August2026; the September9 audit
identified further measurement and provenance defects. The process is retained
as a workflow, not as proof that its former results were trustworthy.

Before using this guide, read `AUDIT_SYSTEM_2026-09-09.md` and the append-only
correction register in `TradingAgents-audit-fixes/docs/audit/corrections.jsonl`.
No validated strategy currently exists. Original gates remain immutable; a
repaired calculation requires a separately committed correction registration.
The current correction checkout provides executable accounting, explicit
forecast fallback coverage, strict availability checks, and preflight provenance.

A negative gate means that the specified adoption claim failed. It does not
establish absence of every useful effect. Report effect uncertainty and power,
keep failed hypotheses in multiplicity denominators, account for model
selection and serial dependence, and distinguish a fixed oracle heuristic from
an objective upper bound. Unrecoverable historical data vintages must remain
qualified rather than being assigned a convenient publication lag.

---

## 1. The core idea

Three ingredients, and all three matter:

1. **A goal stated as a falsifiable claim with pre-agreed success
   criteria** — not "improve the model" but "produce a model that beats
   STRONG baseline X by ≥ floor Y at significance Z on data the search
   never saw."
2. **A file-based state machine the loop can re-enter** — the agent's
   context dies constantly (compaction, restarts); the program must live
   on disk, not in the conversation.
3. **Discipline enforced by artifacts, not intentions** — criteria frozen
   in files *before* results exist; holdout blocked by code; ledger
   append-only. The agent (and you) cannot cheat later without the diff
   showing it.

The loop then runs: pick next backlog item → execute → verify
forensically → record → commit → repeat. Human enters only at declared
decision gates.

## 2. Kickoff — what to write before any experiment

Create a dedicated branch/worktree and a docs folder with five files:

| File | Role |
|---|---|
| `CHARTER.md` (or a spec) | The goal, assumptions (numbered A1..An), success criteria (numbered U1..Un), the evaluation protocol (§5-style: baselines, losses, statistical tests, effect floors, multiplicity handling), the tier ladder, and the holdout definition. This is the constitution — everything later appeals to it. |
| `BACKLOG.md` | Ordered checkbox items, one per loop iteration. Checkbox flips ONLY after: tests green + forensics done + ledger/report updated + committed. Split items rather than overrun. |
| `STATE.md` | Current phase, last completed item, next action, blockers, standing rules, an infra-failure counter ("3 consecutive → stop and surface"). The first thing a fresh context reads. |
| `RALPH_PROMPT.md` | The exact re-entry instructions: read STATE, take ONE backlog item, execute per charter, update STATE/BACKLOG, commit. Nothing else. |
| `RESEARCH.md` | Literature notes / prior findings that inform choices (so the loop doesn't re-derive them). |

Rules that earn their keep:

- **Write-fence**: enumerate the only paths the loop may touch (its
  package, its tests, its data namespace, its docs, an append-only
  findings file). Everything else read-only.
- **Separate memory section** for the program in your persistent memory
  index, updated only at milestones.
- **Human decision gates declared upfront** (e.g. "GPU spend requires
  stop-and-ask"). The loop must surface these, never decide them.

## 3. Required discipline and independently verified enforcement

### Pre-registration before results, always
A machine-readable `gates.json` holds one entry per experiment family,
frozen BEFORE the first result of that family exists: cells/configs,
baselines, losses, effect floors, windows, refit cadences, seeds,
multiplicity plan, stop rules. Registration scripts refuse to overwrite
existing keys. Amendments are allowed only pre-result and must be
declared in-file (e.g. "TabPFN dropped: license blocker — revivable via
TOKEN").

### Append-only trial ledger
Every evaluated config = one JSONL row: timestamp, experiment key, cell,
model, config + config-hash, git commit, window, metrics. The ledger is
the honest denominator for multiplicity later, and the recovery map if a
session dies.

### Sealed holdout with code enforcement
- Split data/test-cases into DEV (search happens here) and HOLDOUT
  (nothing touches it — loaders clip at dev end, and an
  `assert_dev_window()` raises if an evaluation reaches past it unless
  `allow_holdout=True` is passed by the one registered spend path).
- **One-shot spend**: one evaluation per frozen champion, PASS/FAIL per
  pre-registered criteria (typical: beats baseline at p<0.05 AND effect ≥
  0.5× dev effect AND same sign), no re-tuning, no second look. The spend
  script refuses to run if the verdicts file exists.
- After the spend, the holdout is DEAD for new claims. New claims need
  new data (register the next cycle immediately with a fresh sealed
  window and let it accrue).

### Stop rules
Written into every registration: what kills a candidate (failing its dev
gate = dead this cycle; revival requires a new registered cycle on fresh
data), and what may not be added after first results. When a frozen
do-no-harm guard kills a candidate whose headline metric looked great —
let it die. That happened here (S2: tracking-error claim p≈0, SR guard
failed → dead) and the credibility of everything else rests on it.

## 4. The execution ladder

- **Tiers, simplest first**: naive baselines → classical → ML → (deep /
  foundation) → combinations. Each tier fights the incumbent champion,
  not the weakest baseline. Most tiers will add nothing — that is the
  map, not a failure.
- **Strong baselines or nothing**: seasonal-naive, persistence, base-rate,
  domain workhorses (HAR for vol). A win over a weak baseline is not a
  result.
- **Effect floors**, not just significance: with big n everything is
  significant; register a minimum effect size that would matter.
- **Breadth then depth**: enumerate the full matrix (targets × horizons ×
  subjects) cheaply first; spend depth only where tier-1 showed life.
- **Champion freeze before the spend**: a registered selection procedure
  (MCS / best-of-set rule) picks ONE champion per cell; only champions
  get holdout evaluations.

## 5. Verification — every positive gets attacked

Standing rule: no PASS without a forensic kill-test. The ones that caught
real bugs here:

- **Leaky-canary probe** (run once at setup): a deliberately cheating
  model (trains on future) must win big — proves the harness *can* detect
  leakage. If the canary doesn't win, the harness is broken.
- **Planted-alpha recovery test** on every new engine: inject known
  signal, assert the pipeline finds it.
- **Permute/shuffle nulls, multi-seed (≥5)**: destroy the causal channel,
  re-run, expect collapse. Critical subtlety learned twice: **nulls are
  only fair between same-collapse models** — under a shuffled target, a
  regression collapses to the mean while a naive-lag predicts a random
  draw, manufacturing a fake +30% "effect". Pair the champion with a
  same-collapse reference (e.g. historical mean) for the null.
- **Dual-family placebos for strategies**: two *independent* destruction
  mechanisms (circular time-shift AND cross-sectional shuffle); the real
  result must beat both distributions.
- **Multiplicity accounting**: BH-FDR across a battery; Deflated Sharpe
  at the honest trial count (from the ledger, not memory); mind the units
  (a DSR bug here came from mixing hourly and daily Sharpe
  periodizations).
- **Sub-period stability**: any claim must hold in most sub-windows, not
  live in one regime.
- **Verify negatives too**: a zero-result can be a silent bug (empty
  join, all-NaN mask). Probe with mutation tests and honest denominators
  before recording "no effect".
- **Convention swap is two-sided and retroactive** (rail 15, 2026-09-02):
  every PnL claim — positive *or negative* — is re-priced with the return
  convention swapped (Σw·Δlog ↔ Σw·expm1(Δlog)). The ½σ² Itô term is
  25–100 %/yr at crypto volatilities: log booking flatters short legs and
  starves long legs, so a long-book negative can be as much an artifact as
  a short-book positive. Verdicts may stand while mechanism narratives die
  (the July xsect cycles: benchmarks moved +0.8–0.9 SR). The kill-test is
  mandatory forensics, not optional, and applies to engines audited earlier
  under the opposite sign.

## 6. Loop mechanics (agent-operational)

- **One backlog item per iteration.** The stop-hook re-feeds the same
  prompt; STATE.md carries continuity. Never let the loop free-lance
  beyond the item.
- **Long jobs**: launch in background with logs on disk; arm a waiter on
  the completion condition AND a monitor on failure signatures; between
  events, an iteration that just checks progress and exits is correct
  behavior — don't fill idle iterations with unregistered work.
- **Idempotent everything**: caches keyed canonically (never by run
  date), tail-append stores, journal scripts that skip existing rows.
  Recovery after a crash = re-run; the disk is the source of truth.
- **Process hygiene** (learned the hard way): `pgrep` patterns
  self-match — use the `[b]racket` trick; killing a task can orphan its
  children — verify with `pgrep -af` and re-kill; two batteries racing on
  shared files corrupt both.
- **Infra-failure counter** in STATE: 3 consecutive infra failures →
  stop looping, surface to the human.
- **Commit per completed item** with a message stating the finding, not
  just the change. Findings additionally append to a persistent
  `FINDINGS.md` (numbered sections) — the conversation is disposable, the
  findings file is not.
- **End the loop deliberately**: when the backlog is empty and remaining
  work is calendar-blocked or needs human decisions — cancel the loop and
  hand back a summary. Don't let it idle-spin.

## 7. Reporting standard

Every phase produces a short report (map/table + verdicts + method notes
+ artifact paths). The final deliverable is a **map**, not a highlight
reel: what is predictable/solvable, what is not, at what tier, with what
confidence — negatives are first-class results. Language discipline:
"suggestive, not confirmed" for anything that hasn't cleared its
registered gate; failed gates are reported as FAIL even when the
underlying effect is real but attenuated.

## 8. Transfer checklist (start a new project in ~1 hour)

1. Write the charter: goal as falsifiable claim, U-criteria, protocol,
   tier ladder, holdout split, human gates, write-fence.
2. Create BACKLOG / STATE / RALPH_PROMPT / RESEARCH; branch or worktree.
3. Build the eval core FIRST, test-driven, with reference-validated
   statistics; add the leaky-canary and planted-signal probes.
4. Register experiment family 1 in gates.json; init the ledger.
5. Start the loop (Ralph or equivalent) with "one item per iteration".
6. At each phase end: report + findings section + memory milestone +
   commit.
7. Champion freeze → one-shot holdout spend (code-enforced) → forensics
   on every pass → final map.
8. Register the NEXT cycle (upgrades/confirmations) against fresh data
   immediately, then stop.

## 9. Failure modes this system is designed against

| Failure mode | Countermeasure |
|---|---|
| Criteria drift after seeing results | gates.json frozen pre-result; amendments only pre-result, in-file |
| Holdout peeking / repeated testing | code-enforced seal + one-shot spend rule + verdicts-file lock |
| Multiplicity laundering ("we only tried a few") | append-only ledger = honest trial count |
| Plausible-but-fake positives | mandatory forensic kill-tests, multi-seed, dual-family placebos |
| Unfair nulls flattering the model | same-collapse pairing rule |
| Weak-baseline wins | strong-baseline + effect-floor requirement |
| Survivor-bias in the narrative | negatives are registered, reported, and kept in the findings file |
| Context loss / crashes | disk state machine, idempotent jobs, ledger as recovery map |
| Agent overreach | write-fence, declared human gates, one-item iterations, infra counter |
| Quiet scope creep on wins | stop rules: improvements = new registered cycle on fresh data |
