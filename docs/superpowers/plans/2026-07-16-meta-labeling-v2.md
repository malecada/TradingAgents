# Meta-Labeling Experiment v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** Re-register the meta-labeling experiment with an event-density fix: train/G1 on ALL in-trend bars (dense, overlap handled by uniqueness weights + cluster bootstrap), G2 unchanged on entry-event trades. v1 failed G1 as underpowered (203 events, 44 OOS); v2 attacks the power problem without touching barriers, model, τ grid, costs, or gate formulas.

**Architecture:** Delta on the existing `tradingagents/metalabel/` stack (v1 stays intact and frozen — its ledger rows are history). New: `extract_inbar_events` in primary.py, cluster-bootstrap option in `evaluate_g1`, `scripts/metalabel2_run.py`, `scripts/metalabel2_holdout.py`, `experiments/metalabel_v2/{gates,freeze}.json`. Training events = every bar with vote > 0.5; G2 replay still keyed on v1 entry events, whose p̂ comes from the dense OOS predictions (entry bars are a subset of dense bars).

**Tech Stack:** unchanged (Python 3.13 via uv, pandas, lightgbm, sklearn, pytest).

## Global Constraints

- v2 frozen deltas vs v1 (ONLY these change): `event_scheme: "inbar_dense"` (all bars vote > 0.5), `dev_window: ["2022-01-01", "2025-03-31"]` (feature-coverage-dense era), `min_train_events: 75`, `g1_bootstrap: "cluster"` clustered by (coin, calendar-month of event_date). Everything else copied verbatim from `experiments/metalabel/freeze.json` / `gates.json` — barriers 2.0/1.5/15, sigma_span 20, τ grid, 10 bps, vol target 0.30, coins, LGB grid, size-mult formula, holdout ["2025-04-01","2026-06-30"], G1/G2/G3 formulas.
- v1 files under `experiments/metalabel/` and `scripts/metalabel_run.py`/`metalabel_holdout.py` are NOT modified. v1 module code in `tradingagents/metalabel/` may gain new functions/params but existing behavior must stay bit-identical (all 43 existing tests pass unmodified).
- Ledger experiment names: `metalabel2-g1`, `metalabel2-g2`, `metalabel2-g3`. Outputs under `data/metalabel_v2/`. Separate spent flag `data/metalabel_v2/holdout_spent.flag`.
- Prereg artifacts committed BEFORE any v2 experiment run. Holdout untouched; G3 script build-only.
- Causality/costs/execution conventions identical to v1.
- Run tests: `uv run pytest tests/metalabel/ -q` from worktree root.

---

### Task 1: v2 pre-registration + dense events + cluster bootstrap

**Files:**
- Create: `experiments/metalabel_v2/gates.json`, `experiments/metalabel_v2/freeze.json`
- Modify: `docs/superpowers/specs/2026-07-15-meta-labeling-design.md` (append §7 "Experiment v2 (2026-07-16)" — 10 lines: v1 G1-fail summary with numbers, the four registered deltas, rationale)
- Modify: `tradingagents/metalabel/primary.py` (add `extract_inbar_events`)
- Modify: `tradingagents/metalabel/model.py` (add optional `clusters` param to `evaluate_g1`)
- Test: `tests/metalabel/test_v2_prereg.py`, extend `tests/metalabel/test_primary.py`, `tests/metalabel/test_model.py`

**Interfaces:**
- Produces: `extract_inbar_events(votes: pd.Series) -> pd.DatetimeIndex` — every bar with vote > 0.5 (NaN-safe). Superset of `extract_events` dates.
- Produces: `evaluate_g1(preds_by_model, n_boot=2000, seed=7, clusters: pd.Series | None = None) -> dict` — when `clusters` given (aligned to the lgb preds frame rows; values = arbitrary hashable cluster ids), the bootstrap resamples unique cluster ids with replacement and gathers member rows; `clusters=None` keeps v1 iid behavior bit-identical.

- [ ] **Step 1: Failing tests**

```python
# tests/metalabel/test_v2_prereg.py
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    return json.loads((ROOT / "experiments" / "metalabel_v2" / name).read_text())


def test_v2_freeze_deltas_and_inherited_values():
    f = _load("freeze.json")
    v1 = json.loads((ROOT / "experiments" / "metalabel" / "freeze.json").read_text())
    assert f["event_scheme"] == "inbar_dense"
    assert f["dev_window"] == ["2022-01-01", "2025-03-31"]
    assert f["wf"]["min_train_events"] == 75
    assert f["g1_bootstrap"] == "cluster"
    # everything else inherited verbatim
    for key in ("ma_pairs", "donchian", "barriers", "sigma_span", "tau_grid",
                "cost_bps_round_trip", "vol_target_ann", "coins",
                "holdout_window", "lgb_grid", "size_mult"):
        assert f[key] == v1[key], key
    assert f["wf"]["retrain_every_days"] == v1["wf"]["retrain_every_days"]
    assert f["wf"]["embargo_bars"] == v1["wf"]["embargo_bars"]


def test_v2_gates_match_v1_formulas():
    g = _load("gates.json")
    v1 = json.loads((ROOT / "experiments" / "metalabel" / "gates.json").read_text())
    assert g["G1"]["auc_ci_excludes"] == 0.5
    assert g["G1"]["bootstrap"] == "cluster_coin_month"
    assert g["G2"] == v1["G2"]
    assert g["G3"] == v1["G3"]
    assert g["holdout_start"] == "2025-04-01"
    assert g["experiment"] == "metalabel2-2026-07"
```

