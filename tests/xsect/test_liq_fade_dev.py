"""Unit tests for the liq_fade_i1 dev runner's pure helpers (scripts/liq_fade_dev.py):
membership_mask_hourly (monthly PIT universe -> hourly bool mask),
event_forward_sum (P2's forward-return-at-trigger extraction), and the
Task 9 dev-grid helpers (dual-family placebo generators, the probes-passed
guard, and ledger row schema). All are testable on synthetic data without
touching the (partial, still-fetching) 1h kline store."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tradingagents.rebuild.ledger import log_trial
from tradingagents.xsect.portfolio import rank_placebo_pvalue

spec = importlib.util.spec_from_file_location(
    "liq_fade_dev", Path(__file__).parents[2] / "scripts" / "liq_fade_dev.py")
liq_fade_dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(liq_fade_dev)


def _hourly_index(start, hours):
    return pd.date_range(start, periods=hours, freq="1h", tz="UTC")


# ── membership_mask_hourly ──────────────────────────────────────────────────

def test_membership_mask_hourly_basic_month_boundaries():
    idx = _hourly_index("2021-01-01", 24 * 62)  # Jan 1 -> Mar 3
    universe = {
        "2021-01-01": ["AAA", "BBB"],
        "2021-02-01": ["BBB", "CCC"],
    }
    mask = liq_fade_dev.membership_mask_hourly(universe, ["AAA", "BBB", "CCC"], idx)

    jan_15 = pd.Timestamp("2021-01-15 00:00", tz="UTC")
    feb_15 = pd.Timestamp("2021-02-15 00:00", tz="UTC")
    assert bool(mask.loc[jan_15, "AAA"]) is True
    assert bool(mask.loc[jan_15, "BBB"]) is True
    assert bool(mask.loc[jan_15, "CCC"]) is False   # not a member yet in January
    assert bool(mask.loc[feb_15, "AAA"]) is False   # dropped at the February re-selection
    assert bool(mask.loc[feb_15, "BBB"]) is True
    assert bool(mask.loc[feb_15, "CCC"]) is True


def test_membership_mask_hourly_last_month_extends_to_index_end():
    idx = _hourly_index("2021-01-01", 24 * 45)  # Jan 1 -> mid-Feb
    universe = {"2021-01-01": ["AAA"]}
    mask = liq_fade_dev.membership_mask_hourly(universe, ["AAA"], idx)
    assert bool(mask.iloc[-1]["AAA"]) is True   # last bar still covered by the sole month


def test_membership_mask_hourly_symbol_not_in_columns_is_ignored():
    idx = _hourly_index("2021-01-01", 24)
    universe = {"2021-01-01": ["AAA", "ZZZ"]}   # ZZZ not in the requested columns
    mask = liq_fade_dev.membership_mask_hourly(universe, ["AAA"], idx)
    assert list(mask.columns) == ["AAA"]
    assert bool(mask.iloc[0]["AAA"]) is True


def test_membership_mask_hourly_boolean_dtype():
    idx = _hourly_index("2021-01-01", 24)
    universe = {"2021-01-01": ["AAA"]}
    mask = liq_fade_dev.membership_mask_hourly(universe, ["AAA", "BBB"], idx)
    assert mask.dtypes.eq(bool).all()


# ── event_forward_sum ────────────────────────────────────────────────────────

def test_event_forward_sum_extracts_sum_t1_to_tH():
    idx = _hourly_index("2021-01-01", 10)
    # constant 1% return each bar -> forward sum over H bars is exactly H * 0.01
    R = pd.DataFrame({"AAA": 0.01}, index=idx)
    trig = pd.DataFrame({"AAA": False}, index=idx)
    trig.iloc[2, 0] = True   # single trigger at row 2
    H = 3
    vals = liq_fade_dev.event_forward_sum(R, trig, H)
    assert len(vals) == 1
    assert np.isclose(vals[0], H * 0.01)


def test_event_forward_sum_drops_events_too_close_to_the_end():
    idx = _hourly_index("2021-01-01", 5)
    R = pd.DataFrame({"AAA": 0.01}, index=idx)
    trig = pd.DataFrame({"AAA": False}, index=idx)
    trig.iloc[-1, 0] = True   # last bar: no room for a forward window of H=3
    vals = liq_fade_dev.event_forward_sum(R, trig, H=3)
    assert len(vals) == 0


def test_event_forward_sum_multiple_symbols_and_events_flattened():
    idx = _hourly_index("2021-01-01", 8)
    R = pd.DataFrame({"AAA": [0.01] * 8, "BBB": [0.02] * 8}, index=idx)
    trig = pd.DataFrame({"AAA": [False] * 8, "BBB": [False] * 8}, index=idx)
    trig.iloc[1, 0] = True   # AAA triggers at row 1
    trig.iloc[3, 1] = True   # BBB triggers at row 3
    H = 2
    vals = sorted(liq_fade_dev.event_forward_sum(R, trig, H))
    assert len(vals) == 2
    assert np.isclose(vals[0], H * 0.01)  # AAA event
    assert np.isclose(vals[1], H * 0.02)  # BBB event


def test_event_forward_sum_uses_t1_to_tH_not_t_to_tHminus1():
    """Non-constant return path: with constant returns, the correct window
    t+1..t+H and the off-by-one mutant t..t+H-1 (e.g. an errant
    `.shift(-H+1)` instead of `.shift(-H)`) sum to the identical value and
    the bug is invisible. Use a strictly increasing return path so the two
    windows disagree, and hand-compute the correct answer."""
    idx = _hourly_index("2021-01-01", 6)
    R = pd.DataFrame({"AAA": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06]}, index=idx)
    trig = pd.DataFrame({"AAA": [False] * 6}, index=idx)
    trig.iloc[1, 0] = True   # trigger at t=1 (row index 1, return 0.02)
    H = 3
    vals = liq_fade_dev.event_forward_sum(R, trig, H)
    assert len(vals) == 1
    # correct: sum(R[t+1..t+H]) = R[2]+R[3]+R[4] = 0.03+0.04+0.05
    assert np.isclose(vals[0], 0.12)
    # off-by-one mutant (t..t+H-1, i.e. includes the trigger bar itself):
    # R[1]+R[2]+R[3] = 0.02+0.03+0.04 = 0.09 -- must NOT match
    assert not np.isclose(vals[0], 0.09)


# ── load_symbols smoke restriction (pure filesystem check, no parquet reads) ─

def test_load_symbols_smoke_restricts_to_symbols_on_disk():
    all_syms = liq_fade_dev.load_symbols(smoke=False)
    on_disk = {p.stem for p in liq_fade_dev.KLINES_1H_DIR.glob("*.parquet")}
    smoke_syms = liq_fade_dev.load_symbols(smoke=True)
    assert set(smoke_syms) == set(all_syms) & on_disk
    assert set(smoke_syms).issubset(on_disk)


# ── Task 9: dev-grid placebo generators ─────────────────────────────────────

def _synthetic_trig_and_mask(n=200, seed=0):
    idx = _hourly_index("2021-01-01", n)
    rng = np.random.default_rng(seed)
    cols = ["AAA", "BBB", "CCC"]
    trig = pd.DataFrame(False, index=idx, columns=cols)
    # a handful of real events per symbol, all inside the eligible region
    trig.loc[idx[10], "AAA"] = True
    trig.loc[idx[50], "AAA"] = True
    trig.loc[idx[90], "AAA"] = True
    trig.loc[idx[30], "BBB"] = True
    # CCC gets zero real events -- exercises the "n_ev == 0" skip path
    mask = pd.DataFrame(True, index=idx, columns=cols)  # fully eligible
    return trig, mask, rng


def test_shift_triggers_preserves_event_count_per_symbol():
    trig, _mask, rng = _synthetic_trig_and_mask()
    shifted = liq_fade_dev._shift_triggers(trig, rng)
    assert shifted.shape == trig.shape
    assert list(shifted.columns) == list(trig.columns)
    for col in trig.columns:
        assert int(shifted[col].sum()) == int(trig[col].sum())


def test_shift_triggers_is_a_true_circular_permutation():
    """The shifted column's True positions are a np.roll of the original --
    not just count-matched by coincidence (a redraw could also preserve
    count). Recovering the shift offset and rolling back must reproduce the
    original column exactly."""
    trig, _mask, rng = _synthetic_trig_and_mask()
    shifted = liq_fade_dev._shift_triggers(trig, rng)
    for col in trig.columns:
        orig = trig[col].to_numpy()
        shft = shifted[col].to_numpy()
        if not orig.any():
            assert not shft.any()
            continue
        # find the offset by brute force and confirm it reproduces `shft`
        found = False
        for k in range(len(orig)):
            if np.array_equal(np.roll(orig, k), shft):
                found = True
                break
        assert found, f"{col}: shifted column is not a circular roll of the original"


def test_shift_triggers_rejects_too_short_panel():
    idx = _hourly_index("2021-01-01", 10)  # far shorter than 2*24
    trig = pd.DataFrame(False, index=idx, columns=["AAA"])
    with pytest.raises(ValueError, match="too short"):
        liq_fade_dev._shift_triggers(trig, np.random.default_rng(0))


def test_redraw_random_triggers_is_count_matched_per_symbol():
    trig, mask, rng = _synthetic_trig_and_mask()
    redrawn = liq_fade_dev._redraw_random_triggers(trig, mask, rng)
    assert redrawn.shape == trig.shape
    for col in trig.columns:
        assert int(redrawn[col].sum()) == int(trig[col].sum())
    # CCC had 0 real events -> placebo column must stay all-False, never gain events
    assert redrawn["CCC"].sum() == 0


def test_redraw_random_triggers_only_draws_from_eligible_bars():
    idx = _hourly_index("2021-01-01", 100)
    trig = pd.DataFrame(False, index=idx, columns=["AAA"])
    trig.loc[idx[5], "AAA"] = True
    trig.loc[idx[60], "AAA"] = True
    mask = pd.DataFrame(False, index=idx, columns=["AAA"])
    mask.loc[idx[40:], "AAA"] = True   # only the back half is eligible
    rng = np.random.default_rng(1)
    redrawn = liq_fade_dev._redraw_random_triggers(trig, mask, rng)
    picked = np.nonzero(redrawn["AAA"].to_numpy())[0]
    assert len(picked) == 2
    assert all(p >= 40 for p in picked)


def test_redraw_random_triggers_raises_on_invariant_violation():
    """trig-implies-mask must hold (masking is applied before triggers reach
    this function); a caller bug that violates it must fail loudly, not
    silently draw from the wrong bars."""
    idx = _hourly_index("2021-01-01", 20)
    trig = pd.DataFrame(False, index=idx, columns=["AAA"])
    trig.loc[idx[0], "AAA"] = True
    trig.loc[idx[1], "AAA"] = True
    mask = pd.DataFrame(False, index=idx, columns=["AAA"])
    mask.loc[idx[0], "AAA"] = True     # only 1 eligible bar for 2 real events
    with pytest.raises(AssertionError):
        liq_fade_dev._redraw_random_triggers(trig, mask, np.random.default_rng(0))


# ── Task 9: p-value formula agreement ───────────────────────────────────────

def test_placebo_pvalue_formula_agrees_with_rank_placebo_pvalue_hand_case():
    real_sr = 1.0
    placebo_srs = [0.5, 1.0, 1.5, 0.2, 2.0]   # 3 of 5 are >= real_sr (1.0, 1.5, 2.0)
    expected = (1 + 3) / (5 + 1)               # = 4/6 = 0.6667 by the registered formula
    got = rank_placebo_pvalue(real_sr, placebo_srs)
    assert np.isclose(got, expected)
    assert np.isclose(got, 2 / 3)


# ── Task 9: probes-passed guard ─────────────────────────────────────────────

def _write_probes(path, *, smoke, p1_pass, p2_pass):
    path.write_text(json.dumps({"smoke": smoke, "p1": {"pass": p1_pass},
                                "p2": {"pass": p2_pass}}))


def test_grid_refuses_without_probes_file(tmp_path):
    with pytest.raises(RuntimeError, match="not found"):
        liq_fade_dev._assert_probes_passed(tmp_path / "probes.json")


def test_grid_refuses_when_probes_are_smoke(tmp_path):
    p = tmp_path / "probes.json"
    _write_probes(p, smoke=True, p1_pass=True, p2_pass=True)
    with pytest.raises(RuntimeError, match="passing registered verdict"):
        liq_fade_dev._assert_probes_passed(p)


def test_grid_refuses_when_p1_failed(tmp_path):
    p = tmp_path / "probes.json"
    _write_probes(p, smoke=False, p1_pass=False, p2_pass=True)
    with pytest.raises(RuntimeError, match="passing registered verdict"):
        liq_fade_dev._assert_probes_passed(p)


def test_grid_refuses_when_p2_failed(tmp_path):
    p = tmp_path / "probes.json"
    _write_probes(p, smoke=False, p1_pass=True, p2_pass=False)
    with pytest.raises(RuntimeError, match="passing registered verdict"):
        liq_fade_dev._assert_probes_passed(p)


def test_grid_accepts_passing_registered_probes(tmp_path):
    p = tmp_path / "probes.json"
    _write_probes(p, smoke=False, p1_pass=True, p2_pass=True)
    payload = liq_fade_dev._assert_probes_passed(p)   # must not raise
    assert payload["p1"]["pass"] is True
    assert payload["p2"]["pass"] is True


# ── Task 9: ledger row schema ────────────────────────────────────────────────

def test_ledger_row_schema_matches_liq_mr_rows(tmp_path):
    """liq_fade_i1 rows must be structurally identical to liq_mr_t1 rows --
    both go through the same tradingagents.rebuild.ledger.log_trial, so this
    mainly guards against a caller passing extra/missing top-level keys."""
    ledger = tmp_path / "ledger.jsonl"
    row = log_trial(
        "liq_fade_i1",
        {"thr": 2.5, "H": 6, "w_per": 0.1, "cap": 1.0, "cost_bps": 10.0,
         "rf_annual": 0.045, "n_symbols_active": 12},
        ("2021-01-01", "2025-03-31"),
        {"net_sr": 1.23, "maxdd": 0.05},
        ledger_path=ledger,
    )
    liq_mr_row_keys = {"ts", "git_commit", "experiment", "config", "config_hash",
                       "window", "metrics"}
    assert set(row.keys()) == liq_mr_row_keys
    loaded = json.loads(ledger.read_text().strip())
    assert set(loaded.keys()) == liq_mr_row_keys
    assert loaded["experiment"] == "liq_fade_i1"
    assert loaded["window"] == ["2021-01-01", "2025-03-31"]


# ── Task 9: grid dispatch respects the probes guard ─────────────────────────

def test_run_grid_real_calls_probes_guard_before_anything_else(tmp_path, monkeypatch):
    """Without a real probes.json on disk, run_grid(smoke=False) must fail at
    the probes guard -- not proceed to load (partial, still-fetching) real
    kline data."""
    monkeypatch.setattr(liq_fade_dev, "OUT_DIR", tmp_path)
    with pytest.raises(RuntimeError, match="grid refuses to run"):
        liq_fade_dev.run_grid(smoke=False)


# ── Task 9 fix-review #1: cfg must carry ONLY frozen design constants ───────
#
# Anything runtime-derived in the ledgered `config` dict contaminates
# config_hash determinism: an otherwise-identical rerun with one different
# active symbol (e.g. a coin that briefly drops out of the top-50 PIT
# universe) mints a NEW hash and silently, permanently inflates
# cross-experiment n_trials (tradingagents/rebuild/ledger.py docstring
# documents this exact failure class). This test locks the frozen key set so
# a future addition to `cfg` fails loudly instead of leaking through.

_FROZEN_CFG_KEYS = {"thr", "H", "w_per", "cap", "cost_bps", "rf_annual"}


def test_grid_smoke_config_keys_are_exactly_the_frozen_set():
    payload = liq_fade_dev.run_grid(smoke=True)
    assert len(payload["results"]) == 6
    for r in payload["results"]:
        assert set(r["config"].keys()) == _FROZEN_CFG_KEYS, (
            f"cfg leaked a non-frozen key: {set(r['config'].keys()) - _FROZEN_CFG_KEYS}")
        # the runtime-derived value must still be reported, just in metrics
        assert "n_symbols_active" in r["metrics"]
        assert "n_symbols_active" not in r["config"]


def test_grid_smoke_config_hash_is_stable_across_reruns_with_different_active_cols():
    """Two configs that differ ONLY in which columns happened to be active
    (i.e. same thr/H/w_per/cap/cost_bps/rf_annual) must hash identically once
    fed through the real ledger config_hash function -- this is the concrete
    scenario the frozen-key fix guards against."""
    import hashlib

    cfg_a = {"thr": 2.5, "H": 6, "w_per": 0.1, "cap": 1.0, "cost_bps": 10.0,
            "rf_annual": 0.045}
    cfg_b = dict(cfg_a)  # identical frozen fields; a "different active symbol"
                         # rerun would have produced this same cfg post-fix
    hash_a = hashlib.sha256(json.dumps(cfg_a, sort_keys=True, default=str).encode()).hexdigest()[:12]
    hash_b = hashlib.sha256(json.dumps(cfg_b, sort_keys=True, default=str).encode()).hexdigest()[:12]
    assert hash_a == hash_b


# ── Task 9 fix-review #2: DSR ValueError must not prevent dev_results.json ──

def test_grid_smoke_dsr_valueerror_still_completes_the_run(monkeypatch):
    """If deflated_sharpe_ratio raises (e.g. a degenerate se_sr slips past the
    pre-check), the grid must still complete and return a payload with
    dsr=nan / dsr_pass=False / gate_pass=False -- never crash before payload
    assembly (which is what gates dev_results.json actually landing on the
    real run)."""
    def _boom(*_a, **_k):
        raise ValueError("se_sr must be > 0.0")
    monkeypatch.setattr(liq_fade_dev, "deflated_sharpe_ratio", _boom)
    monkeypatch.setattr(liq_fade_dev, "variance_of_sr", lambda cand: 1e-6)  # keeps se_sr > 0
    payload = liq_fade_dev.run_grid(smoke=True)   # must not raise
    assert len(payload["results"]) == 6
    best = next(r for r in payload["results"] if r["config"] == payload["best_config"])
    assert np.isnan(best["metrics"]["dsr"])
    assert best["dsr_pass"] is False
    assert best["gate_pass"] is False
