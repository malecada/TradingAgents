"""Evaluation of the fresher-information change (Charter 4): next-day return from fresh reader records.

No model call and no cache. The item store and the record table of Charter 2 are inputs and everything here is
arithmetic on registered inputs. The decision is taken at 00:00 UTC of every day of the window for the members
of the last weekly universe. Three blocks of decision-time regressors are built per row: price history from the
daily bars up to the bar that closes at the decision (HIST), attention counts of the documents that became
observable on the last day (block A) and signed sums of the reader records of news documents that became
observable on the last day or the six days before it (block R). The target is the simple return of the daily
bar that opens at the decision. Every variable is ranked within the day. The registered question is whether
the net tone of the reader records (of the last day and of the six days before it, ``TONE``) carries
information beyond HIST and block A; the whole block R is a descriptive score. The controls are removed from
both sides in two steps. First a flexible fit on earlier days only is subtracted: boosted trees of the control
ranks for every reader rank, a quadratic surface of the control ranks for the target rank. Then target and
reader ranks are residualised within every day on the control ranks. A ridge model is fitted walk-forward on the residuals, and the two gates
are applied by code to the daily statistic of its score against the target residual. Every statistic outside
the two gates is descriptive and guarded: an error there is recorded in the verdict and cannot void it.

The numeric core takes value matrices with one column per target, so the null-gate script evaluates many
synthetic targets with the functions the registered run uses on its single target.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg

from tradingagents.agents_v2.charter1b import PLACEBO_DRAWS, _errors, _finite, _guard, _utc, json_safe
from tradingagents.agents_v2.evaluate import newey_west_t
from tradingagents.agents_v2.portfolio_eval import COST_PER_SIDE
from tradingagents.dossier.quant_forecast import RIDGE_ALPHA
from tradingagents.reader import charter2, charter3 as c3, consensus, features, model, reading

# registered thresholds (Charter 4 §5)
GATE_T = 2.0                # Newey-West t of the mean daily statistic of the reader score, >=
GATE_YEARS = (2023, 2024)   # calendar years (of the decision day) in which the mean daily statistic must be positive
NW_LAG = 7                  # Bartlett lag of every Newey-West t on a daily series
GATE_FORM = "corr"          # form of the daily gate statistic: within-day correlation ("corr") or covariance ("cov")

PANEL_FIRST, PANEL_LAST = "2022-01-08", "2024-12-28"    # first and last decision day
TIMELY_DAYS = 2             # a news item is timely when it becomes usable at most this many days after its publication date
ATTN_HISTORY, ATTN_MIN_HISTORY = 28, 14     # days in the own-history mean of attention; fewer than the minimum -> missing
PREV_DAYS = 6               # days before the last day that the lagged reader sums cover
MIN_DAY_ROWS = 30           # rows a day needs in a within-day regression and in the gate statistic
# flexible removal of the controls before the within-day step (Charter 4 §3.2); fitted on earlier days only
CLEAN_FIRST = 182           # days at the start of the panel that are fitted on themselves (training-only days)
CLEAN_EVERY = 91            # days between two refits of the boosted trees
CLEAN_PARAMS, CLEAN_ROUNDS, CLEAN_ALPHA = c3.CLEAN_PARAMS, c3.CLEAN_ROUNDS, c3.CLEAN_ALPHA
BURN_IN_DAYS = 364          # earlier days with a closed outcome that the walk-forward ridge needs before it scores
GBM_EVERY = 28              # days between two refits of the boosted-tree forecast
MIN_BARS_SHORT, MIN_BARS_LONG, MIN_BETA_PAIRS = 4, 10, 30
BETA_DAYS = 60
MARKET = "BTCUSDT"
DAY = pd.Timedelta(days=1)
PLACEBO_SEED = 20261114
SHIFT_DAYS = (-182, -91, -28, 28, 91, 182)
AUTOCORR_LAGS = (1, 2, 7)
LARGE = ("BTC", "ETH")      # the two assets that carry most reader records (descriptive exclusion)
YEAR_DAYS = 365

HIST_BARS = ["ret_1d", "ret_7d", "ret_30d", "rv_1d", "rv_7d", "rv_30d", "vsurge_1d", "dvol_30d", "beta_60d"]
CARD_COLUMNS = ["age_weeks", "funding_3d"]
HIST = HIST_BARS + CARD_COLUMNS
BLOCK_A = ["news_1d", "posts_1d", "attn_7d", "attn_abn_1d"]
FRESH = ["tone_1d", "unfav_1d", "evt_1d", "stance_1d"]
BLOCK_R = [*FRESH, "tone_prev6", "unfav_prev6"]
TONE = ["tone_1d", "tone_prev6"]            # features of the gate score (chosen on synthetic targets, design folder)
COUNTS = ["n_subject_1d", "n_subject_7d"]
GAPS = ["gap_1d", "gap_7d"]
TEXT_COLUMNS = [*BLOCK_A, *BLOCK_R, *COUNTS, *GAPS]
TARGET = "fwd_ret_1d"
OTHER_TARGETS = {"fwd_absret_1d": 1, "fwd_rv_1d": 1, "fwd_ret_3d": 3}      # column -> days until the outcome has closed
TARGET_COLUMNS = [TARGET, *OTHER_TARGETS]
CONTROLS = HIST + BLOCK_A

GATE_SCORE, GATE_RESIDUAL = "s_reader", "e_reader"
# partial scores: name -> (features, controls, flexible removal of the controls before the within-day step)
PARTIAL_SCORES = {
    "s_reader": (TONE, CONTROLS, True),
    "s_reader_lin": (TONE, CONTROLS, False),
    "s_reader_hist": (TONE, HIST, True),
    "s_block_r": (BLOCK_R, CONTROLS, True),
    "s_fresh": (FRESH, CONTROLS, True),
    "s_text": (BLOCK_A + BLOCK_R, HIST, True),
    "s_attn": (BLOCK_A, HIST, True),
}
FORECASTS = {"v_hist": HIST, "v_hist_attn": CONTROLS, "v_full": CONTROLS + BLOCK_R}
GBM_FORECASTS = {"g_hist_attn": CONTROLS, "g_full": CONTROLS + BLOCK_R}
LOSS_PAIRS = [("v_hist_attn", "v_full"), ("v_hist", "v_hist_attn"), ("v_hist", "v_full"), ("g_hist_attn", "g_full")]
SCORES = [*PARTIAL_SCORES, *FORECASTS, *GBM_FORECASTS]
PANEL_COLUMNS = ["date", "friday", "symbol", "base", *HIST, *TEXT_COLUMNS, *TARGET_COLUMNS]
OUTPUT_COLUMNS = ["date", "symbol", *BLOCK_R, "n_subject_7d", "gap_7d", TARGET, GATE_RESIDUAL, *SCORES]


# ---------------------------------------------------------------- universe and item timing
def daily_universe(top: pd.DataFrame) -> pd.DataFrame:
    """One row per decision day and member. The members of day D are those of the last Friday before D (the
    Saturday uses the Friday one day earlier, the Friday the one seven days earlier); the card columns are the
    Friday's values. ``date`` is the decision day, ``friday`` the day of the universe."""
    weekly = top[["date", "symbol", "base", *CARD_COLUMNS]].rename(columns={"date": "friday"}).reset_index(drop=True)
    weekly["friday"] = _utc(weekly["friday"].to_numpy()).to_numpy()
    if weekly.duplicated(["friday", "symbol"]).any():
        raise ValueError("universe rows are not unique on (date, symbol)")
    if (weekly["friday"].dt.day_of_week != 4).any():
        raise ValueError("universe dates are not Fridays")
    out = pd.concat([weekly.assign(date=weekly["friday"] + k * DAY) for k in range(1, 8)], ignore_index=True)
    first, last = pd.Timestamp(PANEL_FIRST, tz="UTC"), pd.Timestamp(PANEL_LAST, tz="UTC")
    out = out[(out["date"] >= first) & (out["date"] <= last)]
    days = pd.DatetimeIndex(np.sort(out["date"].unique()))
    if len(days) != (last - first).days + 1 or days[0] != first or days[-1] != last:
        raise ValueError("the weekly universe does not cover every decision day of the window")
    return out.sort_values(["date", "symbol"]).reset_index(drop=True)[["date", "friday", "symbol", "base", *CARD_COLUMNS]]


