"""Fresher information (Charter 4): daily decisions, item timing, signed reader features, partial gate, registered run.

Synthetic fixtures only; no market data, no network. The fixtures of the extraction side are shared with
``test_reader_extract.py``.
"""
from __future__ import annotations

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

import reader_charter4_run as run_script  # noqa: E402
import reader_extract as rx  # noqa: E402
from test_reader_extract import DAY, FakeClient, _doc, _item, _record_row, commit, extract, script_root, sha  # noqa: E402
from tradingagents.agents_v2.charter1b import PLACEBO_DRAWS, CacheError  # noqa: E402
from tradingagents.agents_v2.evaluate import newey_west_t  # noqa: E402
from tradingagents.agents_v2.portfolio_eval import COST_PER_SIDE  # noqa: E402
from tradingagents.dossier.quant_forecast import RIDGE_ALPHA  # noqa: E402
from tradingagents.reader import charter2 as c2, charter3 as c3, charter4 as c4, consensus, model, reading, schema  # noqa: E402

HOUR = pd.Timedelta(hours=1)
D0 = pd.Timestamp("2023-03-11", tz="UTC")                   # a decision day (Saturday)
STORE = pd.Timestamp("2023-01-01", tz="UTC")                # start of the item store in the hand-made cases


# ---------------------------------------------------------------- fixtures
def _day(text: str) -> pd.Timestamp:
    return pd.Timestamp(text, tz="UTC")


