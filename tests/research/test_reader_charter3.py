"""Target change (Charter 3): daily-bar features and targets, unsigned reader features, partial gate, registered run.

Synthetic fixtures only; no market data, no network. The fixtures of the extraction side are shared with
``test_reader_extract.py``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import reader_charter3_run as run_script  # noqa: E402
import reader_extract as rx  # noqa: E402
from test_reader_extract import (DAY, DECISION, FRIDAY, FakeClient, _block_b_case, _reading_row, _record_row, commit,  # noqa: E402
                                 extract, script_root, sha, store_frames)
from tradingagents.agents_v2.charter1b import PLACEBO_DRAWS, CacheError  # noqa: E402
from tradingagents.agents_v2.evaluate import newey_west_t  # noqa: E402
from tradingagents.dossier.quant_forecast import BURN_IN_WEEKS, RIDGE_ALPHA  # noqa: E402
from tradingagents.reader import charter2 as c2, charter3 as c3, consensus, features, model, schema  # noqa: E402
from tradingagents.reader.extract import CallCache, Reader  # noqa: E402

WEEK = pd.Timedelta(days=7)


# ---------------------------------------------------------------- fixtures
def synth(signal: float = 0.0, weeks: int = 156, n: int = 50, seed: int = 0, rho: float = 0.0):
    """(universe rows, text features, bar history, forward targets) of the registered shape. Volatility has a
    persistent asset level that the history columns measure with noise; ``signal`` plants an effect of
    ``evt_7d`` on the forward variance; ``rho`` is the weekly persistence of the part of the variance that no
    history column sees."""
    rng = np.random.default_rng(seed)
    days = pd.date_range(c2.PANEL_START, periods=weeks, freq="7D", tz="UTC")
    syms = [f"S{i:02d}USDT" for i in range(n)]
    top = pd.DataFrame([(d, s) for d in days for s in syms], columns=["date", "symbol"])
    top["base"] = top["symbol"].str[:-4]
    level = rng.normal(size=n)
    h, u = np.zeros((weeks, n)), np.zeros((weeks, n))
    h[0], u[0] = rng.normal(size=n), rng.normal(size=n)
    for t in range(1, weeks):
        h[t] = 0.9 * h[t - 1] + np.sqrt(1 - 0.81) * rng.normal(size=n)
        u[t] = rho * u[t - 1] + np.sqrt(1 - rho ** 2) * rng.normal(size=n)
    h, u = (level[None, :] + h).ravel(), u.ravel()
    hist = top[["date", "symbol"]].copy()
    for col in c3.HIST_BARS:
        hist[col] = np.exp(h + 0.7 * rng.normal(size=len(top))) if col.startswith("rv") else rng.normal(size=len(top))
    hist.loc[rng.uniform(size=len(top)) < 0.03, "rv_90d"] = np.nan
    top["vol_ewma20"] = np.exp(0.5 * h + 0.5 * rng.normal(size=len(top)))
    top["dvol_30d"] = np.exp(rng.normal(size=len(top)))
    top["age_weeks"] = rng.integers(1, 300, len(top)).astype(float)
    top["funding_3d"] = 1e-4 * rng.normal(size=len(top))
    feats = top[["date", "symbol", "base"]].copy()
    for col in c3.TEXT_COLUMNS:
        feats[col] = np.where(rng.uniform(size=len(top)) < 0.5, 0.0, rng.integers(1, 6, len(top)).astype(float))
    feats.loc[feats["date"] < days[min(5, weeks - 1)], "attn_abn"] = np.nan
    fwd = top[["date", "symbol"]].copy()
    fwd[c3.TARGET] = 1e-3 * np.exp(0.8 * h + 0.6 * u + signal * feats["evt_7d"].to_numpy())
    for col in c3.TAILS:
        fwd[col] = np.abs(rng.normal(size=len(top))) * np.sqrt(fwd[c3.TARGET])
    fwd["fwd_bars"] = 7
    fwd = fwd[rng.uniform(size=len(fwd)) > 0.01].reset_index(drop=True)
    return top, feats, hist, fwd


def _records() -> pd.DataFrame:
    """A small record table (20 agreed records and one unresolved) for the extraction-quality block."""
    fields = schema.FIELDS[:-1]
    first = ("subject", "other", "occurred", "neutral", 1)
    rows = [{"doc_id": f"d{i}", "base": "S00", "alias": "Asset_A", "focus_only": False, "resolution": "agreed",
             **dict(zip(fields, first)), "evidence": "x", **{f"a_{f}": v for f, v in zip(fields, first)},
             **{f"b_{f}": v for f, v in zip(fields, ("subject", "other", "occurred", "neutral", 2))}} for i in range(20)]
    rows.append({**rows[0], "doc_id": "u", "resolution": "unresolved", **dict.fromkeys(schema.FIELDS),
                 **{f"a_{f}": None for f in fields}, **{f"b_{f}": None for f in fields}})
    return consensus.record_frame(rows)


def _bars(n: int = 120, seed: int = 0, start: str = "2023-01-01", sigma: float = 0.03) -> pd.DataFrame:
    """Daily bars in the form of the kline store (2023-01-01 is a Sunday)."""
    rng = np.random.default_rng(seed)
    days = pd.date_range(start, periods=n, freq="D", tz="UTC")
    close = 100.0 * np.exp(np.cumsum(sigma * rng.normal(size=n)))
    open_ = np.concatenate([[100.0], close[:-1]])
    high = np.maximum(open_, close) * np.exp(sigma * np.abs(rng.normal(size=n)) / 2)
    low = np.minimum(open_, close) * np.exp(-sigma * np.abs(rng.normal(size=n)) / 2)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close,
                         "quote_volume": 1e6 * np.exp(rng.normal(size=n))}, index=pd.Index(days, name="ts"))


def _gk(bars: pd.DataFrame) -> pd.Series:
    """The Garman-Klass variance written out directly."""
    return 0.5 * np.log(bars["high"] / bars["low"]) ** 2 - (2 * np.log(2) - 1) * np.log(bars["close"] / bars["open"]) ** 2


def _day(text: str) -> pd.Timestamp:
    return pd.Timestamp(text, tz="UTC")


def _keys(days, symbol: str = "AAAUSDT") -> pd.DataFrame:
    return pd.DataFrame({"date": pd.DatetimeIndex(days), "symbol": symbol})


def _gate(panel: pd.DataFrame, name: str | None = None) -> tuple[dict, dict]:
    """(verdict, gate statistics) of an assembled panel, one partial score only (the gate score by default)."""
    feats, controls, squares, flexible = c3.PARTIAL_SCORES[name or c3.GATE_SCORE]
    score, resid, _, _ = c3.partial_score(panel, feats, controls, squares, flexible)
    gates, ic = c3.gate_statistics(c3._dates(panel), score, resid)
    return c3.build_verdict({"gates": gates, "weeks": {"test": int(len(ic))}}, {}), gates


def _evaluation(t=2.5, mean=0.05, y2023=0.01, y2024=0.02, **extra) -> dict:
    return {"gates": {"reader_partial_ic": {"weeks": 104, "mean": mean, "nw_t": t},
                      "reader_partial_ic_by_year": {"2023": {"weeks": 52, "mean": y2023}, "2024": {"weeks": 52, "mean": y2024}}},
            "weeks": {"test": 104}, **extra}


def _verdict(**kwargs) -> dict:
    return c3.build_verdict(_evaluation(**kwargs), {})


# ---------------------------------------------------------------- daily bars
def test_garman_klass_variance_of_a_bar():
    bars = pd.DataFrame({"open": [100.0, 100.0, 0.0, 100.0, 100.0], "high": [110.0, 100.0, 110.0, 101.0, np.nan],
                         "low": [95.0, 100.0, 95.0, 99.0, 95.0], "close": [105.0, 100.0, 105.0, 120.0, 105.0],
                         "quote_volume": 1.0}, index=pd.date_range("2023-01-01", periods=5, freq="D", tz="UTC"))
    gk = c3.gk_variance(bars)
    assert gk.iloc[0] == pytest.approx(0.5 * np.log(110 / 95) ** 2 - (2 * np.log(2) - 1) * np.log(1.05) ** 2)
    assert gk.iloc[1] == 0.0                                    # a flat bar
    assert np.isnan(gk.iloc[2]) and np.isnan(gk.iloc[4])        # a bar without four positive prices is missing
    assert gk.iloc[3] == 0.0                                    # close outside the range: negative value set to zero
    good = _bars(40)
    assert np.allclose(c3.gk_variance(good).to_numpy(), _gk(good).to_numpy()) and (c3.gk_variance(good) > 0).all()


def test_bar_history_values():
    bars = _bars(120)
    hist, gk, k = c3.bar_history(bars), _gk(bars), 100
    assert list(hist.columns) == c3.HIST_BARS and hist.index.equals(bars.index)
    row, close, volume = hist.iloc[k], bars["close"], bars["quote_volume"]
    assert row["rv_1d"] == pytest.approx(gk.iloc[k])
    assert row["rv_7d"] == pytest.approx(gk.iloc[k - 6:k + 1].mean()) and row["rv_max_7d"] == pytest.approx(gk.iloc[k - 6:k + 1].max())
    assert row["rv_30d"] == pytest.approx(gk.iloc[k - 29:k + 1].mean()) and row["rv_90d"] == pytest.approx(gk.iloc[k - 89:k + 1].mean())
    assert row["ret_7d"] == pytest.approx(np.log(close.iloc[k] / close.iloc[k - 7])) and row["absret_7d"] == abs(row["ret_7d"])
    assert row["vsurge_7d"] == pytest.approx(np.log(volume.iloc[k - 6:k + 1].mean() / volume.iloc[k - 29:k + 1].mean()))


def test_bar_history_uses_the_bars_up_to_the_row_only():
    bars = _bars(120)
    full = c3.bar_history(bars)
    for k in (12, 75, 119):
        pd.testing.assert_series_equal(c3.bar_history(bars.iloc[:k + 1]).iloc[-1], full.iloc[k])
    later = bars.copy()
    later.iloc[76:] = later.iloc[76:] * 3.0 + 1.0
    pd.testing.assert_frame_equal(c3.bar_history(later).iloc[:76], full.iloc[:76])
    assert not np.allclose(c3.bar_history(later).iloc[76:].to_numpy(), full.iloc[76:].to_numpy())


def test_bar_history_needs_a_minimum_of_bars():
    hist = c3.bar_history(_bars(12))
    assert hist["rv_7d"].isna().tolist() == [True] * 3 + [False] * 9             # four bars in the 7-day window
    assert hist["rv_max_7d"].isna().tolist() == [True] * 3 + [False] * 9
    assert hist["rv_30d"].isna().tolist() == [True] * 9 + [False] * 3            # ten bars in the longer windows
    assert hist["rv_90d"].isna().tolist() == [True] * 9 + [False] * 3 and hist["vsurge_7d"].isna().tolist() == [True] * 9 + [False] * 3
    assert hist["ret_7d"].isna().tolist() == [True] * 7 + [False] * 5 and hist["rv_1d"].notna().all()
    gaps = _bars(40).drop(index=[_day("2023-01-20"), _day("2023-01-21"), _day("2023-01-22"), _day("2023-01-23")])
    hist = c3.bar_history(gaps)
    assert np.isnan(hist.loc[_day("2023-01-26"), "rv_7d"])                        # three bars left in the window
    assert np.isfinite(hist.loc[_day("2023-01-27"), "rv_7d"])
    assert np.isnan(hist.loc[_day("2023-01-27"), "ret_7d"])                       # no bar seven days earlier
    broken = _bars(40)
    broken.loc[_day("2023-01-20"):_day("2023-01-23"), "low"] = 0.0                # four bars without a usable range
    assert np.isnan(c3.bar_history(broken).loc[_day("2023-01-26"), "rv_7d"])


def test_history_features_read_the_friday_row_of_every_universe_row(tmp_path):
    bars, other = _bars(120), _bars(120, seed=1).drop(index=[_day("2023-03-10")])
    bars.to_parquet(tmp_path / "AAAUSDT.parquet")
    other.to_parquet(tmp_path / "BBBUSDT.parquet")
    fridays = pd.date_range("2023-02-03", "2023-03-31", freq="7D", tz="UTC")
    keys = pd.concat([_keys(fridays), _keys(fridays[2:], "BBBUSDT")]).sample(frac=1.0, random_state=0)
    hist = c3.history_features(tmp_path, keys)
    assert list(hist.columns) == ["date", "symbol", *c3.HIST_BARS] and len(hist) == len(keys) == 16
    got = hist.set_index(["symbol", "date"])
    want = c3.bar_history(bars)
    for f in fridays:
        assert np.allclose(got.loc[("AAAUSDT", f)].to_numpy(dtype=float), want.loc[f].to_numpy(dtype=float))
    assert got.loc[("BBBUSDT", _day("2023-03-10"))].isna().all()                  # no Friday bar: every feature missing
    week_after = got.loc[("BBBUSDT", _day("2023-03-17"))]                         # the 7-day return starts at the missing bar
    assert week_after[["ret_7d", "absret_7d"]].isna().all() and week_after.drop(["ret_7d", "absret_7d"]).notna().all()
    assert got.loc[("BBBUSDT", _day("2023-03-24"))].notna().all()
    bars.iloc[:95].to_parquet(tmp_path / "AAAUSDT.parquet")                       # the store ends after the last decision
    again = c3.history_features(tmp_path, keys).set_index(["symbol", "date"])
    pd.testing.assert_frame_equal(again, got)
    twice = pd.concat([bars, bars.iloc[:1]])
    twice.to_parquet(tmp_path / "AAAUSDT.parquet")
    with pytest.raises(ValueError, match="duplicate bars"):
        c3.history_features(tmp_path, keys)


def test_forward_week_is_the_seven_bars_after_the_friday_bar(tmp_path):
    bars = _bars(120)
    bars.to_parquet(tmp_path / "AAAUSDT.parquet")
    fridays = pd.date_range("2023-01-13", "2023-04-14", freq="7D", tz="UTC")
    fwd = c3.forward_targets(tmp_path, _keys(fridays))
    assert list(fwd.columns) == ["date", "symbol", *c3.TARGET_COLUMNS] and len(fwd) == len(fridays)
    fwd, hist, gk = fwd.set_index("date"), c3.bar_history(bars), _gk(bars)
    for f in fridays:
        week = gk[f + DAY:f + WEEK]
        assert len(week) == 7 and fwd.loc[f, "fwd_bars"] == 7
        assert fwd.loc[f, "fwd_rv"] == pytest.approx(week.mean()) and fwd.loc[f, "fwd_maxday"] == pytest.approx(week.max())
        assert fwd.loc[f, "fwd_rv"] == pytest.approx(hist.loc[f + WEEK, "rv_7d"])  # the target of one week is the history of the next
        assert fwd.loc[f, "fwd_absret"] == pytest.approx(abs(np.log(bars.loc[f + WEEK, "close"] / bars.loc[f, "close"])))
        assert fwd.loc[f, "fwd_drawdown"] == pytest.approx(-np.log(bars.loc[f + DAY:f + WEEK, "low"].min() / bars.loc[f, "close"]))


def test_forward_targets_use_no_bar_up_to_the_decision_and_none_after_the_week(tmp_path):
    bars, f = _bars(120), _day("2023-02-10")
    bars.to_parquet(tmp_path / "AAAUSDT.parquet")
    base = c3.forward_targets(tmp_path, _keys([f]))
    outside = bars.copy()
    outside.loc[:f - DAY] = outside.loc[:f - DAY] * 2.0 + 5.0                     # every bar before the Friday bar
    outside.loc[f, ["open", "high", "low", "quote_volume"]] *= 1.5                # the Friday bar except its close (the start price)
    outside.loc[f + WEEK + DAY:] = outside.loc[f + WEEK + DAY:] * 0.5 + 1.0       # every bar after the week
    outside.to_parquet(tmp_path / "AAAUSDT.parquet")
    pd.testing.assert_frame_equal(c3.forward_targets(tmp_path, _keys([f])), base)
    for day in (f + DAY, f + WEEK):                                              # the first and the last bar of the week count
        inside = bars.copy()
        inside.loc[day, "high"] *= 1.2
        inside.to_parquet(tmp_path / "AAAUSDT.parquet")
        assert c3.forward_targets(tmp_path, _keys([f]))["fwd_rv"].iloc[0] > base["fwd_rv"].iloc[0]
    hist = c3.history_features(tmp_path, _keys([f]))
    later = bars.copy()
    later.loc[f + DAY:] = later.loc[f + DAY:] * 3.0 + 1.0                         # the history of a row ends at its Friday bar
    later.to_parquet(tmp_path / "AAAUSDT.parquet")
    pd.testing.assert_frame_equal(c3.history_features(tmp_path, _keys([f])), hist)


def test_forward_targets_of_short_and_missing_weeks(tmp_path):
    bars = _bars(120)                                                            # last bar 2023-04-30, a Sunday
    bars.drop(index=[_day("2023-03-10")]).to_parquet(tmp_path / "AAAUSDT.parquet")
    fridays = [_day("2023-03-03"), _day("2023-03-10"), _day("2023-04-21"), _day("2023-04-28"), _day("2023-05-05")]
    fwd = c3.forward_targets(tmp_path, _keys(fridays)).set_index("date")
    assert list(fwd.index) == fridays[:4]                                        # no bar after the last Friday: no row
    assert fwd["fwd_bars"].tolist() == [6, 7, 7, 2]
    gk = _gk(bars)
    assert fwd.loc[fridays[0], "fwd_rv"] == pytest.approx(gk[_day("2023-03-04"):_day("2023-03-09")].mean())
    assert fwd.loc[fridays[3], "fwd_rv"] == pytest.approx(gk[_day("2023-04-29"):].mean())
    assert np.isfinite(fwd.loc[fridays[1], "fwd_rv"])                            # without the Friday bar there is no start price
    assert fwd.loc[fridays[1], ["fwd_absret", "fwd_drawdown"]].isna().all()
    assert fwd.loc[fridays[3], "fwd_absret"] == pytest.approx(abs(np.log(bars["close"].iloc[-1] / bars.loc[fridays[3], "close"])))


# ---------------------------------------------------------------- reader features
def _block_v_extra():
    sets, records = _block_b_case()
    more = [_reading_row("o3", 2 * DAY, "analysis_opinion"), _reading_row("o4", 4 * DAY, "analysis_opinion"),
            _reading_row("r1", 5 * DAY), _reading_row("r2", 5 * DAY), _reading_row("r3", 12 * DAY)]
    extra = [_record_row("o3", "opinion_or_forecast", "occurred", "unfavourable", 3),
             _record_row("o4", "opinion_or_forecast", "occurred", "favourable", 1),
             _record_row("r1", "partnership_or_integration", "proposed_or_rumoured", "favourable", 2),
             _record_row("r2", "partnership_or_integration", "proposed_or_rumoured", "favourable", 1),      # repeats r1
             _record_row("r3", "exchange_listing", "proposed_or_rumoured", "neutral", 3)]
    extra = consensus.record_frame([{**dict.fromkeys(consensus.RECORD_COLUMNS), **r} for r in extra])
    return pd.concat([sets, pd.DataFrame(more)], ignore_index=True), pd.concat([records, extra], ignore_index=True)


def test_block_v_sums_and_deduplication():
    sets, records = _block_b_case()
    out = c3.block_v(sets, records).set_index(["date", "base"])
    assert list(out.columns) == [*c3.BLOCK_V, *c3.COUNTS]
    assert out.loc[(FRIDAY, "AAA")].to_dict() == {
        "evt_7d": 5.0,            # 3 (e1 and e2 once, at the higher materiality) + 1 (e6, mixed) + 1 (e3); no sign
        "evt_30d": 4.0,           # 2 (e5, exactly 7 days old) + 2 (e4)
        "unfav_7d": 3.0,
        "sched_30d": 2.0,         # e4
        "rumour_30d": 0.0,        # o2 is an opinion
        "split_7d": 0.0,          # one recent opinion, one side only
        "n_subject_7d": 5.0, "n_subject_30d": 8.0}
    other = out.loc[(FRIDAY, "BBB")]
    assert other["evt_7d"] == 3.0 and other["n_subject_7d"] == 1.0 and other["n_subject_30d"] == 1.0
    assert other.drop(["evt_7d", "n_subject_7d", "n_subject_30d"]).eq(0.0).all()
    assert out.loc[(FRIDAY, "AAA"), "unfav_7d"] == features.block_b(sets, records).set_index(["date", "base"]).loc[(FRIDAY, "AAA"), "unfav_7d"]


def test_block_v_disagreement_and_unconfirmed_events():
    sets, records = _block_v_extra()
    out = c3.block_v(sets, records).set_index(["date", "base"]).loc[(FRIDAY, "AAA")]
    assert out.to_dict() == {
        "evt_7d": 7.0,            # + 2 (r1 and r2 once)
        "evt_30d": 7.0,           # + 3 (r3)
        "unfav_7d": 3.0,
        "sched_30d": 2.0,
        "rumour_30d": 5.0,        # 2 (r1, r2) + 3 (r3): proposed or rumoured events of the 30 days
        "split_7d": 1.0,          # recent opinions: two favourable (o1, o4), one unfavourable (o3)
        "n_subject_7d": 9.0, "n_subject_30d": 13.0}


def test_block_v_without_opinions_or_events():
    sets, records = _block_b_case()
    events = c3.block_v(sets[sets["type"] == "event"], records).set_index(["date", "base"])
    assert events.loc[(FRIDAY, "AAA"), "evt_7d"] == 5.0 and events["split_7d"].eq(0.0).all()
    opinions = c3.block_v(sets[sets["type"] != "event"], records).set_index(["date", "base"])
    assert list(opinions.index) == [(FRIDAY, "AAA")]
    assert opinions.loc[(FRIDAY, "AAA")].to_dict() == {**dict.fromkeys(c3.BLOCK_V, 0.0), "n_subject_7d": 1.0, "n_subject_30d": 2.0}


def test_text_features_of_a_store_agree_with_charter_2(tmp_path, monkeypatch):
    items, docs, cards = store_frames(weeks=8, n_syms=8, docs_per_week=12)
    top = c2.universe(cards)
    sets, work = c2.reading(items, docs, top)
    _, unit_list = rx.build_units(items, docs, cards)
    reader = Reader(FakeClient(), CallCache(tmp_path / "calls.jsonl"))
    records = consensus.record_frame([row for unit in unit_list for row in consensus.resolve(reader, unit)])
    feats = c3.text_features(items, sets, records, top)
    assert list(feats.columns) == ["date", "symbol", "base", *c3.TEXT_COLUMNS] and len(feats) == len(top) == 64
    assert not feats[["date", "symbol"]].duplicated().any()
    old = c2.text_features(items, sets, records, top)
    for col in [*c3.BLOCK_A, "unfav_7d", *c3.COUNTS]:
        assert np.array_equal(feats[col].to_numpy(dtype=float), old[col].to_numpy(dtype=float), equal_nan=True)
    values = feats[[*c3.BLOCK_V, *c3.COUNTS]]
    assert values.notna().all().all() and (values >= 0).all().all() and (values["evt_7d"] > 0).any()
    assert (feats["unfav_7d"] <= feats["evt_7d"]).all() and (feats["sched_30d"] + feats["rumour_30d"] <= feats["evt_7d"] + feats["evt_30d"]).all()
    assert (2 * feats["split_7d"] <= feats["n_subject_7d"]).all()
    pd.testing.assert_frame_equal(c3.text_features(items, sets, records.sample(frac=1.0, random_state=2), top), feats)
    with pytest.raises(ValueError, match="differ"):
        c3.text_features(items, sets, records.iloc[1:], top)                     # the work-list check of Charter 2
    real = c3.block_v
    monkeypatch.setattr(c3, "block_v", lambda reading, recs: real(reading, recs).assign(unfav_7d=lambda t: t["unfav_7d"] + 1.0))
    with pytest.raises(ValueError, match="unfav_7d differs from the Charter 2 feature"):
        c3.text_features(items, sets, records, top)


# ---------------------------------------------------------------- panel
def test_registered_feature_sets():
    assert c3.HIST == ["rv_1d", "rv_7d", "rv_30d", "rv_90d", "rv_max_7d", "absret_7d", "ret_7d", "vsurge_7d",
                       "vol_ewma20", "dvol_30d", "age_weeks", "abs_funding_3d"]
    assert c3.BLOCK_A == ["attn_7d", "attn_abn"]
    assert c3.BLOCK_V == ["evt_7d", "evt_30d", "unfav_7d", "sched_30d", "rumour_30d", "split_7d"]
    assert c3.PARTIAL_SCORES[c3.GATE_SCORE] == (c3.BLOCK_V, c3.HIST + c3.BLOCK_A, (), True) and c3.GATE_SCORE == "s_reader"
    assert c3.PARTIAL_SCORES["s_reader_lin"] == (c3.BLOCK_V, c3.HIST + c3.BLOCK_A, (), False)     # the first design, descriptive
    assert c3.PARTIAL_SCORES["s_reader_sq"] == (c3.BLOCK_V, c3.HIST + c3.BLOCK_A, tuple(c3.HIST_BARS), False)
    assert {n for n, (_, _, _, flexible) in c3.PARTIAL_SCORES.items() if not flexible} == {"s_reader_lin", "s_reader_sq"}
    assert (c3.CLEAN_FIRST, c3.CLEAN_EVERY, c3.CLEAN_ROUNDS, c3.CLEAN_ALPHA) == (26, 13, 300, 1.0) and c3.CLEAN_FIRST <= BURN_IN_WEEKS
    assert c3.CLEAN_PARAMS == {**model.GBM_PARAMS, "learning_rate": 0.05, "num_leaves": 8, "max_depth": 3, "min_data_in_leaf": 50}
    assert c3.TARGET == "fwd_rv" and (c3.GATE_T, c3.GATE_YEARS, c3.SIZE_VISIBLE, c3.MIN_WEEK_ROWS) == (2.0, (2023, 2024), 0.07, 30)
    assert not set(c3.HIST) & set(c3.TEXT_COLUMNS) and not set(c3.TARGET_COLUMNS) & set(c3.HIST + c3.TEXT_COLUMNS)
    used = {c for feats, controls, squares, _ in c3.PARTIAL_SCORES.values() for c in (*feats, *controls, *squares)}
    used |= {c for cols in (*c3.FORECASTS.values(), *c3.GBM_FORECASTS.values()) for c in cols}
    assert used == set(c3.HIST + c3.BLOCK_A + c3.BLOCK_V)                         # no outcome column and no count enters a fit
    assert set(c3.CARD_COLUMNS) <= set(c2.QUANT) | set(c2.CONTROLS)


def test_panel_joins_one_row_per_universe_row():
    top, feats, hist, fwd = synth(0.0, weeks=8, n=6)
    panel = c3.assemble_panel(top.sample(frac=1.0, random_state=1), feats, hist.sample(frac=1.0, random_state=2), fwd)
    assert list(panel.columns) == c3.PANEL_COLUMNS and len(panel) == len(top) == 48
    assert panel[["date", "symbol"]].equals(panel[["date", "symbol"]].sort_values(["date", "symbol"]).reset_index(drop=True))
    assert str(panel["date"].dt.tz) == "UTC"
    key = ["date", "symbol"]
    want = top.merge(fwd, on=key, how="left").merge(hist, on=key).merge(feats, on=[*key, "base"]).sort_values(key)
    for col in (c3.TARGET, "fwd_bars", "rv_7d", "rv_90d", "evt_7d", "attn_abn", "vol_ewma20"):
        assert np.allclose(panel[col].to_numpy(dtype=float), want[col].to_numpy(dtype=float), equal_nan=True), col
    assert np.allclose(panel["abs_funding_3d"].to_numpy(), want["funding_3d"].abs().to_numpy()) and (panel["abs_funding_3d"] >= 0).all()
    assert int(panel[c3.TARGET].isna().sum()) == len(top) - len(fwd) > 0         # a missing outcome stays missing
    assert panel["attn_abn"].isna().any()                                        # allowed: short own history


def test_panel_refuses_incomplete_or_duplicated_inputs():
    top, feats, hist, fwd = synth(0.0, weeks=8, n=6)
    with pytest.raises(ValueError, match="not unique"):
        c3.assemble_panel(pd.concat([top, top.iloc[:1]]), feats, hist, fwd)
    with pytest.raises(ValueError, match="without text features"):
        c3.assemble_panel(top, feats.iloc[1:], hist, fwd)
    with pytest.raises(ValueError, match="without bar history"):
        c3.assemble_panel(top, feats, hist.iloc[1:], fwd)
    broken = feats.copy()
    broken.loc[broken.index[3], "evt_7d"] = np.nan
    with pytest.raises(ValueError, match="missing values"):
        c3.assemble_panel(top, broken, hist, fwd)
    for frames in ((pd.concat([feats, feats.iloc[:1]]), hist, fwd), (feats, pd.concat([hist, hist.iloc[:1]]), fwd),
                   (feats, hist, pd.concat([fwd, fwd.iloc[:1]]))):
        with pytest.raises(pd.errors.MergeError):
            c3.assemble_panel(top, *frames)


# ---------------------------------------------------------------- ranks, residuals, walk-forward
def test_target_rank_is_within_the_week_and_missing_stays_missing():
    panel = pd.DataFrame({"date": [_day("2023-01-06")] * 4 + [_day("2023-01-13")] * 3,
                          c3.TARGET: [4.0, 1.0, np.nan, 2.0, 5.0, 50.0, 0.5], "x": [1.0, np.nan, 3.0, 2.0, 1.0, 1.0, 9.0]})
    assert np.allclose(c3.target_rank(panel), [1 / 2, -1 / 6, np.nan, 1 / 6, 1 / 6, 1 / 2, -1 / 6], equal_nan=True)
    assert np.allclose(c3.feature_ranks(panel, ["x"])[:, 0], [-1 / 6, 0.0, 1 / 2, 1 / 6, 0.0, 0.0, 1 / 2])     # missing: neutral
    logs = c3.log_target(panel)
    week = np.log([4.0, 1.0, 2.0])
    assert np.allclose(logs[[0, 1, 3]], (week - week.mean()) / week.std(ddof=1)) and np.isnan(logs[2])
    zero = panel.assign(**{c3.TARGET: [0.0, 1e-12, 1.0, 2.0, 1.0, 2.0, 3.0]})
    assert c3.log_target(zero)[0] == c3.log_target(zero)[1]                       # floor of the log target


def test_residuals_are_orthogonal_to_the_controls_within_every_week():
    rng = np.random.default_rng(0)
    dates = np.repeat(np.arange(5), 40)
    controls = rng.normal(size=(200, 3))
    values = rng.normal(size=(200, 2)) + controls @ rng.normal(size=(3, 2)) + dates[:, None]
    values[::17, 1] = np.nan
    out = c3.residuals(values, controls, dates)
    assert np.array_equal(np.isnan(out), np.isnan(values))
    for d in range(5):
        idx = np.flatnonzero(dates == d)
        for j in range(2):
            have = np.isfinite(values[idx, j])
            r = out[idx, j][have]
            assert abs(r.sum()) < 1e-9 and np.abs(controls[idx][have].T @ r).max() < 1e-9
    design = np.column_stack([np.ones(40), controls[:40]])                       # the first week written out
    beta = np.linalg.lstsq(design, values[:40, 0], rcond=None)[0]
    assert np.allclose(out[:40, 0], values[:40, 0] - design @ beta)
    short = values.copy()
    short[np.flatnonzero(dates == 2)[:11], 0] = np.nan                           # 29 rows left in the third week
    out = c3.residuals(short, controls, dates)
    assert np.isnan(out[dates == 2, 0]).all() and np.isfinite(out[dates != 2, 0]).all()
    assert np.isfinite(c3.residuals(short, controls, dates, min_rows=29)[np.flatnonzero(dates == 2)[11:], 0]).all()


def test_control_matrix_adds_the_squared_ranks():
    top, feats, hist, fwd = synth(0.0, weeks=4, n=40)
    panel = c3.assemble_panel(top, feats, hist, fwd)
    plain = c3.control_matrix(panel, ["rv_7d", "evt_7d"])
    assert np.array_equal(plain, c3.feature_ranks(panel, ["rv_7d", "evt_7d"]))
    squared = c3.control_matrix(panel, ["rv_7d", "evt_7d"], ("rv_7d",))
    assert squared.shape == (160, 3) and np.array_equal(squared[:, 2], plain[:, 0] ** 2)


def _weekly_arrays(weeks: int = 12, n: int = 10, k: int = 3, seed: int = 0):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2022-01-07", periods=weeks, freq="7D", tz="UTC")
    dates = np.repeat(days.as_unit("ns").asi8, n)
    X = rng.normal(size=(weeks * n, k))
    return X, X @ np.array([0.5, -0.2, 0.0][:k]) + rng.normal(size=weeks * n), dates, np.unique(dates)


def test_walk_forward_equals_a_ridge_fit_on_the_earlier_weeks():
    X, y, dates, weeks = _weekly_arrays()
    score, info = c3.walk_forward(X, y, dates, burn_in=3)
    assert np.isnan(score[np.isin(dates, weeks[:3])]).all() and np.isfinite(score[np.isin(dates, weeks[3:])]).all()
    assert list(info) == [pd.Timestamp(int(d), tz="UTC") for d in weeks[3:]]
    for i in (3, 7, 11):
        train = np.isin(dates, weeks[:i])
        beta = np.linalg.solve(X[train].T @ X[train] + RIDGE_ALPHA * np.eye(3), X[train].T @ y[train])
        assert np.allclose(score[dates == weeks[i]], X[dates == weeks[i]] @ beta)
        assert np.allclose(info[pd.Timestamp(int(weeks[i]), tz="UTC")], beta)
    assert np.isnan(c3.walk_forward(X, y, dates)[0]).all()                       # the registered burn-in is longer than the sample


def test_walk_forward_does_not_use_the_own_week_or_a_later_one():
    X, y, dates, weeks = _weekly_arrays()
    score, _ = c3.walk_forward(X, y, dates, burn_in=3)
    late = np.isin(dates, weeks[7:])
    other_y = np.where(late, y[::-1] * 5.0, y)
    changed, _ = c3.walk_forward(X, other_y, dates, burn_in=3)
    assert np.array_equal(changed[np.isin(dates, weeks[:8])], score[np.isin(dates, weeks[:8])], equal_nan=True)     # week 7 does not see its own outcome
    assert not np.allclose(changed[np.isin(dates, weeks[8:])], score[np.isin(dates, weeks[8:])])
    other_X = np.where(late[:, None], X[::-1], X)
    changed, _ = c3.walk_forward(other_X, y, dates, burn_in=3)
    assert np.array_equal(changed[~late], score[~late], equal_nan=True)


def test_walk_forward_rows_without_outcome_or_features():
    X, y, dates, weeks = _weekly_arrays()
    y[np.flatnonzero(dates == weeks[5])[:4]] = np.nan                            # scored, left out of the training
    X[np.flatnonzero(dates == weeks[6])[0], 1] = np.nan                          # neither scored nor used
    score, _ = c3.walk_forward(X, y, dates, burn_in=3)
    assert np.isfinite(score[dates == weeks[5]]).all()
    assert np.isnan(score[np.flatnonzero(dates == weeks[6])[0]]) and np.isfinite(score[np.flatnonzero(dates == weeks[6])[1:]]).all()
    train = np.isin(dates, weeks[:9]) & np.isfinite(y) & np.isfinite(X).all(axis=1)
    beta = np.linalg.solve(X[train].T @ X[train] + RIDGE_ALPHA * np.eye(3), X[train].T @ y[train])
    assert np.allclose(score[dates == weeks[9]], X[dates == weeks[9]] @ beta)
    daily = dates.copy()
    daily[dates == weeks[4]] = weeks[5] - pd.Timedelta(days=3).value             # an outcome that is not realised by the next Friday
    late, _ = c3.walk_forward(X, y, daily, burn_in=3)
    train = np.isin(dates, weeks[:4]) & np.isfinite(y)
    beta = np.linalg.solve(X[train].T @ X[train] + RIDGE_ALPHA * np.eye(3), X[train].T @ y[train])
    assert np.allclose(late[dates == weeks[5]], X[dates == weeks[5]] @ beta)


# ---------------------------------------------------------------- flexible step (fitted on earlier weeks)
def _clean_arrays(weeks: int = 60, n: int = 30, k: int = 3, cols: int = 2, seed: int = 0):
    """(values, controls, dates, week position) with a curved relation of the values to the first control."""
    rng = np.random.default_rng(seed)
    days = pd.date_range("2022-01-07", periods=weeks, freq="7D", tz="UTC")
    dates = np.repeat(days.as_unit("ns").asi8, n)
    controls = rng.uniform(-0.5, 0.5, size=(weeks * n, k))
    values = 4.0 * controls[:, :1] ** 2 + rng.normal(scale=0.3, size=(weeks * n, cols))
    return values, controls, dates, np.searchsorted(np.unique(dates), dates)


def _booster(values: np.ndarray, controls: np.ndarray, rows: np.ndarray):
    import lightgbm as lgb
    return lgb.train(dict(c3.CLEAN_PARAMS), lgb.Dataset(controls[rows], label=values[rows]), num_boost_round=c3.CLEAN_ROUNDS)


def test_past_trees_are_fitted_on_the_earlier_weeks_only(monkeypatch):
    monkeypatch.setattr(c3, "CLEAN_ROUNDS", 20)
    values, controls, dates, widx = _clean_arrays()
    out = c3.past_trees(values, controls, dates)
    assert out.shape == values.shape and np.isfinite(out).all()
    served = {0: 26, 25: 26, 26: 26, 38: 26, 39: 39, 51: 39, 52: 52, 59: 52}       # week -> weeks before the fit that serves it
    for week, before in served.items():
        rows = widx == week
        for j in range(2):
            want = values[rows, j] - _booster(values[:, j], controls, widx < before).predict(controls[rows])
            assert np.allclose(out[rows, j], want), (week, j)
    other = values.copy()
    other[widx == 45] += 1.0
    changed = c3.past_trees(other, controls, dates)
    assert np.array_equal(changed[widx < 45], out[widx < 45])
    assert np.allclose(changed[widx == 45], out[widx == 45] + 1.0)               # a week is not in the fit that serves it
    assert np.array_equal(changed[(widx > 45) & (widx < 52)], out[(widx > 45) & (widx < 52)])
    assert not np.allclose(changed[widx >= 52], out[widx >= 52])                 # the refit of week 52 has seen week 45
    moved = controls.copy()
    moved[widx == 45] = moved[widx == 45][::-1]
    changed = c3.past_trees(values, moved, dates)
    assert np.array_equal(changed[widx < 45], out[widx < 45])                    # nor do its controls reach an earlier week
    assert np.array_equal(changed[(widx > 45) & (widx < 52)], out[(widx > 45) & (widx < 52)])


def test_past_trees_of_a_short_panel_and_of_broken_inputs(monkeypatch):
    monkeypatch.setattr(c3, "CLEAN_ROUNDS", 20)
    values, controls, dates, widx = _clean_arrays()
    short = widx < 10                                                            # fewer weeks than the first fit: fitted on themselves
    out = c3.past_trees(values[short], controls[short], dates[short])
    everything = np.ones(int(short.sum()), dtype=bool)
    want = values[short, 0] - _booster(values[short, 0], controls[short], everything).predict(controls[short])
    assert np.allclose(out[:, 0], want)
    for broken in ("values", "controls"):
        arrays = {"values": values.copy(), "controls": controls.copy()}
        arrays[broken][3, 0] = np.nan
        with pytest.raises(ValueError, match="missing value in a rank"):
            c3.past_trees(arrays["values"], arrays["controls"], dates)
    daily = dates.copy()
    daily[widx == 4] = np.unique(dates)[5] - pd.Timedelta(days=3).value          # an outcome not realised by the next week
    with pytest.raises(ValueError, match="closer than the forward horizon"):
        c3.past_trees(values, controls, daily)
    with pytest.raises(ValueError, match="closer than the forward horizon"):
        c3.past_surface(values[:, 0], controls, daily)


def test_quadratic_basis_columns():
    rng = np.random.default_rng(0)
    c = rng.uniform(-0.5, 0.5, size=(7, 3))
    basis = c3.quadratic_basis(c)
    assert basis.shape == (7, 10)
    assert np.array_equal(basis[:, 0], np.ones(7)) and np.array_equal(basis[:, 1:4], c)
    assert np.allclose(basis[:, 4:7], c ** 2 - 1.0 / 12.0)                       # centred for a uniform rank
    assert np.allclose(basis[:, 7:], np.column_stack([c[:, 0] * c[:, 1], c[:, 0] * c[:, 2], c[:, 1] * c[:, 2]]))
    registered = len(c3.PARTIAL_SCORES[c3.GATE_SCORE][1])
    assert registered == 14 and c3.quadratic_basis(np.zeros((2, registered))).shape == (2, 120)


def _surface(values: np.ndarray, controls: np.ndarray, rows: np.ndarray) -> np.ndarray:
    """The quadratic surface of the rows, as penalised least squares written out (intercept free)."""
    basis = c3.quadratic_basis(controls)
    rows = rows & np.isfinite(values)
    k = basis.shape[1]
    stacked = np.vstack([basis[rows], np.sqrt(c3.CLEAN_ALPHA) * np.eye(k)[1:]])
    beta = np.linalg.lstsq(stacked, np.concatenate([values[rows], np.zeros(k - 1)]), rcond=None)[0]
    return basis @ beta


def test_past_surface_is_a_ridge_fit_on_the_earlier_weeks():
    values, controls, dates, widx = _clean_arrays(weeks=40)
    y = values[:, 0].copy()
    y[::13] = np.nan
    out = c3.past_surface(y, controls, dates)
    assert np.array_equal(np.isnan(out), np.isnan(y))                            # missing stays missing
    for week, before in {0: 26, 25: 26, 26: 26, 27: 27, 39: 39}.items():
        rows = (widx == week) & np.isfinite(y)
        assert np.allclose(out[rows], (y - _surface(y, controls, widx < before))[rows]), week
    head = widx < 26
    assert np.nanvar(out[head]) < 0.8 * np.nanvar(y[head]) and np.nanvar(out[~head]) < 0.8 * np.nanvar(y[~head])     # the curve is taken out
    other = y.copy()
    other[widx == 30] += 1.0
    changed = c3.past_surface(other, controls, dates)
    assert np.array_equal(changed[widx < 30], out[widx < 30], equal_nan=True)
    assert np.allclose(changed[widx == 30], out[widx == 30] + 1.0, equal_nan=True)     # a week is not in its own fit
    assert not np.allclose(changed[widx > 30], out[widx > 30], equal_nan=True)
    moved = controls.copy()
    moved[widx == 30] = moved[widx == 30][::-1]
    changed = c3.past_surface(y, moved, dates)
    assert np.array_equal(changed[widx < 30], out[widx < 30], equal_nan=True)


def test_past_surface_of_a_short_panel_and_without_earlier_rows():
    values, controls, dates, widx = _clean_arrays(weeks=40)
    y = values[:, 0].copy()
    short = widx < 10                                                            # fewer weeks than the first fit: fitted on themselves
    assert np.allclose(c3.past_surface(y[short], controls[short], dates[short]), (y - _surface(y, controls, short))[short])
    late = y.copy()
    late[widx < 27] = np.nan
    out = c3.past_surface(late, controls, dates)
    assert np.isnan(out[widx < 27]).all() and np.array_equal(out[widx == 27], late[widx == 27])     # nothing earlier: no surface
    assert np.allclose(out[widx == 28], (late - _surface(late, controls, widx == 27))[widx == 28])
    assert np.isnan(c3.past_surface(np.full(len(y), np.nan), controls, dates)).all()


# ---------------------------------------------------------------- partial score
def test_partial_score_is_the_walk_forward_fit_on_the_residuals(monkeypatch):
    monkeypatch.setattr(c3, "CLEAN_ROUNDS", 20)
    top, feats, hist, fwd = synth(0.1, weeks=60, n=40, seed=3)
    panel = c3.assemble_panel(top, feats, hist, fwd)
    reader, controls, squares, flexible = c3.PARTIAL_SCORES[c3.GATE_SCORE]
    assert flexible and squares == ()
    score, e, X, frame = c3.partial_score(panel, reader, controls, squares, flexible)
    dates, design = c3._dates(panel), c3.feature_ranks(panel, controls)
    y = c3.target_rank(panel)
    # the gate: a fit on the earlier weeks first, then the regression within the week, on both sides
    assert np.allclose(X, c3.residuals(c3.past_trees(c3.feature_ranks(panel, reader), design, dates), design, dates))
    assert np.allclose(e, c3.residuals(c3.past_surface(y, design, dates)[:, None], design, dates)[:, 0], equal_nan=True)
    assert np.array_equal(np.isnan(e), panel[c3.TARGET].isna().to_numpy())
    want, _ = c3.walk_forward(X, e, dates)
    assert np.allclose(score, want, equal_nan=True) and list(frame.columns) == reader and len(frame) == 60 - BURN_IN_WEEKS
    weeks = np.unique(dates)
    assert np.isnan(score[np.isin(dates, weeks[:BURN_IN_WEEKS])]).all() and np.isfinite(score[np.isin(dates, weeks[BURN_IN_WEEKS:])]).all()
    # the first design: the regression within the week alone
    lin_score, lin_e, lin_X, _ = c3.partial_score(panel, *c3.PARTIAL_SCORES["s_reader_lin"])
    assert np.allclose(lin_X, c3.residuals(c3.feature_ranks(panel, reader), design, dates))
    assert np.allclose(lin_e, c3.residuals(y[:, None], design, dates)[:, 0], equal_nan=True)
    assert np.allclose(lin_score, c3.walk_forward(lin_X, lin_e, dates)[0], equal_nan=True) and not np.allclose(lin_X, X)
    sq_score, sq_e, _, _ = c3.partial_score(panel, *c3.PARTIAL_SCORES["s_reader_sq"])
    wide = c3.control_matrix(panel, controls, tuple(c3.HIST_BARS))
    assert wide.shape[1] == len(controls) + len(c3.HIST_BARS)
    assert np.allclose(sq_e, c3.residuals(y[:, None], wide, dates)[:, 0], equal_nan=True)
    # another target takes the same two steps
    other, e_log, _, _ = c3.partial_score(panel, reader, controls, squares, flexible, target=c3.log_target(panel))
    log_surface = c3.past_surface(c3.log_target(panel), design, dates)
    assert np.allclose(e_log, c3.residuals(log_surface[:, None], design, dates)[:, 0], equal_nan=True)

    def no_trees(*args, **kwargs):
        raise AssertionError("tree step repeated")

    monkeypatch.setattr(c3, "past_trees", no_trees)                              # feature residuals handed in: no tree step
    again, _, X_again, _ = c3.partial_score(panel, reader, controls, squares, flexible, X=X)
    assert X_again is X and np.allclose(again, score, equal_nan=True)
    with pytest.raises(AssertionError, match="tree step repeated"):
        c3.partial_score(panel, reader, controls, squares, flexible)


def test_tree_step_is_kept_per_feature_and_control_set(monkeypatch):
    monkeypatch.setattr(c3, "CLEAN_ROUNDS", 5)
    top, feats, hist, fwd = synth(0.0, weeks=30, n=40)
    panel = c3.assemble_panel(top, feats, hist, fwd)
    calls, real = [], c3.past_trees

    def counted(values, controls, dates):
        calls.append((values.shape[1], controls.shape[1]))
        return real(values, controls, dates)

    monkeypatch.setattr(c3, "past_trees", counted)
    cache: dict = {}
    first = c3.feature_residuals(panel, c3.BLOCK_V, c3.HIST, flexible=True, cache=cache)
    assert calls == [(6, 12)] and set(cache) == {(f, tuple(c3.HIST)) for f in c3.BLOCK_V}
    both = c3.feature_residuals(panel, c3.BLOCK_A + c3.BLOCK_V, c3.HIST, flexible=True, cache=cache)
    assert calls == [(6, 12), (2, 12)] and np.array_equal(both[:, 2:], first)    # only the two new features are fitted
    c3.feature_residuals(panel, c3.BLOCK_A, c3.HIST, flexible=True, cache=cache)
    assert len(calls) == 2
    c3.feature_residuals(panel, c3.BLOCK_V, c3.HIST + c3.BLOCK_A, flexible=True, cache=cache)
    assert calls[2:] == [(6, 14)]                                                # other controls: another fit
    c3.feature_residuals(panel, c3.BLOCK_V, c3.HIST, cache=cache)
    assert len(calls) == 3                                                       # no flexible step: no trees
    without = c3.feature_residuals(panel, c3.BLOCK_V, c3.HIST, flexible=True)
    assert calls[3:] == [(6, 12)] and np.array_equal(without, first)             # no cache: fitted again, same values


def test_control_removal_reports_the_variance_left_by_each_step():
    top, feats, hist, fwd = synth(0.0, weeks=60, n=40, seed=5)
    panel = c3.assemble_panel(top, feats, hist, fwd)
    rng = np.random.default_rng(1)
    q = c3.feature_ranks(panel, ["rv_7d"])[:, 0]
    panel["evt_7d"] = 12.0 * q ** 2 + 0.5 * rng.normal(size=len(panel))          # a curved function of the history
    reader, controls, squares, flexible = c3.PARTIAL_SCORES[c3.GATE_SCORE]
    score, e, X, _ = c3.partial_score(panel, reader, controls, squares, flexible)
    scored = np.isfinite(score)
    out = c3.control_removal(panel, X, e, scored)
    assert set(out) == {"features", "target"} and list(out["features"]) == reader
    dates, design = c3._dates(panel), c3.feature_ranks(panel, controls)
    ranks, y = c3.feature_ranks(panel, reader), c3.target_rank(panel)
    line = c3.residuals(ranks, design, dates)
    for j, name in enumerate(reader):
        total = ((ranks[scored, j] - ranks[scored, j].mean()) ** 2).sum()
        assert out["features"][name] == pytest.approx({"within_week_step_alone": (line[scored, j] ** 2).sum() / total,
                                                       "both_steps": (X[scored, j] ** 2).sum() / total})
    ok = scored & np.isfinite(y)
    total = ((y[ok] - y[ok].mean()) ** 2).sum()
    line_y = c3.residuals(y[:, None], design, dates)[:, 0]
    assert out["target"] == pytest.approx({"within_week_step_alone": (line_y[ok] ** 2).sum() / total, "both_steps": (e[ok] ** 2).sum() / total})
    curved, plain = out["features"]["evt_7d"], out["features"]["unfav_7d"]
    assert curved["both_steps"] < 0.5 * curved["within_week_step_alone"]         # the line within the week leaves the curve in
    assert 0.5 < plain["both_steps"] <= 1.1 and 0.5 < plain["within_week_step_alone"] <= 1.0
    assert c3.control_removal(panel, X, e, np.zeros(len(panel), dtype=bool))["target"] == {"within_week_step_alone": None, "both_steps": None}


# ---------------------------------------------------------------- gate statistics
def test_weekly_correlation_needs_rows_and_variation():
    rng = np.random.default_rng(1)
    days = pd.date_range("2023-01-06", periods=4, freq="7D", tz="UTC")
    dates = np.repeat(days.as_unit("ns").asi8, 40)
    a, b = rng.normal(size=160), rng.normal(size=160)
    a[40:80] = 1.0                                                               # no variation in the second week
    b[80:91] = np.nan                                                            # 29 rows in the third week
    out = c3.weekly_corr(dates, a, b)
    assert list(out.index) == [days[0], days[3]]
    assert out.iloc[0] == pytest.approx(np.corrcoef(a[:40], b[:40])[0, 1]) and out.iloc[1] == pytest.approx(np.corrcoef(a[120:], b[120:])[0, 1])
    assert list(c3.weekly_corr(dates, a, b, min_rows=29).index) == [days[0], days[2], days[3]]


def test_gate_statistics_split_the_weekly_correlation_by_calendar_year():
    rng = np.random.default_rng(2)
    days = pd.date_range("2022-12-16", periods=110, freq="7D", tz="UTC")         # 3 weeks of 2022, 52 of 2023, 52 of 2024, 3 of 2025
    dates = np.repeat(days.as_unit("ns").asi8, 40)
    resid = rng.normal(size=len(dates))
    score = 0.3 * resid + rng.normal(size=len(dates))
    gates, ic = c3.gate_statistics(dates, score, resid)
    assert len(ic) == 110 and list(ic.index) == list(days)
    assert gates["reader_partial_ic"] == {"weeks": 110, "mean": pytest.approx(ic.mean()), "nw_t": pytest.approx(newey_west_t(ic))}
    years = gates["reader_partial_ic_by_year"]
    assert set(years) == {"2023", "2024"} and years["2023"]["weeks"] == 52 and years["2024"]["weeks"] == 52
    assert years["2023"]["mean"] == pytest.approx(ic[ic.index.year == 2023].mean())
    assert years["2024"]["mean"] == pytest.approx(ic[ic.index.year == 2024].mean())
    none, empty = c3.gate_statistics(dates, np.full(len(dates), np.nan), resid)
    assert len(empty) == 0 and none["reader_partial_ic"] == {"weeks": 0, "mean": None, "nw_t": None}
    assert none["reader_partial_ic_by_year"] == {"2023": {"weeks": 0, "mean": None}, "2024": {"weeks": 0, "mean": None}}
    assert c3.build_verdict({"gates": none, "weeks": {"test": 0}}, {})["verdict"] == "FAIL"


def test_size_statistics_are_out_of_sample_shares():
    rng = np.random.default_rng(3)
    target = rng.normal(size=500)
    resid = 0.5 * target + rng.normal(size=500) * 0.1
    score = 0.4 * resid
    score[:100] = np.nan
    size = c3.size_statistics(score, resid, target)
    r2 = 1 - ((resid[100:] - score[100:]) ** 2).sum() / (resid[100:] ** 2).sum()
    share = (resid[100:] ** 2).sum() / ((target[100:] - target[100:].mean()) ** 2).sum()
    assert size == {"rows": 400, "oos_r2_residual": pytest.approx(r2), "residual_share_of_target": pytest.approx(share),
                    "oos_r2_target": pytest.approx(r2 * share)}
    assert r2 == pytest.approx(1 - 0.6 ** 2)


# ---------------------------------------------------------------- verdict
def test_verdict_passes_only_with_both_gates():
    passed = _verdict()
    assert passed["verdict"] == "PASS" and passed["failed_gates"] == [] and passed["descriptive_errors"] == []
    assert passed["test_weeks"] == 104 and set(passed["gates"]) == {"reader_partial_ic", "reader_partial_ic_sign_by_year"}
    assert passed["gates"]["reader_partial_ic"]["value"] == {"nw_t": 2.5, "mean": 0.05, "weeks": 104}
    assert passed["gates"]["reader_partial_ic_sign_by_year"]["value"] == {"2023": 0.01, "2024": 0.02}
    assert _verdict(t=2.0)["verdict"] == "PASS" and _verdict(t=np.float64(2.0))["verdict"] == "PASS"
    both = _verdict(t=1.0, y2023=-0.01)
    assert both["verdict"] == "FAIL" and both["failed_gates"] == ["reader_partial_ic", "reader_partial_ic_sign_by_year"]
    assert str(c3.GATE_T) in passed["gates"]["reader_partial_ic"]["rule"]


@pytest.mark.parametrize("kwargs", [{"t": 1.999}, {"t": None}, {"t": float("nan")}, {"t": float("inf")}, {"t": "3.0"},
                                    {"mean": 0.0}, {"mean": -0.01}, {"mean": None}, {"mean": float("nan")}, {"t": -2.5, "mean": -0.05}])
def test_partial_correlation_gate_fails(kwargs):
    verdict = _verdict(**kwargs)
    assert verdict["verdict"] == "FAIL" and verdict["failed_gates"] == ["reader_partial_ic"] and verdict["size_reading"] is None
    assert verdict["gates"]["reader_partial_ic_sign_by_year"]["pass"] is True


@pytest.mark.parametrize("kwargs", [{"y2023": 0.0}, {"y2024": 0.0}, {"y2023": -0.001}, {"y2024": -0.5}, {"y2023": None},
                                    {"y2024": float("nan")}])
def test_year_sign_gate_fails(kwargs):
    verdict = _verdict(**kwargs)
    assert verdict["verdict"] == "FAIL" and verdict["failed_gates"] == ["reader_partial_ic_sign_by_year"]
    assert verdict["gates"]["reader_partial_ic"]["pass"] is True and verdict["size_reading"] is None


def test_year_sign_gate_fails_without_a_year():
    evaluation = _evaluation()
    del evaluation["gates"]["reader_partial_ic_by_year"]["2024"]
    verdict = c3.build_verdict(evaluation, {})
    assert verdict["verdict"] == "FAIL" and verdict["failed_gates"] == ["reader_partial_ic_sign_by_year"]
    assert verdict["gates"]["reader_partial_ic_sign_by_year"]["value"] == {"2023": 0.01, "2024": None}


def test_size_reading_of_a_pass_is_a_label_and_no_gate():
    assert _verdict(mean=c3.SIZE_VISIBLE)["size_reading"] == "visible" and _verdict(mean=0.2)["size_reading"] == "visible"
    thin = _verdict(mean=c3.SIZE_VISIBLE - 1e-9)
    assert thin["size_reading"] == "thin" and thin["verdict"] == "PASS" and thin["failed_gates"] == []
    assert _verdict(mean=0.2, t=1.0)["size_reading"] is None


def test_descriptive_errors_are_listed_and_cannot_change_the_verdict():
    evaluation = _evaluation(forecasts={"error": "ValueError: boom"}, variants={"log_variance": {"error": "KeyError: x"}, "fwd_absret": {}},
                             fit_errors={"g_full": {"error": "RuntimeError: no booster"}})
    verdict = c3.build_verdict(evaluation, {"quality": {"error": "TypeError: y"}, "extraction": None})
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == [] and verdict["size_reading"] == "thin"
    assert verdict["descriptive_errors"] == ["evaluation/forecasts", "evaluation/variants/log_variance", "evaluation/fit_errors/g_full",
                                             "reader/quality"]
    failed = c3.build_verdict(_evaluation(t=0.5, placebo_shift={"error": "ValueError: boom"}), {})
    assert failed["verdict"] == "FAIL" and failed["descriptive_errors"] == ["evaluation/placebo_shift"]


def test_planted_signal_passes_and_a_noise_draw_fails():
    top, feats, hist, fwd = synth(0.15)
    planted, gates = _gate(c3.assemble_panel(top, feats, hist, fwd))
    assert planted["verdict"] == "PASS" and planted["test_weeks"] == 104 and planted["size_reading"] == "visible"
    assert planted["gates"]["reader_partial_ic"]["value"]["nw_t"] > 4.0
    assert gates["reader_partial_ic_by_year"]["2023"]["weeks"] == 52 and gates["reader_partial_ic_by_year"]["2024"]["weeks"] == 52
    # One noise draw. A gate of t >= 2 passes a few noise draws in a hundred by construction (charter §5), so
    # this shows the failing branch on real statistics, not a rejection rate.
    top, feats, hist, fwd = synth(0.0)
    noise, _ = _gate(c3.assemble_panel(top, feats, hist, fwd))
    assert noise["verdict"] == "FAIL" and "reader_partial_ic" in noise["failed_gates"]
    assert abs(noise["gates"]["reader_partial_ic"]["value"]["nw_t"]) < 2.0


def test_a_reader_feature_that_repeats_the_price_history_earns_nothing():
    top, feats, hist, fwd = synth(0.0, seed=2)
    rng = np.random.default_rng(5)
    feats["evt_7d"] = hist.groupby("date")["rv_7d"].rank(pct=True).to_numpy() + 0.3 * rng.normal(size=len(feats))
    panel = c3.assemble_panel(top, feats, hist, fwd)
    raw = c3.weekly_corr(c3._dates(panel), c3.feature_ranks(panel, ["evt_7d"])[:, 0], c3.target_rank(panel))
    assert raw.mean() > 0.3 and newey_west_t(raw) > 20                           # strongly related to the target on its own
    verdict, gates = _gate(panel)
    assert verdict["verdict"] == "FAIL" and abs(gates["reader_partial_ic"]["nw_t"]) < 2.0
    assert abs(gates["reader_partial_ic"]["mean"]) < 0.03


def test_a_reader_feature_that_is_a_curved_function_of_the_history_earns_nothing():
    top, feats, hist, fwd = synth(0.0, seed=7)
    panel = c3.assemble_panel(top, feats, hist, fwd)
    rng = np.random.default_rng(11)
    q = c3.feature_ranks(panel, ["rv_7d"])[:, 0]
    panel["evt_7d"] = 12.0 * q ** 2 + 0.5 * rng.normal(size=len(panel))          # high at both ends of the past week's variance
    panel[c3.TARGET] = panel[c3.TARGET] * np.exp(6.0 * q ** 2)                   # and so is the forward variance
    first, line = _gate(panel, "s_reader_lin")                                   # the first design reads the curve as reader information
    assert first["verdict"] == "PASS" and line["reader_partial_ic"]["nw_t"] > 8.0 and line["reader_partial_ic"]["mean"] > 0.2
    # One draw of the registered gate (charter section 4 has the rates over many draws on the real regressors).
    verdict, gates = _gate(panel)
    assert verdict["verdict"] == "FAIL" and abs(gates["reader_partial_ic"]["nw_t"]) < 2.0
    assert abs(gates["reader_partial_ic"]["mean"]) < 0.03


def test_a_signal_carried_by_the_attention_counts_does_not_pass_the_reader_gate(monkeypatch):
    monkeypatch.setattr(model, "GBM_ROUNDS", 5)
    top, feats, hist, fwd = synth(0.0, seed=2)
    panel = c3.assemble_panel(top, feats, hist, fwd)
    lift = np.exp(0.2 * panel["attn_7d"].to_numpy())
    panel[c3.TARGET] = panel[c3.TARGET] * lift                                   # the attention count moves the variance
    panel, parts, errors = c3.fit_scores(panel)
    dates = c3._dates(panel)
    attn = c3.ic_stats(c3.weekly_corr(dates, panel["s_attn"].to_numpy(), parts["s_attn"]["resid"]))
    reader = c3.ic_stats(c3.weekly_corr(dates, panel["s_reader"].to_numpy(), parts["s_reader"]["resid"]))
    assert attn["nw_t"] > 6.0 and abs(reader["nw_t"]) < 2.0 and errors == {}


# ---------------------------------------------------------------- descriptive panels and outputs
def _gate_alone(top, feats, hist, fwd) -> dict:
    return _gate(c3.assemble_panel(top, feats, hist, fwd))[1]


def test_finalize_returns_the_registered_outputs_in_json_form(monkeypatch):
    monkeypatch.setattr(model, "GBM_ROUNDS", 5)
    monkeypatch.setattr(c3, "CLEAN_ROUNDS", 10)
    data = synth(0.15, weeks=110, n=40, seed=4)
    out = c3.finalize(*data, _records(), extraction={"note": "synthetic"}, n_placebo=5)
    assert set(out) == set(run_script.OUTPUTS)
    assert json.loads(json.dumps(out, allow_nan=False)) == out                   # plain JSON types, no NaN
    verdict, evaluation = out["verdict.json"], out["evaluation.json"]
    assert verdict["descriptive_errors"] == [] and evaluation["fit_errors"] == {}
    assert verdict["verdict"] == "PASS" and verdict["test_weeks"] == 58 and verdict["size_reading"] == "visible"
    assert evaluation["weeks"]["panel"] == 110 and evaluation["weeks"]["first_test"].startswith("2023-01-06")
    assert evaluation["weeks"]["last_test"].startswith("2024-02-09")
    assert evaluation["gates"]["reader_partial_ic_by_year"]["2023"]["weeks"] == 52
    assert evaluation["gates"]["reader_partial_ic_by_year"]["2024"]["weeks"] == 6
    assert len(evaluation["gate_weekly_partial_ic"]) == 58
    forecasts = out["forecasts.json"]
    assert forecasts["columns"] == c3.OUTPUT_COLUMNS and len(forecasts["rows"]) == 110 * 40
    table = pd.DataFrame(forecasts["rows"], columns=forecasts["columns"])
    burn_in = table["date"] < "2023-01-06"
    assert table.loc[burn_in, c3.SCORES].isna().all().all()                      # no score inside the burn-in
    assert table.loc[~burn_in, c3.SCORES].notna().all().all()
    assert table[c3.GATE_RESIDUAL].isna().equals(table[c3.TARGET].isna()) and table[c3.TARGET].isna().sum() == 4400 - len(data[3])
    assert set(evaluation["partial_scores"]) == set(c3.PARTIAL_SCORES)
    for name, (reader, _, _, _) in c3.PARTIAL_SCORES.items():
        part = evaluation["partial_scores"][name]
        assert set(part) == {"partial_ic", "nw_t_long_lag", "size", "univariate", "coefficients"}
        assert part["partial_ic"]["weeks"] == 58 and set(part["univariate"]) == set(reader)
        assert part["coefficients"]["weeks"] == 58 and set(part["coefficients"]["features"]) == set(reader)
    assert set(evaluation["forecasts"]["scores"]) == {*c3.FORECASTS, *c3.GBM_FORECASTS}
    assert set(evaluation["forecasts"]["loss_difference"]) == {f"{a}_minus_{b}" for a, b in c3.LOSS_PAIRS}
    assert set(evaluation["variants"]) == {"log_variance", *c3.TAILS}
    removal = evaluation["control_removal"]
    assert set(removal) == {"features", "target"} and set(removal["features"]) == set(c3.BLOCK_V)
    for part in (*removal["features"].values(), removal["target"]):
        assert set(part) == {"within_week_step_alone", "both_steps"} and all(0.0 < v < 1.2 for v in part.values())
    assert evaluation["placebo_permutation"]["draws"] == 5 and set(evaluation["placebo_shift"]) == {str(k) for k in c3.SHIFT_WEEKS}
    assert set(evaluation["residual_autocorrelation"]) == {str(k) for k in c3.AUTOCORR_LAGS}
    assert evaluation["feature_coverage"]["all_weeks"]["rows"] == 4400 and evaluation["feature_coverage"]["test_weeks"]["weeks"] == 58
    assert set(evaluation["feature_coverage"]["all_weeks"]["features"]) == {*c3.HIST, *c3.TEXT_COLUMNS}
    assert evaluation["target_coverage"]["all_weeks"]["missing"][c3.TARGET] == 4400 - len(data[3])
    assert out["reader.json"]["extraction"] == {"note": "synthetic"} and out["reader.json"]["quality"]["records"] == 21
    gates = _gate_alone(*data)                                                   # the gate values are those of the gate score alone
    assert evaluation["gates"]["reader_partial_ic"] == pytest.approx(gates["reader_partial_ic"])
    assert verdict["gates"]["reader_partial_ic"]["value"]["nw_t"] == pytest.approx(gates["reader_partial_ic"]["nw_t"])
    reader_score = evaluation["partial_scores"][c3.GATE_SCORE]
    assert reader_score["partial_ic"]["mean"] == pytest.approx(gates["reader_partial_ic"]["mean"])
    assert reader_score["univariate"]["evt_7d"]["nw_t"] > 4.0                     # the planted feature
    assert reader_score["coefficients"]["features"]["evt_7d"]["share_positive"] == 1.0


def test_a_failing_boosted_tree_is_recorded_and_the_gates_stand(monkeypatch):
    def no_booster(X, y):
        raise RuntimeError("no booster")

    monkeypatch.setattr(model, "fit_gbm", no_booster)
    monkeypatch.setattr(c3, "CLEAN_ROUNDS", 10)
    data = synth(0.15, weeks=110, n=40, seed=4)
    out = c3.finalize(*data, _records(), n_placebo=5)
    evaluation, verdict = out["evaluation.json"], out["verdict.json"]
    assert evaluation["fit_errors"] == dict.fromkeys(c3.GBM_FORECASTS, {"error": "RuntimeError: no booster"})
    assert verdict["descriptive_errors"] == [f"evaluation/fit_errors/{name}" for name in c3.GBM_FORECASTS]
    assert set(evaluation["forecasts"]["scores"]) == set(c3.FORECASTS)           # the fitted forecasts are still reported
    assert set(evaluation["forecasts"]["loss_difference"]) == {f"{a}_minus_{b}" for a, b in c3.LOSS_PAIRS if b in c3.FORECASTS}
    assert evaluation["gates"]["reader_partial_ic"] == pytest.approx(_gate_alone(*data)["reader_partial_ic"])
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == []
    json.dumps(out, allow_nan=False)


def test_a_failing_descriptive_score_is_recorded_and_the_gates_stand(monkeypatch):
    real = c3.partial_score

    def gate_only(panel, feats, controls, squares=(), flexible=False, target=None, X=None, cache=None):
        if (feats, controls, tuple(squares), flexible) != c3.PARTIAL_SCORES[c3.GATE_SCORE] or target is not None:
            raise ValueError("descriptive fit")
        return real(panel, feats, controls, squares, flexible, target, X, cache)

    monkeypatch.setattr(c3, "partial_score", gate_only)
    monkeypatch.setattr(model, "GBM_ROUNDS", 5)
    monkeypatch.setattr(c3, "CLEAN_ROUNDS", 10)
    data = synth(0.15, weeks=110, n=40, seed=4)
    out = c3.finalize(*data, _records(), n_placebo=5)
    evaluation, verdict = out["evaluation.json"], out["verdict.json"]
    others = [n for n in c3.PARTIAL_SCORES if n != c3.GATE_SCORE]
    assert evaluation["fit_errors"] == dict.fromkeys(others, {"error": "ValueError: descriptive fit"})
    assert set(evaluation["partial_scores"]) == {c3.GATE_SCORE}
    assert {f"evaluation/variants/{name}" for name in ("log_variance", *c3.TAILS)} <= set(verdict["descriptive_errors"])
    assert {f"evaluation/fit_errors/{name}" for name in others} <= set(verdict["descriptive_errors"])
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == []
    json.dumps(out, allow_nan=False)


def test_a_failing_tree_step_stops_the_gate_score_and_only_marks_a_descriptive_score(monkeypatch):
    monkeypatch.setattr(model, "GBM_ROUNDS", 5)
    monkeypatch.setattr(c3, "CLEAN_ROUNDS", 10)
    data = synth(0.15, weeks=110, n=40, seed=4)
    real = c3.past_trees

    def gate_controls_only(values, controls, dates):
        if controls.shape[1] != len(c3.PARTIAL_SCORES[c3.GATE_SCORE][1]):
            raise RuntimeError("no trees")
        return real(values, controls, dates)

    monkeypatch.setattr(c3, "past_trees", gate_controls_only)
    out = c3.finalize(*data, _records(), n_placebo=5)
    evaluation, verdict = out["evaluation.json"], out["verdict.json"]
    flexible_others = [n for n, (_, _, _, flexible) in c3.PARTIAL_SCORES.items() if flexible and n != c3.GATE_SCORE]
    assert evaluation["fit_errors"] == dict.fromkeys(flexible_others, {"error": "RuntimeError: no trees"})
    assert set(evaluation["partial_scores"]) == set(c3.PARTIAL_SCORES) - set(flexible_others)
    assert verdict["descriptive_errors"] == [f"evaluation/fit_errors/{name}" for name in flexible_others]
    assert evaluation["gates"]["reader_partial_ic"] == pytest.approx(_gate_alone(*data)["reader_partial_ic"])
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == []

    def no_trees(values, controls, dates):
        raise RuntimeError("no trees at all")

    monkeypatch.setattr(c3, "past_trees", no_trees)                              # the gate score has no fallback
    with pytest.raises(RuntimeError, match="no trees at all"):
        c3.finalize(*data, _records(), n_placebo=5)


def test_placebos_break_the_planted_link():
    top, feats, hist, fwd = synth(0.15, seed=1)
    panel = c3.assemble_panel(top, feats, hist, fwd)
    reader, controls, squares, flexible = c3.PARTIAL_SCORES[c3.GATE_SCORE]
    score, e, X, _ = c3.partial_score(panel, reader, controls, squares, flexible)
    dates = c3._dates(panel)
    observed = c3.gate_statistics(dates, score, e)[0]["reader_partial_ic"]["nw_t"]
    assert observed > 8.0
    placebo = c3.permutation_placebo(dates, X, e, observed, draws=12)
    assert placebo["draws"] == 12 and placebo["share_ge_observed"] == 0.0 and placebo["t_observed"] == observed
    assert abs(placebo["t_mean"]) < 1.5 and placebo["t_q975"] < 4.0
    assert c3.permutation_placebo(dates, X, e, observed, draws=12) == placebo     # seeded
    assert c3.permutation_placebo(dates, X, e, observed, draws=12, seed=1)["t_mean"] != placebo["t_mean"]
    shifted = c3.shift_placebo(panel, X, e)
    assert set(shifted) == {str(k) for k in c3.SHIFT_WEEKS}
    assert all(abs(v["nw_t"]) < 4.0 for v in shifted.values())                   # the features of another week do not carry it
    none = c3.permutation_placebo(dates, np.full_like(X, np.nan), e, observed, draws=3)
    assert none == {"draws": 0, "t_observed": observed, "share_ge_observed": None, "t_mean": None, "t_sd": None, "t_q975": None}


def test_residual_autocorrelation_sees_the_persistence_the_controls_miss():
    for rho, low, high in ((0.0, -0.08, 0.08), (0.8, 0.25, 0.9)):
        top, feats, hist, fwd = synth(0.0, weeks=80, n=40, seed=6, rho=rho)
        panel = c3.assemble_panel(top, feats, hist, fwd)
        reader, controls, squares, flexible = c3.PARTIAL_SCORES[c3.GATE_SCORE]
        _, e, _, _ = c3.partial_score(panel, reader, controls, squares, flexible)
        auto = c3.residual_autocorrelation(panel, e)
        assert set(auto) == {str(k) for k in c3.AUTOCORR_LAGS} and auto["1"]["pairs"] > 2500
        assert low < auto["1"]["corr"] < high, (rho, auto["1"])
    assert auto["1"]["corr"] > auto["4"]["corr"] > auto["8"]["corr"]


def test_coverage_tables_count_missing_values_and_short_weeks():
    top, feats, hist, fwd = synth(0.0, weeks=8, n=6)
    fwd.loc[fwd.index[:3], "fwd_bars"] = 5
    fwd.loc[fwd.index[3], c3.TARGET] = 0.0
    fwd.loc[fwd.index[4], "fwd_absret"] = np.nan
    panel = c3.assemble_panel(top, feats, hist, fwd)
    target = c3.target_coverage(panel)
    lost = 48 - len(fwd)
    assert target == {"rows": 48, "missing": {c3.TARGET: lost, "fwd_absret": lost + 1, "fwd_drawdown": lost, "fwd_maxday": lost},
                      "short_weeks": 3, "zero_variance": 1}
    cover = c3.feature_coverage(panel)
    assert cover["rows"] == 48 and cover["weeks"] == 8
    assert cover["features"]["rv_90d"]["missing"] == pytest.approx(panel["rv_90d"].isna().mean())
    assert cover["features"]["attn_abn"]["missing"] == pytest.approx(panel["attn_abn"].isna().mean()) and panel["attn_abn"].isna().any()
    assert cover["features"]["evt_7d"]["nonzero"] == pytest.approx((panel["evt_7d"] != 0).mean())
    assert cover["features"]["evt_7d"]["mean_assets_nonzero_per_week"] == pytest.approx((panel["evt_7d"] != 0).sum() / 8)


# ---------------------------------------------------------------- extraction manifest
def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _manifest_and_experiment() -> tuple[dict, dict]:
    manifest = {"charter": {"path": "charter2.md", "sha256": _digest("charter 2")}, "prompt_sha256": schema.prompt_sha256(),
                "inputs": {name: {"path": name, "sha256": _digest(name)} for name in ("items", "docs", "cards")},
                "records_file": {"path": "records", "sha256": _digest("records")},
                "cache": {"path": "calls", "sha256": _digest("calls")},
                "source_files": {"a.py": _digest("a"), "b.py": _digest("b")}}
    experiment = {"charter": {"path": "charter3.md", "sha256": _digest("charter 3")},        # the run has its own charter
                  "inputs": {name: {"path": name, "sha256": _digest(name)} for name in ("items", "docs", "cards", "records", "calls")},
                  "source_files": {"a.py": _digest("a"), "b.py": _digest("b"), "c.py": _digest("c"), "charter2.md": _digest("charter 2")}}
    return manifest, experiment


def test_manifest_of_the_registered_extraction_is_accepted():
    run_script.check_manifest(*_manifest_and_experiment())


@pytest.mark.parametrize("where, key, message", [
    ("manifest", ("charter", "sha256"), "charter text of the extraction is not a registered source file"),
    ("experiment", ("source_files", "charter2.md"), "charter text of the extraction is not a registered source file"),
    ("manifest", ("prompt_sha256",), "agent instructions differ"),
    ("experiment", ("inputs", "items", "sha256"), "items differs from the registered input"),
    ("experiment", ("inputs", "docs", "sha256"), "docs differs from the registered input"),
    ("experiment", ("inputs", "cards", "sha256"), "cards differs from the registered input"),
    ("manifest", ("records_file", "sha256"), "records differs from the registered input"),
    ("experiment", ("inputs", "calls", "sha256"), "calls differs from the registered input"),
    ("experiment", ("source_files", "a.py"), "a.py changed since the extraction"),
])
def test_manifest_of_another_extraction_is_refused(where, key, message):
    manifest, experiment = _manifest_and_experiment()
    node = manifest if where == "manifest" else experiment
    for part in key[:-1]:
        node = node[part]
    node[key[-1]] = _digest("something else")
    with pytest.raises(SystemExit, match=message):
        run_script.check_manifest(manifest, experiment)


def test_manifest_needs_its_charter_and_its_source_files_registered():
    manifest, experiment = _manifest_and_experiment()
    del experiment["source_files"]["b.py"]
    with pytest.raises(SystemExit, match="b.py changed since the extraction"):
        run_script.check_manifest(manifest, experiment)
    manifest, experiment = _manifest_and_experiment()
    del experiment["source_files"]["charter2.md"]
    with pytest.raises(SystemExit, match="not a registered source file"):
        run_script.check_manifest(manifest, experiment)
    manifest, experiment = _manifest_and_experiment()                            # the charter of the run does not stand in for it
    experiment["source_files"]["charter3.md"] = experiment["source_files"].pop("charter2.md")
    with pytest.raises(SystemExit, match="not a registered source file"):
        run_script.check_manifest(manifest, experiment)


def test_rehearsal_targets_are_seeded_noise_of_the_registered_shape():
    top, *_ = synth(0.0, weeks=20, n=10)
    fwd = run_script.synthetic_targets(top)
    pd.testing.assert_frame_equal(fwd, run_script.synthetic_targets(top))
    other = run_script.synthetic_targets(top, seed=1)
    assert not np.allclose(other[c3.TARGET].to_numpy()[:50], fwd[c3.TARGET].to_numpy()[:50])
    assert list(fwd.columns) == ["date", "symbol", *c3.TARGET_COLUMNS] and (fwd["fwd_bars"] == 7).all()
    assert 0 < len(top) - len(fwd) < 0.05 * len(top) and not fwd[["date", "symbol"]].duplicated().any()
    assert (fwd[[c3.TARGET, *c3.TAILS]] > 0).all().all() and fwd[[c3.TARGET, *c3.TAILS]].notna().all().all()


# ---------------------------------------------------------------- registered run on a synthetic checkout
RUN_SHAPE = {"weeks": 110, "n_syms": 40, "docs_per_week": 18}                    # 52 burn-in weeks, 52 weeks of 2023, 6 of 2024
RUN_INPUTS = {"items": rx.INPUTS["items"], "docs": rx.INPUTS["docs"], "cards": rx.INPUTS["cards"], "calls": rx.CACHE,
              "records": rx.RECORDS, "extraction_manifest": rx.MANIFEST, "klines_digest": "klines_digest.json"}
PLANTED, BASE_SIGMA, LEAD_DAYS = 0.25, 0.03, 100


def _run_root(root: Path) -> dict:
    """A synthetic checkout in the state before the registered run: sources and the charter of the extraction
    committed, the extraction complete (stub client), a kline store of daily bars whose volatility in the week
    after a decision rises with the reader's event feature of that decision, and a committed registration under
    a charter of its own."""
    from tradingagents.research import runtime_hashes
    items, docs, cards = script_root(root, frozen=True, **RUN_SHAPE)
    manifest = extract(root, "--cost-cap", "5", client=FakeClient())
    records = pd.read_parquet(root / rx.RECORDS)
    top = c2.universe(cards)
    sets, _ = c2.reading(items, docs, top)
    feats = c3.text_features(items, sets, records, top)
    fridays = sorted(top["date"].unique())
    days = pd.date_range(fridays[0] - LEAD_DAYS * DAY, fridays[-1] + WEEK, freq="D", tz="UTC")
    (root / "klines").mkdir()
    for i, (sym, rows) in enumerate(feats.groupby("symbol")):
        lift = rows.set_index("date")["evt_7d"].clip(upper=4.0).reindex(fridays).fillna(0.0).to_numpy()
        sigma = np.full(len(days), BASE_SIGMA)
        sigma[LEAD_DAYS + 1:] = BASE_SIGMA * np.exp(PLANTED * np.repeat(lift, 7))  # the seven bars after each Friday bar
        _bars(len(days), seed=100 + i, start=days[0], sigma=sigma).to_parquet(root / "klines" / f"{sym}.parquet")
    digest = {f"klines/{p.name}": sha(p) for p in sorted((root / "klines").glob("*.parquet"))}
    (root / "klines_digest.json").write_text(json.dumps(digest))
    (root / "charter3.md").write_text("synthetic charter of the target change\n")
    spec = {"schema_version": 1, "program_id": "synthetic-c3",
            "families": {"fam": {"mechanism_id": "synthetic-mechanism", "attempt_budget": 3, "prior_attempts": 0,
                                 "history_reference": "synthetic"}},
            "datasets": {"sample": {"identity": "synthetic-sample", "history_reference": "synthetic", "exposures": []}},
            "experiments": {"c3": {
                "family": "fam", "parent": None, "question": "synthetic",
                "charter": {"path": "charter3.md", "sha256": sha(root / "charter3.md")},
                "stage": "development", "reuse": "exploratory", "selection": None,
                "source_files": {**manifest["source_files"], "charter.md": sha(root / "charter.md")},
                "runtime_hashes": runtime_hashes(),
                "windows": [{"dataset": "sample", "start": "2022-01-01T00:00:00Z", "end": "2024-03-01T00:00:00Z",
                             "availability": "existing"}],
                "inputs": {name: {"path": path, "sha256": sha(root / path), "dataset": "sample"} for name, path in RUN_INPUTS.items()},
                "cells": list(run_script.CELLS), "outputs": list(run_script.OUTPUTS)}}}
    (root / "registration.json").write_text(json.dumps(spec))
    commit(root, "synthetic registration", "registration.json", "charter3.md")
    return {"manifest": manifest, "feats": feats, "fridays": fridays, "top": top}


def _run(root: Path, *extra: str) -> int:
    return run_script.main(["--registration", "registration.json", "--experiment", "c3", *extra], root=root)


def _output(root: Path, name: str):
    return json.loads((root / "research_runs" / "c3" / "outputs" / name).read_text())


def test_registered_run_checks_everything_before_the_claim_and_joins_outcomes_once(tmp_path, monkeypatch, capsys):
    from tradingagents.research.verify import verify_run
    ctx = _run_root(tmp_path)
    assert ctx["manifest"]["charter"]["path"] == "charter.md"                    # the extraction ran under the other charter
    joins, real_join, real_finalize = [], run_script.forward_targets, c3.finalize

    def counted_join(klines_dir, keys):
        joins.append(len(keys))
        return real_join(klines_dir, keys)

    def no_join(*args, **kwargs):
        raise AssertionError("outcome join outside the registered step")

    def quick_finalize(*args, **kwargs):
        kwargs.setdefault("n_placebo", 5)
        return real_finalize(*args, **kwargs)

    rehearsals, real_rehearse = [], run_script.rehearse

    def counted_rehearse(ctx):
        rehearsals.append(len(ctx["top"]))
        return real_rehearse(ctx)

    monkeypatch.setattr(run_script, "rehearse", counted_rehearse)
    monkeypatch.setattr(run_script, "forward_targets", counted_join)
    monkeypatch.setattr(c3, "forward_targets", no_join)                          # no other path to the outcomes
    monkeypatch.setattr(c3, "finalize", quick_finalize)
    monkeypatch.setattr(run_script, "REHEARSAL_PLACEBO", 5)
    monkeypatch.setattr(model, "GBM_ROUNDS", 5)
    monkeypatch.setattr(c3, "CLEAN_ROUNDS", 10)
    claimed = tmp_path / "research_runs"

    # a record edited after the extraction: found before the claim, no outcome read
    records_path = tmp_path / rx.RECORDS
    original = records_path.read_bytes()
    edited = pd.read_parquet(records_path)
    row = edited.index[edited["direction"].notna()][0]
    edited.loc[row, "direction"] = "favourable" if edited.loc[row, "direction"] != "favourable" else "unfavourable"
    edited.to_parquet(records_path, index=False)
    with pytest.raises(SystemExit, match="record table differs from the rebuild"):
        _run(tmp_path)
    records_path.write_bytes(original)
    assert not claimed.exists() and joins == [] and rehearsals == []

    # a kline file changed after the digest was taken: found before the claim
    kline = tmp_path / "klines" / "S03USDT.parquet"
    stored = kline.read_bytes()
    frame = pd.read_parquet(kline)
    frame.iloc[5, 0] *= 1.01
    frame.to_parquet(kline)
    with pytest.raises(CacheError, match="kline store: changed since freeze"):
        _run(tmp_path)
    kline.write_bytes(stored)
    assert not claimed.exists() and joins == [] and rehearsals == []

    # pre-flight alone: inputs verified, records rebuilt, rehearsal on synthetic targets, no claim
    assert _run(tmp_path, "--preflight-only") == 0
    assert "pre-flight passed" in capsys.readouterr().out
    assert not claimed.exists() and joins == [] and rehearsals == [4400]

    # the registered run
    assert _run(tmp_path) == 0
    directory = claimed / "c3"
    assert (directory / "claim.json").is_file() and (directory / "complete.json").is_file()
    assert not (directory / "failed.json").exists() and verify_run(directory)["status"] == "complete"
    assert sorted(p.name for p in (directory / "outputs").iterdir()) == sorted(run_script.OUTPUTS)
    assert joins == [40 * 110]                                                   # the single outcome join
    assert rehearsals == [4400, 4400]                                            # one rehearsal per process, before the claim
    verdict, evaluation = _output(tmp_path, "verdict.json"), _output(tmp_path, "evaluation.json")
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == [] and verdict["descriptive_errors"] == []
    assert verdict["test_weeks"] == 58 and verdict["gates"]["reader_partial_ic"]["value"]["nw_t"] > 4.0
    assert evaluation["fit_errors"] == {} and evaluation["weeks"]["first_test"].startswith("2023-01-06")
    assert evaluation["target_coverage"]["all_weeks"] == {"rows": 4400, "missing": dict.fromkeys([c3.TARGET, *c3.TAILS], 0),
                                                           "short_weeks": 0, "zero_variance": 0}
    reader = _output(tmp_path, "reader.json")
    assert set(reader["extraction"]) == set(run_script.EXTRACTION_KEYS)
    assert reader["extraction"]["model"]["id"] == "fake/model" and reader["extraction"]["units"] == ctx["manifest"]["units"]
    assert reader["quality"]["records"] == ctx["manifest"]["records"] > 1000
    forecasts = _output(tmp_path, "forecasts.json")
    table = pd.DataFrame(forecasts["rows"], columns=forecasts["columns"])
    table = table.assign(date=pd.to_datetime(table["date"], utc=True)).set_index(["date", "symbol"])
    want_fwd, want_hist = {}, {}
    for sym in sorted(ctx["top"]["symbol"].unique()):                            # an independent rolling computation on the store
        weekly = _gk(pd.read_parquet(tmp_path / "klines" / f"{sym}.parquet")).rolling(7).mean()
        for f in ctx["fridays"]:
            want_fwd[(f, sym)], want_hist[(f, sym)] = weekly[f + WEEK], weekly[f]
    assert np.allclose(table[c3.TARGET].to_numpy(dtype=float), pd.Series(want_fwd).reindex(table.index).to_numpy())
    assert np.allclose(table["rv_7d"].to_numpy(dtype=float), pd.Series(want_hist).reindex(table.index).to_numpy())
    feats = ctx["feats"].set_index(["date", "symbol"])
    for col in ("evt_7d", "unfav_7d", "attn_7d"):
        assert np.allclose(table[col].to_numpy(dtype=float), feats[col].reindex(table.index).to_numpy()), col
    assert (table["fwd_bars"] == 7).all() and (feats["evt_7d"] > 0).mean() > 0.1

    # one registered run per registration
    monkeypatch.setattr(run_script, "rehearse", lambda ctx: rehearsals.append(0))    # the rehearsal is not the subject here
    with pytest.raises(ValueError, match="repeat run prohibited"):
        _run(tmp_path)
    assert joins == [40 * 110] and rehearsals == [4400, 4400, 0]
    assert verify_run(directory)["status"] == "complete"


# ---------------------------------------------------------------- registration
CLOSURE = """
import json, sys
from pathlib import Path
root = Path.cwd().resolve()
import reader_charter3_register, reader_charter3_run  # noqa: F401,E401
out = set()
for module in list(sys.modules.values()):
    name = getattr(module, "__file__", None)
    path = Path(name).resolve() if name else None
    if path and path.is_relative_to(root) and ".venv" not in path.parts:
        out.add(path.relative_to(root).as_posix())