def item_days(items: pd.DataFrame) -> pd.DataFrame:
    """Adds ``day`` (the first decision at which the item is usable: the midnight after its observation time,
    so an item stamped exactly at midnight waits one more day), ``news`` and ``timely``. A news item is timely
    when ``day`` is at most ``TIMELY_DAYS`` after its publication date; a community post always is."""
    out = items.copy()
    seen = pd.to_datetime(out["as_of_ts"], utc=True).dt.as_unit("ns")
    published = pd.to_datetime(out["event_ts"], utc=True).dt.as_unit("ns").dt.floor("D")
    out["day"] = seen.dt.floor("D") + DAY
    out["news"] = out["source"] != "reddit"
    out["timely"] = ~out["news"] | ((out["day"] - published) <= TIMELY_DAYS * DAY)
    return out


def timing_facts(items: pd.DataFrame) -> dict:
    """Timing of the news item rows against the daily decision (no price quantity): how many days after the
    publication date a row becomes usable, the share that is timely, and the hours a row waits between its
    observation and the first decision that may use it. By year of that decision."""
    rows = item_days(items)
    news = rows[rows["news"]]
    seen = pd.to_datetime(news["as_of_ts"], utc=True).dt.as_unit("ns")
    published = pd.to_datetime(news["event_ts"], utc=True).dt.as_unit("ns").dt.floor("D")
    after = ((news["day"] - published) / DAY).to_numpy(dtype=float)
    wait = ((news["day"] - seen) / pd.Timedelta(hours=1)).to_numpy(dtype=float)
    timely, year = news["timely"].to_numpy(dtype=bool), news["day"].dt.year.to_numpy()

    def block(mask: np.ndarray) -> dict:
        n = int(mask.sum())
        if n == 0:
            return {"rows": 0}
        days = after[mask]
        return {"rows": n, "timely_share": float(timely[mask].mean()),
                "usable_days_after_publication": {"1": float((days <= 1).mean()), "2": float((days == 2).mean()),
                                                  "3_or_more": float((days > 2).mean())},
                "hours_from_observation_to_decision": {q: float(np.quantile(wait[mask], v))
                                                       for q, v in (("q25", 0.25), ("median", 0.5), ("q75", 0.75))}}

    return {"timely_days": TIMELY_DAYS, "news_rows": block(np.ones(len(news), dtype=bool)),
            "by_year": {str(int(y)): block(year == y) for y in sorted(set(year.tolist()))},
            "community_rows": int((~rows["news"]).sum())}


def _grid(keys: pd.DataFrame, store_start: pd.Timestamp) -> tuple[pd.DatetimeIndex, list[str]]:
    """Days from the first usable day of the store to the last decision day, and the bases of the panel."""
    last = _utc(keys["date"].to_numpy()).max()
    return pd.date_range(store_start + DAY, last, freq="D"), sorted(set(keys["base"]))


def _dense(table: pd.Series, days: pd.DatetimeIndex, bases: list[str]) -> np.ndarray:
    """A (day, base) series as a days x bases matrix with zeros where the series has no entry."""
    out = np.zeros((len(days), len(bases)))
    if len(table):
        di = days.get_indexer(pd.DatetimeIndex(table.index.get_level_values(0)))
        bi = pd.Index(bases).get_indexer(table.index.get_level_values(1))
        ok = (di >= 0) & (bi >= 0)
        out[di[ok], bi[ok]] = table.to_numpy(dtype=float)[ok]
    return out


def _window(values: np.ndarray, back: int, ahead: int = 0) -> np.ndarray:
    """Per day i the sum over the days i - back .. i + ahead that lie inside the grid (ahead <= 0)."""
    total = np.vstack([np.zeros((1, values.shape[1])), np.cumsum(values, axis=0)])
    i = np.arange(len(values))
    return total[i + ahead + 1] - total[np.maximum(i - back, 0)]


def _lookup(keys: pd.DataFrame, days: pd.DatetimeIndex, bases: list[str], columns: dict[str, np.ndarray]) -> pd.DataFrame:
    out = keys[["date", "base"]].drop_duplicates().reset_index(drop=True)
    di = days.get_indexer(pd.DatetimeIndex(_utc(out["date"].to_numpy())))
    bi = pd.Index(bases).get_indexer(out["base"])
    if (di < 0).any() or (bi < 0).any():
        raise ValueError("decision days outside the item grid")
    for name, matrix in columns.items():
        out[name] = matrix[di, bi]
    return out


# ---------------------------------------------------------------- block A (attention) and block R (reader)
def attention_daily(items: pd.DataFrame, keys: pd.DataFrame, store_start: pd.Timestamp = charter2.STORE_START) -> pd.DataFrame:
    """(date, base, block A) for every (date, base) of ``keys``; ``items`` carry the columns of ``item_days``.

    Counts are distinct documents linked to the asset at any salience, by the day at which they became usable.
    ``news_1d`` and ``posts_1d`` count the timely news documents and the community posts of the last day,
    ``attn_7d`` both sources over the last seven days. ``attn_abn_1d`` is log(1 + documents of the last day)
    minus the asset's mean of the same daily value over the ``ATTN_HISTORY`` preceding days; a history day
    counts only inside the store, and with fewer than ``ATTN_MIN_HISTORY`` of them the value is missing."""
    days, bases = _grid(keys, store_start)
    rows = items[items["timely"] & items["base"].isin(bases)]
    count = lambda part: _dense(part.groupby(["day", "base"])["doc_id"].nunique(), days, bases)   # noqa: E731
    news, posts = count(rows[rows["news"]]), count(rows[~rows["news"]])
    level = np.log1p(news + posts)
    i = np.arange(len(days))
    n_hist = np.minimum(i, ATTN_HISTORY)[:, None]
    past = _window(level, ATTN_HISTORY, -1)                                 # the days i - 28 .. i - 1 inside the store
    own = np.where(n_hist >= ATTN_MIN_HISTORY, past / np.maximum(n_hist, 1), np.nan)
    return _lookup(keys, days, bases, {"news_1d": np.log1p(news), "posts_1d": np.log1p(posts),
                                       "attn_7d": np.log1p(_window(news + posts, 6)), "attn_abn_1d": level - own})


def subject_rows(items: pd.DataFrame, records: pd.DataFrame) -> pd.DataFrame:
    """Timely news item rows joined with their record, restricted to resolved records about the asset as the
    subject. The item type is the one of the item row."""
    rec = records[["doc_id", "base", "resolution", "relevance", "event_class", "status", "direction", "materiality"]]
    rows = items.loc[items["news"] & items["timely"], ["day", "doc_id", "base", "type"]].merge(
        rec, on=["doc_id", "base"], how="inner", validate="m:1")
    subj = rows[(rows["resolution"] != "unresolved") & (rows["relevance"] == "subject")].copy()
    subj["materiality"] = subj["materiality"].astype(int)
    subj["sign"] = subj["direction"].map(features.DIRECTION_SIGN).astype(float)
    if subj["sign"].isna().any():
        raise ValueError("record with an unknown direction")
    return subj