def _last_friday(days: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """The last Friday strictly before every day."""
    back = (days.day_of_week.to_numpy() - 4) % 7
    return days - pd.to_timedelta(np.where(back == 0, 7, back), unit="D")


def synth(signal: float = 0.0, days: int = 760, n: int = 40, seed: int = 0, week: float = 0.0, attention: float = 0.0,
          rho: float = 0.0):
    """(daily universe rows, text features, bar history, forward targets) of the registered shape. ``signal``
    plants an effect of the sign of ``tone_1d`` on the next-day return, ``week`` one of the sign of the tone of
    the last seven days, ``attention`` one of the news count; ``rho`` is the daily persistence of a drift that
    no regressor sees."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(c4.PANEL_FIRST, periods=days, freq="D", tz="UTC")
    syms = [f"S{i:02d}USDT" for i in range(n)]
    uni = pd.DataFrame([(d, s) for d in dates for s in syms], columns=["date", "symbol"])
    uni["friday"] = _last_friday(pd.DatetimeIndex(uni["date"]))
    uni["base"] = uni["symbol"].str[:-4]
    uni["age_weeks"] = rng.integers(1, 300, len(uni)).astype(float)
    uni["funding_3d"] = 1e-4 * rng.normal(size=len(uni))
    hist = uni[["date", "symbol"]].copy()
    for col in c4.HIST_BARS:
        hist[col] = np.exp(rng.normal(size=len(uni))) if col.startswith(("rv", "dvol")) else rng.normal(size=len(uni))
    hist.loc[rng.uniform(size=len(uni)) < 0.03, "beta_60d"] = np.nan
    tone = np.where(rng.uniform(size=(days, n)) < 0.15, rng.integers(-3, 4, size=(days, n)), 0).astype(float)
    prev6 = np.vstack([np.zeros((1, n)), np.cumsum(tone, axis=0)])
    prev6 = prev6[np.arange(days)] - prev6[np.maximum(np.arange(days) - 6, 0)]          # the six days before the day
    feats = uni[["date", "base"]].copy()
    feats["tone_1d"], feats["tone_prev6"] = tone.ravel(), prev6.ravel()
    feats["unfav_1d"] = np.maximum(-tone, 0).ravel()
    feats["unfav_prev6"] = np.maximum(-prev6, 0).ravel()
    feats["evt_1d"] = np.abs(tone).ravel() + (rng.uniform(size=len(uni)) < 0.05)
    feats["stance_1d"] = np.where(rng.uniform(size=len(uni)) < 0.1, rng.integers(-2, 3, len(uni)), 0).astype(float)
    for col in ("news_1d", "posts_1d", "attn_7d"):
        feats[col] = np.log1p(rng.poisson(1.0, len(uni)))
    feats["attn_abn_1d"] = rng.normal(size=len(uni))
    feats.loc[feats["date"] < dates[min(14, days - 1)], "attn_abn_1d"] = np.nan
    feats["n_subject_1d"] = (feats["evt_1d"] > 0).astype(float)
    feats["n_subject_7d"] = feats["n_subject_1d"] + rng.integers(0, 3, len(uni))
    feats["gap_1d"] = (rng.uniform(size=len(uni)) < 0.02).astype(float)
    feats["gap_7d"] = feats["gap_1d"] + (rng.uniform(size=len(uni)) < 0.05)
    drift = np.zeros((days, n))
    for t in range(1, days):
        drift[t] = rho * drift[t - 1] + np.sqrt(1 - rho ** 2) * rng.normal(size=n)
    ret = (0.03 * rng.normal(size=len(uni)) + 0.03 * (rho > 0) * drift.ravel() + signal * np.sign(tone.ravel())
           + week * np.sign((tone + prev6).ravel()) + attention * (feats["news_1d"].to_numpy() - np.log(2)))
    fwd = uni[["date", "symbol"]].assign(fwd_ret_1d=ret, fwd_absret_1d=np.abs(ret),
                                         fwd_rv_1d=1e-3 * np.exp(rng.normal(size=len(uni))),
                                         fwd_ret_3d=ret + 0.05 * rng.normal(size=len(uni)))
    fwd = fwd[rng.uniform(size=len(fwd)) > 0.01].reset_index(drop=True)
    return uni, feats[["date", "base", *c4.TEXT_COLUMNS]], hist, fwd


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


def _bars(n: int = 120, seed: int = 0, start="2023-01-01", sigma=0.03, drift=0.0) -> pd.DataFrame:
    """Daily bars in the form of the kline store; ``drift`` is added to the log return of every bar."""
    rng = np.random.default_rng(seed)
    days = pd.date_range(start, periods=n, freq="D", tz="UTC")
    close = 100.0 * np.exp(np.cumsum(sigma * rng.normal(size=n) + drift))
    open_ = np.concatenate([[100.0], close[:-1]])
    high = np.maximum(open_, close) * np.exp(0.03 * np.abs(rng.normal(size=n)) / 2)
    low = np.minimum(open_, close) * np.exp(-0.03 * np.abs(rng.normal(size=n)) / 2)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close,
                         "quote_volume": 1e6 * np.exp(rng.normal(size=n))}, index=pd.Index(days, name="ts"))


def _gk(bars: pd.DataFrame) -> pd.Series:
    """The Garman-Klass variance written out directly."""
    return 0.5 * np.log(bars["high"] / bars["low"]) ** 2 - (2 * np.log(2) - 1) * np.log(bars["close"] / bars["open"]) ** 2


def _keys(days, symbol: str = "AAAUSDT") -> pd.DataFrame:
    return pd.DataFrame({"date": pd.DatetimeIndex(days), "symbol": symbol})


def _grid_keys(first: pd.Timestamp, last: pd.Timestamp, bases=("AAA", "BBB")) -> pd.DataFrame:
    return pd.DataFrame([(d, b) for d in pd.date_range(first, last, freq="D") for b in bases], columns=["date", "base"])


def _gate(panel: pd.DataFrame, name: str | None = None) -> tuple[dict, dict]:
    """(verdict, gate statistics) of an assembled panel, one partial score only (the gate score by default)."""
    feats, controls, flexible = c4.PARTIAL_SCORES[name or c4.GATE_SCORE]
    score, resid, _, _ = c4.partial_score(panel, feats, controls, flexible)
    gates, daily = c4.gate_statistics(c4._dates(panel), score, resid)
    return c4.build_verdict({"gates": gates, "days": {"test": int(len(daily))}}, {}), gates


def _evaluation(t=2.5, mean=0.05, y2023=0.01, y2024=0.02, **extra) -> dict:
    return {"gates": {"reader_partial": {"form": "corr", "days": 722, "mean": mean, "nw_t": t},
                      "reader_partial_by_year": {"2023": {"days": 359, "mean": y2023}, "2024": {"days": 363, "mean": y2024}}},
            "days": {"test": 722}, **extra}


def _verdict(**kwargs) -> dict:
    return c4.build_verdict(_evaluation(**kwargs), {})


# ---------------------------------------------------------------- daily universe
def _weekly(members: dict) -> pd.DataFrame:
    """Weekly universe rows; ``members`` maps a Friday to its symbols."""
    rows = [{"date": _day(f), "symbol": s, "base": s[:-4], "age_weeks": float(10 * i + j), "funding_3d": 1e-4 * (i + 1) * (j + 1)}
            for i, (f, syms) in enumerate(members.items()) for j, s in enumerate(syms)]
    return pd.DataFrame(rows)


def test_daily_universe_takes_the_members_of_the_last_friday_before_the_day(monkeypatch):
    monkeypatch.setattr(c4, "PANEL_FIRST", "2023-03-11")
    monkeypatch.setattr(c4, "PANEL_LAST", "2023-03-24")
    top = _weekly({"2023-03-10": ["AAAUSDT", "BBBUSDT"], "2023-03-17": ["AAAUSDT", "CCCUSDT"]})
    uni = c4.daily_universe(top)
    assert list(uni.columns) == ["date", "friday", "symbol", "base", "age_weeks", "funding_3d"]
    assert len(uni) == 14 * 2 and not uni.duplicated(["date", "symbol"]).any()
    by_symbol = uni.groupby("symbol")["date"].agg(["min", "max", "size"])
    assert by_symbol.loc["BBBUSDT"].tolist() == [_day("2023-03-11"), _day("2023-03-17"), 7]     # the Friday itself still uses the week before
    assert by_symbol.loc["CCCUSDT"].tolist() == [_day("2023-03-18"), _day("2023-03-24"), 7]
    assert by_symbol.loc["AAAUSDT", "size"] == 14
    assert ((uni["date"] - uni["friday"]) >= DAY).all() and ((uni["date"] - uni["friday"]) <= 7 * DAY).all()
    cards = top.rename(columns={"date": "friday"})
    joined = uni.merge(cards, on=["friday", "symbol"], suffixes=("", "_card"), validate="m:1")
    assert (joined["age_weeks"] == joined["age_weeks_card"]).all() and (joined["funding_3d"] == joined["funding_3d_card"]).all()


def test_daily_universe_covers_the_registered_window():
    fridays = pd.date_range("2022-01-07", "2024-12-27", freq="W-FRI", tz="UTC")
    top = pd.DataFrame([{"date": f, "symbol": s, "base": s[:-4], "age_weeks": 1.0, "funding_3d": 0.0}
                        for f in fridays for s in ("AAAUSDT", "BBBUSDT")])
    uni = c4.daily_universe(top)
    days = pd.DatetimeIndex(uni["date"].unique())
    assert len(fridays) == 156 and len(days) == 1086 and len(uni) == 2 * 1086
    assert days.min() == _day("2022-01-08") and days.max() == _day("2024-12-28")
    assert (np.diff(days.sort_values().asi8) == DAY.value).all()


def test_daily_universe_refuses_a_broken_weekly_table(monkeypatch):
    monkeypatch.setattr(c4, "PANEL_FIRST", "2023-03-11")
    monkeypatch.setattr(c4, "PANEL_LAST", "2023-03-24")
    good = _weekly({"2023-03-10": ["AAAUSDT"], "2023-03-17": ["AAAUSDT"]})
    with pytest.raises(ValueError, match="not unique"):
        c4.daily_universe(pd.concat([good, good.iloc[[0]]], ignore_index=True))
    with pytest.raises(ValueError, match="not Fridays"):
        c4.daily_universe(good.assign(date=good["date"] + DAY))
    with pytest.raises(ValueError, match="does not cover every decision day"):
        c4.daily_universe(good.iloc[[0]])
    monkeypatch.setattr(c4, "PANEL_LAST", "2023-03-25")
    with pytest.raises(ValueError, match="does not cover every decision day"):
        c4.daily_universe(good)


# ---------------------------------------------------------------- item timing
def _timed(seen: str, published: str, source: str = "wayback", doc: str = "d", base: str = "AAA") -> dict:
    return _item(doc, base, source=source, event_ts=pd.Timestamp(published, tz="UTC"), as_of_ts=pd.Timestamp(seen, tz="UTC"))


def test_item_day_is_the_midnight_after_the_observation_and_midnight_itself_waits():
    items = pd.DataFrame([_timed("2023-03-10 23:59:59", "2023-03-10 20:00"), _timed("2023-03-11 00:00:00", "2023-03-10 20:00"),
                          _timed("2023-03-11 00:00:01", "2023-03-10 20:00"), _timed("2023-03-10 00:00:00", "2023-03-09 20:00")])
    out = c4.item_days(items)
    assert out["day"].tolist() == [_day("2023-03-11"), _day("2023-03-12"), _day("2023-03-12"), _day("2023-03-11")]
    assert (out["day"] > pd.to_datetime(out["as_of_ts"], utc=True)).all()         # strictly after the observation
    assert list(items.columns) == [c for c in out.columns if c not in ("day", "news", "timely")]


def test_news_is_timely_up_to_two_days_after_its_publication_date_and_posts_always():
    items = pd.DataFrame([
        _timed("2023-03-10 12:00", "2023-03-10 01:00"),                    # usable one day after the publication date
        _timed("2023-03-10 12:00", "2023-03-09 00:00"),                    # two days after
        _timed("2023-03-10 12:00", "2023-03-08 23:59"),                    # three days after: late
        _timed("2023-03-11 00:00", "2023-03-09 23:00"),                    # midnight waits a day, which makes it late
        _timed("2023-03-10 12:00", "2023-03-01 00:00", source="reddit")])  # a community post is always timely
    out = c4.item_days(items)
    assert out["news"].tolist() == [True, True, True, True, False]
    assert out["timely"].tolist() == [True, True, False, False, True]
    assert c4.TIMELY_DAYS == 2


def test_timing_facts_count_days_after_publication_and_hours_to_the_decision():
    items = pd.DataFrame([
        _timed("2023-03-10 12:00", "2023-03-10 10:00"),                    # one day after, waits 12 hours
        _timed("2023-03-10 18:00", "2023-03-09 10:00"),                    # two days after, waits 6 hours
        _timed("2023-03-10 00:00", "2023-03-07 10:00"),                    # four days after, waits 24 hours
        _timed("2022-12-31 23:00", "2022-12-31 22:00"),                    # decision of 2023-01-01: counted in 2023
        _timed("2022-06-01 02:00", "2022-06-01 01:00"),                    # waits 22 hours
        _timed("2023-03-10 12:00", "2023-03-10 10:00", source="reddit"),
        _timed("2023-03-10 12:00", "2023-01-01 10:00", source="reddit")])
    facts = c4.timing_facts(items)
    news = facts["news_rows"]
    assert facts["timely_days"] == 2 and facts["community_rows"] == 2 and news["rows"] == 5
    assert news["timely_share"] == pytest.approx(4 / 5)
    assert news["usable_days_after_publication"] == {"1": pytest.approx(3 / 5), "2": pytest.approx(1 / 5), "3_or_more": pytest.approx(1 / 5)}
    assert news["hours_from_observation_to_decision"]["median"] == pytest.approx(12.0)
    assert set(facts["by_year"]) == {"2022", "2023"} and facts["by_year"]["2022"]["rows"] == 1 and facts["by_year"]["2023"]["rows"] == 4
    assert facts["by_year"]["2022"]["hours_from_observation_to_decision"]["median"] == pytest.approx(22.0)
    assert facts["by_year"]["2023"]["timely_share"] == pytest.approx(3 / 4)
    json.dumps(facts)


def test_window_sums_the_days_inside_the_grid():
    values = np.random.default_rng(0).normal(size=(40, 3))
    for back, ahead in ((6, 0), (6, -1), (28, -1), (0, 0)):
        got = c4._window(values, back, ahead)
        for i in (0, 1, 5, 6, 7, 30, 39):
            lo, hi = max(i - back, 0), i + ahead
            assert np.allclose(got[i], values[lo:hi + 1].sum(axis=0) if hi >= lo else 0.0)


# ---------------------------------------------------------------- block A
def _random_items(seed: int = 0, n: int = 600) -> pd.DataFrame:
    """Item rows of two assets over ten weeks from the store start: mixed sources, late news, repeated documents."""
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(n):
        seen = STORE + pd.Timedelta(minutes=int(rng.integers(0, 70 * 24 * 60)))
        lag = pd.Timedelta(hours=float(rng.choice([1, 5, 30, 60, 100])))
        rows.append(_item(f"d{int(rng.integers(0, n // 2))}", str(rng.choice(["AAA", "BBB", "ZZZ"])),
                          source=str(rng.choice(["wayback", "cryptopanic", "reddit"])), event_ts=seen - lag, as_of_ts=seen))
    return pd.DataFrame(rows)


def _attention_by_hand(items: pd.DataFrame, day: pd.Timestamp, base: str) -> dict:
    rows = items[items["timely"] & (items["base"] == base)]
    count = lambda d, news: rows[(rows["day"] == d) & (rows["news"] == news)]["doc_id"].nunique()     # noqa: E731
    both = lambda d: count(d, True) + count(d, False)                                                 # noqa: E731
    first = STORE + DAY
    history = [d for d in pd.date_range(day - 28 * DAY, day - DAY, freq="D") if d >= first]
    own = np.mean([np.log1p(both(d)) for d in history]) if len(history) >= 14 else np.nan
    return {"news_1d": np.log1p(count(day, True)), "posts_1d": np.log1p(count(day, False)),
            "attn_7d": np.log1p(sum(both(d) for d in pd.date_range(day - 6 * DAY, day, freq="D"))),
            "attn_abn_1d": np.log1p(both(day)) - own}


def test_attention_counts_distinct_timely_documents_by_usable_day():
    items = c4.item_days(_random_items())
    assert (~items["timely"]).sum() > 20 and items.duplicated(["day", "base", "doc_id"]).any()
    keys = _grid_keys(STORE + 5 * DAY, STORE + 70 * DAY)
    out = c4.attention_daily(items, keys, STORE).set_index(["date", "base"])
    assert list(out.columns) == c4.BLOCK_A and len(out) == len(keys)
    for day in (STORE + 5 * DAY, STORE + 14 * DAY, STORE + 15 * DAY, STORE + 16 * DAY, STORE + 40 * DAY, STORE + 70 * DAY):
        for base in ("AAA", "BBB"):
            hand = _attention_by_hand(items, day, base)
            for col in c4.BLOCK_A:
                assert out.loc[(day, base), col] == pytest.approx(hand[col], nan_ok=True, abs=1e-12), (day, base, col)
    missing = out["attn_abn_1d"].isna().groupby(level="date").all()
    assert missing[missing].index.max() == STORE + 14 * DAY                 # fourteen history days from the fifteenth grid day on
    assert out.drop(columns="attn_abn_1d").notna().all().all()


def test_attention_ignores_late_news_and_other_assets():
    base_rows = [_timed("2023-03-10 12:00", "2023-03-10 10:00", doc="a"), _timed("2023-03-10 13:00", "2023-03-10 10:00", doc="p", source="reddit")]
    extra = [_timed("2023-03-10 12:00", "2023-03-07 10:00", doc="late"), _timed("2023-03-10 12:00", "2023-03-10 10:00", doc="other", base="ZZZ"),
             _timed("2023-03-11 00:00", "2023-03-10 10:00", doc="midnight")]
    keys = _grid_keys(D0, D0, bases=("AAA",))
    plain = c4.attention_daily(c4.item_days(pd.DataFrame(base_rows)), keys, STORE)
    more = c4.attention_daily(c4.item_days(pd.DataFrame(base_rows + extra)), keys, STORE)
    pd.testing.assert_frame_equal(plain, more)
    assert plain["news_1d"].tolist() == [pytest.approx(np.log(2))] and plain["posts_1d"].tolist() == [pytest.approx(np.log(2))]
    assert plain["attn_7d"].tolist() == [pytest.approx(np.log(3))]


def test_decision_days_before_the_store_are_refused():
    items = c4.item_days(pd.DataFrame([_timed("2023-03-10 12:00", "2023-03-10 10:00")]))
    with pytest.raises(ValueError, match="outside the item grid"):
        c4.attention_daily(items, _grid_keys(STORE, STORE + 3 * DAY), STORE)


# ---------------------------------------------------------------- block R
def _seen(doc: str, back: pd.Timedelta = DAY - 5 * HOUR, base: str = "AAA", lag: pd.Timedelta = 2 * HOUR, **kwargs) -> dict:
    """An item row observed ``back`` before the decision day ``D0`` (published ``lag`` earlier)."""
    return _item(doc, base, event_ts=D0 - back - lag, as_of_ts=D0 - back, **kwargs)


def _reader_case():
    """Hand-made rows around the decision day ``D0``; the expected features are in the test below."""
    items = [
        _seen("e1"), _seen("e2"), _seen("e3"), _seen("e4"),
        _seen("o1", type_="analysis_opinion"), _seen("o2", type_="analysis_opinion"), _seen("o3", type_="analysis_opinion"),
        _seen("o4", type_="analysis_opinion"),
        _seen("u1"), _seen("s1"),
        _seen("late", lag=4 * DAY),                                         # published four days before it was seen
        _seen("r1", source="reddit"),                                       # a community post never enters block R
        _seen("x1", base="BBB"),
        _seen("p1", back=2 * DAY - HOUR), _seen("p6", back=7 * DAY - HOUR), _seen("p7", back=8 * DAY - HOUR),
        _seen("m1", back=pd.Timedelta(0)),                                  # stamped at the decision itself: next day
        _seen("g1", type_=None), _seen("g2"), _seen("g3", salience="mentioned"),
    ]
    records = [
        _record_row("e1", "security_incident", "occurred", "unfavourable", 2),
        _record_row("e2", "security_incident", "occurred", "unfavourable", 3),           # same event as e1: once, at 3
        _record_row("e3", "security_incident", "occurred", "mixed", 1),                  # same class, another direction
        _record_row("e4", "protocol_upgrade_or_launch", "occurred", "favourable", 2, resolution="adjudicated"),
        _record_row("o1", "opinion_or_forecast", "occurred", "favourable", 2),
        _record_row("o2", "opinion_or_forecast", "occurred", "unfavourable", 3),
        _record_row("o3", "opinion_or_forecast", "occurred", "favourable", 1),
        _record_row("o4", "opinion_or_forecast", "occurred", "mixed", 1),
        _record_row("u1", resolution="unresolved"),
        _record_row("s1", "legal_regulatory", "occurred", "unfavourable", 3, relevance="side_mention"),
        _record_row("late", "listing", "occurred", "favourable", 3),
        _record_row("r1", "listing", "occurred", "favourable", 3),
        _record_row("x1", "listing", "occurred", "favourable", 1, base="BBB"),
        _record_row("p1", "legal_regulatory", "occurred", "unfavourable", 1),
        _record_row("p6", "listing", "occurred", "favourable", 2),
        _record_row("p7", "listing", "occurred", "favourable", 3),
        _record_row("m1", "listing", "occurred", "favourable", 3),
    ]
    docs = [_doc(row["doc_id"], {"Asset_A": f"asset:{'BBB' if row['doc_id'] in ('x1', 'g3') else 'AAA'}"}) for row in items]
    recs = consensus.record_frame([{**dict.fromkeys(consensus.RECORD_COLUMNS), **r} for r in records])
    return pd.DataFrame(items), pd.DataFrame(docs), recs


def test_reader_features_sum_signed_materiality_per_usable_day():
    items, docs, recs = _reader_case()
    flagged = c4.item_days(reading.flag_items(items, docs))
    keys = _grid_keys(D0 - 10 * DAY, D0 + DAY)
    out = c4.reader_daily(flagged, recs, keys, STORE).set_index(["date", "base"])
    today = out.loc[(D0, "AAA")]
    assert today["tone_1d"] == -3 + 0 + 2                                   # e1 and e2 once at 3, e3 mixed, e4 favourable
    assert today["unfav_1d"] == 3 and today["evt_1d"] == 3 + 1 + 2
    assert today["stance_1d"] == 1 - 1 + 1 + 0
    assert today["tone_prev6"] == -1 + 2 and today["unfav_prev6"] == 1      # p1 the day before, p6 six days before, p7 outside
    assert today["n_subject_1d"] == 8 and today["n_subject_7d"] == 10       # rows before the events are merged
    assert today["gap_1d"] == 2 and today["gap_7d"] == 2                    # untyped g1, read g2 without a record; g3 is not read
    tomorrow = out.loc[(D0 + DAY, "AAA")]
    assert tomorrow["tone_1d"] == 3 and tomorrow["evt_1d"] == 3 and tomorrow["unfav_1d"] == 0     # m1 waits a day
    assert tomorrow["tone_prev6"] == -1 - 1 and tomorrow["unfav_prev6"] == 3 + 1                  # p6 has left the six days
    assert out.loc[(D0, "BBB"), "tone_1d"] == 1 and out.loc[(D0, "BBB"), "gap_1d"] == 0
    before = out.loc[(D0 - DAY, "AAA")]
    assert before["tone_1d"] == -1 and before["tone_prev6"] == 2 + 3        # p6 and p7 are both within the six days before
    assert list(out.columns) == [*c4.BLOCK_R, *c4.COUNTS, *c4.GAPS]


def test_reader_features_ignore_unresolved_side_mention_late_and_community_rows():
    items, docs, recs = _reader_case()
    drop = ["u1", "s1", "late", "r1"]
    flag = lambda frame: c4.item_days(reading.flag_items(frame, docs))      # noqa: E731
    keys = _grid_keys(D0 - 10 * DAY, D0 + DAY)
    full = c4.reader_daily(flag(items), recs, keys, STORE)
    less = c4.reader_daily(flag(items[~items["doc_id"].isin(drop)].reset_index(drop=True)), recs[~recs["doc_id"].isin(drop)], keys, STORE)
    pd.testing.assert_frame_equal(full, less)
    subj = c4.subject_rows(flag(items), recs)
    assert not set(drop) & set(subj["doc_id"]) and {"e1", "e4", "o1", "p7", "m1", "x1"} <= set(subj["doc_id"])


def test_gap_rows_are_untyped_rows_and_read_rows_without_a_record():
    items, docs, recs = _reader_case()
    flagged = c4.item_days(reading.flag_items(items, docs))
    assert set(c4.gap_rows(flagged, recs)["doc_id"]) == {"g1", "g2"}
    assert set(c4.gap_rows(flagged, recs[recs["doc_id"] != "e1"])["doc_id"]) == {"g1", "g2", "e1"}
    late = flagged.assign(timely=flagged["timely"] & (flagged["doc_id"] != "g2"))
    assert set(c4.gap_rows(late, recs)["doc_id"]) == {"g1"}


def test_an_unknown_direction_is_refused():
    items, docs, recs = _reader_case()
    recs.loc[recs["doc_id"] == "e4", "direction"] = "sideways"
    with pytest.raises(ValueError, match="unknown direction"):
        c4.subject_rows(c4.item_days(reading.flag_items(items, docs)), recs)


def test_text_features_join_both_blocks_on_the_panel_keys():
    items, docs, recs = _reader_case()
    keys = _grid_keys(D0 - 3 * DAY, D0 + DAY).assign(symbol=lambda f: f["base"] + "USDT")
    out = c4.text_features(items, docs, recs, keys)
    assert list(out.columns) == ["date", "base", *c4.TEXT_COLUMNS] and len(out) == len(keys)
    row = out.set_index(["date", "base"]).loc[(D0, "AAA")]
    assert row["tone_1d"] == -1 and row["tone_prev6"] == 1 and row["gap_1d"] == 2
    assert row["news_1d"] == pytest.approx(np.log1p(13)) and row["posts_1d"] == pytest.approx(np.log(2))
    assert out[[c for c in c4.TEXT_COLUMNS if c != "attn_abn_1d"]].notna().all().all()
    assert set(c4.TONE) <= set(c4.BLOCK_R) and set(c4.FRESH) <= set(c4.BLOCK_R)


# ---------------------------------------------------------------- bar history and forward targets
def _log_returns(bars: pd.DataFrame) -> pd.Series:
    return np.log(bars["close"] / bars["close"].shift(1))


def test_bar_history_uses_the_bars_up_to_the_bar_itself():
    bars, market = _bars(120, seed=0), _log_returns(_bars(120, seed=1))
    hist = c4.bar_history(bars, market)
    assert list(hist.columns) == c4.HIST_BARS and hist.index.equals(bars.index)
    k = 100
    close, volume, gk, own = bars["close"].to_numpy(), bars["quote_volume"].to_numpy(), _gk(bars).to_numpy(), _log_returns(bars).to_numpy()
    row = hist.iloc[k]
    assert row["ret_1d"] == pytest.approx(np.log(close[k] / close[k - 1]))
    assert row["ret_7d"] == pytest.approx(np.log(close[k] / close[k - 7]))
    assert row["ret_30d"] == pytest.approx(np.log(close[k] / close[k - 30]))
    assert row["rv_1d"] == pytest.approx(gk[k])
    assert row["rv_7d"] == pytest.approx(gk[k - 6:k + 1].mean()) and row["rv_30d"] == pytest.approx(gk[k - 29:k + 1].mean())
    assert row["dvol_30d"] == pytest.approx(volume[k - 29:k + 1].mean())
    assert row["vsurge_1d"] == pytest.approx(np.log(volume[k] / volume[k - 29:k + 1].mean()))
    pair = slice(k - 59, k + 1)
    assert row["beta_60d"] == pytest.approx(np.cov(own[pair], market.to_numpy()[pair])[0, 1] / market.to_numpy()[pair].var(ddof=1))
    pd.testing.assert_series_equal(c4.bar_history(bars.iloc[:k + 1], market).iloc[k], row)      # no later bar
    changed = bars.copy()
    changed.iloc[k + 1:] *= 3.0
    pd.testing.assert_frame_equal(c4.bar_history(changed, market).iloc[:k + 1], hist.iloc[:k + 1])


def test_bar_history_needs_a_minimum_of_bars():
    bars, market = _bars(120, seed=2), _log_returns(_bars(120, seed=3))
    hist = c4.bar_history(bars, market)
    assert np.isnan(hist["ret_1d"].iloc[0]) and np.isfinite(hist["ret_1d"].iloc[1])
    assert np.isnan(hist["ret_7d"].iloc[6]) and np.isfinite(hist["ret_7d"].iloc[7])
    assert np.isnan(hist["rv_7d"].iloc[c4.MIN_BARS_SHORT - 2]) and np.isfinite(hist["rv_7d"].iloc[c4.MIN_BARS_SHORT - 1])
    assert np.isnan(hist["rv_30d"].iloc[c4.MIN_BARS_LONG - 2]) and np.isfinite(hist["rv_30d"].iloc[c4.MIN_BARS_LONG - 1])
    assert np.isnan(hist["dvol_30d"].iloc[c4.MIN_BARS_LONG - 2]) and np.isfinite(hist["vsurge_1d"].iloc[c4.MIN_BARS_LONG - 1])
    assert np.isnan(hist["beta_60d"].iloc[c4.MIN_BETA_PAIRS - 1]) and np.isfinite(hist["beta_60d"].iloc[c4.MIN_BETA_PAIRS])
    gap = bars.drop(index=bars.index[50])
    assert np.isnan(c4.bar_history(gap, market).loc[bars.index[51], "ret_1d"])             # a calendar day back, not a bar back
    assert c4.bar_history(bars, _log_returns(bars))["beta_60d"].iloc[-1] == pytest.approx(1.0)


def _store(tmp_path, n: int = 120) -> tuple[pd.DataFrame, pd.DataFrame]:
    bars, market = _bars(n, seed=0), _bars(n, seed=1)
    bars.to_parquet(tmp_path / "AAAUSDT.parquet")
    market.to_parquet(tmp_path / f"{c4.MARKET}.parquet")
    return bars, market


def test_history_features_read_the_bar_that_closes_at_the_decision(tmp_path):
    bars, market = _store(tmp_path)
    days = pd.date_range("2023-03-11", "2023-03-20", freq="D", tz="UTC")
    hist = c4.history_features(tmp_path, _keys(days))
    assert list(hist.columns) == ["date", "symbol", *c4.HIST_BARS] and hist["date"].tolist() == list(days)
    full = c4.bar_history(bars, _log_returns(market))
    for day, (_, row) in zip(days, hist.iterrows()):
        expected = full.loc[day - DAY]
        assert all(row[c] == pytest.approx(expected[c]) for c in c4.HIST_BARS)
    later = bars.copy()
    later.loc[later.index >= days[-1]] *= 5.0                                # the bar of the last decision day and later
    later.to_parquet(tmp_path / "AAAUSDT.parquet")
    moved = market.copy()
    moved.loc[moved.index >= days[-1]] *= 5.0
    moved.to_parquet(tmp_path / f"{c4.MARKET}.parquet")
    pd.testing.assert_frame_equal(c4.history_features(tmp_path, _keys(days)), hist)
    one = c4.history_features(tmp_path, _keys(days[:4]))                      # an earlier row does not depend on later decisions
    pd.testing.assert_frame_equal(one, hist.iloc[:4])
    inside = bars.copy()
    inside.loc[inside.index >= days[4]] *= 5.0                                # bars from the fifth decision day on
    inside.to_parquet(tmp_path / "AAAUSDT.parquet")
    market.to_parquet(tmp_path / f"{c4.MARKET}.parquet")
    pd.testing.assert_frame_equal(c4.history_features(tmp_path, _keys(days)).iloc[:5], hist.iloc[:5])


def test_history_features_are_missing_without_the_bar_of_the_day_before(tmp_path):
    bars, _ = _store(tmp_path)
    bars.drop(index=[_day("2023-03-12")]).to_parquet(tmp_path / "AAAUSDT.parquet")
    hist = c4.history_features(tmp_path, _keys(pd.date_range("2023-03-12", "2023-03-14", freq="D", tz="UTC"))).set_index("date")
    assert hist.loc[_day("2023-03-13"), c4.HIST_BARS].isna().all()
    assert hist.loc[_day("2023-03-12"), c4.HIST_BARS].notna().all()
    assert np.isnan(hist.loc[_day("2023-03-14"), "ret_1d"]) and np.isfinite(hist.loc[_day("2023-03-14"), "rv_30d"])


def test_forward_targets_are_the_bars_from_the_decision_on(tmp_path):
    bars, _ = _store(tmp_path)
    days = pd.date_range("2023-03-11", "2023-03-20", freq="D", tz="UTC")
    fwd = c4.forward_targets(tmp_path, _keys(days))
    assert list(fwd.columns) == ["date", "symbol", *c4.TARGET_COLUMNS]
    close, gk = bars["close"], _gk(bars)
    for _, row in fwd.iterrows():
        day = row["date"]
        assert row["fwd_ret_1d"] == pytest.approx(close[day] / close[day - DAY] - 1.0)
        assert row["fwd_absret_1d"] == pytest.approx(abs(close[day] / close[day - DAY] - 1.0))
        assert row["fwd_rv_1d"] == pytest.approx(gk[day])
        assert row["fwd_ret_3d"] == pytest.approx(close[day + 2 * DAY] / close[day - DAY] - 1.0)
    later = bars.copy()
    later.loc[later.index > days[-1] + 2 * DAY] *= 7.0                       # nothing after the third bar of the last decision
    later.to_parquet(tmp_path / "AAAUSDT.parquet")
    pd.testing.assert_frame_equal(c4.forward_targets(tmp_path, _keys(days)), fwd)
    bars[bars.index <= days[-1]].to_parquet(tmp_path / "AAAUSDT.parquet")    # the store ends with the bar of the last decision
    short = c4.forward_targets(tmp_path, _keys(days)).set_index("date")
    assert short["fwd_ret_1d"].notna().all() and short["fwd_ret_3d"].isna().sum() == 2
    bars.drop(index=[days[3]]).to_parquet(tmp_path / "AAAUSDT.parquet")
    holed = c4.forward_targets(tmp_path, _keys(days)).set_index("date")
    assert np.isnan(holed.loc[days[3], "fwd_ret_1d"]) and np.isnan(holed.loc[days[4], "fwd_ret_1d"])       # exit, then entry missing
    assert np.isnan(holed.loc[days[3], "fwd_rv_1d"]) and np.isfinite(holed.loc[days[2], "fwd_ret_1d"])
    assert np.isnan(holed.loc[days[1], "fwd_ret_3d"])


def test_registered_target_and_feature_sets():
    assert c4.TARGET == "fwd_ret_1d" and c4.TARGET_COLUMNS[0] == c4.TARGET and set(c4.OTHER_TARGETS) == set(c4.TARGET_COLUMNS[1:])
    assert c4.OTHER_TARGETS == {"fwd_absret_1d": 1, "fwd_rv_1d": 1, "fwd_ret_3d": 3}
    assert c4.GATE_SCORE == "s_reader" and c4.PARTIAL_SCORES["s_reader"] == (c4.TONE, c4.CONTROLS, True)
    assert c4.TONE == ["tone_1d", "tone_prev6"] and c4.PARTIAL_SCORES["s_block_r"] == (c4.BLOCK_R, c4.CONTROLS, True)
    assert c4.CONTROLS == c4.HIST + c4.BLOCK_A and len(c4.CONTROLS) == 15 and not set(c4.CONTROLS) & set(c4.BLOCK_R)
    assert (c4.GATE_T, c4.GATE_YEARS, c4.NW_LAG, c4.GATE_FORM, c4.BURN_IN_DAYS) == (2.0, (2023, 2024), 7, "corr", 364)
    assert (c4.PANEL_FIRST, c4.PANEL_LAST, c4.MIN_DAY_ROWS) == ("2022-01-08", "2024-12-28", 30)
    assert set(c4.SCORES) == set(c4.PARTIAL_SCORES) | set(c4.FORECASTS) | set(c4.GBM_FORECASTS)
    assert not any(c.startswith("fwd_") for c in [*c4.HIST, *c4.TEXT_COLUMNS])


# ---------------------------------------------------------------- panel
def test_assemble_panel_joins_on_day_and_contract():
    uni, feats, hist, fwd = synth(days=20, n=6)
    fwd = fwd.iloc[3:]
    panel = c4.assemble_panel(uni.sample(frac=1.0, random_state=0), feats.sample(frac=1.0, random_state=1), hist, fwd)
    assert list(panel.columns) == c4.PANEL_COLUMNS and len(panel) == len(uni)
    assert (c4._dates(panel) == c4._dates(uni)).all() and panel["symbol"].tolist() == uni["symbol"].tolist()
    assert panel[c4.TARGET].isna().sum() == len(uni) - len(fwd) > 0                # rows without an outcome stay in the panel
    for col, source in (("tone_1d", feats), ("gap_7d", feats), ("rv_30d", hist), ("age_weeks", uni)):
        assert np.allclose(panel[col].to_numpy(), source[col].to_numpy(), equal_nan=True)
    with_target = panel.merge(fwd, on=["date", "symbol"], suffixes=("", "_source"))
    assert np.allclose(with_target[c4.TARGET], with_target[f"{c4.TARGET}_source"])
    assert panel["attn_abn_1d"].isna().any()                                        # the one text column that may be missing


def test_assemble_panel_refuses_incomplete_inputs():
    uni, feats, hist, fwd = synth(days=20, n=6)
    with pytest.raises(ValueError, match="not unique"):
        c4.assemble_panel(pd.concat([uni, uni.iloc[[0]]], ignore_index=True), feats, hist, fwd)
    with pytest.raises(ValueError, match="without text features"):
        c4.assemble_panel(uni, feats.iloc[1:], hist, fwd)
    with pytest.raises(ValueError, match="without bar history"):
        c4.assemble_panel(uni, feats, hist.iloc[1:], fwd)
    broken = feats.copy()
    broken.loc[3, "tone_1d"] = np.nan
    with pytest.raises(ValueError, match="text features with missing values"):
        c4.assemble_panel(uni, broken, hist, fwd)


def test_target_rank_is_the_within_day_rank_of_the_rows_with_an_outcome():
    frame = pd.DataFrame({"date": [D0] * 4 + [D0 + DAY] * 2, c4.TARGET: [0.03, -0.01, 0.02, np.nan, 0.5, 0.4]})
    rank = c4.target_rank(frame)
    assert np.allclose(rank[:3], [0.5, 1 / 3 - 0.5, 2 / 3 - 0.5]) and np.isnan(rank[3]) and np.allclose(rank[4:], [0.5, 0.0])


# ---------------------------------------------------------------- residuals and walk-forward
def _stamps(n_days: int, rows: int, start=D0) -> np.ndarray:
    days = pd.date_range(start, periods=n_days, freq="D")
    return c4._dates(pd.DataFrame({"date": np.repeat(days, rows)}))


def test_residuals_are_orthogonal_to_the_controls_within_every_day():
    rng = np.random.default_rng(0)
    dates = _stamps(6, 40)
    controls, values = rng.normal(size=(240, 3)), rng.normal(size=(240, 2))
    values[5, 1] = np.nan                                                    # the columns differ in one missing row
    values[40:80][5:, 0] = np.nan                                            # second day: five rows left in the first column
    out = c4.residuals(values, controls, dates, min_rows=10)
    assert np.isnan(out[40:80, 0]).all() and np.isfinite(out[40:80, 1]).all()       # too few rows: missing on that day
    assert np.isnan(out[5, 1]) and np.isfinite(out[5, 0])
    for day in range(6):
        rows = np.arange(40 * day, 40 * day + 40)
        for j in range(2):
            have = np.isfinite(values[rows, j])
            if have.sum() < 10:
                continue
            design = np.column_stack([np.ones(have.sum()), controls[rows][have]])
            beta, *_ = np.linalg.lstsq(design, values[rows, j][have], rcond=None)
            assert np.allclose(out[rows[have], j], values[rows, j][have] - design @ beta)
            assert np.allclose(design.T @ out[rows[have], j], 0.0, atol=1e-9)
    default = c4.residuals(values, controls, dates)                          # the registered minimum of 30 rows a day
    assert np.isfinite(default[:40, 1]).sum() == 39 and np.isnan(default[40:80, 0]).all()
    assert np.isnan(c4.residuals(values, controls, dates, min_rows=40)[:40, 1]).all()


def _ridge(X: np.ndarray, y: np.ndarray, alpha: float = RIDGE_ALPHA) -> np.ndarray:
    return np.linalg.solve(X.T @ X + alpha * np.eye(X.shape[1]), X.T @ y)


@pytest.mark.parametrize("horizon", [1, 3])
def test_walk_forward_is_a_ridge_on_the_days_whose_outcome_has_closed(horizon):
    rng = np.random.default_rng(1)
    n_days, rows, burn = 30, 12, 10
    dates = _stamps(n_days, rows)
    day = np.repeat(np.arange(n_days), rows)
    X, E = rng.normal(size=(n_days * rows, 2)), rng.normal(size=(n_days * rows, 1))
    X[7, 0], E[20, 0] = np.nan, np.nan
    last = n_days * rows - 1
    E[last, 0] = np.nan                                                      # a row without an outcome is still scored
    score, coef = c4.walk_forward(X, E, dates, horizon, burn_in=burn)
    assert coef.shape == (n_days, 2, 1) and score.shape == (n_days * rows, 1)
    usable = np.isfinite(X).all(axis=1) & np.isfinite(E[:, 0])
    for d in range(n_days):
        if d - horizon + 1 < burn:
            assert np.isnan(score[day == d]).all() and np.isnan(coef[d]).all()
            continue
        train = usable & (day <= d - horizon)
        beta = _ridge(X[train], E[train, 0])
        assert np.allclose(coef[d, :, 0], beta) and np.allclose(score[day == d, 0], X[day == d] @ beta)
    assert np.isfinite(score[last, 0])
    changed = E.copy()
    changed[day >= 20] += 5.0                                                # outcomes that close after the decision of day 20
    again, _ = c4.walk_forward(X, changed, dates, horizon, burn_in=burn)
    assert np.allclose(again[day <= 20 + horizon - 1], score[day <= 20 + horizon - 1], equal_nan=True)
    assert not np.allclose(again[day == 20 + horizon], score[day == 20 + horizon])


def test_walk_forward_skips_rows_without_features_and_takes_several_targets():
    rng = np.random.default_rng(2)
    dates = _stamps(20, 10)
    X, E = rng.normal(size=(200, 2)), rng.normal(size=(200, 3))
    X[150, 1] = np.nan
    score, coef = c4.walk_forward(X, E, dates, burn_in=5)
    assert np.isnan(score[150]).all() and np.isfinite(score[151:160]).all()
    for j in range(3):
        one, _ = c4.walk_forward(X, E[:, [j]], dates, burn_in=5)
        assert np.allclose(one[:, 0], score[:, j], equal_nan=True)
    assert c4.walk_forward.__defaults__[:2] == (1, c4.BURN_IN_DAYS) and c4.BURN_IN_DAYS == 364


def test_days_must_be_consecutive_calendar_days():
    dates = _stamps(10, 4)
    with pytest.raises(ValueError, match="not consecutive calendar days"):
        c4._day_index(dates[dates != dates[20]])
    days, idx = c4._day_index(dates[::-1])
    assert len(days) == 10 and (np.diff(days) == DAY.value).all() and idx[0] == 9


def test_past_trees_serve_a_day_with_trees_fitted_on_earlier_days(monkeypatch):
    import lightgbm as lgb

    monkeypatch.setattr(c4, "CLEAN_ROUNDS", 15)
    monkeypatch.setattr(c4, "CLEAN_FIRST", 20)
    monkeypatch.setattr(c4, "CLEAN_EVERY", 10)
    rng = np.random.default_rng(3)
    n_days, rows = 45, 40
    dates, day = _stamps(n_days, rows), np.repeat(np.arange(n_days), rows)
    controls = rng.uniform(-0.5, 0.5, size=(n_days * rows, 3))
    values = np.column_stack([np.abs(controls[:, 0]) + 0.1 * rng.normal(size=len(controls)), rng.normal(size=len(controls))])
    out = c4.past_trees(values, controls, dates)

    def by_hand(train, serve, j):
        booster = lgb.train(dict(c4.CLEAN_PARAMS), lgb.Dataset(controls[train], label=values[train, j]), num_boost_round=15)
        return values[serve, j] - booster.predict(controls[serve])

    for j in range(2):
        assert np.allclose(out[day < 20, j], by_hand(day < 20, day < 20, j))                     # the head is fitted on itself
        assert np.allclose(out[(day >= 20) & (day < 30), j], by_hand(day < 20, (day >= 20) & (day < 30), j))
        assert np.allclose(out[(day >= 30) & (day < 40), j], by_hand(day < 30, (day >= 30) & (day < 40), j))
        assert np.allclose(out[day >= 40, j], by_hand(day < 40, day >= 40, j))
    assert out[day >= 20, 0].var() < values[day >= 20, 0].var()                                  # the curve is taken out
    later = values.copy()
    later[day >= 30] += 1.0
    assert np.allclose(c4.past_trees(later, controls, dates)[day < 30], out[day < 30])           # nothing from later days
    broken = values.copy()
    broken[3, 0] = np.nan
    with pytest.raises(ValueError, match="missing value in a rank"):
        c4.past_trees(broken, controls, dates)


@pytest.mark.parametrize("horizon", [1, 3])
def test_past_surface_is_fitted_on_the_days_whose_outcome_has_closed(monkeypatch, horizon):
    monkeypatch.setattr(c4, "CLEAN_FIRST", 5)
    rng = np.random.default_rng(4)
    n_days, rows = 14, 30
    dates, day = _stamps(n_days, rows), np.repeat(np.arange(n_days), rows)
    controls = rng.uniform(-0.5, 0.5, size=(n_days * rows, 2))
    values = np.column_stack([controls[:, 0] ** 2 + 0.05 * rng.normal(size=len(controls)), rng.normal(size=len(controls))])
    values[[4, 200]] = np.nan
    out = c4.past_surface(values, controls, dates, horizon)
    basis, have = c3.quadratic_basis(controls), np.isfinite(values[:, 0])
    penalty = c4.CLEAN_ALPHA * np.eye(basis.shape[1])
    penalty[0, 0] = 0.0

    def by_hand(train, serve):
        beta = np.linalg.solve(basis[train].T @ basis[train] + penalty, basis[train].T @ values[train])
        return values[serve] - basis[serve] @ beta

    assert np.isnan(out[[4, 200]]).all() and np.isfinite(out[have]).all()
    assert np.allclose(out[have & (day < 5)], by_hand(have & (day < 5), have & (day < 5)))       # the head is fitted on itself
    for d in range(5, n_days):
        assert np.allclose(out[have & (day == d)], by_hand(have & (day <= d - horizon), have & (day == d)))
    later = values.copy()
    later[day >= 9] += 1.0
    again = c4.past_surface(later, controls, dates, horizon)
    assert np.allclose(again[have & (day <= 9 + horizon - 1) & (day < 9)], out[have & (day <= 9 + horizon - 1) & (day < 9)])
    uneven = values.copy()
    uneven[7, 1] = np.nan
    with pytest.raises(ValueError, match="differ in their missing rows"):
        c4.past_surface(uneven, controls, dates, horizon)


# ---------------------------------------------------------------- daily statistics
def test_daily_statistics_are_the_within_day_correlation_and_covariance():
    rng = np.random.default_rng(5)
    dates, day = _stamps(4, 40), np.repeat(np.arange(4), 40)
    a, b = rng.normal(size=160), rng.normal(size=160)
    a[40:80] = 1.0                                                               # no variation on the second day
    b[80:91] = np.nan                                                            # 29 rows on the third day
    days, corr, cov = c4.daily_stats(dates, a, b)
    assert corr.shape == cov.shape == (4, 1) and [c4._stamp(d) for d in days] == [D0 + i * DAY for i in range(4)]
    for d in (0, 3):
        x, y = a[day == d], b[day == d]
        assert corr[d, 0] == pytest.approx(np.corrcoef(x, y)[0, 1])
        assert cov[d, 0] == pytest.approx(((x - x.mean()) * (y - y.mean())).mean())
    assert np.isnan(corr[[1, 2], 0]).all() and np.isnan(cov[[1, 2], 0]).all()
    _, few, few_cov = c4.daily_stats(dates, a, b, min_rows=29)
    x, y = a[91:120], b[91:120]
    assert few[2, 0] == pytest.approx(np.corrcoef(x, y)[0, 1]) and few_cov[2, 0] == pytest.approx(((x - x.mean()) * (y - y.mean())).mean())
    assert c4.MIN_DAY_ROWS == 30
    series = c4.daily_statistic(dates, a, b)
    assert list(series.index) == [D0, D0 + 3 * DAY] and np.allclose(series.to_numpy(), corr[[0, 3], 0])
    assert np.allclose(c4.daily_statistic(dates, a, b, "cov").to_numpy(), cov[[0, 3], 0]) and c4.GATE_FORM == "corr"


def test_daily_statistics_take_columns_with_their_own_missing_rows():
    rng = np.random.default_rng(6)
    dates, day = _stamps(3, 40), np.repeat(np.arange(3), 40)
    A, B = rng.normal(size=(120, 3)), rng.normal(size=(120, 3))
    A[5, 1], B[50, 2] = np.nan, np.nan                                           # one missing row in one column only
    A[80:95, 0] = np.nan                                                         # 25 rows left on the third day in the first column
    _, corr, cov = c4.daily_stats(dates, A, B)
    for j in range(3):
        _, one, one_cov = c4.daily_stats(dates, A[:, j], B[:, j])
        assert np.allclose(corr[:, j], one[:, 0], equal_nan=True) and np.allclose(cov[:, j], one_cov[:, 0], equal_nan=True)
    ok = np.isfinite(A[:40, 1])
    assert corr[0, 1] == pytest.approx(np.corrcoef(A[:40, 1][ok], B[:40, 1][ok])[0, 1])
    assert np.isnan(corr[2, 0]) and np.isfinite(corr[2, 1:]).all() and np.isfinite(corr[:2]).all()
    same, _, _ = c4.daily_stats(dates, A, np.repeat(B[:, :1], 3, axis=1))        # one target against three scores
    assert same.shape == (3,) and (day == np.repeat(np.arange(3), 40)).all()


def test_newey_west_t_per_column_and_the_series_summary():
    rng = np.random.default_rng(7)
    values = rng.normal(0.2, 1.0, size=(60, 3))
    values[::5, 1] = np.nan
    values[2:, 2] = np.nan                                                       # two days only: no t
    t = c4.nw_t(values)
    assert t[0] == pytest.approx(newey_west_t(pd.Series(values[:, 0]), c4.NW_LAG))
    assert t[1] == pytest.approx(newey_west_t(pd.Series(values[:, 1]).dropna(), c4.NW_LAG)) and np.isnan(t[2])
    assert c4.nw_t(values[:, 0])[0] == pytest.approx(t[0]) and c4.NW_LAG == 7
    assert c4.nw_t(values[:, 0], lag=0)[0] == pytest.approx(values[:, 0].mean() / values[:, 0].std(ddof=0) * np.sqrt(60), rel=0.05)
    days = pd.date_range("2023-12-02", periods=60, freq="D", tz="UTC")           # 30 days of 2023, 30 of 2024
    series = pd.Series(values[:, 0], index=days)
    stats = c4.series_stats(series)
    assert stats == {"days": 60, "mean": pytest.approx(values[:, 0].mean()), "nw_t": pytest.approx(t[0]),
                     "hit_rate": pytest.approx((values[:, 0] > 0).mean()),
                     "by_year": {"2023": pytest.approx(values[:30, 0].mean()), "2024": pytest.approx(values[30:, 0].mean())}}
    assert c4.series_stats(series.iloc[:2]) == {"days": 2, "mean": None, "nw_t": None, "hit_rate": None, "by_year": {}}
    assert c4.series_stats(pd.Series(values[:, 1], index=days))["days"] == 48


def test_gate_statistics_split_the_daily_statistic_by_calendar_year():
    rng = np.random.default_rng(8)
    days = pd.date_range("2022-12-22", periods=750, freq="D", tz="UTC")          # 10 days of 2022, 365 of 2023, 366 of 2024, 9 of 2025
    dates = np.repeat(days.as_unit("ns").asi8, 30)
    resid = rng.normal(size=len(dates))
    score = 0.3 * resid + rng.normal(size=len(dates))
    gates, daily = c4.gate_statistics(dates, score, resid)
    assert len(daily) == 750 and list(daily.index) == list(days)
    assert gates["reader_partial"] == {"form": "corr", "days": 750, "mean": pytest.approx(daily.mean()),
                                       "nw_t": pytest.approx(newey_west_t(daily, 7))}
    years = gates["reader_partial_by_year"]
    assert set(years) == {"2023", "2024"} and years["2023"]["days"] == 365 and years["2024"]["days"] == 366
    assert years["2023"]["mean"] == pytest.approx(daily[daily.index.year == 2023].mean())
    assert years["2024"]["mean"] == pytest.approx(daily[daily.index.year == 2024].mean())
    assert c4.GATE_YEARS == (2023, 2024) and c4.GATE_T == 2.0
    none, empty = c4.gate_statistics(dates, np.full(len(dates), np.nan), resid)
    assert len(empty) == 0 and none["reader_partial"] == {"form": "corr", "days": 0, "mean": None, "nw_t": None}
    assert none["reader_partial_by_year"] == {"2023": {"days": 0, "mean": None}, "2024": {"days": 0, "mean": None}}
    assert c4.build_verdict({"gates": none, "days": {"test": 0}}, {})["verdict"] == "FAIL"


def test_gate_statistic_in_the_covariance_form(monkeypatch):
    rng = np.random.default_rng(9)
    dates = _stamps(40, 30, start=_day("2023-06-01"))
    resid = rng.normal(size=len(dates))
    score = 0.3 * resid + rng.normal(size=len(dates))
    monkeypatch.setattr(c4, "GATE_FORM", "cov")
    gates, daily = c4.gate_statistics(dates, score, resid)
    _, _, cov = c4.daily_stats(dates, score, resid)
    assert gates["reader_partial"]["form"] == "cov" and np.allclose(daily.to_numpy(), cov[:, 0])
    assert gates["reader_partial"]["mean"] == pytest.approx(cov.mean())


# ---------------------------------------------------------------- partial scores
def test_partial_score_is_the_walk_forward_fit_on_the_residuals(monkeypatch):
    monkeypatch.setattr(c4, "CLEAN_ROUNDS", 10)
    uni, feats, hist, fwd = synth(0.01, days=400, n=40, seed=3)
    panel = c4.assemble_panel(uni, feats, hist, fwd)
    reader, controls, flexible = c4.PARTIAL_SCORES[c4.GATE_SCORE]
    assert flexible and reader == c4.TONE and controls == c4.CONTROLS
    score, e, X, frame = c4.partial_score(panel, reader, controls, flexible)
    dates, design = c4._dates(panel), c4.feature_ranks(panel, controls)
    y = c4.target_rank(panel)
    # the gate: a fit on the earlier days first, then the regression within the day, on both sides
    assert np.allclose(X, c4.residuals(c4.past_trees(c4.feature_ranks(panel, reader), design, dates), design, dates))
    assert np.allclose(e, c4.residuals(c4.past_surface(y[:, None], design, dates), design, dates)[:, 0], equal_nan=True)
    assert np.array_equal(np.isnan(e), panel[c4.TARGET].isna().to_numpy())
    want, _ = c4.walk_forward(X, e[:, None], dates)
    assert np.allclose(score, want[:, 0], equal_nan=True) and list(frame.columns) == reader and len(frame) == 400 - c4.BURN_IN_DAYS
    days = np.unique(dates)
    assert np.isnan(score[np.isin(dates, days[:c4.BURN_IN_DAYS])]).all() and np.isfinite(score[np.isin(dates, days[c4.BURN_IN_DAYS:])]).all()
    assert frame.index[0] == _day(c4.PANEL_FIRST) + c4.BURN_IN_DAYS * DAY
    # the within-day regression alone
    lin_score, lin_e, lin_X, _ = c4.partial_score(panel, *c4.PARTIAL_SCORES["s_reader_lin"])
    assert np.allclose(lin_X, c4.residuals(c4.feature_ranks(panel, reader), design, dates))
    assert np.allclose(lin_e, c4.residuals(y[:, None], design, dates)[:, 0], equal_nan=True)
    assert np.allclose(lin_score, c4.walk_forward(lin_X, lin_e[:, None], dates)[0][:, 0], equal_nan=True) and not np.allclose(lin_X, X)
    # another target and horizon take the same two steps
    y3 = c4.target_rank(panel, "fwd_ret_3d")
    other, e3, _, _ = c4.partial_score(panel, reader, controls, flexible, target=y3, horizon=3)
    assert np.allclose(e3, c4.residuals(c4.past_surface(y3[:, None], design, dates, 3), design, dates)[:, 0], equal_nan=True)
    assert np.allclose(other, c4.walk_forward(X, e3[:, None], dates, 3)[0][:, 0], equal_nan=True)
    assert np.isnan(other[np.isin(dates, days[:c4.BURN_IN_DAYS + 2])]).all() and np.isfinite(other[dates == days[c4.BURN_IN_DAYS + 2]]).all()

    def no_trees(*args, **kwargs):
        raise AssertionError("tree step repeated")

    monkeypatch.setattr(c4, "past_trees", no_trees)                              # feature residuals handed in: no tree step
    again, _, X_again, _ = c4.partial_score(panel, reader, controls, flexible, X=X)
    assert X_again is X and np.allclose(again, score, equal_nan=True)
    with pytest.raises(AssertionError, match="tree step repeated"):
        c4.partial_score(panel, reader, controls, flexible)


def test_tree_step_is_kept_per_feature_and_control_set(monkeypatch):
    monkeypatch.setattr(c4, "CLEAN_ROUNDS", 5)
    uni, feats, hist, fwd = synth(0.0, days=60, n=40)
    panel = c4.assemble_panel(uni, feats, hist, fwd)
    calls, real = [], c4.past_trees

    def counted(values, controls, dates):
        calls.append((values.shape[1], controls.shape[1]))
        return real(values, controls, dates)

    monkeypatch.setattr(c4, "past_trees", counted)
    cache: dict = {}
    first = c4.feature_residuals(panel, c4.TONE, c4.CONTROLS, flexible=True, cache=cache)
    assert calls == [(2, 15)] and set(cache) == {(f, tuple(c4.CONTROLS)) for f in c4.TONE}
    both = c4.feature_residuals(panel, c4.BLOCK_R, c4.CONTROLS, flexible=True, cache=cache)
    assert calls == [(2, 15), (4, 15)]                                           # only the four new features are fitted
    at = [c4.BLOCK_R.index(f) for f in c4.TONE]
    assert first.shape == (len(panel), 2) and both.shape == (len(panel), 6) and np.allclose(both[:, at], first)
    c4.feature_residuals(panel, c4.FRESH, c4.CONTROLS, flexible=True, cache=cache)
    assert len(calls) == 2
    c4.feature_residuals(panel, c4.TONE, c4.HIST, flexible=True, cache=cache)
    assert calls[2:] == [(2, 11)]                                                # other controls: another fit
    c4.feature_residuals(panel, c4.TONE, c4.CONTROLS, cache=cache)
    assert len(calls) == 3                                                       # no flexible step: no trees
    without = c4.feature_residuals(panel, c4.TONE, c4.CONTROLS, flexible=True)
    assert calls[3:] == [(2, 15)] and np.allclose(without, first)             # no cache: fitted again, same values


def test_control_removal_reports_the_variance_left_by_each_step(monkeypatch):
    monkeypatch.setattr(c4, "CLEAN_ROUNDS", 10)
    uni, feats, hist, fwd = synth(0.0, days=380, n=40, seed=4)
    panel = c4.assemble_panel(uni, feats, hist, fwd)
    reader, controls, flexible = c4.PARTIAL_SCORES[c4.GATE_SCORE]
    score, e, X, _ = c4.partial_score(panel, reader, controls, flexible)
    scored = np.isfinite(score)
    out = c4.control_removal(panel, X, e, scored)
    assert set(out) == {"features", "target"} and list(out["features"]) == reader
    dates, design, y = c4._dates(panel), c4.feature_ranks(panel, controls), c4.target_rank(panel)
    ranks, linear = c4.feature_ranks(panel, reader), c4.residuals(c4.feature_ranks(panel, reader), design, dates)

    def share(part, whole, ok):
        return (part[ok] ** 2).sum() / ((whole[ok] - whole[ok].mean()) ** 2).sum()

    for j, f in enumerate(reader):
        assert out["features"][f] == {"within_day_step_alone": pytest.approx(share(linear[:, j], ranks[:, j], scored)),
                                      "both_steps": pytest.approx(share(X[:, j], ranks[:, j], scored))}
        assert 0.3 < out["features"][f]["both_steps"] <= 1.05                    # independent draws: little is removed
    ok = scored & np.isfinite(e)
    e_linear = c4.residuals(y[:, None], design, dates)[:, 0]
    assert out["target"] == {"within_day_step_alone": pytest.approx(share(e_linear, y, ok)), "both_steps": pytest.approx(share(e, y, ok))}
    assert 0.5 < out["target"]["within_day_step_alone"] < 1.0                    # 15 regressors and an intercept on 40 rows
    nothing = c4.control_removal(panel, X, e, np.zeros(len(panel), dtype=bool))
    assert nothing["target"] == {"within_day_step_alone": None, "both_steps": None}


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


# ---------------------------------------------------------------- verdict
def test_verdict_passes_only_with_both_gates():
    passed = _verdict()
    assert passed["verdict"] == "PASS" and passed["failed_gates"] == [] and passed["descriptive_errors"] == []
    assert passed["test_days"] == 722 and set(passed["gates"]) == {"reader_partial", "reader_partial_sign_by_year"}
    assert passed["gates"]["reader_partial"]["value"] == {"nw_t": 2.5, "mean": 0.05, "days": 722, "form": "corr"}
    assert passed["gates"]["reader_partial_sign_by_year"]["value"] == {"2023": 0.01, "2024": 0.02}
    assert passed["gates"]["reader_partial_sign_by_year"]["days"] == {"2023": 359, "2024": 363}
    assert _verdict(t=2.0)["verdict"] == "PASS" and _verdict(t=np.float64(2.0))["verdict"] == "PASS"
    both = _verdict(t=1.0, y2023=-0.01)
    assert both["verdict"] == "FAIL" and both["failed_gates"] == ["reader_partial", "reader_partial_sign_by_year"]
    assert passed["gates"]["reader_partial"]["rule"] == "Newey-West t >= 2.0 and mean daily statistic > 0"
    assert passed["gates"]["reader_partial_sign_by_year"]["rule"] == "mean daily statistic > 0 in 2023 and in 2024"
    assert "Charter 4" in passed["charter"]


@pytest.mark.parametrize("kwargs", [{"t": 1.999}, {"t": None}, {"t": float("nan")}, {"t": float("inf")}, {"t": "3.0"},
                                    {"mean": 0.0}, {"mean": -0.01}, {"mean": None}, {"mean": float("nan")}, {"t": -2.5, "mean": -0.05}])
def test_partial_gate_fails(kwargs):
    verdict = _verdict(**kwargs)
    assert verdict["verdict"] == "FAIL" and verdict["failed_gates"] == ["reader_partial"] and verdict["size_reading"] is None
    assert verdict["gates"]["reader_partial_sign_by_year"]["pass"] is True


@pytest.mark.parametrize("kwargs", [{"y2023": 0.0}, {"y2024": 0.0}, {"y2023": -0.001}, {"y2024": -0.5}, {"y2023": None},
                                    {"y2024": float("nan")}])
def test_year_sign_gate_fails(kwargs):
    verdict = _verdict(**kwargs)
    assert verdict["verdict"] == "FAIL" and verdict["failed_gates"] == ["reader_partial_sign_by_year"]
    assert verdict["gates"]["reader_partial"]["pass"] is True and verdict["size_reading"] is None


def test_year_sign_gate_fails_without_a_year():
    evaluation = _evaluation()
    del evaluation["gates"]["reader_partial_by_year"]["2024"]
    verdict = c4.build_verdict(evaluation, {})
    assert verdict["verdict"] == "FAIL" and verdict["failed_gates"] == ["reader_partial_sign_by_year"]
    assert verdict["gates"]["reader_partial_sign_by_year"]["value"] == {"2023": 0.01, "2024": None}


def test_size_reading_of_a_pass_is_a_label_and_no_gate():
    def book(net):
        return {"score_book": {"days": 722, "net": {"mean_bp": net}}}

    assert _verdict(**book(0.4))["size_reading"] == "above cost"
    below = _verdict(**book(-3.0))
    assert below["size_reading"] == "below cost" and below["verdict"] == "PASS" and below["failed_gates"] == []
    assert _verdict(**book(0.0))["size_reading"] == "below cost"
    assert _verdict()["size_reading"] == "not available"                         # no book in the evaluation
    assert _verdict(score_book={"days": 2})["size_reading"] == "not available"   # too few days for a book
    assert _verdict(**book(float("nan")))["size_reading"] == "not available"
    broken = _verdict(score_book={"error": "ValueError: boom"})
    assert broken["size_reading"] == "not available" and broken["verdict"] == "PASS"
    assert broken["descriptive_errors"] == ["evaluation/score_book"]
    assert _verdict(t=1.0, **book(5.0))["size_reading"] is None


def test_descriptive_errors_are_listed_and_cannot_change_the_verdict():
    evaluation = _evaluation(forecasts={"error": "ValueError: boom"}, variants={"fwd_rv_1d": {"error": "KeyError: x"}, "fwd_ret_3d": {}},
                             fit_errors={"g_full": {"error": "RuntimeError: no booster"}})
    verdict = c4.build_verdict(evaluation, {"quality": {"error": "TypeError: y"}, "extraction": None, "timing": {"news_rows": 3}})
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == [] and verdict["size_reading"] == "not available"
    assert verdict["descriptive_errors"] == ["evaluation/forecasts", "evaluation/variants/fwd_rv_1d", "evaluation/fit_errors/g_full",
                                             "reader/quality"]
    failed = c4.build_verdict(_evaluation(t=0.5, placebo_shift={"error": "ValueError: boom"}), {})
    assert failed["verdict"] == "FAIL" and failed["descriptive_errors"] == ["evaluation/placebo_shift"]


# ---------------------------------------------------------------- the gate on planted panels
@pytest.fixture
def light(monkeypatch):
    """Fewer boosting rounds than registered; the synthetic panels carry no curve that needs more."""
    monkeypatch.setattr(c4, "CLEAN_ROUNDS", 20)
    monkeypatch.setattr(model, "GBM_ROUNDS", 5)


def test_planted_signal_passes_and_a_noise_draw_fails(light):
    uni, feats, hist, fwd = synth(0.01)
    planted, gates = _gate(c4.assemble_panel(uni, feats, hist, fwd))
    assert planted["verdict"] == "PASS" and planted["test_days"] == 396 and planted["size_reading"] == "not available"
    assert planted["gates"]["reader_partial"]["value"]["nw_t"] > 4.0
    assert gates["reader_partial_by_year"]["2023"]["days"] == 359 and gates["reader_partial_by_year"]["2024"]["days"] == 37
    # One noise draw. A gate of t >= 2 passes a few noise draws in a hundred by construction (charter §4), so
    # this shows the failing branch on real statistics, not a rejection rate.
    uni, feats, hist, fwd = synth(0.0)
    noise, _ = _gate(c4.assemble_panel(uni, feats, hist, fwd))
    assert noise["verdict"] == "FAIL" and "reader_partial" in noise["failed_gates"]
    assert abs(noise["gates"]["reader_partial"]["value"]["nw_t"]) < 2.0


def test_a_signal_of_the_week_before_passes_through_the_lagged_tone(light):
    uni, feats, hist, fwd = synth(0.0, week=0.01)
    panel = c4.assemble_panel(uni, feats, hist, fwd)
    feats_, controls, flexible = c4.PARTIAL_SCORES[c4.GATE_SCORE]
    score, e, X, frame = c4.partial_score(panel, feats_, controls, flexible)
    gates, _ = c4.gate_statistics(c4._dates(panel), score, e)
    assert gates["reader_partial"]["nw_t"] > 4.0 and (frame["tone_prev6"] > 0).all() and (frame["tone_1d"] > 0).all()
    fresh, _ = _gate(panel, "s_fresh")                                           # the fresh features alone see the day's part of it
    assert fresh["gates"]["reader_partial"]["value"]["mean"] < gates["reader_partial"]["mean"]


def test_a_reader_feature_that_repeats_the_price_history_earns_nothing(light):
    uni, feats, hist, fwd = synth(0.0, seed=2)
    panel = c4.assemble_panel(uni, feats, hist, fwd)
    rng = np.random.default_rng(5)
    q = c4.feature_ranks(panel, ["ret_1d"])[:, 0]
    panel["tone_1d"] = q + 0.3 * rng.normal(size=len(panel))                     # the tone follows yesterday's return
    panel[c4.TARGET] = panel[c4.TARGET] + 0.03 * q                               # and so does the next return
    raw = c4.daily_statistic(c4._dates(panel), c4.feature_ranks(panel, ["tone_1d"])[:, 0], c4.target_rank(panel))
    assert raw.mean() > 0.15 and newey_west_t(raw, c4.NW_LAG) > 20               # strongly related to the target on its own
    verdict, gates = _gate(panel)
    assert verdict["verdict"] == "FAIL" and abs(gates["reader_partial"]["nw_t"]) < 2.0
    assert abs(gates["reader_partial"]["mean"]) < 0.03


def test_a_reader_feature_that_is_a_curved_function_of_the_history_earns_nothing(light):
    uni, feats, hist, fwd = synth(0.0, seed=7)
    panel = c4.assemble_panel(uni, feats, hist, fwd)
    rng = np.random.default_rng(11)
    q = c4.feature_ranks(panel, ["rv_7d"])[:, 0]
    panel["tone_1d"] = 12.0 * q ** 2 + 0.5 * rng.normal(size=len(panel))         # high at both ends of the past week's variance
    panel[c4.TARGET] = panel[c4.TARGET] + 0.25 * q ** 2                          # and so is the next return
    first, line = _gate(panel, "s_reader_lin")                                   # the within-day step alone reads the curve as reader information
    assert first["verdict"] == "PASS" and line["reader_partial"]["nw_t"] > 8.0 and line["reader_partial"]["mean"] > 0.2
    # One draw of the registered gate (charter section 4 has the rates over many draws on the real regressors).
    verdict, gates = _gate(panel)
    assert verdict["verdict"] == "FAIL" and abs(gates["reader_partial"]["nw_t"]) < 2.0
    assert abs(gates["reader_partial"]["mean"]) < 0.03


def test_a_signal_carried_by_the_attention_counts_does_not_pass_the_reader_gate(light):
    uni, feats, hist, fwd = synth(0.0, seed=2, attention=0.02)                   # the news count moves the next return
    rng = np.random.default_rng(12)
    feats = feats.copy()
    feats["tone_1d"] = np.round(2.0 * feats["news_1d"]) * (rng.uniform(size=len(feats)) < 0.5)      # a tone that grows with the count
    panel, parts, errors = c4.fit_scores(c4.assemble_panel(uni, feats, hist, fwd))
    dates = c4._dates(panel)

    def stat(name):
        return c4.series_stats(c4.daily_statistic(dates, panel[name].to_numpy(), parts[name]["resid"]))["nw_t"]

    assert errors == {} and set(parts) == set(c4.PARTIAL_SCORES)
    assert stat("s_attn") > 6.0 and stat("s_text") > 6.0
    assert stat("s_reader_hist") > 6.0                                           # without the counts among the controls the tone takes it
    assert abs(stat("s_reader")) < 2.0 and abs(stat("s_block_r")) < 2.0 and abs(stat("s_fresh")) < 2.0


# ---------------------------------------------------------------- descriptive panels and outputs
SHORT_DAYS, SHORT_TEST = 520, 156                                # a panel of 520 days from 2022-10-01: test days 2023-09-30 to 2024-03-03


@pytest.fixture
def short(monkeypatch, light):
    """A later first day, so that a short panel still has test days in both gate years, and fewer tree refits."""
    monkeypatch.setattr(c4, "PANEL_FIRST", "2022-10-01")
    monkeypatch.setattr(c4, "CLEAN_EVERY", 182)
    monkeypatch.setattr(c4, "CLEAN_ROUNDS", 10)


def _gate_alone(uni, feats, hist, fwd) -> dict:
    return _gate(c4.assemble_panel(uni, feats, hist, fwd))[1]


def test_finalize_returns_the_registered_outputs_in_json_form(short):
    data = synth(0.02, days=SHORT_DAYS, n=40, seed=4)
    out = c4.finalize(*data, _records(), extraction={"note": "synthetic"}, timing={"news_rows": 7}, n_placebo=5)
    assert set(out) == set(run_script.OUTPUTS)
    assert json.loads(json.dumps(out, allow_nan=False)) == out                   # plain JSON types, no NaN
    verdict, evaluation = out["verdict.json"], out["evaluation.json"]
    assert verdict["descriptive_errors"] == [] and evaluation["fit_errors"] == {}
    assert verdict["verdict"] == "PASS" and verdict["test_days"] == SHORT_TEST
    assert verdict["size_reading"] == c4.size_reading(evaluation) and verdict["size_reading"] in ("above cost", "below cost")
    assert evaluation["days"]["panel"] == SHORT_DAYS and evaluation["days"]["test"] == SHORT_TEST
    assert evaluation["days"]["first_test"].startswith("2023-09-30") and evaluation["days"]["last_test"].startswith("2024-03-03")
    assert evaluation["gates"]["reader_partial_by_year"]["2023"]["days"] == 93
    assert evaluation["gates"]["reader_partial_by_year"]["2024"]["days"] == 63
    assert len(evaluation["gate_daily_statistic"]) == SHORT_TEST and set(evaluation["gate_daily_statistic"][0]) == {"date", "value"}
    assert evaluation["gate_other_form"]["form"] == "cov" and evaluation["gate_other_form"]["days"] == SHORT_TEST
    forecasts = out["forecasts.json"]
    assert forecasts["columns"] == c4.OUTPUT_COLUMNS and len(forecasts["rows"]) == SHORT_TEST * 40      # the rows of the test days
    table = pd.DataFrame(forecasts["rows"], columns=forecasts["columns"])
    assert table["date"].min().startswith("2023-09-30") and table[c4.SCORES].notna().all().all()
    assert table[c4.GATE_RESIDUAL].isna().equals(table[c4.TARGET].isna()) and 0 < table[c4.TARGET].isna().sum() < 100
    assert set(evaluation["partial_scores"]) == set(c4.PARTIAL_SCORES)
    for name, (reader, _, _) in c4.PARTIAL_SCORES.items():
        part = evaluation["partial_scores"][name]
        assert set(part) == {"daily_correlation", "daily_covariance", "size", "univariate", "coefficients"}
        assert part["daily_correlation"]["days"] == SHORT_TEST and set(part["univariate"]) == set(reader)
        assert part["coefficients"]["days"] == SHORT_TEST and set(part["coefficients"]["features"]) == set(reader)
        assert len(part["coefficients"]["path"]["dates"]) == len(range(0, SHORT_TEST, 7))
    assert set(evaluation["forecasts"]["scores"]) == {*c4.FORECASTS, *c4.GBM_FORECASTS}
    assert set(evaluation["forecasts"]["loss_difference"]) == {f"{a}_minus_{b}" for a, b in c4.LOSS_PAIRS}
    assert set(evaluation["variants"]) == set(c4.OTHER_TARGETS)
    assert evaluation["variants"]["fwd_absret_1d"]["daily_correlation"]["days"] == SHORT_TEST
    assert evaluation["variants"]["fwd_ret_3d"]["daily_correlation"]["days"] == SHORT_TEST - 2          # its outcome closes two days later
    removal = evaluation["control_removal"]
    assert set(removal) == {"features", "target"} and set(removal["features"]) == set(c4.TONE)
    for part in (*removal["features"].values(), removal["target"]):
        assert set(part) == {"within_day_step_alone", "both_steps"} and all(0.0 < v < 1.2 for v in part.values())
    assert evaluation["placebo_permutation"]["draws"] == 5 and set(evaluation["placebo_shift"]) == {str(k) for k in c4.SHIFT_DAYS}
    assert set(evaluation["residual_autocorrelation"]) == {str(k) for k in c4.AUTOCORR_LAGS}
    rows = SHORT_DAYS * 40
    assert evaluation["feature_coverage"]["all_days"]["rows"] == rows and evaluation["feature_coverage"]["test_days"]["days"] == SHORT_TEST
    assert set(evaluation["feature_coverage"]["all_days"]["features"]) == {*c4.HIST, *c4.TEXT_COLUMNS}
    assert evaluation["target_coverage"]["all_days"]["missing"][c4.TARGET] == rows - len(data[3])
    assert evaluation["target_coverage"]["test_days"]["rows"] == SHORT_TEST * 40
    assert evaluation["score_book"]["days"] == SHORT_TEST and set(evaluation["event_study"]) == set(c4.EVENT_GROUPS)
    assert evaluation["excluding_large"]["rows_dropped"] == 0                    # no synthetic asset is one of the two large ones
    assert evaluation["excluding_gap_rows"]["rows_dropped"] > 500
    assert out["reader.json"]["extraction"] == {"note": "synthetic"} and out["reader.json"]["quality"]["records"] == 21
    assert out["reader.json"]["timing"] == {"news_rows": 7}
    gates = _gate_alone(*data)                                                   # the gate values are those of the gate score alone
    assert evaluation["gates"]["reader_partial"] == pytest.approx(gates["reader_partial"])
    assert verdict["gates"]["reader_partial"]["value"]["nw_t"] == pytest.approx(gates["reader_partial"]["nw_t"])
    reader_score = evaluation["partial_scores"][c4.GATE_SCORE]
    assert reader_score["daily_correlation"]["mean"] == pytest.approx(gates["reader_partial"]["mean"])
    assert evaluation["excluding_large"]["daily_correlation"]["mean"] == pytest.approx(gates["reader_partial"]["mean"])
    assert reader_score["univariate"]["tone_1d"]["nw_t"] > 4.0                    # the planted feature
    assert reader_score["coefficients"]["features"]["tone_1d"]["share_positive"] == 1.0
    assert evaluation["event_study"]["tone_positive"]["mean_bp"] > 100 and evaluation["event_study"]["tone_negative"]["mean_bp"] < -100


def test_a_failing_boosted_tree_is_recorded_and_the_gates_stand(short, monkeypatch):
    def no_booster(X, y):
        raise RuntimeError("no booster")

    monkeypatch.setattr(model, "fit_gbm", no_booster)
    data = synth(0.02, days=SHORT_DAYS, n=40, seed=4)
    out = c4.finalize(*data, _records(), n_placebo=3)
    evaluation, verdict = out["evaluation.json"], out["verdict.json"]
    assert evaluation["fit_errors"] == dict.fromkeys(c4.GBM_FORECASTS, {"error": "RuntimeError: no booster"})
    assert verdict["descriptive_errors"] == [f"evaluation/fit_errors/{name}" for name in c4.GBM_FORECASTS]
    assert set(evaluation["forecasts"]["scores"]) == set(c4.FORECASTS)           # the fitted forecasts are still reported
    assert set(evaluation["forecasts"]["loss_difference"]) == {f"{a}_minus_{b}" for a, b in c4.LOSS_PAIRS if b in c4.FORECASTS}
    assert evaluation["gates"]["reader_partial"] == pytest.approx(_gate_alone(*data)["reader_partial"])
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == []
    json.dumps(out, allow_nan=False)


def test_a_failing_descriptive_score_is_recorded_and_the_gates_stand(short, monkeypatch):
    real = c4.partial_score

    def gate_only(panel, feats, controls, flexible=False, target=None, X=None, cache=None, horizon=1):
        if (feats, controls, flexible) != c4.PARTIAL_SCORES[c4.GATE_SCORE] or horizon != 1 or X is not None:
            raise ValueError("descriptive fit")
        return real(panel, feats, controls, flexible, target, X, cache, horizon)

    monkeypatch.setattr(c4, "partial_score", gate_only)
    data = synth(0.02, days=SHORT_DAYS, n=40, seed=4)
    out = c4.finalize(*data, _records(), n_placebo=3)
    evaluation, verdict = out["evaluation.json"], out["verdict.json"]
    others = [n for n in c4.PARTIAL_SCORES if n != c4.GATE_SCORE]
    assert evaluation["fit_errors"] == dict.fromkeys(others, {"error": "ValueError: descriptive fit"})
    assert set(evaluation["partial_scores"]) == {c4.GATE_SCORE}
    assert {f"evaluation/variants/{name}" for name in c4.OTHER_TARGETS} <= set(verdict["descriptive_errors"])
    assert {f"evaluation/fit_errors/{name}" for name in others} <= set(verdict["descriptive_errors"])
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == []
    json.dumps(out, allow_nan=False)


def test_a_failing_tree_step_stops_the_gate_score_and_only_marks_a_descriptive_score(short, monkeypatch):
    data = synth(0.02, days=SHORT_DAYS, n=40, seed=4)
    real = c4.past_trees

    def gate_controls_only(values, controls, dates):
        if controls.shape[1] != len(c4.PARTIAL_SCORES[c4.GATE_SCORE][1]):
            raise RuntimeError("no trees")
        return real(values, controls, dates)

    monkeypatch.setattr(c4, "past_trees", gate_controls_only)
    out = c4.finalize(*data, _records(), n_placebo=3)
    evaluation, verdict = out["evaluation.json"], out["verdict.json"]
    stopped = [n for n, (_, controls, flexible) in c4.PARTIAL_SCORES.items() if flexible and controls != c4.CONTROLS]
    assert stopped == ["s_reader_hist", "s_text", "s_attn"]
    assert evaluation["fit_errors"] == dict.fromkeys(stopped, {"error": "RuntimeError: no trees"})
    assert set(evaluation["partial_scores"]) == set(c4.PARTIAL_SCORES) - set(stopped)
    assert verdict["descriptive_errors"] == [f"evaluation/fit_errors/{name}" for name in stopped]
    assert evaluation["gates"]["reader_partial"] == pytest.approx(_gate_alone(*data)["reader_partial"])
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == []

    def no_trees(values, controls, dates):
        raise RuntimeError("no trees at all")

    monkeypatch.setattr(c4, "past_trees", no_trees)                              # the gate score has no fallback
    with pytest.raises(RuntimeError, match="no trees at all"):
        c4.finalize(*data, _records(), n_placebo=3)


def test_placebos_break_the_planted_link(light):
    uni, feats, hist, fwd = synth(0.02, days=460, seed=1)
    panel = c4.assemble_panel(uni, feats, hist, fwd)
    reader, controls, flexible = c4.PARTIAL_SCORES[c4.GATE_SCORE]
    score, e, X, _ = c4.partial_score(panel, reader, controls, flexible)
    dates = c4._dates(panel)
    observed = c4.gate_statistics(dates, score, e)[0]["reader_partial"]["nw_t"]
    assert observed > 8.0
    placebo = c4.permutation_placebo(dates, X, e, observed, draws=12)
    assert placebo["draws"] == 12 and placebo["share_ge_observed"] == 0.0 and placebo["t_observed"] == observed
    assert abs(placebo["t_mean"]) < 1.5 and placebo["t_q975"] < 4.0
    assert c4.permutation_placebo(dates, X, e, observed, draws=12) == placebo     # seeded
    assert c4.permutation_placebo(dates, X, e, observed, draws=12, seed=1)["t_mean"] != placebo["t_mean"]
    shifted = c4.shift_placebo(panel, X, e)
    assert set(shifted) == {str(k) for k in c4.SHIFT_DAYS}
    full = [v for v in shifted.values() if v["days"] >= 60]                      # the features of another day do not carry it
    assert len(full) == 4 and all(abs(v["nw_t"]) < observed / 2 for v in full)
    assert shifted["182"] == {"form": "corr", "days": 0, "mean": None, "nw_t": None}       # every shifted day is outside the panel
    none = c4.permutation_placebo(dates, np.full_like(X, np.nan), e, observed, draws=3)
    assert none == {"draws": 0, "t_observed": observed, "share_ge_observed": None, "t_mean": None, "t_sd": None, "t_q975": None}
    unknown = c4.permutation_placebo(dates, X, e, None, draws=3)                 # no observed t: no share
    assert unknown["draws"] == 3 and unknown["share_ge_observed"] is None


def test_shift_placebo_takes_the_features_of_the_same_asset_k_days_later(monkeypatch):
    monkeypatch.setattr(c4, "SHIFT_DAYS", (2,))
    seen = {}

    def spy(X, E, dates, *args, **kwargs):
        seen["X"] = X.copy()
        return np.zeros_like(E), None

    monkeypatch.setattr(c4, "walk_forward", spy)
    days = pd.date_range(D0, periods=5, freq="D")
    panel = pd.DataFrame([(d, s) for d in days for s in ("AAAUSDT", "BBBUSDT")], columns=["date", "symbol"])
    panel = panel[~((panel["symbol"] == "BBBUSDT") & (panel["date"] == days[3]))].reset_index(drop=True)      # one asset-day is absent
    X = np.arange(1.0, len(panel) + 1)[:, None]
    c4.shift_placebo(panel, X, np.zeros(len(panel)))
    value = dict(zip(zip(panel["date"], panel["symbol"]), X[:, 0]))
    want = [value.get((d + 2 * DAY, s), 0.0) for d, s in zip(panel["date"], panel["symbol"])]
    assert seen["X"][:, 0].tolist() == want and want[0] == value[(days[2], "AAAUSDT")] and want[3] == 0.0 and want[-1] == 0.0


def test_residual_autocorrelation_sees_the_persistence_the_controls_miss(light):
    for rho, low, high in ((0.0, -0.05, 0.05), (0.8, 0.2, 0.9)):
        uni, feats, hist, fwd = synth(0.0, days=200, n=40, seed=6, rho=rho)
        panel = c4.assemble_panel(uni, feats, hist, fwd)
        e = c4.target_residual(panel, c4.target_rank(panel), c4.CONTROLS, True)[:, 0]
        auto = c4.residual_autocorrelation(panel, e)
        assert set(auto) == {str(k) for k in c4.AUTOCORR_LAGS} and auto["1"]["pairs"] > 7500
        assert low < auto["1"]["corr"] < high, (rho, auto["1"])
    assert auto["1"]["corr"] > auto["2"]["corr"] > auto["7"]["corr"] > 0
    by_hand = pd.DataFrame({"date": panel["date"], "symbol": panel["symbol"], "e": e}).pivot(index="date", columns="symbol", values="e")
    pairs = pd.DataFrame({"now": by_hand.iloc[7:].to_numpy().ravel(), "then": by_hand.iloc[:-7].to_numpy().ravel()}).dropna()
    assert auto["7"] == {"pairs": len(pairs), "corr": pytest.approx(pairs["now"].corr(pairs["then"]))}


def test_coverage_tables_count_missing_values_and_zero_returns():
    uni, feats, hist, fwd = synth(0.0, days=20, n=6)
    fwd = fwd.iloc[3:].reset_index(drop=True)
    fwd.loc[3, c4.TARGET] = 0.0
    fwd.loc[4, "fwd_absret_1d"] = np.nan
    panel = c4.assemble_panel(uni, feats, hist, fwd)
    everything = np.ones(len(panel), dtype=bool)
    lost = 120 - len(fwd)
    assert lost >= 3 and c4.target_coverage(panel, everything) == {
        "rows": 120, "missing": {c4.TARGET: lost, "fwd_absret_1d": lost + 1, "fwd_rv_1d": lost, "fwd_ret_3d": lost}, "zero_return": 1}
    cover = c4.feature_coverage(panel, everything)
    assert cover["rows"] == 120 and cover["days"] == 20 and set(cover["features"]) == {*c4.HIST, *c4.TEXT_COLUMNS}
    assert cover["features"]["beta_60d"]["missing"] == pytest.approx(panel["beta_60d"].isna().mean())
    assert cover["features"]["attn_abn_1d"]["missing"] == pytest.approx(panel["attn_abn_1d"].isna().mean()) and panel["attn_abn_1d"].isna().any()
    assert cover["features"]["tone_1d"]["nonzero"] == pytest.approx((panel["tone_1d"] != 0).mean())
    assert cover["features"]["tone_1d"]["mean_assets_nonzero_per_day"] == pytest.approx((panel["tone_1d"] != 0).sum() / 20)
    late = (panel["date"] >= panel["date"].unique()[15]).to_numpy()              # a subset of the days
    part = c4.feature_coverage(panel, late)
    assert part["rows"] == 30 and part["days"] == 5
    assert part["features"]["evt_1d"]["nonzero"] == pytest.approx((panel.loc[late, "evt_1d"] != 0).mean())
    assert c4.target_coverage(panel, late)["rows"] == 30


def _book_panel(scores: dict, returns: dict) -> tuple[pd.DataFrame, np.ndarray]:
    days = pd.date_range(D0, periods=len(scores), freq="D")
    rows = [(day, f"{name}USDT", s, r) for day, key in zip(days, scores) for name, s, r in zip("ABC", scores[key], returns[key])]
    frame = pd.DataFrame(rows, columns=["date", "symbol", "s", c4.TARGET])
    return frame[["date", "symbol", c4.TARGET]], frame["s"].to_numpy(dtype=float)


def test_score_book_arithmetic_by_hand():
    nan = np.nan
    scores = {1: (1, 2, 3), 2: (3, 1, 2), 3: (5, 5, 5), 4: (2, 4, nan), 5: (1, 2, 6)}
    returns = {1: (0.01, 0.02, 0.03), 2: (0.02, -0.01, 0.05), 3: (0.01, 0.01, 0.01), 4: (0.00, 0.01, 0.09), 5: (0.03, 0.00, 0.02)}
    # weights: day 1 (-1, 0, 1); day 2 (1, -1, 0); day 3 has no spread and no book; day 4 (-1, 1, 0); day 5 (-2/3, -1/3, 1)
    gross = pd.Series([-0.01 + 0.03, 0.02 + 0.01, 0.01, -0.02 + 0.02])
    turnover = pd.Series([2.0, 4.0, 4.0, 1 / 3 + 4 / 3 + 1.0])               # the first day builds the book
    net = gross - COST_PER_SIDE * turnover
    book = c4.score_book(*_book_panel(scores, returns))
    assert book["days"] == 4 and book["cost_per_side"] == COST_PER_SIDE and book["mean_turnover"] == pytest.approx(turnover.mean())
    for name, series in (("gross", gross), ("net", net)):
        assert book[name] == {"mean_bp": pytest.approx(series.mean() * 1e4), "nw_t": pytest.approx(newey_west_t(series, c4.NW_LAG)),
                              "sharpe_annual": pytest.approx(series.mean() / series.std() * np.sqrt(365))}
    assert book["net"]["mean_bp"] == pytest.approx(book["gross"]["mean_bp"] - COST_PER_SIDE * turnover.mean() * 1e4)
    missing = {**returns, 5: (0.03, nan, 0.02)}                              # an asset without an outcome is not held
    held = c4.score_book(*_book_panel(scores, missing))                      # day 5: scores (1, 6), weights (-1, 0, 1)
    assert held["gross"]["mean_bp"] == pytest.approx(np.mean([0.02, 0.03, 0.01, -0.03 + 0.02]) * 1e4)
    assert held["mean_turnover"] == pytest.approx(np.mean([2.0, 4.0, 4.0, 0.0 + 1.0 + 1.0]))
    two = {k: scores[k] for k in (1, 2, 3)}
    assert c4.score_book(*_book_panel(two, returns)) == {"days": 2}          # fewer than three days with a book
    flat = {k: (0.01, 0.01, 0.01) for k in scores}
    with np.errstate(invalid="ignore"):
        still = c4.score_book(*_book_panel({k: (1, 2, 3) for k in scores}, flat))     # an unchanged book of equal returns
    assert still["gross"]["mean_bp"] == 0.0 and still["gross"]["sharpe_annual"] is None and np.isnan(still["gross"]["nw_t"])
    assert still["mean_turnover"] == pytest.approx(2.0 / 5) and still["net"]["mean_bp"] == pytest.approx(-COST_PER_SIDE * 0.4 * 1e4)


def test_event_study_by_hand():
    nan = np.nan
    cases = {                        # asset: (return, tone_1d, evt_1d, unfav_1d, n_subject_1d)
        0: {"A": (0.04, 1, 1, 0, 1), "B": (0.00, -1, 1, 1, 1), "C": (0.02, 0, 1, 0, 2), "D": (-0.02, 0, 0, 0, 0)},
        1: {"A": (0.01, 2, 1, 0, 1), "B": (0.03, 0, 0, 0, 1), "C": (nan, 1, 1, 0, 1), "D": (-0.01, 0, 0, 0, 0)},
        2: {"A": (0.50, 1, 1, 0, 1), "B": (0.00, 0, 0, 0, 0), "C": (0.00, 0, 0, 0, 0), "D": (0.00, 0, 0, 0, 0)},      # not selected
        3: {"A": (0.00, 0, 0, 0, 0), "B": (0.02, 1, 2, 1, 2), "C": (0.01, 0, 0, 0, 0), "D": (0.01, 0, 0, 0, 0)},
    }
    days = pd.date_range(D0, periods=4, freq="D")
    panel = pd.DataFrame([(days[k], f"{a}USDT", *v) for k, day in cases.items() for a, v in day.items()],
                         columns=["date", "symbol", c4.TARGET, "tone_1d", "evt_1d", "unfav_1d", "n_subject_1d"])
    rows = (panel["date"] != days[2]).to_numpy()
    # abnormal return in basis points (every selected day has the mean 0.01): day 0: A +300, B -100, C +100, D -300;
    # day 1: A 0, B +200, D -200 (C has no outcome); day 3: A -100, B +100, C 0, D 0

    def group(values_by_day: list[list[float]]) -> dict:
        pooled = [v for day in values_by_day for v in day]
        means = pd.Series([np.mean(day) for day in values_by_day])
        return {"rows": len(pooled), "days": len(means), "mean_bp": pytest.approx(np.mean(pooled), abs=1e-9),
                "day_mean_bp": pytest.approx(means.mean(), abs=1e-9),
                "nw_t": pytest.approx(newey_west_t(means, c4.NW_LAG)) if len(means) >= 3 else None}

    study = c4.event_study(panel, rows)
    assert study == {"tone_positive": group([[300.0], [0.0], [100.0]]), "tone_negative": group([[-100.0]]),
                     "event_zero_tone": group([[100.0]]), "unfavourable_event": group([[-100.0], [100.0]]),
                     "record_no_event": group([[200.0]]), "no_record": group([[-300.0], [-200.0], [-100.0, 0.0, 0.0]])}
    assert study["no_record"]["mean_bp"] == pytest.approx(-120.0) and study["no_record"]["day_mean_bp"] == pytest.approx(-1600 / 9)
    later = c4.event_study(panel, rows & (panel["date"] > days[0]).to_numpy())
    assert later["tone_negative"] == {"rows": 0, "days": 0, "mean_bp": None, "day_mean_bp": None, "nw_t": None}
    assert later["tone_positive"]["rows"] == 2 and later["tone_positive"]["nw_t"] is None


def test_masked_gate_keeps_the_dropped_rows_out_of_the_fit_and_the_statistic():
    rng = np.random.default_rng(3)
    n_days, per_day = 400, 40
    dates = _stamps(n_days, per_day)
    panel = pd.DataFrame({"date": pd.to_datetime(dates, utc=True)})
    X = rng.normal(size=(n_days * per_day, 2))
    resid = 0.5 * X[:, 0] + rng.normal(size=len(X))
    drop = np.tile(np.arange(per_day) < 8, n_days)
    resid[drop] = -50.0 * X[drop, 0]                                         # the dropped rows carry the opposite relation
    keep = ~drop
    score, _ = c4.walk_forward(X, resid[:, None], dates)                     # fitted on every row, the kept rows are forecast upside down
    assert c4.series_stats(c4.daily_statistic(dates[keep], score[keep, 0], resid[keep], "corr"))["mean"] < -0.3
    masked = c4.masked_gate(panel, X, resid, drop)
    assert masked["rows_dropped"] == 8 * n_days and masked["daily_correlation"]["days"] == n_days - c4.BURN_IN_DAYS
    assert masked["daily_correlation"]["mean"] > 0.3 and masked["daily_correlation"]["nw_t"] > 10
    alone, _ = c4.walk_forward(X[keep], resid[keep][:, None], dates[keep])
    assert masked["daily_correlation"] == c4.series_stats(c4.daily_statistic(dates[keep], alone[:, 0], resid[keep], "corr"))
    assert masked["daily_covariance"] == c4.series_stats(c4.daily_statistic(dates[keep], alone[:, 0], resid[keep], "cov"))     # a panel without those rows
    other = resid.copy()
    other[drop] = rng.normal(size=int(drop.sum())) * 1e3                     # whatever the dropped rows hold
    other[np.flatnonzero(drop)[:5]] = np.nan
    again = c4.masked_gate(panel, X, other, drop)
    assert again["rows_dropped"] == 8 * n_days - 5 and {k: again[k] for k in ("daily_correlation", "daily_covariance")} == \
        {k: masked[k] for k in ("daily_correlation", "daily_covariance")}
    nothing = c4.masked_gate(panel, X, resid, np.zeros(len(X), dtype=bool))
    assert nothing["rows_dropped"] == 0 and nothing["daily_correlation"] == c4.series_stats(c4.daily_statistic(dates, score[:, 0], resid, "corr"))


# ---------------------------------------------------------------- pre-flight: manifest and rehearsal
def test_extraction_manifest_is_checked_by_the_charter_3_rule():
    import reader_charter3_run as parent_run

    assert run_script.check_manifest is parent_run.check_manifest and run_script.EXTRACTION_KEYS is parent_run.EXTRACTION_KEYS
    assert run_script.OUTPUTS == ("forecasts.json", "evaluation.json", "reader.json", "verdict.json")
    assert 0 < run_script.REHEARSAL_PLACEBO < PLACEBO_DRAWS and len(run_script.CELLS) == len(set(run_script.CELLS)) == 4


def test_rehearsal_targets_are_seeded_noise_of_the_registered_shape():
    uni, *_ = synth(0.0, days=60, n=20)
    fwd = run_script.synthetic_targets(uni)
    pd.testing.assert_frame_equal(fwd, run_script.synthetic_targets(uni))
    other = run_script.synthetic_targets(uni, seed=1)
    assert not np.allclose(other[c4.TARGET].to_numpy()[:50], fwd[c4.TARGET].to_numpy()[:50])
    assert list(fwd.columns) == ["date", "symbol", *c4.TARGET_COLUMNS]
    assert 0 < len(uni) - len(fwd) < 0.05 * len(uni) and not fwd[["date", "symbol"]].duplicated().any()
    assert fwd[c4.TARGET_COLUMNS].notna().all().all() and (fwd["fwd_rv_1d"] > 0).all()
    assert (fwd["fwd_absret_1d"] == fwd["fwd_ret_1d"].abs()).all() and 0.03 < fwd["fwd_ret_1d"].std() < 0.07
    assert abs(fwd["fwd_ret_1d"].mean()) < 0.01 and (fwd["fwd_ret_1d"] > -1).all()
    panel = c4.assemble_panel(uni, *synth(0.0, days=60, n=20)[1:3], fwd)       # joins like the real targets
    assert panel[c4.TARGET].notna().sum() == len(fwd)


def test_rehearsal_stops_on_any_error_and_on_a_missing_verdict(monkeypatch):
    seen = {}

    def outputs(**changes) -> dict:
        out = {"forecasts.json": {"rows": []}, "reader.json": {}, "evaluation.json": {"fit_errors": {}},
               "verdict.json": {"verdict": "FAIL", "test_days": 5, "descriptive_errors": []}}
        for path, value in changes.items():
            name, _, key = path.partition("__")
            if key:
                out[f"{name}.json"][key] = value
            else:
                out[f"{name}.json"] = value
        return out

    def fake(result):
        def finalize(universe, feats, hist, fwd, records, **kwargs):
            seen.update(kwargs, fwd=fwd)
            return result
        monkeypatch.setattr(c4, "finalize", finalize)

    monkeypatch.setattr(run_script, "synthetic_targets", lambda universe: ("synthetic", universe))
    ctx = {"universe": "u", "feats": 1, "hist": 2, "records": 3, "extraction": {"e": 1}, "timing": {"t": 2}}
    fake(outputs())
    assert run_script.rehearse(ctx) is None
    assert seen == {"extraction": {"e": 1}, "timing": {"t": 2}, "n_placebo": run_script.REHEARSAL_PLACEBO, "fwd": ("synthetic", "u")}
    fake(outputs(verdict__verdict="PASS"))
    assert run_script.rehearse(ctx) is None
    fake(outputs(reader__value=float("nan")))
    with pytest.raises(ValueError):
        run_script.rehearse(ctx)
    fake({**outputs(), "extra.json": {}})
    with pytest.raises(SystemExit, match="output names differ"):
        run_script.rehearse(ctx)
    fake({k: v for k, v in outputs().items() if k != "forecasts.json"})
    with pytest.raises(SystemExit, match="output names differ"):
        run_script.rehearse(ctx)
    fake(outputs(verdict__descriptive_errors=["evaluation.placebo_shift"]))
    with pytest.raises(SystemExit, match="rehearsal: errors"):
        run_script.rehearse(ctx)
    fake(outputs(evaluation__fit_errors={"g_full": {"error": "ValueError: x"}}))
    with pytest.raises(SystemExit, match="rehearsal: errors"):
        run_script.rehearse(ctx)
    fake(outputs(verdict__verdict="ERROR"))
    with pytest.raises(SystemExit, match="rehearsal: no verdict"):
        run_script.rehearse(ctx)
    fake(outputs(verdict__test_days=0))
    with pytest.raises(SystemExit, match="rehearsal: no verdict"):
        run_script.rehearse(ctx)


# ---------------------------------------------------------------- registered run on a synthetic checkout
RUN_FRIDAY, RUN_WEEKS, RUN_SYMS, RUN_DOCS = "2022-12-02", 60, 36, 40            # 420 decision days from 2022-12-03 to 2024-01-26
RUN_DAYS, RUN_TEST = 420, 56                                                    # test days 2023-12-02 to 2024-01-26 (30 and 26 by year)
RUN_INPUTS = {"items": rx.INPUTS["items"], "docs": rx.INPUTS["docs"], "cards": rx.INPUTS["cards"], "calls": rx.CACHE,
              "records": rx.RECORDS, "extraction_manifest": rx.MANIFEST, "klines_digest": "klines_digest.json"}
PLANTED, LEAD_DAYS = 0.02, 100


@pytest.fixture
def run_window(monkeypatch, light):
    """The registered window moved onto the synthetic store (the store builder starts at the first Friday)."""
    monkeypatch.setattr(c2, "PANEL_START", RUN_FRIDAY)
    monkeypatch.setattr(c4, "PANEL_FIRST", "2022-12-03")
    monkeypatch.setattr(c4, "PANEL_LAST", "2024-01-26")
    monkeypatch.setattr(c4, "CLEAN_EVERY", 182)
    monkeypatch.setattr(c4, "CLEAN_ROUNDS", 10)
    monkeypatch.setattr(run_script, "REHEARSAL_PLACEBO", 5)


def _run_root(root: Path) -> dict:
    """A synthetic checkout in the state before the registered run: sources and the charter of the extraction
    committed, the extraction complete (stub client), a kline store of daily bars in which the return of the bar
    after a decision rises with the reader's fresh tone at that decision, and a committed registration under a
    charter of its own."""
    from tradingagents.research import runtime_hashes
    items, docs, cards = script_root(root, frozen=True, weeks=RUN_WEEKS, n_syms=RUN_SYMS, docs_per_week=RUN_DOCS)
    manifest = extract(root, "--cost-cap", "5", client=FakeClient())
    records = pd.read_parquet(root / rx.RECORDS)
    universe = c4.daily_universe(c2.universe(cards))
    feats = c4.text_features(items, docs, records, universe)
    first, last = universe["date"].min(), universe["date"].max()
    days = pd.date_range(first - LEAD_DAYS * DAY, last + 3 * DAY, freq="D")
    (root / "klines").mkdir()
    for i, (base, rows) in enumerate(feats.groupby("base")):
        tone = rows.set_index("date")["tone_1d"].clip(-3.0, 3.0).reindex(days).fillna(0.0).to_numpy()
        _bars(len(days), seed=100 + i, start=days[0], drift=PLANTED * tone).to_parquet(root / "klines" / f"{base}USDT.parquet")
    _bars(len(days), seed=99, start=days[0]).to_parquet(root / "klines" / f"{c4.MARKET}.parquet")
    digest = {f"klines/{p.name}": sha(p) for p in sorted((root / "klines").glob("*.parquet"))}
    (root / "klines_digest.json").write_text(json.dumps(digest))
    (root / "charter4.md").write_text("synthetic charter of the daily decision\n")
    spec = {"schema_version": 1, "program_id": "synthetic-c4",
            "families": {"fam": {"mechanism_id": "synthetic-mechanism", "attempt_budget": 3, "prior_attempts": 0,
                                 "history_reference": "synthetic"}},
            "datasets": {"sample": {"identity": "synthetic-sample", "history_reference": "synthetic", "exposures": []}},
            "experiments": {"c4": {
                "family": "fam", "parent": None, "question": "synthetic",
                "charter": {"path": "charter4.md", "sha256": sha(root / "charter4.md")},
                "stage": "development", "reuse": "exploratory", "selection": None,
                "source_files": {**manifest["source_files"], "charter.md": sha(root / "charter.md")},
                "runtime_hashes": runtime_hashes(),
                "windows": [{"dataset": "sample", "start": "2022-01-01T00:00:00Z", "end": "2024-03-01T00:00:00Z",
                             "availability": "existing"}],
                "inputs": {name: {"path": path, "sha256": sha(root / path), "dataset": "sample"} for name, path in RUN_INPUTS.items()},
                "cells": list(run_script.CELLS), "outputs": list(run_script.OUTPUTS)}}}
    (root / "registration.json").write_text(json.dumps(spec))
    commit(root, "synthetic registration", "registration.json", "charter4.md")
    return {"manifest": manifest, "feats": feats, "universe": universe, "digest": digest}


def _run(root: Path, *extra: str) -> int:
    return run_script.main(["--registration", "registration.json", "--experiment", "c4", *extra], root=root)


def _output(root: Path, name: str):
    return json.loads((root / "research_runs" / "c4" / "outputs" / name).read_text())


def test_registered_run_checks_everything_before_the_claim_and_joins_outcomes_once(tmp_path, monkeypatch, capsys, run_window):
    from tradingagents.research.verify import verify_run
    ctx = _run_root(tmp_path)
    assert ctx["manifest"]["charter"]["path"] == "charter.md"                    # the extraction ran under the other charter
    rows = RUN_DAYS * RUN_SYMS
    assert len(ctx["universe"]) == rows and (ctx["feats"]["tone_1d"] != 0).mean() > 0.02
    joins, real_join, real_finalize = [], run_script.forward_targets, c4.finalize

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
        rehearsals.append(len(ctx["universe"]))
        return real_rehearse(ctx)

    monkeypatch.setattr(run_script, "rehearse", counted_rehearse)
    monkeypatch.setattr(run_script, "forward_targets", counted_join)
    monkeypatch.setattr(c4, "forward_targets", no_join)                          # no other path to the outcomes
    monkeypatch.setattr(c4, "finalize", quick_finalize)
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

    # a store without the market contract (the digest agrees with the store): found before the claim
    market, digest_path = tmp_path / "klines" / f"{c4.MARKET}.parquet", tmp_path / "klines_digest.json"
    digest_text = digest_path.read_text()
    market.rename(tmp_path / "market.parquet")
    digest_path.write_text(json.dumps({k: v for k, v in ctx["digest"].items() if not k.endswith(market.name)}))
    with pytest.raises(SystemExit, match=f"kline store: no file for .*{c4.MARKET}"):
        _run(tmp_path)
    (tmp_path / "market.parquet").rename(market)
    digest_path.write_text(digest_text)
    assert not claimed.exists() and joins == [] and rehearsals == []

    # pre-flight alone: inputs verified, records rebuilt, rehearsal on synthetic targets, no claim
    assert _run(tmp_path, "--preflight-only") == 0
    assert "pre-flight passed" in capsys.readouterr().out
    assert not claimed.exists() and joins == [] and rehearsals == [rows]

    # the registered run
    assert _run(tmp_path) == 0
    directory = claimed / "c4"
    assert (directory / "claim.json").is_file() and (directory / "complete.json").is_file()
    assert not (directory / "failed.json").exists() and verify_run(directory)["status"] == "complete"
    assert sorted(p.name for p in (directory / "outputs").iterdir()) == sorted(run_script.OUTPUTS)
    assert joins == [rows]                                                       # the single outcome join
    assert rehearsals == [rows, rows]                                            # one rehearsal per process, before the claim
    verdict, evaluation = _output(tmp_path, "verdict.json"), _output(tmp_path, "evaluation.json")
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == [] and verdict["descriptive_errors"] == []
    assert verdict["test_days"] == RUN_TEST and verdict["gates"]["reader_partial"]["value"]["nw_t"] > 3.0
    assert verdict["gates"]["reader_partial_sign_by_year"]["days"] == {"2023": 30, "2024": 26}
    assert evaluation["fit_errors"] == {} and evaluation["placebo_permutation"]["draws"] == 5
    assert evaluation["days"]["first_test"].startswith("2023-12-02") and evaluation["days"]["last_test"].startswith("2024-01-26")
    assert evaluation["target_coverage"]["all_days"] == {"rows": rows, "missing": dict.fromkeys(c4.TARGET_COLUMNS, 0), "zero_return": 0}
    reader = _output(tmp_path, "reader.json")
    assert set(reader["extraction"]) == set(run_script.EXTRACTION_KEYS)
    assert reader["extraction"]["model"]["id"] == "fake/model" and reader["extraction"]["units"] == ctx["manifest"]["units"]
    assert reader["quality"]["records"] == ctx["manifest"]["records"] > 1000
    items = pd.read_parquet(tmp_path / rx.INPUTS["items"])
    assert reader["timing"] == json.loads(json.dumps(c4.json_safe(c4.timing_facts(items))))
    forecasts = _output(tmp_path, "forecasts.json")
    assert forecasts["columns"] == c4.OUTPUT_COLUMNS and len(forecasts["rows"]) == RUN_TEST * RUN_SYMS
    table = pd.DataFrame(forecasts["rows"], columns=forecasts["columns"])
    table = table.assign(date=pd.to_datetime(table["date"], utc=True)).set_index(["date", "symbol"])
    want = {}
    for sym in sorted(ctx["universe"]["symbol"].unique()):                       # the close-to-close return written out on the store
        close = pd.read_parquet(tmp_path / "klines" / f"{sym}.parquet")["close"]
        for day in table.index.get_level_values("date").unique():
            want[(day, sym)] = close[day] / close[day - DAY] - 1.0
    assert np.allclose(table[c4.TARGET].to_numpy(dtype=float), pd.Series(want).reindex(table.index).to_numpy())
    feats = ctx["feats"].assign(symbol=ctx["feats"]["base"] + "USDT").set_index(["date", "symbol"])
    for col in (*c4.BLOCK_R, "n_subject_7d", "gap_7d"):
        assert np.allclose(table[col].to_numpy(dtype=float), feats[col].reindex(table.index).to_numpy()), col
    assert table[[c4.GATE_SCORE, c4.GATE_RESIDUAL]].notna().all().all() and (table["tone_1d"] != 0).mean() > 0.02

    # one registered run per registration
    monkeypatch.setattr(run_script, "rehearse", lambda ctx: rehearsals.append(0))    # the rehearsal is not the subject here
    with pytest.raises(ValueError, match="repeat run prohibited"):
        _run(tmp_path)
    assert joins == [rows] and rehearsals == [rows, rows, 0]
    assert verify_run(directory)["status"] == "complete"


# ---------------------------------------------------------------- registration
CLOSURE = """
import json, sys
from pathlib import Path
root = Path.cwd().resolve()
import reader_charter4_register, reader_charter4_run  # noqa: F401,E401
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

    import reader_charter4_register as reg

    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(ROOT), str(ROOT / "scripts")])}
    done = subprocess.run([sys.executable, "-c", CLOSURE], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    imported = set(json.loads(done.stdout.strip().splitlines()[-1]))
    helper = {p for p in imported if p.startswith("tradingagents/research/")}       # pinned by the runtime hashes, if loaded
    assert {"scripts/reader_charter4_run.py", "tradingagents/reader/charter4.py", "scripts/reader_charter3_run.py"} <= imported
    assert imported - helper <= set(reg.SOURCE_FILES), sorted(imported - helper - set(reg.SOURCE_FILES))
    assert len(set(reg.SOURCE_FILES)) == len(reg.SOURCE_FILES) and all((ROOT / p).is_file() for p in reg.SOURCE_FILES)
    assert set(rx.SOURCES) <= set(reg.SOURCE_FILES)                                 # the manifest is checked against these
    assert {"uv.lock", reg.EXTRACTION_CHARTER, reg.PARENT_CHARTER} <= set(reg.SOURCE_FILES) and reg.CHARTER not in reg.SOURCE_FILES


def test_registration_continues_the_charter_3_registration():
    import reader_charter4_register as reg

    parent_spec = json.loads((ROOT / reg.PARENT_REGISTRATION).read_text())
    parent = parent_spec["experiments"][reg.PARENT]
    assert set(parent["source_files"]) <= set(reg.SOURCE_FILES)                     # nothing of the parent run is unpinned
    assert {p: sha(ROOT / p) for p in parent["source_files"]} == parent["source_files"]      # and nothing changed since
    assert reg.PARENT_CHARTER == parent["charter"]["path"] and sha(ROOT / reg.PARENT_CHARTER) == parent["charter"]["sha256"]
    assert reg.EXTRACTION_CHARTER == rx.CHARTER and reg.EXTRACTION_CHARTER in parent["source_files"]
    for frozen in (reg.EXTRACTION_CHARTER, reg.PARENT_CHARTER):
        assert rx.DRAFT_MARK not in (ROOT / frozen).read_text(encoding="utf-8")
    assert set(reg.INPUTS) == set(RUN_INPUTS) and set(reg.SAME_AS_PARENT) == set(reg.INPUTS)
    assert {name: parent["inputs"][name]["path"] for name in reg.INPUTS} == reg.INPUTS
    assert reg.FAMILY_KEY == parent["family"] == "llm-multiagent-v2" and parent_spec["families"][reg.FAMILY_KEY]["attempt_budget"] == 6
    assert len(parent_spec["experiments"]) == 4                                     # the four attempts so far
    assert reg.DATASET not in parent_spec["datasets"] and reg.CHARTER not in (reg.EXTRACTION_CHARTER, reg.PARENT_CHARTER)
    assert reg.DRAFT_MARK == rx.DRAFT_MARK and reg.experiment_id("20261114") == "llm-v2c4-fresh-news-dev-run-20261114"
    assert reg.experiment_id("20261114") not in parent_spec["experiments"]
    assert reg.WINDOW["start"] == parent["windows"][0]["start"] == c2.STORE_START.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = pd.Timestamp(reg.WINDOW["end"])
    assert end >= pd.Timestamp(c4.PANEL_LAST, tz="UTC") + 3 * DAY                   # the third forward bar of the last decision has closed
    assert end <= pd.Timestamp("2025-01-01", tz="UTC") and end <= pd.Timestamp(parent["windows"][0]["end"])     # nothing of the sealed windows


def test_registration_builds_an_exploratory_fifth_attempt_on_the_exposed_window():
    import reader_charter4_register as reg

    target, spec = reg.build("20991231")
    parent_spec = json.loads((ROOT / reg.PARENT_REGISTRATION).read_text())
    name = reg.experiment_id("20991231")
    assert target == "research/llm-v2-charter4-20991231/gates.json" and not (ROOT / target).exists()
    assert spec["families"] == {reg.FAMILY_KEY: parent_spec["families"][reg.FAMILY_KEY]}
    assert {k: spec["datasets"][k] for k in parent_spec["datasets"]} == parent_spec["datasets"]
    assert {k: spec["experiments"][k] for k in parent_spec["experiments"]} == parent_spec["experiments"]
    assert list(spec["experiments"]) == [*parent_spec["experiments"], name]
    assert spec["datasets"][reg.DATASET]["exposures"] == [{**reg.WINDOW, "state": "exposed"}]
    exp = spec["experiments"][name]
    assert exp["parent"] == reg.PARENT and exp["stage"] == "development" and exp["reuse"] == "exploratory" and exp["selection"] is None
    assert exp["charter"] == {"path": reg.CHARTER, "sha256": sha(ROOT / reg.CHARTER)}
    assert exp["windows"] == [{"dataset": reg.DATASET, **reg.WINDOW, "availability": "existing"}]
    assert exp["cells"] == list(run_script.CELLS) and exp["outputs"] == list(run_script.OUTPUTS)
    parent = parent_spec["experiments"][reg.PARENT]
    assert {k: v["sha256"] for k, v in exp["inputs"].items()} == {k: parent["inputs"][k]["sha256"] for k in reg.INPUTS}
    assert all(v["dataset"] == reg.DATASET for v in exp["inputs"].values())
    assert set(exp["source_files"]) == set(reg.SOURCE_FILES) and exp["source_files"][reg.PARENT_CHARTER] == parent["charter"]["sha256"]
    for word in ("tone", "next day", "722 test days", f"t at least {c4.GATE_T}"):
        assert word in exp["question"], word
    assert "FAIL" in spec["datasets"][reg.DATASET]["history_reference"] and "synthetic" in spec["datasets"][reg.DATASET]["history_reference"]


def test_charter_states_the_registered_constants():
    import reader_charter4_register as reg

    text = (ROOT / reg.CHARTER).read_text(encoding="utf-8")
    assert text.count(reg.DRAFT_MARK) == int(text.splitlines()[0].endswith(reg.DRAFT_MARK))     # in the title or nowhere
    names = [*c4.HIST, *c4.BLOCK_A, *c4.BLOCK_R, *c4.COUNTS, *c4.GAPS, *c4.SCORES, c4.TARGET, *c4.OTHER_TARGETS, c4.GATE_RESIDUAL]
    for stated in (f"t at least {c4.GATE_T}", f"lag {c4.NW_LAG}", f"penalty {RIDGE_ALPHA:g}", f"penalty {c4.CLEAN_ALPHA}",
                   f"{c4.BURN_IN_DAYS} days", f"{c4.MIN_DAY_ROWS} rows", f"seed {c4.PLACEBO_SEED}", f"{PLACEBO_DRAWS} draws",
                   f"first {c4.CLEAN_FIRST} days", f"every {c4.CLEAN_EVERY} days", f"{c4.CLEAN_ROUNDS} rounds",
                   f"every {c4.GBM_EVERY} days", f"at least {c4.MIN_BARS_SHORT} bars", f"at least {c4.MIN_BARS_LONG} bars",
                   f"at least {c4.MIN_BETA_PAIRS} pairs", f"at most {c4.TIMELY_DAYS} days", f"{c4.ATTN_HISTORY} preceding days",
                   f"fewer than {c4.ATTN_MIN_HISTORY}", f"{COST_PER_SIDE * 1e4:g} bp", *(f"{abs(k)} days" for k in c4.SHIFT_DAYS),
                   f"{c4.PANEL_FIRST} to {c4.PANEL_LAST}", reg.PARENT, reg.DATASET, reg.EXTRACTION_CHARTER, reg.PARENT_CHARTER,
                   *(f"`{n}`" for n in names)):
        assert stated in text, stated
    assert "we " not in text.lower() and " our " not in text.lower()                # impersonal prose
