"""Primary-run mechanics: DSR denominators, placebo families, and the
single-ledger-row invariant."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def test_dsr_at_n1_has_zero_deflation():
    """expected_max_sharpe(1, var) == 0 by definition, so DSR at n=1 is just
    Phi(SR/SE). This is the whole point of the confirmatory denominator."""
    from tradingagents.strategies.v3.backtest.dsr import expected_max_sharpe
    assert expected_max_sharpe(1, 0.05) == 0.0
    assert expected_max_sharpe(13, 0.05) > 0.0
    assert expected_max_sharpe(121, 0.05) > expected_max_sharpe(13, 0.05)


def test_compute_dsr_reports_all_three_denominators():
    from liq_fade_repl import compute_dsr_table
    rng = np.random.default_rng(5)
    net = pd.Series(rng.normal(0.001, 0.01, 800))
    table = compute_dsr_table(net, denominators=(1, 13, 121))
    assert set(table.keys()) == {"1", "13", "121"}
    for v in table.values():
        assert 0.0 <= v <= 1.0
    assert table["1"] >= table["13"] >= table["121"], (
        "DSR must be monotonically non-increasing in n_trials")


def test_compute_dsr_table_survives_degenerate_series():
    """deflated_sharpe_ratio raises ValueError on se_sr <= 0. A constant series
    must yield nan rather than crash the run after ledger rows are written."""
    from liq_fade_repl import compute_dsr_table
    table = compute_dsr_table(pd.Series([0.001] * 50), denominators=(1,))
    assert np.isnan(table["1"])


def test_shift_placebo_preserves_event_count():
    from liq_fade_repl import shift_triggers
    rng = np.random.default_rng(1)
    idx = pd.date_range("2021-01-01", periods=500, freq="1h", tz="UTC")
    trig = pd.DataFrame({"A": rng.random(500) < 0.05,
                         "B": rng.random(500) < 0.02}, index=idx)
    out = shift_triggers(trig, rng)
    assert out.shape == trig.shape
    for col in trig.columns:
        assert out[col].sum() == trig[col].sum(), f"{col}: event count changed"
    assert not out.equals(trig), "shift produced an identical panel"


def test_random_placebo_is_count_matched_and_mask_respecting():
    from liq_fade_repl import redraw_random_triggers
    rng = np.random.default_rng(2)
    idx = pd.date_range("2021-01-01", periods=400, freq="1h", tz="UTC")
    trig = pd.DataFrame({"A": [False] * 400, "B": [False] * 400}, index=idx)
    trig.iloc[[10, 50, 90], 0] = True
    mask = pd.DataFrame({"A": [True] * 200 + [False] * 200,
                         "B": [True] * 400}, index=idx)
    out = redraw_random_triggers(trig, mask, rng)
    assert out["A"].sum() == 3
    assert out["B"].sum() == 0, "symbol with 0 real events must gain none"
    placed = np.nonzero(out["A"].to_numpy())[0]
    assert (placed < 200).all(), "placebo placed outside the eligible mask"


def test_exactly_one_ledger_row_per_run(tmp_path, monkeypatch):
    """The registered n_trials is 1. Secondary configs and cost sensitivities
    are descriptive and must NOT be logged."""
    import liq_fade_repl as m
    ledger = tmp_path / "ledger.jsonl"
    rows = []

    def fake_log(experiment, config, window, metrics, **kw):
        rows.append({"experiment": experiment, "config": config})
        return rows[-1]

    monkeypatch.setattr(m, "log_trial", fake_log)
    net = pd.Series(np.random.default_rng(0).normal(0.001, 0.01, 300),
                    index=pd.date_range("2021-01-01", periods=300, freq="D", tz="UTC"))
    m.log_primary_trial(net_sr=1.2, metrics={"net_sr": 1.2}, ledger_path=ledger)
    assert len(rows) == 1
    assert rows[0]["experiment"] == "liq_fade_r1"
    assert rows[0]["config"]["cost_bps"] == 20.0
    assert rows[0]["config"]["thr"] == 3.5
    assert rows[0]["config"]["H"] == 48


def test_primary_config_hash_is_frozen():
    """config_hash must depend only on frozen design constants. If a runtime
    value leaks in, a rerun mints a new hash and inflates n_trials forever."""
    import hashlib
    import liq_fade_repl as m
    cfg = m.primary_config()
    assert set(cfg.keys()) == {"thr", "H", "w_per", "cap", "cost_bps", "rf_annual"}
    h = hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:12]
    assert h == hashlib.sha256(
        json.dumps(m.primary_config(), sort_keys=True, default=str).encode()
    ).hexdigest()[:12], "primary_config() is not deterministic"
