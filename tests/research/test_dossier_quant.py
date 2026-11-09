from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.dossier.quant_forecast import FEATURES, calibration, fit_predict, forward_returns, render_forecast  # noqa: E402


def _cards(fridays, symbols, rng):
    rows = []
    for f in fridays:
        for s in symbols:
            rows.append({"date": f, "symbol": s, **{c: rng.normal() for c in FEATURES}})
    return pd.DataFrame(rows)


def test_walk_forward_shapes_and_leak_guard(tmp_path):
    rng = np.random.default_rng(0)
    fridays = pd.date_range("2022-01-07", periods=70, freq="W-FRI", tz="UTC")
    symbols = [f"S{i}USDT" for i in range(12)]
    cards = _cards(fridays, symbols, rng)
    days = pd.date_range(fridays[0], fridays[-1] + pd.Timedelta(days=7), freq="D", tz="UTC")
    for s in symbols:
        k = pd.DataFrame({"close": np.cumprod(1 + rng.normal(0, 0.02, len(days))) * 100}, index=days)
        k.index.name = "ts"
        k.to_parquet(tmp_path / f"{s}.parquet")
    fwd = forward_returns(symbols, fridays, klines_dir=tmp_path)
    assert len(fwd) == 70 * 12
    assert fit_predict(cards, fwd, fridays[30]).empty                      # before burn-in
    pred = fit_predict(cards, fwd, fridays[60])
    assert len(pred) == 12 and pred["pred_rank_pct"].between(0, 1).all()
    # leak guard: the decision Friday's own forward return must not be in the training set
    fwd_leak = fwd.copy()
    fwd_leak.loc[fwd_leak["date"] == fridays[60], "fwd_ret"] = 1e6
    pred2 = fit_predict(cards, fwd_leak, fridays[60])
    assert np.allclose(pred["pred_rank_pct"].to_numpy(), pred2["pred_rank_pct"].to_numpy())
    preds = pd.concat([fit_predict(cards, fwd, f).assign(date=f) for f in fridays[55:65]])
    calib = calibration(preds, fwd, fridays[65])
    assert calib["weeks"] == 10 and -1 <= calib["rank_ic_mean"] <= 1
    text = render_forecast(0.83, calib)
    assert "percentile 83" in text and "2022" not in text
    assert "unavailable" in render_forecast(None, calib)



def test_forward_returns_keep_delisted_week(tmp_path):
    import numpy as np
    import pandas as pd
    from tradingagents.dossier.quant_forecast import forward_returns
    idx = pd.date_range("2024-01-01", "2024-01-10", freq="D", tz="UTC")       # stops trading Jan 10
    pd.DataFrame({"close": np.linspace(100, 50, len(idx))}, index=idx).to_parquet(tmp_path / "XXXUSDT.parquet")
    idx2 = pd.date_range("2024-01-01", "2024-01-20", freq="D", tz="UTC")
    pd.DataFrame({"close": np.linspace(10, 20, len(idx2))}, index=idx2).to_parquet(tmp_path / "YYYUSDT.parquet")
    f = pd.Timestamp("2024-01-05", tz="UTC")
    out = forward_returns(["XXXUSDT", "YYYUSDT"], [f], klines_dir=tmp_path)
    assert set(out["symbol"]) == {"XXXUSDT", "YYYUSDT"}
    x = out[out["symbol"] == "XXXUSDT"].iloc[0]
    assert bool(x["delisted"]) and x["fwd_ret"] < 0                        # last close booked, week kept
    assert not bool(out[out["symbol"] == "YYYUSDT"].iloc[0]["delisted"])
