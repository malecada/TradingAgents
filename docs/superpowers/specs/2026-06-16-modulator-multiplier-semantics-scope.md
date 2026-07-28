# Scope — Modulator multiplier semantics (Fix 2)

Date: 2026-06-16
Status: IMPLEMENTED (v1/v2 flag, default v1); A/B QUEUED (ETH 1-yr, runs after prod gens clear)
Branch context: feature/adhoc-prediction-runner (defect lives in hybrid stack, shared with hybrid-modulator)

## Implementation note (2026-06-16)

Option 1 + flag shipped to BOTH repos:
- `TradingAgents` (feature/adhoc-prediction-runner) and `TradingAgents-research`
  (where the v5 hybrid §23.9 stack + running prod gens live).
- `agents/modulator.py`: `_SYS_V1` (frozen, byte-identical to old prompt) /
  `_SYS_V2` (realigned); `_build_prompt(..., prompt_version=)`; node reads
  `state.config["modulator_prompt_version"]`.
- `default_config.py`: `modulator_prompt_version: "v1"` (default).
- `scripts/generate_hybrid_signals.py`: `--prompt-version {v1,v2}`.
- Guard test (TradingAgents): `tests/test_modulator_prompt_version.py` (5 pass).
- Verified research v1 == old hardcoded prompt → the running prod run
  `data/hybrid_signals_v5_eth_prod3_1y` is a VALID v1 arm (reused, not regenerated).

## A/B execution

Detached launcher `TradingAgents-research/scripts/run_modprompt_ab.sh`
(setsid, survives session). Waits for the in-flight prod gens to clear (avoids
OpenAI 429 contention), then generates only the v2 arm
(`data/hybrid_signals_v5_eth_prod3_1y_v2`, ETH, same window/preset/analysts as
prod), backtests both arms vs the identical v5_2coin baseline, bootstraps each,
writes `data/ab_modprompt/VERDICT.json` + `DONE`.

v1 baseline to beat (published §23.9): ETH hybrid SR 4.681 vs pure-quant 3.586
(Δ +1.10). Gate: v2 must NOT regress ETH (v2_hybrid_sr ≥ v1_hybrid_sr within CI).

## Problem

The Layer-2 LLM modulator prompt mislabels the multiplier scale relative to
the composition formula it feeds.

Composition (identical in backtest and live):
- `tradingagents/strategies/modulator.py:66`
- `tradingagents/execution/live/hybrid_compose.py:23` (`compose_final`)

```
position = base * (1.0 + effective_weight * (multiplier - 1.0))
```

Neutral ("do not adjust the quant magnitude") is therefore **multiplier = 1.0**
(the `(mult-1)` term vanishes). Bounds `[0.0, 1.5]` (contracts.py:27,39).

But the system prompt (`tradingagents/agents/modulator.py:79-86`) tells the LLM:
- `"0.0 — fully damp the LLM signal; trust quant only."`
- Rule 3: `"If you believe the quant signal is wrong, return Multiplier: 0.0"`

Both are wrong against the math:
- "Trust quant only / neutral" is **1.0**, not 0.0.
- `multiplier = 0.0` → `position = base * (1 - effective_weight)`, i.e. it
  **shrinks** the position by the effective-weight fraction. It is a strong bet
  to *cut size*, not a no-op.
- Rule 3 implies 0.0 defers to quant; it cannot flip direction (by design) and
  only shrinks magnitude. Misleading.

## Symptom observed

Ad-hoc "Run prediction" for bitcoin (2026-06-16) shows **LLM multiplier 0.000**.
Confirmed this is a genuine LLM output (mean of 5 Self-MoA samples), not a
degradation default — degradation/parse-fail defaults return **1.0**
(`hybrid_compose.py:38`, `agents/modulator.py:159`). The BTC modulator, told
"trust quant → 0.0", emits 0.0.

## Why it is mostly latent today (and where it bites)

For BTC, `effective_weight ≈ 0` (bull regime band 0.2–0.3, midpoint 0.25,
further dampened by uncertainty and any negative rolling edge). With eff_w≈0,
`position ≈ base` regardless of multiplier → collapses to pure quant. Harmless,
but the displayed 0.000 is alarming.