Append to `tests/metalabel/test_primary.py`:

```python
def test_inbar_events_dense_superset_of_entries():
    from tradingagents.metalabel.primary import extract_inbar_events
    closes = np.concatenate([np.linspace(200, 100, 80), np.linspace(100, 300, 70)])
    df = _ohlcv(closes)
    v = compute_votes(df)
    dense = extract_inbar_events(v)
    entries = extract_events(v)
    assert set(entries) <= set(dense)
    assert len(dense) > len(entries)
    assert (v.loc[dense] > 0.5).all()
    # NaN warm-up bars never emit events
    assert not any(d in dense for d in v.index[v.isna()])
```

Append to `tests/metalabel/test_model.py`:

```python
def test_cluster_bootstrap_wider_ci_and_default_unchanged():
    X, y, w = _learnable()
    ev = pd.date_range("2021-07-01", periods=len(X), freq="D")
    meta = pd.DataFrame({"event_date": ev, "touch_date": ev + pd.Timedelta(days=10),
                         "coin": "bitcoin"})
    folds = [(np.arange(0, 500), np.arange(500, 800))]
    preds = {m: run_walk_forward(X, y, w, meta, folds, m)
             for m in ("constant", "logit", "lgb")}
    iid = evaluate_g1(preds, n_boot=300)
    lgb_df = preds["lgb"]
    clusters = lgb_df["event_date"].dt.to_period("M").astype(str) + "_" + lgb_df["coin"]
    clu = evaluate_g1(preds, n_boot=300, clusters=clusters)
    # point estimates identical, only CI differs
    assert clu["lgb_auc"] == iid["lgb_auc"]
    assert (clu["auc_ci_high"] - clu["auc_ci_low"]) >= (iid["auc_ci_high"] - iid["auc_ci_low"]) * 0.8
    assert "g1_pass" in clu
```

- [ ] **Step 2: Run to verify failures** — `uv run pytest tests/metalabel/test_v2_prereg.py tests/metalabel/test_primary.py tests/metalabel/test_model.py -v` → new tests FAIL, old PASS.

- [ ] **Step 3: Implement**

`experiments/metalabel_v2/freeze.json`: copy v1 freeze.json, then set `"frozen": "2026-07-16"`, add `"event_scheme": "inbar_dense"`, `"g1_bootstrap": "cluster"`, set `dev_window` and `wf.min_train_events` per deltas.

`experiments/metalabel_v2/gates.json`: copy v1 gates.json, set `"experiment": "metalabel2-2026-07"`, `"registered": "2026-07-16"`, add `"bootstrap": "cluster_coin_month"` inside G1. G2/G3 byte-identical to v1.

`primary.py` addition:

```python
def extract_inbar_events(votes: pd.Series) -> pd.DatetimeIndex:
    """Dense event scheme (v2): every bar in-trend (vote > 0.5) is an event.

    Overlapping label windows are handled downstream by uniqueness weights
    (labeler) and cluster bootstrap (evaluate_g1)."""
    return pd.DatetimeIndex(votes.index[(votes > 0.5) & votes.notna()])
```

`model.py` — extend `evaluate_g1` signature with `clusters: pd.Series | None = None`; in the bootstrap loop, when clusters is not None:

```python
    cluster_ids = np.asarray(clusters)
    uniq = np.unique(cluster_ids)
    members = {c: np.where(cluster_ids == c)[0] for c in uniq}
    ...
    for _ in range(n_boot):
        if clusters is not None:
            picked = rng.choice(uniq, size=len(uniq), replace=True)
            idx = np.concatenate([members[c] for c in picked])
        else:
            idx = rng.integers(0, n, n)
        ...
```

Point estimates (`lgb_auc` etc.) unchanged. Docstring updated.

- [ ] **Step 4: All tests pass** — `uv run pytest tests/metalabel/ -q` → 43 old + new all green.
- [ ] **Step 5: Commit** — `prereg(metalabel2): v2 registration — dense in-bar events, cluster bootstrap, min-train 75, dev from 2022-01`

---

### Task 2: v2 dev orchestration (`scripts/metalabel2_run.py`)

**Files:**
- Create: `scripts/metalabel2_run.py`
- Test: `tests/metalabel/test_run2_script.py`