def gap_rows(items: pd.DataFrame, records: pd.DataFrame) -> pd.DataFrame:
    """Timely news item rows without a judgement that the reading rule would have asked for: untyped rows and
    rows the rule reads that have no record. ``items`` carry the flags of ``reading.flag_items``."""
    rows = items.loc[items["news"] & items["timely"], ["day", "doc_id", "base", "typed", "read"]]
    have = records[["doc_id", "base"]].drop_duplicates().assign(record=True)
    rows = rows.merge(have, on=["doc_id", "base"], how="left", validate="m:1")
    return rows[~rows["typed"].astype(bool) | (rows["read"] & rows["record"].isna())]


def reader_daily(items: pd.DataFrame, records: pd.DataFrame, keys: pd.DataFrame,
                 store_start: pd.Timestamp = charter2.STORE_START) -> pd.DataFrame:
    """(date, base, block R, record counts, gap counts) for every (date, base) of ``keys``; ``items`` carry the
    columns of ``item_days`` and ``reading.flag_items``.

    Per asset and day at which the rows became usable: ``tone`` is the sum of direction sign times materiality
    over events, ``unfav`` the materiality of unfavourable events, ``evt`` the materiality of all events (events
    equal on class, status and direction within the asset-day count once at their highest materiality),
    ``stance`` favourable minus unfavourable opinion items. The ``_1d`` features take the last day, the
    ``_prev6`` features the sum of the daily values over the ``PREV_DAYS`` days before it."""
    days, bases = _grid(keys, store_start)
    subj = subject_rows(items, records)
    subj = subj[subj["base"].isin(bases)]
    events, opinions = subj[subj["type"] == "event"], subj[subj["type"] == "analysis_opinion"]
    ev = events.groupby(["day", "base", "event_class", "status", "direction"], sort=False, observed=True).agg(
        materiality=("materiality", "max"), sign=("sign", "first")).reset_index()
    ev["tone"] = ev["sign"] * ev["materiality"]
    ev["unfav"] = ev["materiality"].where(ev["direction"] == "unfavourable", 0)
    total = lambda frame, col: _dense(frame.groupby(["day", "base"])[col].sum(), days, bases)     # noqa: E731
    tone, unfav, evt = total(ev, "tone"), total(ev, "unfav"), total(ev, "materiality")
    stance = total(opinions, "sign")
    n_subject = _dense(subj.groupby(["day", "base"]).size(), days, bases)
    gaps = gap_rows(items, records)
    gap = _dense(gaps[gaps["base"].isin(bases)].groupby(["day", "base"]).size(), days, bases)
    return _lookup(keys, days, bases, {
        "tone_1d": tone, "unfav_1d": unfav, "evt_1d": evt, "stance_1d": stance,
        "tone_prev6": _window(tone, PREV_DAYS, -1), "unfav_prev6": _window(unfav, PREV_DAYS, -1),
        "n_subject_1d": n_subject, "n_subject_7d": _window(n_subject, 6), "gap_1d": gap, "gap_7d": _window(gap, 6)})


def text_features(items: pd.DataFrame, docs: pd.DataFrame, records: pd.DataFrame, keys: pd.DataFrame) -> pd.DataFrame:
    """One row per (date, base) of ``keys`` with block A, block R, the record counts and the gap counts."""
    flagged = item_days(reading.flag_items(items, docs))
    out = attention_daily(flagged, keys).merge(reader_daily(flagged, records, keys), on=["date", "base"], validate="1:1")
    return out[["date", "base", *TEXT_COLUMNS]]


# ---------------------------------------------------------------- bar history (HIST) and forward targets
def bar_history(bars: pd.DataFrame, market: pd.Series) -> pd.DataFrame:
    """Per bar, statistics of the bars up to and including it; ``market`` is the daily log return of the market
    contract. Time windows are closed on the bar itself, so a row never uses a later bar."""
    gk, close, volume = c3.gk_variance(bars), bars["close"].where(bars["close"] > 0), bars["quote_volume"]
    back = lambda k: np.log(close.to_numpy() / close.reindex(close.index - k * DAY).to_numpy())     # noqa: E731
    out = pd.DataFrame({"ret_1d": back(1), "ret_7d": back(7), "ret_30d": back(30)}, index=bars.index)
    out["rv_1d"] = gk
    out["rv_7d"] = gk.rolling("7D", min_periods=MIN_BARS_SHORT).mean()
    out["rv_30d"] = gk.rolling("30D", min_periods=MIN_BARS_LONG).mean()
    v30 = volume.rolling("30D", min_periods=MIN_BARS_LONG).mean()
    out["vsurge_1d"] = np.log((volume / v30).where((volume > 0) & (v30 > 0)))
    out["dvol_30d"] = v30
    own, mkt = out["ret_1d"], market.reindex(bars.index)
    both = own.notna() & mkt.notna()
    own, mkt = own.where(both), mkt.where(both)
    window = f"{BETA_DAYS}D"
    var = mkt.rolling(window, min_periods=MIN_BETA_PAIRS).var()
    out["beta_60d"] = (own.rolling(window, min_periods=MIN_BETA_PAIRS).cov(mkt) / var).where(var > 0)
    return out[HIST_BARS]


def market_returns(klines_dir: Path, before: pd.Timestamp) -> pd.Series:
    """Daily log return of the market contract over the bars that open before ``before``."""
    bars = c3.load_bars(klines_dir, MARKET)
    close = bars.loc[bars.index < before, "close"]
    close = close.where(close > 0)
    return pd.Series(np.log(close.to_numpy() / close.reindex(close.index - DAY).to_numpy()), index=close.index)


def history_features(klines_dir: Path, keys: pd.DataFrame) -> pd.DataFrame:
    """(date, symbol, bar-history features) for every panel row, from the bars up to the bar of the day before
    the decision day, which closes at the decision. A row without that bar has every feature missing."""
    days_all = pd.DatetimeIndex(_utc(keys["date"].to_numpy()))
    market = market_returns(klines_dir, days_all.max())
    parts = []
    for symbol, rows in keys.groupby("symbol", sort=True):
        days = pd.DatetimeIndex(_utc(rows["date"].to_numpy()))
        bars = c3.load_bars(klines_dir, symbol)
        hist = bar_history(bars[bars.index < days.max()], market).reindex(days - DAY)
        parts.append(hist.reset_index(drop=True).assign(date=days, symbol=symbol))
    return pd.concat(parts, ignore_index=True)[["date", "symbol", *HIST_BARS]]


def forward_targets(klines_dir: Path, keys: pd.DataFrame) -> pd.DataFrame:
    """The outcome join: per panel row the simple return of the bar that opens at the decision (close of the
    decision day over the close of the day before), its absolute value, the Garman-Klass variance of that bar
    and the simple return over three bars. A row without the bars it needs has the target missing. No bar
    later than two days after the decision day is read."""
    parts = []
    for symbol, rows in keys.groupby("symbol", sort=True):
        days = pd.DatetimeIndex(_utc(rows["date"].to_numpy()))
        bars = c3.load_bars(klines_dir, symbol)
        bars = bars[bars.index <= days.max() + 2 * DAY]
        close, gk = bars["close"].where(bars["close"] > 0), c3.gk_variance(bars)
        entry = close.reindex(days - DAY).to_numpy()
        ret = close.reindex(days).to_numpy() / entry - 1.0
        parts.append(pd.DataFrame({"date": days, "symbol": symbol, "fwd_ret_1d": ret, "fwd_absret_1d": np.abs(ret),
                                   "fwd_rv_1d": gk.reindex(days).to_numpy(),
                                   "fwd_ret_3d": close.reindex(days + 2 * DAY).to_numpy() / entry - 1.0}))
    return pd.concat(parts, ignore_index=True)[["date", "symbol", *TARGET_COLUMNS]]


