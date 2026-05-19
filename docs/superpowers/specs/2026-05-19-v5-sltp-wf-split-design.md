# V5 MIX TP/SL Walk-Forward Parameter Split — Design

**Date:** 2026-05-19
**Status:** Draft, follow-up to §30 (intrabar sweep, partial confirm)
**Scope:** Research-only. No live trading change.
**Repo:** TradingAgents
**Branch:** `feature/v5-sltp-wf-split`
**Predecessors:**
- `docs/superpowers/specs/2026-05-19-v5-sltp-sweep-design.md` (§29 close-only)
- `docs/superpowers/specs/2026-05-19-v5-sltp-intrabar-design.md` (§30 intrabar)

## 1. Motivation

§29 found best (close-only) cell SL=10%, EE=disabled, TP=off → SR +3.335 / DD 3.6%.
§30 (intrabar wick test) **partial-confirmed**: ΔSR threshold met (+0.344) but
the optimal regime **flipped completely** — new winner SL=disabled, EE=0.005,
TP=12% → SR +3.391. The §29 winning cluster degrades −0.06 to −0.27 SR under
intrabar.

Both §29 and §30 were single-window in-sample analyses. The flipped regime
between engines is exactly the kind of finding that motivates **walk-forward
parameter validation**: do either winner's parameters generalise out-of-sample,
or are both products of overfitting to the 2021-11 → 2026-04 window?

This study runs the full 378-cell sweep on a **train window** (2021-11-07 →
2024-12-31), identifies the train-best cell per engine, then scores it on a
held-out **test window** (2025-01-01 → 2026-04-15). Acceptance: the train-best
cell's OOS Sharpe must exceed the V5 baseline cell's OOS Sharpe (the minimum
"sweep finds something better than do-nothing" bar).

## 2. Out of Scope

- Per-coin parameter optimisation (still global tuple)
- ATR-scaled SL/TP (approach C)
- Bootstrap CI / DSR (separate follow-up — would test statistical significance of OOS delta)
- Rolling-window k-fold (single train/test split only)
- Live deployment recommendation (regardless of verdict; one OOS window is necessary but not sufficient)
- Per-coin OOS analysis (portfolio-level only)

## 3. Architecture

### 3.1 No engine change

The §29 + §30 engines already support arbitrary `--start` / `--end` windows.
Both sweep scripts (`scripts/v5_mix_sltp_sweep.py` and
`scripts/v5_mix_sltp_sweep_intrabar.py`) are reused unchanged. The WF
orchestrator calls each twice (train window, test window) and writes a
unified analysis.

### 3.2 Orchestrator

New script: `scripts/v5_sltp_wf_orchestrator.py`. Responsibilities:

1. Run close-only sweep on TRAIN window → `data/v5_sltp_wf/co_train/`
2. Run close-only sweep on TEST window → `data/v5_sltp_wf/co_test/`
3. Run intrabar sweep on TRAIN window → `data/v5_sltp_wf/ib_train/`
4. Run intrabar sweep on TEST window → `data/v5_sltp_wf/ib_test/`
5. Build comparison: join train + test results on (sl, ee, tp), per engine
6. Identify train-best per engine, look up its OOS (test-window) Sharpe
7. Compare to baseline OHS-test Sharpe per engine
8. Write `wf_results.csv`, `wf_summary.json`, `wf_report.md`

Wall-clock estimate: 4 × ~15 s = ~60 s.

### 3.3 Window definitions

| Window | Start | End | Length |
|---|---|---|---|
| TRAIN | 2021-11-07 | 2024-12-31 | ~3.15 yr |
| TEST  | 2025-01-01 | 2026-04-15 | ~1.30 yr |

The test window starts immediately after train (no gap, no embargo). This is
acceptable because positions reset between calls (each `_load_coin_data` call
is fresh) and prediction CSVs are PIT — no leakage path exists.

The TEST window of 1.3 yr is short by traditional WF standards but is bounded
by the data range (2026-04-15 is the latest available). For the deferred
bootstrap CI follow-up, a longer history would be required.

## 4. Grid

**Same 378-cell grid as §29 / §30**, on BOTH engines, on BOTH windows.

| Parameter | Values |
|---|---|
| stop_loss | off, 0.5%, 1%, 1.5%, 2%, 3% (V5), 5%, 7%, 10% |
| early_exit_loss | disabled, 0.5%, 1%, 1.5% (V5), 2%, 3% |
| take_profit | off (V5), 1%, 2%, 3%, 5%, 8%, 12% |

Total: 4 × 378 = **1512 cell-runs**. Per-EE position cache (§29 trick) applies
within each sweep call.

## 5. Outputs

`data/v5_sltp_wf/`:

| Artifact | Contents |
|---|---|
| `co_train/results.csv` | §29 sweep on TRAIN window — 1890 rows |
| `co_train/summary.json` | §29 sweep summary on TRAIN |
| `co_test/results.csv` | §29 sweep on TEST window — 1890 rows |
| `co_test/summary.json` | §29 sweep summary on TEST |
| `ib_train/results.csv` | §30 sweep on TRAIN window — 1890 rows |
| `ib_train/summary.json` | §30 sweep summary on TRAIN |
| `ib_test/results.csv` | §30 sweep on TEST window — 1890 rows |
| `ib_test/summary.json` | §30 sweep summary on TEST |
| `wf_results.csv` | Joined: per-cell IS-SR + OOS-SR per engine. Cols: sl, ee, tp, engine, is_sr, oos_sr, is_dd, oos_dd, is_calmar, oos_calmar |
| `wf_summary.json` | Train-best per engine, OOS scores, verdict per engine, baseline OOS comparison |
| `wf_report.md` | Side-by-side report: TRAIN winner + OOS performance + baseline OOS for both engines, with verdict |
| `wf_sweep.log` | tee'd orchestrator output |