print(json.dumps(sorted(out)))
"""


def test_registration_pins_every_project_file_the_run_imports():
    import os
    import subprocess

    import reader_charter3_register as reg

    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(ROOT), str(ROOT / "scripts")])}
    done = subprocess.run([sys.executable, "-c", CLOSURE], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    imported = set(json.loads(done.stdout.strip().splitlines()[-1]))
    helper = {p for p in imported if p.startswith("tradingagents/research/")}       # pinned by the runtime hashes, if loaded
    assert "scripts/reader_charter3_run.py" in imported and "tradingagents/reader/charter3.py" in imported
    assert imported - helper <= set(reg.SOURCE_FILES), sorted(imported - helper - set(reg.SOURCE_FILES))
    assert len(set(reg.SOURCE_FILES)) == len(reg.SOURCE_FILES) and all((ROOT / p).is_file() for p in reg.SOURCE_FILES)
    assert set(rx.SOURCES) <= set(reg.SOURCE_FILES)                                 # the manifest is checked against these
    assert {"uv.lock", reg.EXTRACTION_CHARTER} <= set(reg.SOURCE_FILES) and reg.CHARTER not in reg.SOURCE_FILES


def test_registration_continues_the_charter_2_registration():
    import reader_charter3_register as reg

    parent_spec = json.loads((ROOT / reg.PARENT_REGISTRATION).read_text())
    parent = parent_spec["experiments"][reg.PARENT]
    assert set(parent["source_files"]) <= set(reg.SOURCE_FILES)                     # nothing of the extraction is unpinned
    assert reg.EXTRACTION_CHARTER == parent["charter"]["path"] == rx.CHARTER
    assert sha(ROOT / reg.EXTRACTION_CHARTER) == parent["charter"]["sha256"]        # the frozen text, byte for byte
    assert rx.DRAFT_MARK not in (ROOT / reg.EXTRACTION_CHARTER).read_text(encoding="utf-8")
    assert set(reg.INPUTS) == set(RUN_INPUTS) and set(reg.SAME_AS_PARENT) == set(reg.INPUTS)
    assert {name: parent["inputs"][name]["path"] for name in reg.INPUTS} == reg.INPUTS
    assert reg.FAMILY_KEY == parent["family"] == "llm-multiagent-v2" and reg.FAMILY_KEY in parent_spec["families"]
    assert reg.DATASET not in parent_spec["datasets"] and reg.CHARTER != reg.EXTRACTION_CHARTER
    assert reg.DRAFT_MARK == rx.DRAFT_MARK and reg.experiment_id("20261113") == "llm-v2c3-volatility-dev-run-20261113"
    assert reg.experiment_id("20261113") not in parent_spec["experiments"]
    assert reg.WINDOW == {k: parent["windows"][0][k] for k in ("start", "end")}
    last = pd.Timestamp(c2.PANEL_END, tz="UTC") if pd.Timestamp(c2.PANEL_END).tzinfo is None else pd.Timestamp(c2.PANEL_END)
    assert pd.Timestamp(reg.WINDOW["end"]) >= last + WEEK                           # the forward week of the last decision


# ---------------------------------------------------------------- charter text
def test_charter_states_the_registered_constants():
    import reader_charter3_register as reg

    text = (ROOT / reg.CHARTER).read_text(encoding="utf-8")
    assert text.count(reg.DRAFT_MARK) == int(text.splitlines()[0].endswith(reg.DRAFT_MARK))     # in the title or nowhere
    names = [*c3.HIST, *c3.BLOCK_A, *c3.BLOCK_V, *c3.COUNTS, *c3.SCORES, c3.TARGET, *c3.TAILS, c3.GATE_RESIDUAL]
    for stated in (f"t at least {c3.GATE_T}", f"at least {c3.SIZE_VISIBLE}", f"penalty {RIDGE_ALPHA:g}", f"{BURN_IN_WEEKS} weeks",
                   f"{c3.MIN_WEEK_ROWS} rows", f"seed {c3.PLACEBO_SEED}", f"{PLACEBO_DRAWS} draws", f"lag {c3.LONG_LAG}", "lag 4",
                   f"{model.GBM_ROUNDS} rounds", f"at least {c3.MIN_BARS_SHORT} bars", f"at least {c3.MIN_BARS_LONG} bars",
                   f"first {c3.CLEAN_FIRST} weeks", f"every {c3.CLEAN_EVERY} weeks", f"{c3.CLEAN_ROUNDS} rounds", f"penalty {c3.CLEAN_ALPHA}",
                   reg.PARENT, reg.DATASET, reg.EXTRACTION_CHARTER, *(f"`{n}`" for n in names)):
        assert stated in text, stated
    assert "we " not in text.lower() and " our " not in text.lower()                # impersonal prose