# ---------------------------------------------------------------- panel
def _keyed(frame: pd.DataFrame, key: list[str], cols: list[str]) -> pd.DataFrame:
    out = frame[[*key, *cols]].copy()
    out["date"] = _utc(out["date"].to_numpy()).to_numpy()
    return out


def assemble_panel(universe: pd.DataFrame, feats: pd.DataFrame, hist: pd.DataFrame, fwd: pd.DataFrame) -> pd.DataFrame:
    """Daily universe rows joined with the text features (on day and asset), the bar history and the forward
    targets (on day and contract). Every panel row needs its text row and its history row."""
    key = ["date", "symbol"]
    panel = _keyed(universe, key, ["friday", "base", *CARD_COLUMNS])
    if panel.duplicated(key).any():
        raise ValueError("panel rows are not unique on (date, symbol)")
    panel = panel.merge(_keyed(feats, ["date", "base"], TEXT_COLUMNS), on=["date", "base"], how="left", validate="m:1", indicator=True)
    if (panel.pop("_merge") != "both").any():
        raise ValueError("panel rows without text features")
    panel = panel.merge(_keyed(hist, key, HIST_BARS), on=key, how="left", validate="1:1", indicator=True)
    if (panel.pop("_merge") != "both").any():
        raise ValueError("panel rows without bar history")
    filled = [c for c in TEXT_COLUMNS if c != "attn_abn_1d"]         # attn_abn_1d alone may be missing (short own history)
    if panel[filled].isna().any().any():
        raise ValueError("text features with missing values")
    panel = panel.merge(_keyed(fwd, key, TARGET_COLUMNS), on=key, how="left", validate="1:1")
    for col in TARGET_COLUMNS:
        panel[col] = pd.to_numeric(panel[col], errors="coerce")
    return panel.sort_values(key).reset_index(drop=True)[PANEL_COLUMNS]


# ---------------------------------------------------------------- ranks, residuals, walk-forward
_dates, _stamp, feature_ranks = c3._dates, c3._stamp, c3.feature_ranks


def target_rank(panel: pd.DataFrame, col: str = TARGET) -> np.ndarray:
    """Within-day percentile rank minus 0.5 over the rows that have the target; missing stays missing."""
    return (panel.groupby("date")[col].rank(pct=True) - 0.5).to_numpy(dtype=float)