**Hidden risk:** in a **sideways** regime the band is 0.6–0.8 (eff_w high). An
LLM that outputs 0.0 *intending* "neutral / defer to quant" would actually slash
the position to `base * (0.2–0.4)` — a 60–80% unintended size cut. This is a
real sizing error driven purely by prompt confusion, not visible in the
BTC-bull case.

## Out of scope

- The composition formula and `[0,1.5]` contract bounds are mathematically clean
  (1.0 = neutral). Do **not** change them.
- Effective-weight formula (`effective_weight.py`) unchanged.

## Options

### Option 1 — Realign the prompt (RECOMMENDED)
Edit `_build_prompt` system text in `agents/modulator.py` so multiplier semantics
match the formula:
- `1.0` = neutral / defer to quant (no adjustment). **This is the "trust quant" value.**
- `<1.0` = reduce conviction (quant position looks oversized / contradicted);
  `0.0` = maximally shrink (toward `base*(1-eff_w)`).
- `>1.0` (up to 1.5) = amplify conviction.
Rewrite Rule 3: cannot flip direction; if quant looks wrong, emit a low
multiplier (<1.0) to shrink and explain — do not say 0.0 = "defer".

Pros: minimal, no math/contract change.
Cons: shifts the multiplier **distribution** → invalidates stale rolling-edge
parquet + per-coin isotonic calibration (both trained under old semantics);
changes live ETH sizing (ETH is the only coin with confirmed LLM alpha).

### Option 2 — Rescale formula so 0.0 = neutral
Rejected. Formula is clean; the defect is the prompt, not the math.

### Option 3 — UI relabel only
Rename card / add tooltip ("0.000 = LLM fully deferred to quant"). Does NOT fix
the hidden sideways-regime sizing bug. Acceptable only as a *pair* with Option 1,
never alone.

**Recommendation:** Option 1 + Option 3 tooltip.

## Thesis-reproducibility constraint (IMPORTANT)

The published §23 / §23.9 Hybrid V5 1-yr ETH alpha (ΔSR +1.10) was produced under
the **old** prompt. Silently changing the prompt means that number no longer
reproduces from the code. Mitigate with a config flag:

- `modulator_prompt_version: "v1"` (frozen, reproduces thesis) | `"v2"` (corrected).
- Default `v1` until v2 passes its gate, then flip default and note in THESIS_FINDINGS.

## Blast radius

- `tradingagents/agents/modulator.py` — `_build_prompt` system text + Rule 3 (+ flag branch).
- `tradingagents/monitor/frontend/src/tabs/RunTab.tsx` (+ DecisionsTab.tsx) — card tooltip.
- Stale artifacts to rebuild/clear after semantics change:
  - rolling-edge parquet (`rolling_edge.py` DEFAULT_PARQUET) — mixed-semantics history.
  - per-coin isotonic calibration models (`strategies/calibration.py`).
- Live hybrid bot (all gpt-4o-mini): ETH sizing changes; BTC should stay ≈ pure quant.

## Validation plan

1. Unit: `effective_weight` + `apply_modulator` unchanged → existing tests stay green.
   Add a guard test asserting prompt no longer claims `0.0 = neutral` (string check).
2. Regenerate hybrid signals under v2 prompt: `scripts/generate_hybrid_signals.py`
   (full LLM cache miss — replay cache does NOT help prompt changes per
   `feedback_replay_cache_model_variation`; ≈ $15–25/run).
3. A/B backtest v1 vs v2 prompt:
   - `scripts/backtest_hybrid.py` + `scripts/bootstrap_hybrid.py`
   - ETH 1-yr window matching §23.9 (the alpha coin) + BTC (do-no-harm).
4. Acceptance gates:
   - ETH: ΔSR ≥ 0 vs current hybrid; must **not regress** the published +1.10 alpha CI.
   - BTC: stays ≈ pure quant (|ΔSR| within noise; position ≈ base).
   - Sideways-regime synthetic check: confirm a "defer" intent no longer slashes size.
5. Stage on testnet before any live flip; keep `v1` default until gate passes.

## Effort / cost

Prompt edit + flag: ~1h. UI tooltip: ~15m. Validation dominates: 1 signal-regen
($15–25) + backtest + bootstrap per coin. Total ~1 backtest cycle.

## Decision needed from operator

- Approve Option 1 + flag approach?
- Run the ETH/BTC A/B now, or defer until next hybrid evaluation window?