**Interfaces:**
- Consumes: everything v1's run script consumes, plus `extract_inbar_events`, `evaluate_g1(..., clusters=...)`.
- Produces: `data/metalabel_v2/dev_results.json`, `oos_predictions.csv`; ledger rows `metalabel2-g1`/`metalabel2-g2`; functions `load_coin_blob(coin, end_date) -> dict` (v2 semantics) and `main(end_date=DEV_END) -> dict`.

Implementation = copy `scripts/metalabel_run.py` with these exact deltas (keep everything else identical, including the zero-coverage RuntimeError guard, coverage report, tz-normalization, fail-loud `.loc` lookups):

1. `FREEZE` loads `experiments/metalabel_v2/freeze.json`; `OUT_DIR = ... / "data" / "metalabel_v2"`.
2. `load_coin_blob` builds TWO event sets: `dense = extract_inbar_events(votes)` and `entries = extract_events(votes)`, both window-filtered to `[DEV_START, end_date]`. Labels/weights computed on DENSE events (`labels = triple_barrier_labels(ohlcv, dense)`); additionally `blob["entry_dates"] = pd.DatetimeIndex(entries)`.
3. G1: identical pipeline (assemble_dataset → purged_walk_forward with freeze params → run_walk_forward × 3 models) but `evaluate_g1(preds, clusters=lgb_df["event_date"].dt.to_period("M").astype(str) + "_" + lgb_df["coin"])` where `lgb_df = preds["lgb"]`. Ledger name `metalabel2-g1`.
4. G2 (only if g1_pass): per coin, `trade_labels = labels.loc[labels.index.isin(blob["entry_dates"])]` further restricted to entry dates present in the lgb OOS preds for that coin (same membership filter as v1); BOTH arms replay `trade_labels`; meta arm p̂ = dense OOS prediction at the entry bar. Ledger name `metalabel2-g2` per τ. `select_tau` identical.
5. Prints prefixed `[v2]`.

Tests (mirror v1's test_run_script.py, adjusted):

```python
# tests/metalabel/test_run2_script.py
import pandas as pd
import scripts.metalabel2_run as run2


def test_v2_freeze_wiring():
    assert run2.DEV_START == "2022-01-01"
    assert run2.DEV_END == "2025-03-31"
    assert run2.FREEZE["wf"]["min_train_events"] == 75
    assert run2.OUT_DIR.name == "metalabel_v2"


def test_dev_end_inside_dev_window():
    from tradingagents.rebuild.ledger import assert_dev_window
    assert_dev_window(run2.DEV_END)


def test_tau_selection_same_rule_as_v1():
    rows = [
        {"tau": 0.45, "g2_pass": False, "delta_sr": 0.9},
        {"tau": 0.50, "g2_pass": True, "delta_sr": 0.3},
        {"tau": 0.55, "g2_pass": True, "delta_sr": 0.5},
    ]
    assert run2.select_tau(rows) == 0.55
    assert run2.select_tau([{"tau": 0.45, "g2_pass": False, "delta_sr": 0.1}]) is None
```

Steps: failing tests → implement → `uv run pytest tests/metalabel/ -q` green → commit `feat(metalabel2): v2 dev orchestration — dense training events, entry-event G2`.

---

### Task 3: v2 holdout script (build only) + smoke verification

**Files:**
- Create: `scripts/metalabel2_holdout.py`
- Test: `tests/metalabel/test_holdout2_script.py`

`scripts/metalabel2_holdout.py` = copy of `scripts/metalabel_holdout.py` with deltas: imports `FREEZE, load_coin_blob` from `scripts.metalabel2_run`; `DEV_RESULTS`/`SPENT_FLAG`/output under `data/metalabel_v2/`; ledger name `metalabel2-g3`; `g3_train_mask` reused semantics (import EMBARGO_CAL_DAYS, same purge at HOLDOUT_START); training on dense dev events, prediction on dense holdout events; G2 replay restricted to entry events (same filter as v2 run script). DO NOT RUN main().

Tests: mirror v1's two refusal tests (chosen_tau None → "G2 did not pass"; spent flag → "already spent") with monkeypatched tmp paths, plus reuse of the boundary-purge mask test pattern against `metalabel2_holdout.g3_train_mask`.

Smoke verification steps (this task, after tests green):
1. `uv run pytest -q` — full suite green (v1's 583-baseline + new).
2. BTC dense smoke: `load_coin_blob('bitcoin','2023-12-31')` → print `len(labels)` (expect ≈ hundreds, >> v1's 16), label base rate ∈ (0.2, 0.8), touch-type distribution, weight stats (`weights.mean()` well below 1 — overlap present).
3. Commit `feat(metalabel2): G3 holdout one-shot (v2) + dense smoke verification`.

---

## Execution notes
- After Task 3: run `uv run python scripts/metalabel2_run.py` ONCE (ledgered experiment), report G1/G2, stop. Holdout only on explicit user sign-off.
- Expected dense event count ≈ 3-5K pooled; LGB fold fits stay < 1 min; full run maybe 15-40 min.