## 6. Acceptance Criterion (locked)

Per-engine verdict:

> **OOS SR of train-best cell > OOS SR of V5 baseline cell** (SL=0.03, EE=0.015, TP=off)

Both engines evaluated independently:
- **Close-only WF verdict**: train-best CO cell's OOS SR > baseline OOS SR (CO)?
- **Intrabar WF verdict**: train-best IB cell's OOS SR > baseline OOS SR (IB)?

Outcomes (joint):

| CO verdict | IB verdict | Action |
|---|---|---|
| pass | pass | **Both stand.** Update §31 reporting + recommend bootstrap CI follow-up before any live consideration. |
| pass | fail | Close-only finding generalises OOS; intrabar finding is window-specific. Document; intrabar finding goes from "candidate" to "rejected OOS". |
| fail | pass | Close-only finding does not generalise; intrabar finding does. Strengthens the §30 narrative; intrabar finding becomes leading candidate. |
| fail | fail | **Both rejected.** No WF-confirmed alpha; the §29 + §30 results are window-specific. §31 documents this as the controlled-negative conclusion of the parameter-sweep family. No further follow-ups in this family. |

## 7. Test Plan

`tests/strategies/test_sltp_wf.py`:

1. **Orchestrator output schema** — running `--smoke` produces all expected files (`co_train/`, `co_test/`, `ib_train/`, `ib_test/`, `wf_results.csv`, `wf_summary.json`, `wf_report.md`)
2. **Window non-overlap** — `wf_summary.json` train/test windows must not overlap
3. **Per-engine verdict computed** — `wf_summary.json` has `close_only.verdict` and `intrabar.verdict`, each one of {pass, fail}
4. **Cell-join correctness** — sampled cell from `wf_results.csv` matches the same cell looked up in `{co,ib}_{train,test}/results.csv`
5. **`@pytest.mark.slow` full orchestrator reproduction** — full WF run completes in <300 s, produces a valid `wf_summary.json` with both verdicts populated

## 8. Reproduce Commands

```bash
# Full WF (~60s wall)
python scripts/v5_sltp_wf_orchestrator.py \
    --train-start 2021-11-07 --train-end 2024-12-31 \
    --test-start 2025-01-01 --test-end 2026-04-15 \
    --output-dir data/v5_sltp_wf

# Smoke (single small grid on both windows + both engines)
python scripts/v5_sltp_wf_orchestrator.py --smoke
```

## 9. Reporting

### 9.1 THESIS_FINDINGS.md §31

Title: `## 31. V5 MIX TP/SL Walk-Forward Parameter Split — §29 + §30 OOS Validation (2026-05-19)`.

Body must include:
- Methodology (train/test split, joint engine evaluation, acceptance criterion)
- Train-best cell per engine (from TRAIN sweep)
- OOS Sharpe per engine for both train-best and baseline cells
- Per-engine verdict
- Joint outcome interpretation (table from §6 above)
- Side-by-side comparison: §29 cell vs §30 cell vs train-best cells, OOS performance
- Limitations (single split, short test window, no statistical test)
- Recommendation (always: no live change without bootstrap CI on OOS delta)

### 9.2 §30 update

Append a single line: `**Follow-up:** §31 walk-forward validates this OOS; see verdict there.`

## 10. Acceptance for THIS Spec

Done when:
- Orchestrator implemented (no engine change required)
- 4 sweep runs complete without errors
- `wf_results.csv`, `wf_summary.json`, `wf_report.md` written
- All 5 tests pass
- THESIS §31 added with verdict + §30 cross-reference line
- Recommendation explicit: any live change requires bootstrap CI on OOS delta (deferred work)

## 11. Risks

1. **TEST window is short (1.3 yr).** Single split has high variance. If both verdicts pass, a follow-up bootstrap CI on the OOS delta is needed before any live consideration.
2. **No embargo between train and test.** Predictions are PIT and positions reset between sweep calls — no leakage path exists, but document this.
3. **2025 may be uncharacteristic.** If 2025-01 → 2026-04 has a regime shift, OOS results may misrepresent the underlying parameter sensitivity. The single-split limitation is acknowledged in the report.
4. **§30 winner has very tight EE (0.005) + high TP (12%).** Likely overfit to wick noise specific to 2021-2024. If it fails OOS, that's evidence the §30 finding was window-specific; the §29 close-only finding being already-rejected by §30 means the parameter family as a whole may be exhausted.

## 12. Follow-ups (Conditional)

- **Bootstrap CI on OOS delta:** If at least one engine's verdict = pass, run bootstrap CI on the OOS SR difference (train-best vs baseline) to test whether the OOS improvement is statistically distinguishable from sampling noise.
- **Live A/B spec:** Requires bootstrap CI pass on at least one engine. Out of scope for this study.
- **Per-coin OOS:** If verdict-pass at portfolio level, examine per-coin breakdown to flag any coin where the parameter shift hurts vs portfolio average.
