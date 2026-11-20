"""Event-time study: event table, lead rule, bar prices, return windows, slope gate. Offline, synthetic data only."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tradingagents.eventtime import study

T = pd.Timestamp("2023-06-01 12:00:00", tz="UTC")


def _events(rows):
    frame = pd.DataFrame(rows, columns=["doc_id", "base", "t0", "clock", "sign", "event_class"])
    frame["t0"] = pd.to_datetime(frame["t0"], utc=True)
    return frame.assign(source="ccnews", outlet="o", direction="x", materiality=2, status="occurred")[
        study.EVENT_COLUMNS]


def test_url_key_ignores_scheme_www_query_and_slash():
    assert study.url_key("https://www.Site.com/a/b/?x=1#y") == study.url_key("http://site.com/a/b")
    assert study.url_key(None) == "" and study.url_key(float("nan")) == ""


def test_publication_times_accept_only_consistent_unique_matches():
    pages = pd.DataFrame({"doc_id": ["a", "b", "c", "d"], "url": ["https://s.com/1", "https://s.com/2", "https://s.com/3", "https://s.com/4"],
                          "event_ts": [T.floor("D")] * 4, "as_of_ts": [T + pd.Timedelta(minutes=20)] * 4})
    feed = pd.DataFrame({"url": ["http://www.s.com/1/", "https://s.com/2", "https://s.com/3", "https://s.com/3", "https://s.com/4"],
                         "event_ts": [T, T + pd.Timedelta(hours=2), T, T, T - pd.Timedelta(days=5)]})
    pub = study.publication_times(pages, feed)
    assert list(pub.index) == ["a"] and pub["a"] == T      # b: later than the capture, c: two feed rows, d: other date


def test_event_table_clocks():
    stamp = lambda ts: pd.Timestamp(ts, tz="UTC")
    items = pd.DataFrame({"doc_id": ["p1", "p2"], "base": ["ETH", "ETH"], "source": "wayback", "outlet": "coindesk",
                          "event_ts": [stamp("2023-06-01")] * 2, "as_of_ts": [stamp("2023-06-01 13:00"), stamp("2023-06-01 15:00")]})
    feed_items = pd.DataFrame({"doc_id": ["f1", "f2"], "base": ["SOL", "SOL"], "source": "ccnews", "outlet": "x",
                               "event_ts": [stamp("2023-06-01 10:00:07"), stamp("2023-06-01 10:00")],
                               "as_of_ts": [stamp("2023-06-01 11:00:07"), stamp("2023-06-03 10:00")]})
    rec = lambda ids, base, d: pd.DataFrame({"doc_id": ids, "base": base, "direction": d, "materiality": 1,
                                             "event_class": "exchange_listing", "status": "occurred"})
    out = study.event_table(items, rec(["p1", "p2"], "ETH", ["favourable", "neutral"]), feed_items,
                            rec(["f1", "f2"], "SOL", ["unfavourable", "favourable"]), pd.Series({"p1": stamp("2023-06-01 12:30")}))
    got = out.set_index("doc_id")
    assert got.loc["p1", ["clock", "sign"]].tolist() == ["publication", 1] and got.loc["p1", "t0"] == stamp("2023-06-01 12:30")
    assert got.loc["p2", ["clock", "sign"]].tolist() == ["capture", 0] and got.loc["p2", "t0"] == stamp("2023-06-01 15:00")
    assert got.loc["f1", ["clock", "sign"]].tolist() == ["publication", -1] and got.loc["f1", "t0"] == stamp("2023-06-01 10:00:07")
    assert got.loc["f2", "clock"] == "late" and got.loc["f2", "t0"] == stamp("2023-06-03 10:00")


def test_lead_events_never_overlap_and_skip_soft_classes_and_other_clocks():
    rows = [("a", "ETH", T, "publication", 1, "exchange_listing"),
            ("b", "ETH", T + pd.Timedelta(hours=1), "publication", -1, "exchange_listing"),              # inside the hold: follower
            ("c", "ETH", T + study.HOLD, "publication", 1, "security_incident"),                           # first allowed
            ("d", "ETH", T + pd.Timedelta(days=3), "publication", 1, "opinion_or_forecast"),              # soft class
            ("e", "ETH", T + pd.Timedelta(days=4), "capture", 1, "exchange_listing"),                     # other clock
            ("f", "ETH", T + pd.Timedelta(days=5), "publication", 0, "exchange_listing"),                 # no direction
            ("g", "SOL", T + pd.Timedelta(minutes=1), "publication", -1, "legal_regulatory")]
    out = study.mark_leads(_events(rows)).set_index("doc_id")
    assert out["lead"].to_dict() == {"a": True, "b": False, "c": True, "d": False, "e": False, "f": False, "g": True}
    assert out.loc["a", ["n_following", "n_opposed"]].tolist() == [1, 1]
    assert out["fresh"].to_dict() == {"a": True, "b": False, "c": False, "d": True, "e": True, "f": True, "g": True}
    leads = out[out["lead"]].sort_values(["base", "t0"])
    assert (leads.groupby("base")["t0"].diff().dropna() >= study.HOLD).all()


def _store(tmp_path, prices):
    for name, series in prices.items():
        series.rename("open").to_frame().rename_axis("ts").to_parquet(tmp_path / f"{name}.parquet")
    return tmp_path


def _minutes(start, n, values):
    return pd.Series(values, index=pd.date_range(start, periods=n, freq="1min", tz="UTC"), dtype=float)


def test_bars_price_is_first_open_at_or_after_and_missing_past_the_gap(tmp_path):
    series = _minutes("2023-06-01 12:00", 10, np.arange(100.0, 110.0)).drop(pd.Timestamp("2023-06-01 12:03", tz="UTC"))
    bars = study.Bars(_store(tmp_path, {"ETHUSDT": series, "1000PEPEUSDT": series}))
    times = pd.DatetimeIndex(["2023-06-01 12:01:00", "2023-06-01 12:01:30", "2023-06-01 12:03:00", "2023-06-01 11:50:00",
                              "2023-06-01 12:30:00"], tz="UTC")
    got = bars.price("ETH", times)
    assert got[:3].tolist() == [101.0, 102.0, 104.0] and np.isnan(got[3]) and np.isnan(got[4])
    assert bars.has("PEPE") and not bars.has("XYZ") and np.isnan(bars.price("XYZ", times)).all()


def test_event_returns_windows_use_no_bar_before_the_entry(tmp_path):
    n = 3200
    start = pd.Timestamp("2023-05-31 00:00", tz="UTC")
    eth = _minutes(start, n, 100.0 * (1.0 + 0.0001 * np.arange(n)))
    btc = _minutes(start, n, np.full(n, 50.0))
    store = _store(tmp_path, {"ETHUSDT": eth, "BTCUSDT": btc})
    t0 = start + pd.Timedelta(minutes=1500, seconds=20)                       # between two bars: the price is the next open
    panel = study.event_returns(_events([("a", "ETH", t0, "publication", 1, "exchange_listing")]), store)
    p = lambda k: eth.iloc[1501 + k]
    row = panel.iloc[0]
    assert row["ar_post_5_240"] == pytest.approx(p(245) / p(5) - 1.0) and row["r_post_5_240"] == row["ar_post_5_240"]
    assert row["ar_imm_5"] == pytest.approx(p(5) / p(0) - 1.0)
    assert row["ar_pre_60"] == pytest.approx(p(0) / p(-60) - 1.0)
    assert row["ar_post_0_15"] == pytest.approx(p(15) / p(0) - 1.0)
    late = study.event_returns(_events([("a", "ETH", eth.index[-1] + pd.Timedelta(hours=1), "publication", 1, "exchange_listing")]), store)
    assert np.isnan(late.iloc[0]["ar_post_5_240"])


def _panel(n=4000, effect=0.0, drift=0.0, seed=0):
    rng = np.random.default_rng(seed)
    t0 = pd.Timestamp("2023-01-02", tz="UTC") + pd.to_timedelta(np.sort(rng.uniform(0, 725, n)), unit="D")
    sign = np.where(rng.uniform(size=n) < 0.68, 1, -1)
    frame = pd.DataFrame({"doc_id": [f"d{i}" for i in range(n)], "base": rng.choice(["ETH", "SOL", "XRP"], n), "source": "ccnews",
                          "outlet": "o", "t0": t0, "clock": "publication", "sign": sign, "direction": "x", "materiality": 2,
                          "event_class": "exchange_listing", "status": "occurred", "lead": True, "fresh": True,
                          "n_following": 0, "n_opposed": 0})
    for c in study.return_columns():
        r = drift + effect * sign + 0.02 * rng.normal(size=n)
        frame[f"r_{c}"], frame[f"ar_{c}"] = r, r
    return frame


def test_slope_ignores_a_common_drift_that_a_signed_mean_would_book():
    panel = _panel(drift=0.01)
    g = study.gate(panel)
    assert abs(g["total"]["t"]) < 3 and g["verdict"] == "FAIL"
    plain = study.clustered((panel["sign"] * panel[study.GATE_COLUMN]).to_numpy(), panel["t0"].dt.floor("D").to_numpy())
    assert plain["t"] > 5                                                       # the drift times the share of favourable events


def test_gate_passes_on_a_planted_effect_and_reads_the_size():
    g = study.gate(_panel(effect=0.002))
    assert g["verdict"] == "PASS" and g["g1"] and g["g2"] and g["size_reading"] == "above cost"
    assert g["total"]["mean_bp"] == pytest.approx(20.0, abs=8.0)
    assert study.gate(_panel(effect=-0.002))["verdict"] == "FAIL"


def test_gate_needs_both_years():
    panel = _panel(effect=0.004)
    late = panel["t0"].dt.year == 2024
    panel.loc[late, study.GATE_COLUMN] = panel.loc[late, study.GATE_COLUMN] - 0.006 * panel.loc[late, "sign"]
    g = study.gate(panel)
    assert g["by_year"]["2023"]["mean"] > 0 > g["by_year"]["2024"]["mean"] and not g["g2"] and g["verdict"] == "FAIL"


def test_gate_set_leaves_out_the_market_contract_and_other_years():
    panel = _panel(n=300)
    panel.loc[:9, "base"] = study.MARKET
    panel.loc[10:19, "t0"] = pd.Timestamp("2022-06-01", tz="UTC")
    panel.loc[20:29, "lead"] = False
    assert len(study.gate_set(panel)) == 270


def test_evaluate_writes_json_safe_outputs_with_missing_returns():
    import json
    panel = _panel(n=600)
    panel.loc[::7, [c for c in panel.columns if c.startswith(("r_", "ar_"))]] = np.nan
    out = study.json_safe(study.evaluate(panel, n_placebo=10))
    json.dumps(out, allow_nan=False)
    assert set(out) == {"verdict.json", "evaluation.json"} and out["verdict.json"]["verdict"] in ("PASS", "FAIL")
    assert out["evaluation.json"]["descriptive"]["permutation"]["n"] == 10


def test_store_digest_detects_a_changed_or_added_file(tmp_path):
    (tmp_path / "bars").mkdir()
    _store(tmp_path / "bars", {"BTCUSDT": _minutes("2023-06-01", 5, np.arange(5.0))})
    digest = study.store_digest(tmp_path, "bars")
    assert study.verify_store(tmp_path, digest) == tmp_path / "bars"
    _store(tmp_path / "bars", {"ETHUSDT": _minutes("2023-06-01", 5, np.arange(5.0))})
    with pytest.raises(ValueError):
        study.verify_store(tmp_path, digest)