def _day_index(dates: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(days in time order, position of every row's day). The panel days are consecutive calendar days, so the
    day ``horizon`` positions earlier is the day whose ``horizon``-day outcome closes at the decision."""
    days, idx = np.unique(dates, return_inverse=True)
    if len(days) > 1 and (np.diff(days) != DAY.value).any():
        raise ValueError("panel days are not consecutive calendar days")
    return days, idx


def _rows_by_day(idx: np.ndarray, n_days: int) -> list[np.ndarray]:
    order = np.argsort(idx, kind="stable")
    bounds = np.searchsorted(idx[order], np.arange(n_days + 1))
    return [order[bounds[k]:bounds[k + 1]] for k in range(n_days)]


def _columns(values: np.ndarray) -> np.ndarray:
    return values[:, None] if values.ndim == 1 else values


def _present(values: np.ndarray) -> np.ndarray:
    """Rows where the value columns are present. The columns of one call share their missing rows."""
    have = np.isfinite(values)
    if (have.any(axis=1) != have.all(axis=1)).any():
        raise ValueError("value columns differ in their missing rows")
    return have[:, 0]


def residuals(values: np.ndarray, controls: np.ndarray, dates: np.ndarray, min_rows: int | None = None) -> np.ndarray:
    """Within-day OLS residual of every column of ``values`` on an intercept and the controls. A column is
    fitted on the rows of the day where it is present; with fewer than ``min_rows`` such rows it is missing
    on that day."""
    min_rows = MIN_DAY_ROWS if min_rows is None else min_rows
    days, idx = _day_index(dates)
    out = np.full(values.shape, np.nan)
    for rows in _rows_by_day(idx, len(days)):
        design = np.column_stack([np.ones(len(rows)), controls[rows]])
        block = values[rows]
        have = np.isfinite(block)
        if (have == have[:, :1]).all():                         # every column present on the same rows: one fit
            h = have[:, 0]
            if h.sum() >= min_rows:
                beta, *_ = np.linalg.lstsq(design[h], block[h], rcond=None)
                out[rows[h]] = block[h] - design[h] @ beta
            continue
        for j in range(values.shape[1]):
            h = have[:, j]
            if h.sum() >= min_rows:
                beta, *_ = np.linalg.lstsq(design[h], block[h, j], rcond=None)
                out[rows[h], j] = block[h, j] - design[h] @ beta
    return out


def past_trees(values: np.ndarray, controls: np.ndarray, dates: np.ndarray) -> np.ndarray:
    """Every column of ``values`` minus what boosted trees predict from the controls. The trees that serve a
    day are fitted on earlier days only: they are refitted every ``CLEAN_EVERY`` days on all days before the
    refit day. The first ``CLEAN_FIRST`` days are fitted on themselves; they lie inside the burn-in and are
    never scored."""
    import lightgbm as lgb

    if not (np.isfinite(values).all() and np.isfinite(controls).all()):
        raise ValueError("flexible step: missing value in a rank")
    days, idx = _day_index(dates)
    out = np.full(values.shape, np.nan)

    def fit(rows):
        return [lgb.train(dict(CLEAN_PARAMS), lgb.Dataset(controls[rows], label=values[rows, j]), num_boost_round=CLEAN_ROUNDS)
                for j in range(values.shape[1])]

    def subtract(rows, boosters):
        out[rows] = values[rows] - np.column_stack([b.predict(controls[rows]) for b in boosters])

    head = idx < CLEAN_FIRST
    subtract(head, fit(head))
    for start in range(CLEAN_FIRST, len(days), CLEAN_EVERY):
        subtract((idx >= start) & (idx < start + CLEAN_EVERY), fit(idx < start))
    return out


def past_surface(values: np.ndarray, controls: np.ndarray, dates: np.ndarray, horizon: int = 1) -> np.ndarray:
    """``values`` (rows x columns, missing rows shared by the columns) minus a quadratic surface of the controls,
    fitted by ridge on the rows of all earlier days whose ``horizon``-day outcome has closed by the decision,
    refitted every day. The first ``CLEAN_FIRST`` days are fitted on themselves; they lie inside the burn-in and
    are never scored. A missing value stays missing."""
    days, idx = _day_index(dates)
    basis, have = c3.quadratic_basis(controls), _present(values)
    rows = _rows_by_day(np.where(have, idx, len(days)), len(days))           # present rows per day
    k = basis.shape[1]
    penalty = CLEAN_ALPHA * np.eye(k)
    penalty[0, 0] = 0.0
    out = np.full(values.shape, np.nan)
    gram, moment = np.zeros((k, k)), np.zeros((k, values.shape[1]))

    def add(day):
        nonlocal gram, moment
        gram, moment = gram + basis[rows[day]].T @ basis[rows[day]], moment + basis[rows[day]].T @ values[rows[day]]

    def beta():                                                 # no row so far: no surface
        if gram[0, 0] <= 0:
            return np.zeros((k, values.shape[1]))
        return linalg.solve(gram + penalty, moment, assume_a="pos")           # positive definite once a row is there

    n_head = min(CLEAN_FIRST, len(days))
    for day in range(n_head):
        add(day)
    head = beta()
    for day in range(n_head):
        out[rows[day]] = values[rows[day]] - basis[rows[day]] @ head
    gram, moment, included = np.zeros((k, k)), np.zeros((k, values.shape[1])), -1
    for day in range(n_head, len(days)):
        while included < day - horizon:
            included += 1
            add(included)
        out[rows[day]] = values[rows[day]] - basis[rows[day]] @ beta()
    return out


def walk_forward(X: np.ndarray, E: np.ndarray, dates: np.ndarray, horizon: int = 1, burn_in: int = BURN_IN_DAYS,
                 alpha: float = RIDGE_ALPHA) -> tuple[np.ndarray, np.ndarray]:
    """(score per row and column of ``E``, ridge coefficients per day, feature and column). A day is forecast by
    a ridge without intercept fitted on the days whose ``horizon``-day outcome has closed by its decision; a day
    with fewer than ``burn_in`` such days is training only (score and coefficients missing)."""
    days, idx = _day_index(dates)
    full = np.isfinite(X).all(axis=1)
    usable = full & _present(E)
    train = _rows_by_day(np.where(usable, idx, len(days)), len(days))
    k, m = X.shape[1], E.shape[1]
    score, coef = np.full((len(X), m), np.nan), np.full((len(days), k, m), np.nan)
    S, C, n_train, included = np.zeros((k, k)), np.zeros((k, m)), 0, -1
    ridge = alpha * np.eye(k)
    for day, rows in enumerate(_rows_by_day(idx, len(days))):
        while included < day - horizon:
            included += 1
            r = train[included]
            S, C, n_train = S + X[r].T @ X[r], C + X[r].T @ E[r], n_train + len(r)
        if day - horizon + 1 < burn_in or n_train == 0:
            continue
        coef[day] = np.linalg.solve(S + ridge, C)
        rows = rows[full[rows]]
        score[rows] = X[rows] @ coef[day]
    return score, coef


# ---------------------------------------------------------------- daily statistics
def daily_stats(dates: np.ndarray, a: np.ndarray, b: np.ndarray, min_rows: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(days, correlation, covariance) of ``a`` and ``b`` per day and column over the rows where both exist. A
    day counts for a column when it has ``min_rows`` such rows and both sides vary; otherwise both are missing."""
    min_rows = MIN_DAY_ROWS if min_rows is None else min_rows
    a, b = _columns(a), _columns(b)
    days, idx = _day_index(dates)
    corr, cov = np.full((len(days), a.shape[1]), np.nan), np.full((len(days), a.shape[1]), np.nan)

    def moments(x, y):
        xc, yc = x - x.mean(axis=0), y - y.mean(axis=0)
        return (xc * yc).sum(axis=0), (xc ** 2).sum(axis=0), (yc ** 2).sum(axis=0), np.ptp(x, axis=0) > 0, np.ptp(y, axis=0) > 0

    for day, rows in enumerate(_rows_by_day(idx, len(days))):
        x, y = a[rows], b[rows]
        have = np.isfinite(x) & np.isfinite(y)
        groups = [(slice(None), have[:, 0])] if (have == have[:, :1]).all() else [([j], have[:, j]) for j in range(a.shape[1])]
        for cols, h in groups:
            if h.sum() < min_rows:
                continue
            sxy, sxx, syy, vx, vy = moments(x[h][:, cols], y[h][:, cols])
            ok = vx & vy
            with np.errstate(invalid="ignore", divide="ignore"):
                corr[day, cols] = np.where(ok, sxy / np.sqrt(sxx * syy), np.nan)
            cov[day, cols] = np.where(ok, sxy / h.sum(), np.nan)
    return days, corr, cov


def nw_t(series: np.ndarray, lag: int = NW_LAG) -> np.ndarray:
    """Newey-West t of the mean of every column (Bartlett weights, missing days dropped per column)."""
    series = _columns(np.asarray(series, dtype=float))
    return np.array([newey_west_t(pd.Series(series[:, j]), lag) if np.isfinite(series[:, j]).sum() >= 3 else np.nan
                     for j in range(series.shape[1])])


def _series(days: np.ndarray, values: np.ndarray) -> pd.Series:
    out = pd.Series(values, index=pd.DatetimeIndex([_stamp(d) for d in days]), dtype=float)
    return out.dropna()


def series_stats(series: pd.Series) -> dict:
    series = series.dropna()
    if len(series) < 3:
        return {"days": int(len(series)), "mean": None, "nw_t": None, "hit_rate": None, "by_year": {}}
    by_year = {str(int(y)): float(v.mean()) for y, v in series.groupby(c3._years(series.index))}
    return {"days": int(len(series)), "mean": float(series.mean()), "nw_t": newey_west_t(series, NW_LAG),
            "hit_rate": float((series > 0).mean()), "by_year": by_year}


# ---------------------------------------------------------------- partial scores and the gate statistic
def feature_residuals(panel: pd.DataFrame, feats, controls, flexible: bool = False, cache: dict | None = None) -> np.ndarray:
    """The feature ranks with the controls removed: within every day the OLS residual on the control ranks.
    ``flexible`` subtracts before that what boosted trees fitted on earlier days predict from the control
    ranks (``past_trees``). ``cache`` keeps the tree step of a (feature, controls) pair for a later call."""
    dates, ranks = _dates(panel), feature_ranks(panel, feats)
    if flexible:
        cache, key = ({} if cache is None else cache), tuple(controls)
        todo = [f for f in feats if (f, key) not in cache]
        if todo:
            cleaned = past_trees(feature_ranks(panel, todo), feature_ranks(panel, controls), dates)
            cache.update({(f, key): cleaned[:, j] for j, f in enumerate(todo)})
        ranks = np.column_stack([cache[(f, key)] for f in feats])
    return residuals(ranks, feature_ranks(panel, controls), dates)


def target_residual(panel: pd.DataFrame, target: np.ndarray, controls, flexible: bool = False, horizon: int = 1) -> np.ndarray:
    """The target (one column per target) with the controls removed: within every day the OLS residual on the
    control ranks. ``flexible`` subtracts before that a quadratic surface of the control ranks fitted on
    earlier days (``past_surface``)."""
    dates, ranks = _dates(panel), feature_ranks(panel, controls)
    target = _columns(target)
    if flexible:
        target = past_surface(target, ranks, dates, horizon)
    return residuals(target, ranks, dates)


def coefficient_frame(dates: np.ndarray, coef: np.ndarray, feats) -> pd.DataFrame:
    days = _day_index(dates)[0]
    frame = pd.DataFrame(coef[:, :, 0], index=pd.DatetimeIndex([_stamp(d) for d in days]), columns=list(feats))
    return frame.dropna(how="all")


def partial_score(panel: pd.DataFrame, feats, controls, flexible: bool = False, target: np.ndarray | None = None,
                  X: np.ndarray | None = None, cache: dict | None = None, horizon: int = 1):
    """(walk-forward ridge score, target residual, feature residuals, coefficients per test day) of one
    partial question: do ``feats`` carry information on the target beyond ``controls``? ``X`` hands in feature
    residuals that were already built for the same features and controls."""
    dates = _dates(panel)
    if X is None:
        X = feature_residuals(panel, feats, controls, flexible, cache)
    e = target_residual(panel, target_rank(panel) if target is None else target, controls, flexible, horizon)
    score, coef = walk_forward(X, e, dates, horizon)
    return score[:, 0], e[:, 0], X, coefficient_frame(dates, coef, feats)


def daily_statistic(dates: np.ndarray, score: np.ndarray, resid: np.ndarray, form: str | None = None) -> pd.Series:
    """The daily statistic of a score against a target residual in the registered form: the within-day Pearson
    correlation (``corr``) or the within-day covariance (``cov``), on the days that have ``MIN_DAY_ROWS`` rows
    with both and variation on both sides."""
    days, corr, cov = daily_stats(dates, score, resid)
    return _series(days, {"corr": corr, "cov": cov}[GATE_FORM if form is None else form][:, 0])


def gate_statistics(dates: np.ndarray, score: np.ndarray, resid: np.ndarray) -> tuple[dict, pd.Series]:
    """The two registered statistics and the daily series they are built from."""
    daily = daily_statistic(dates, score, resid)
    years = c3._years(daily.index)
    by_year = {}
    for y in GATE_YEARS:
        vals = daily.to_numpy()[years == y]
        by_year[str(y)] = {"days": int(len(vals)), "mean": float(vals.mean()) if len(vals) else None}
    summary = {"form": GATE_FORM, "days": int(len(daily)), "mean": float(daily.mean()) if len(daily) else None,
               "nw_t": newey_west_t(daily, NW_LAG) if len(daily) >= 3 else None}
    return {"reader_partial": summary, "reader_partial_by_year": by_year}, daily


# ---------------------------------------------------------------- fitted scores
def gbm_forward(X: np.ndarray, y: np.ndarray, dates: np.ndarray, burn_in: int = BURN_IN_DAYS) -> np.ndarray:
    """Boosted-tree forecast of ``y`` per row. The model that serves a day is fitted on the days whose outcome
    had closed at the last refit; it is refitted every ``GBM_EVERY`` days from the first day with ``burn_in``
    such days."""
    days, idx = _day_index(dates)
    usable, score = np.isfinite(y) & np.isfinite(X).all(axis=1), np.full(len(y), np.nan)
    for start in range(burn_in, len(days), GBM_EVERY):
        train = usable & (idx < start)
        if not train.any():
            continue
        predict, _ = model.fit_gbm(X[train], y[train])
        rows = np.flatnonzero((idx >= start) & (idx < start + GBM_EVERY) & np.isfinite(X).all(axis=1))
        score[rows] = predict(X[rows])
    return score


def fit_scores(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict, dict]:
    """(panel with the gate residual and one column per score, working arrays of the partial scores, errors).
    The gate score is fitted unguarded; a failure of any other fit leaves its column missing and is recorded."""
    out, parts, errors, cache = panel.copy(), {}, {}, {}
    dates, y = _dates(panel), target_rank(panel)

    def _partial(name):
        feats, controls, flexible = PARTIAL_SCORES[name]
        score, e, X, frame = partial_score(panel, feats, controls, flexible, target=y, cache=cache)
        parts[name] = {"resid": e, "X": X, "coefficients": frame, "features": list(feats)}
        return score

    out[GATE_SCORE] = _partial(GATE_SCORE)
    out[GATE_RESIDUAL] = parts[GATE_SCORE]["resid"]
    jobs = [(n, lambda n=n: _partial(n)) for n in PARTIAL_SCORES if n != GATE_SCORE]
    jobs += [(n, lambda c=c: walk_forward(feature_ranks(panel, c), y[:, None], dates)[0][:, 0]) for n, c in FORECASTS.items()]
    jobs += [(n, lambda c=c: gbm_forward(feature_ranks(panel, c), y, dates)) for n, c in GBM_FORECASTS.items()]
    for name, job in jobs:
        try:
            out[name] = job()
        except Exception as exc:                                    # noqa: BLE001
            out[name], errors[name] = np.nan, {"error": f"{type(exc).__name__}: {exc}"}
    return out, parts, errors


def univariate(dates: np.ndarray, X: np.ndarray, resid: np.ndarray, names) -> dict:
    """Daily correlation of every residualised feature with the target residual (no fit)."""
    days, corr, _ = daily_stats(dates, X, np.repeat(resid[:, None], X.shape[1], axis=1))
    return {name: series_stats(_series(days, corr[:, j])) for j, name in enumerate(names)}


def coefficient_summary(frame: pd.DataFrame) -> dict:
    """Mean, spread and sign share of the ridge coefficients over the test days and their path at every
    seventh test day."""
    path = frame.iloc[::7]
    return {"days": int(len(frame)),
            "features": {c: {"mean": float(frame[c].mean()), "sd": float(frame[c].std()),
                             "share_positive": float((frame[c] > 0).mean())} for c in frame.columns},
            "path": {"dates": list(path.index), **{c: path[c].to_numpy() for c in path.columns}}}


def partial_summary(dates: np.ndarray, score: np.ndarray, part: dict, target: np.ndarray) -> dict:
    """Daily statistic in both forms, size and feature detail of one partial score. Only test days enter."""
    scored = np.isfinite(score)
    masked = np.where(scored, part["resid"], np.nan)
    return {"daily_correlation": series_stats(daily_statistic(dates, score, part["resid"], "corr")),
            "daily_covariance": series_stats(daily_statistic(dates, score, part["resid"], "cov")),
            "size": c3.size_statistics(score, part["resid"], target),
            "univariate": univariate(dates, np.where(scored[:, None], part["X"], np.nan), masked, part["features"]),
            "coefficients": coefficient_summary(part["coefficients"])}


def forecast_table(panel: pd.DataFrame, scored: np.ndarray) -> dict:
    """Rank IC and mean squared error of every walk-forward forecast of the target rank on the test rows, and
    the daily loss differences of the nested pairs (positive: the larger model has the smaller error)."""
    dates, y = _dates(panel), np.where(scored, target_rank(panel), np.nan)
    out, mse = {"scores": {}, "loss_difference": {}}, {}
    for name in [*FORECASTS, *GBM_FORECASTS]:
        v = panel[name].to_numpy(dtype=float)
        if not np.isfinite(v).any():
            continue                                                # a failed fit, recorded under fit_errors
        ranked = (panel.groupby("date")[name].rank(pct=True) - 0.5).to_numpy(dtype=float)
        mse[name] = pd.Series((y - v) ** 2).groupby(dates).mean().dropna()
        out["scores"][name] = {"rank_ic": series_stats(daily_statistic(dates, ranked, y, "corr")),
                               "mse": float(np.nanmean((y - v) ** 2))}
    for small, large in LOSS_PAIRS:
        if small not in mse or large not in mse:
            continue
        diff = (mse[small] - mse[large]).dropna()
        base = float(mse[small].mean())
        out["loss_difference"][f"{small}_minus_{large}"] = {
            "days": int(len(diff)), "mean": float(diff.mean()), "nw_t": newey_west_t(diff, NW_LAG),
            "relative": float(diff.mean() / base) if base > 0 else None}
    return out


# ---------------------------------------------------------------- descriptive panels
def _both_forms(dates: np.ndarray, score: np.ndarray, resid: np.ndarray) -> dict:
    return {"daily_correlation": series_stats(daily_statistic(dates, score, resid, "corr")),
            "daily_covariance": series_stats(daily_statistic(dates, score, resid, "cov"))}


def variants(panel: pd.DataFrame, X: np.ndarray) -> dict:
    """The daily statistics with another target and the registered features and controls (all descriptive).
    ``X`` are the feature residuals of the gate score."""
    feats, controls, flexible = PARTIAL_SCORES[GATE_SCORE]
    dates, out = _dates(panel), {}
    for col, horizon in OTHER_TARGETS.items():
        def _one(col=col, horizon=horizon):
            score, e, _, _ = partial_score(panel, feats, controls, flexible, target=target_rank(panel, col), X=X, horizon=horizon)
            return _both_forms(dates, score, e)
        out[col] = _guard(_one)
    return out


def masked_gate(panel: pd.DataFrame, X: np.ndarray, resid: np.ndarray, drop: np.ndarray) -> dict:
    """The gate fit and statistic with the target residual of the rows in ``drop`` set to missing: they enter
    neither the walk-forward fit nor the daily statistic."""
    dates, kept = _dates(panel), np.where(drop, np.nan, resid)
    score, _ = walk_forward(X, kept[:, None], dates)
    return {"rows_dropped": int((drop & np.isfinite(resid)).sum()), **_both_forms(dates, score[:, 0], kept)}


def control_removal(panel: pd.DataFrame, X: np.ndarray, resid: np.ndarray, scored: np.ndarray) -> dict:
    """Share of the rank variance of every gate feature and of the target that is left on the test days after
    the within-day step alone and after both steps."""
    feats, controls, _ = PARTIAL_SCORES[GATE_SCORE]
    ranks, y = feature_ranks(panel, feats), target_rank(panel)
    linear = feature_residuals(panel, feats, controls, False)
    e_linear = target_residual(panel, y, controls, False)[:, 0]

    def share(part, whole):
        ok = scored & np.isfinite(part) & np.isfinite(whole)
        total = float(((whole[ok] - whole[ok].mean()) ** 2).sum()) if ok.any() else 0.0
        return float((part[ok] ** 2).sum() / total) if total > 0 else None

    return {"features": {f: {"within_day_step_alone": share(linear[:, j], ranks[:, j]), "both_steps": share(X[:, j], ranks[:, j])}
                         for j, f in enumerate(feats)},
            "target": {"within_day_step_alone": share(e_linear, y), "both_steps": share(resid, y)}}


def _placebo_t(dates: np.ndarray, X: np.ndarray, resid: np.ndarray) -> float:
    score, _ = walk_forward(X, resid[:, None], dates)
    t = gate_statistics(dates, score[:, 0], resid)[0]["reader_partial"]["nw_t"]
    return np.nan if t is None else t


def permutation_placebo(dates: np.ndarray, X: np.ndarray, resid: np.ndarray, observed_t, draws: int, seed: int = PLACEBO_SEED) -> dict:
    """The gate statistic after the feature rows are permuted across the assets of every day (the link between
    features and target is broken, the persistence of the features within an asset as well)."""
    rng = np.random.default_rng(seed)
    days, idx = _day_index(dates)
    by_day = _rows_by_day(idx, len(days))
    ts = []
    for _ in range(draws):
        shuffled = X.copy()
        for rows in by_day:
            shuffled[rows] = X[rng.permutation(rows)]
        ts.append(_placebo_t(dates, shuffled, resid))
    ts = np.asarray(ts, dtype=float)
    ts = ts[np.isfinite(ts)]
    if not len(ts):
        return {"draws": 0, "t_observed": observed_t, "share_ge_observed": None, "t_mean": None, "t_sd": None, "t_q975": None}
    share = float((ts >= observed_t).mean()) if _finite(observed_t) else None
    return {"draws": int(len(ts)), "t_observed": observed_t, "share_ge_observed": share, "t_mean": float(ts.mean()),
            "t_sd": float(ts.std()), "t_q975": float(np.quantile(ts, 0.975))}


def shift_placebo(panel: pd.DataFrame, X: np.ndarray, resid: np.ndarray) -> dict:
    """The gate statistic with every asset's feature residuals taken from ``k`` days later or earlier (the asset
    is kept, the timing is broken). A row whose shifted day is outside the asset's panel days is neutral."""
    dates = _dates(panel)
    cols = [f"x{j}" for j in range(X.shape[1])]
    frame = pd.DataFrame(X, columns=cols).assign(date=_utc(panel["date"].to_numpy()).to_numpy(), symbol=panel["symbol"].to_numpy())
    out = {}
    for k in SHIFT_DAYS:
        moved = frame.assign(date=frame["date"] - k * DAY)
        shifted = frame[["date", "symbol"]].merge(moved, on=["date", "symbol"], how="left")[cols].fillna(0.0).to_numpy()
        score, _ = walk_forward(shifted, resid[:, None], dates)
        out[str(k)] = gate_statistics(dates, score[:, 0], resid)[0]["reader_partial"]
    return out


def residual_autocorrelation(panel: pd.DataFrame, resid: np.ndarray) -> dict:
    """Correlation of an asset's target residual with its own residual k days earlier, pooled over the panel."""
    frame = pd.DataFrame({"date": _utc(panel["date"].to_numpy()).to_numpy(), "symbol": panel["symbol"].to_numpy(), "e": resid}).dropna()
    out = {}
    for lag in AUTOCORR_LAGS:
        earlier = frame.assign(date=frame["date"] + lag * DAY).rename(columns={"e": "e_lag"})
        pair = frame.merge(earlier, on=["date", "symbol"], how="inner")
        out[str(lag)] = {"pairs": int(len(pair)), "corr": float(pair["e"].corr(pair["e_lag"])) if len(pair) > 2 else None}
    return out


def feature_coverage(panel: pd.DataFrame, rows: np.ndarray) -> dict:
    part = panel[rows]
    out = {"rows": int(len(part)), "days": int(part["date"].nunique()), "features": {}}
    for c in [*HIST, *TEXT_COLUMNS]:
        nonzero = part[c].fillna(0.0) != 0
        out["features"][c] = {"missing": float(part[c].isna().mean()), "nonzero": float(nonzero.mean()),
                              "mean_assets_nonzero_per_day": float(nonzero.groupby(part["date"]).sum().mean())}
    return out


def target_coverage(panel: pd.DataFrame, rows: np.ndarray) -> dict:
    part = panel[rows]
    return {"rows": int(len(part)), "missing": {c: int(part[c].isna().sum()) for c in TARGET_COLUMNS},
            "zero_return": int((part[TARGET] == 0).sum())}


def score_book(panel: pd.DataFrame, score: np.ndarray) -> dict:
    """A dollar-neutral book that holds every asset in proportion to its demeaned score for one day (gross
    exposure 2), booked with the simple return of the bar after the decision. Turnover is the sum of absolute
    weight changes from the previous day's book (the first day builds the book); the cost is ``COST_PER_SIDE``
    per unit of turnover."""
    frame = pd.DataFrame({"date": _utc(panel["date"].to_numpy()).to_numpy(), "symbol": panel["symbol"].to_numpy(),
                          "s": score, "r": panel[TARGET].to_numpy(dtype=float)}).dropna()
    centred = frame["s"] - frame.groupby("date")["s"].transform("mean")
    gross = centred.abs().groupby(frame["date"]).transform("sum")
    frame = frame.assign(w=(2.0 * centred / gross).where(gross > 0)).dropna()
    weights = frame.pivot(index="date", columns="symbol", values="w").fillna(0.0)
    if len(weights) < 3:
        return {"days": int(len(weights))}
    turnover = weights.diff().abs().sum(axis=1)
    turnover.iloc[0] = weights.iloc[0].abs().sum()
    ret = (frame["w"] * frame["r"]).groupby(frame["date"]).sum().reindex(weights.index)
    net = ret - COST_PER_SIDE * turnover

    def stats(x):
        sd = float(x.std())
        return {"mean_bp": float(x.mean() * 1e4), "nw_t": newey_west_t(x, NW_LAG),
                "sharpe_annual": float(x.mean() / sd * np.sqrt(YEAR_DAYS)) if sd > 0 else None}

    return {"days": int(len(weights)), "gross": stats(ret), "net": stats(net), "mean_turnover": float(turnover.mean()),
            "cost_per_side": COST_PER_SIDE}


EVENT_GROUPS = {
    "tone_positive": lambda p: p["tone_1d"] > 0,
    "tone_negative": lambda p: p["tone_1d"] < 0,
    "event_zero_tone": lambda p: (p["evt_1d"] > 0) & (p["tone_1d"] == 0),
    "unfavourable_event": lambda p: p["unfav_1d"] > 0,
    "record_no_event": lambda p: (p["n_subject_1d"] > 0) & (p["evt_1d"] == 0),
    "no_record": lambda p: p["n_subject_1d"] == 0,
}


def event_study(panel: pd.DataFrame, rows: np.ndarray) -> dict:
    """Mean return of the bar after the decision minus the equal-weight mean of the day's panel rows, in basis
    points, for asset-days grouped by their records of the last day. ``mean_bp`` pools the rows; ``day_mean_bp``
    and its t take the mean per day first (Newey-West over the days that have a row of the group)."""
    part = panel[rows & panel[TARGET].notna().to_numpy()]
    abnormal = (part[TARGET] - part.groupby("date")[TARGET].transform("mean")) * 1e4
    out = {}
    for name, rule in EVENT_GROUPS.items():
        sel = rule(part)
        daily = abnormal[sel].groupby(part.loc[sel, "date"]).mean()
        out[name] = {"rows": int(sel.sum()), "days": int(len(daily)), "mean_bp": float(abnormal[sel].mean()) if sel.any() else None,
                     "day_mean_bp": float(daily.mean()) if len(daily) else None,
                     "nw_t": newey_west_t(daily, NW_LAG) if len(daily) >= 3 else None}
    return out


# ---------------------------------------------------------------- evaluation and verdict
def evaluate(panel: pd.DataFrame, parts: dict, fit_errors: dict, n_placebo: int = PLACEBO_DRAWS) -> dict:
    """evaluation.json: the gate statistics on the test days and the descriptive panels of Charter 4 §5."""
    dates, y = _dates(panel), target_rank(panel)
    score, gate = panel[GATE_SCORE].to_numpy(dtype=float), parts[GATE_SCORE]
    gates, daily = gate_statistics(dates, score, gate["resid"])
    scored = np.isfinite(score)
    everything = np.ones(len(panel), dtype=bool)
    days = sorted(panel.loc[scored, "date"].unique())
    observed_t = gates["reader_partial"]["nw_t"]
    other = "cov" if GATE_FORM == "corr" else "corr"
    large, gap = panel["base"].isin(LARGE).to_numpy(), (panel["gap_7d"] > 0).to_numpy()
    return {"gates": gates,
            "gate_daily_statistic": [{"date": d, "value": v} for d, v in daily.items()],
            "gate_other_form": _guard(lambda: {"form": other, **series_stats(daily_statistic(dates, score, gate["resid"], other))}),
            "days": {"panel": int(panel["date"].nunique()), "test": len(days), "first_test": days[0] if days else None,
                     "last_test": days[-1] if days else None},
            "fit_errors": fit_errors,
            "partial_scores": {name: _guard(lambda name=name: partial_summary(dates, panel[name].to_numpy(dtype=float), parts[name], y))
                               for name in PARTIAL_SCORES if name in parts},
            "forecasts": _guard(forecast_table, panel, scored),
            "variants": variants(panel, gate["X"]),
            "control_removal": _guard(control_removal, panel, gate["X"], gate["resid"], scored),
            "placebo_permutation": _guard(permutation_placebo, dates, gate["X"], gate["resid"], observed_t, n_placebo),
            "placebo_shift": _guard(shift_placebo, panel, gate["X"], gate["resid"]),
            "residual_autocorrelation": _guard(residual_autocorrelation, panel, gate["resid"]),
            "excluding_large": _guard(masked_gate, panel, gate["X"], gate["resid"], large),
            "excluding_gap_rows": _guard(masked_gate, panel, gate["X"], gate["resid"], gap),
            "score_book": _guard(score_book, panel, score),
            "event_study": _guard(event_study, panel, scored),
            "feature_coverage": {"all_days": _guard(feature_coverage, panel, everything), "test_days": _guard(feature_coverage, panel, scored)},
            "target_coverage": {"all_days": _guard(target_coverage, panel, everything), "test_days": _guard(target_coverage, panel, scored)}}


def size_reading(evaluation: dict) -> str:
    """Reading rule of a PASS (a label, no gate): the net mean daily return of the score book against zero."""
    book = evaluation.get("score_book")
    net = book.get("net", {}).get("mean_bp") if isinstance(book, dict) else None
    if not _finite(net):
        return "not available"
    return "above cost" if net > 0 else "below cost"


def build_verdict(evaluation: dict, reader: dict) -> dict:
    """The registered gates applied by code. A statistic that cannot be computed fails its gate."""
    g = evaluation["gates"]
    stat, years = g["reader_partial"], g["reader_partial_by_year"]
    t, mean = stat["nw_t"], stat["mean"]
    means = {str(y): years.get(str(y), {}).get("mean") for y in GATE_YEARS}
    gates = {
        "reader_partial": {"value": {"nw_t": t, "mean": mean, "days": stat["days"], "form": stat.get("form")},
                           "rule": f"Newey-West t >= {GATE_T} and mean daily statistic > 0",
                           "pass": bool(_finite(t) and _finite(mean) and t >= GATE_T and mean > 0)},
        "reader_partial_sign_by_year": {"value": means, "days": {y: years.get(y, {}).get("days") for y in means},
                                        "rule": "mean daily statistic > 0 in " + " and in ".join(means),
                                        "pass": bool(all(_finite(v) and v > 0 for v in means.values()))},
    }
    failed = [k for k, v in gates.items() if not v["pass"]]
    errors = _errors({k: v for k, v in evaluation.items() if k != "gates"}, "evaluation") + _errors(reader, "reader")
    return {"charter": "llm-v2 Charter 4 (fresher information: daily decision, next-day return)",
            "test_days": evaluation["days"]["test"], "gates": gates, "failed_gates": failed,
            "size_reading": None if failed else size_reading(evaluation), "descriptive_errors": errors,
            "verdict": "FAIL" if failed else "PASS"}


def finalize(universe: pd.DataFrame, feats: pd.DataFrame, hist: pd.DataFrame, fwd: pd.DataFrame, records: pd.DataFrame,
             extraction: dict | None = None, timing: dict | None = None, n_placebo: int = PLACEBO_DRAWS) -> dict:
    """Everything after the feature build: panel, fitted scores, gates, descriptive panels and the verdict,
    already in JSON-safe form (file name -> object). ``forecasts.json`` holds the rows of the test days."""
    panel = assemble_panel(universe, feats, hist, fwd)
    panel, parts, fit_errors = fit_scores(panel)
    evaluation = evaluate(panel, parts, fit_errors, n_placebo=n_placebo)
    reader = {"quality": _guard(lambda: consensus.quality(consensus.record_rows(records))), "extraction": extraction,
              "timing": timing}
    verdict = build_verdict(evaluation, reader)
    test_days = panel.loc[panel[GATE_SCORE].notna(), "date"].unique()
    shown = panel.loc[panel["date"].isin(test_days), OUTPUT_COLUMNS]
    rows = shown.astype(object).where(shown.notna(), None).to_numpy().tolist()          # one list per row, column order below
    return {"forecasts.json": json_safe({"columns": OUTPUT_COLUMNS, "rows": rows}), "evaluation.json": json_safe(evaluation),
            "reader.json": json_safe(reader), "verdict.json": json_safe(verdict)}
