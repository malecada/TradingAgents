"""Evaluation of the target change (Charter 3): next-week realised volatility from the reader records.

No model call and no cache. The record table of Charter 2 is an input and everything here is arithmetic on
registered inputs. Three blocks of decision-time regressors are built per universe row: price history from the
daily bars up to the decision (HIST), attention counts (block A) and unsigned sums of the reader records
(block V). The target is the realised variance of the seven daily bars after the decision. Every variable is
ranked within the week. The registered question is whether block V carries information beyond HIST and block A.
The controls are removed from both sides in two steps. First a flexible fit on earlier weeks only is subtracted:
boosted trees of the control ranks for every block-V rank, a quadratic surface of the control ranks for the
target rank. Then target and block V are residualised within every week on the control ranks. A ridge model is
fitted walk-forward on the residuals, and the two gates are applied by code to the weekly correlation of its
score with the target residual. Every statistic outside the two gates is descriptive and guarded: an error
there is recorded in the verdict and cannot void it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg

from tradingagents.agents_v2.charter1b import PLACEBO_DRAWS, _errors, _finite, _guard, _utc, json_safe
from tradingagents.agents_v2.evaluate import newey_west_t
from tradingagents.dossier.quant_forecast import BURN_IN_WEEKS, HORIZON_DAYS
from tradingagents.reader import charter2, consensus, features, model

# registered thresholds (Charter 3 §5)
GATE_T = 2.0                # Newey-West t of the mean weekly partial correlation of the reader score, >=
GATE_YEARS = (2023, 2024)   # calendar years (of the Friday) in which the mean weekly partial correlation must be positive
SIZE_VISIBLE = 0.07         # mean weekly partial correlation from which a PASS is read as visible (reading rule, no gate)

MIN_WEEK_ROWS = 30          # rows a week needs in a within-week regression
# flexible removal of the controls before the within-week step (Charter 3 §3.2); fitted on earlier weeks only
CLEAN_FIRST = 26            # weeks at the start of the panel that are fitted on themselves (training-only weeks)
CLEAN_EVERY = 13            # weeks between two refits of the boosted trees
CLEAN_PARAMS = {**model.GBM_PARAMS, "learning_rate": 0.05, "num_leaves": 8, "max_depth": 3, "min_data_in_leaf": 50}
CLEAN_ROUNDS = 300
CLEAN_ALPHA = 1.0           # ridge penalty of the quadratic surface fitted to the target rank (intercept free)
MIN_BARS_SHORT, MIN_BARS_LONG = 4, 10      # bars a 7-day window and a 30- or 90-day window need
FORWARD = pd.Timedelta(days=HORIZON_DAYS)
DAY = pd.Timedelta(days=1)
GK_CLOSE = 2.0 * np.log(2.0) - 1.0
LOG_FLOOR = 1e-10           # daily variance floor of the descriptive log target
PLACEBO_SEED = 20261113
SHIFT_WEEKS = (-52, -26, -13, 13, 26, 52)
AUTOCORR_LAGS = (1, 2, 4, 8)
LONG_LAG = 12

BAR_COLUMNS = ["open", "high", "low", "close", "quote_volume"]
HIST_BARS = ["rv_1d", "rv_7d", "rv_30d", "rv_90d", "rv_max_7d", "absret_7d", "ret_7d", "vsurge_7d"]
CARD_COLUMNS = ["vol_ewma20", "dvol_30d", "age_weeks", "funding_3d"]
HIST_CARD = ["vol_ewma20", "dvol_30d", "age_weeks", "abs_funding_3d"]
HIST = HIST_BARS + HIST_CARD
BLOCK_A = list(features.BLOCK_A)
BLOCK_V = ["evt_7d", "evt_30d", "unfav_7d", "sched_30d", "rumour_30d", "split_7d"]
COUNTS = ["n_subject_7d", "n_subject_30d"]
TEXT_COLUMNS = [*BLOCK_A, *BLOCK_V, *COUNTS]
TARGET = "fwd_rv"
TAILS = ["fwd_absret", "fwd_drawdown", "fwd_maxday"]
TARGET_COLUMNS = [TARGET, *TAILS, "fwd_bars"]

GATE_SCORE, GATE_RESIDUAL = "s_reader", "e_reader"
# partial scores: name -> (features, controls, controls that also enter squared in the within-week step,
# flexible removal of the controls before the within-week step)
PARTIAL_SCORES = {
    "s_reader": (BLOCK_V, HIST + BLOCK_A, (), True),
    "s_reader_lin": (BLOCK_V, HIST + BLOCK_A, (), False),
    "s_reader_sq": (BLOCK_V, HIST + BLOCK_A, tuple(HIST_BARS), False),
    "s_reader_hist": (BLOCK_V, HIST, (), True),
    "s_text": (BLOCK_A + BLOCK_V, HIST, (), True),
    "s_attn": (BLOCK_A, HIST, (), True),
}
FORECASTS = {"v_hist": HIST, "v_hist_attn": HIST + BLOCK_A, "v_full": HIST + BLOCK_A + BLOCK_V}
GBM_FORECASTS = {"g_hist_attn": HIST + BLOCK_A, "g_full": HIST + BLOCK_A + BLOCK_V}
LOSS_PAIRS = [("v_hist_attn", "v_full"), ("v_hist", "v_hist_attn"), ("v_hist", "v_full"), ("g_hist_attn", "g_full")]
SCORES = [*PARTIAL_SCORES, *FORECASTS, *GBM_FORECASTS]
PANEL_COLUMNS = ["date", "symbol", "base", *HIST, *TEXT_COLUMNS, *TARGET_COLUMNS]
OUTPUT_COLUMNS = [*PANEL_COLUMNS, GATE_RESIDUAL, *SCORES]


# ---------------------------------------------------------------- daily bars
def load_bars(klines_dir: Path, symbol: str) -> pd.DataFrame:
    """Daily bars of one contract, UTC index in time order."""
    bars = pd.read_parquet(Path(klines_dir) / f"{symbol}.parquet")[BAR_COLUMNS].astype(float)
    bars.index = pd.to_datetime(bars.index, utc=True)
    bars = bars.sort_index()
    if bars.index.duplicated().any():
        raise ValueError(f"{symbol}: duplicate bars")
    return bars


def gk_variance(bars: pd.DataFrame) -> pd.Series:
    """Garman-Klass variance of every daily bar, 0.5 ln(H/L)^2 - (2 ln 2 - 1) ln(C/O)^2. A bar without four
    positive prices is missing."""
    ok = (bars[["open", "high", "low", "close"]] > 0).all(axis=1)
    safe = bars.where(ok)
    value = 0.5 * np.log(safe["high"] / safe["low"]) ** 2 - GK_CLOSE * np.log(safe["close"] / safe["open"]) ** 2
    return value.clip(lower=0.0)


def bar_history(bars: pd.DataFrame) -> pd.DataFrame:
    """Per bar, statistics of the bars up to and including it. Time windows are closed on the bar itself, so a
    row never uses a later bar."""
    gk, close, volume = gk_variance(bars), bars["close"].where(bars["close"] > 0), bars["quote_volume"]
    week = gk.rolling("7D", min_periods=MIN_BARS_SHORT)
    out = pd.DataFrame({"rv_1d": gk, "rv_7d": week.mean(), "rv_30d": gk.rolling("30D", min_periods=MIN_BARS_LONG).mean(),
                        "rv_90d": gk.rolling("90D", min_periods=MIN_BARS_LONG).mean(), "rv_max_7d": week.max()})
    out["ret_7d"] = np.log(close.to_numpy() / close.reindex(close.index - 7 * DAY).to_numpy())
    out["absret_7d"] = out["ret_7d"].abs()
    v7 = volume.rolling("7D", min_periods=MIN_BARS_SHORT).mean()
    v30 = volume.rolling("30D", min_periods=MIN_BARS_LONG).mean()
    out["vsurge_7d"] = np.log((v7 / v30).where((v7 > 0) & (v30 > 0)))
    return out[HIST_BARS]


def history_features(klines_dir: Path, keys: pd.DataFrame) -> pd.DataFrame:
    """(date, symbol, bar-history features) for every universe row, from the bars up to the Friday bar, which
    closes at the decision. A row without its Friday bar has every feature missing."""
    parts = []
    for symbol, rows in keys.groupby("symbol", sort=True):
        fridays = pd.DatetimeIndex(_utc(rows["date"].to_numpy()))
        bars = load_bars(klines_dir, symbol)
        hist = bar_history(bars[bars.index <= fridays.max()]).reindex(fridays)
        parts.append(hist.reset_index(drop=True).assign(date=fridays, symbol=symbol))
    return pd.concat(parts, ignore_index=True)[["date", "symbol", *HIST_BARS]]


def forward_targets(klines_dir: Path, keys: pd.DataFrame) -> pd.DataFrame:
    """The outcome join: per universe row the statistics of the daily bars after the decision, Friday + 1 to
    Friday + 7. ``fwd_rv`` is the mean Garman-Klass variance of those bars, ``fwd_maxday`` their largest,
    ``fwd_absret`` the absolute log return from the Friday close to the last of them, ``fwd_drawdown`` the
    largest fall of a daily low below the Friday close (log, sign turned). A row with no usable bar in the
    week is absent; ``fwd_bars`` counts the bars used."""
    rows = []
    for symbol, group in keys.groupby("symbol", sort=True):
        bars = load_bars(klines_dir, symbol)
        gk = gk_variance(bars).dropna()
        close, low = bars["close"].where(bars["close"] > 0), bars["low"].where(bars["low"] > 0)
        for friday in pd.DatetimeIndex(_utc(group["date"].to_numpy())):
            week = gk[(gk.index > friday) & (gk.index <= friday + FORWARD)]
            if not len(week):
                continue
            start = close.get(friday, np.nan)
            last = close.reindex(week.index).dropna()
            lows = low.reindex(week.index).dropna()
            ok = np.isfinite(start) and len(last) and len(lows)
            rows.append((friday, symbol, float(week.mean()), abs(float(np.log(last.iloc[-1] / start))) if ok else np.nan,
                         float(-np.log(lows.min() / start)) if ok else np.nan, float(week.max()), int(len(week))))
    return pd.DataFrame(rows, columns=["date", "symbol", TARGET, *TAILS, "fwd_bars"])


# ---------------------------------------------------------------- text features
def block_v(reading: pd.DataFrame, records: pd.DataFrame) -> pd.DataFrame:
    """Raw block-V features and record counts per (date, base) with any record. Rows, time buckets and the
    removal of near-duplicates are those of block B of Charter 2 (``features.block_b``); nothing is signed."""
    rec = records[["doc_id", "base", "resolution", "relevance", "event_class", "status", "direction", "materiality"]]
    rows = reading.loc[reading["read"], ["friday", "decision", "doc_id", "base", "event_ts", "type"]].merge(
        rec, on=["doc_id", "base"], how="inner", validate="m:1")
    age = rows["decision"] - rows["event_ts"]
    rows = rows.assign(bucket=(age // features.WEEK).astype(int), recent=age < features.WEEK)
    subj = rows[(rows["resolution"] != "unresolved") & (rows["relevance"] == "subject")].copy()
    subj["materiality"] = subj["materiality"].astype(int)
    events, opinions = subj[subj["type"] == "event"], subj[(subj["type"] == "analysis_opinion") & subj["recent"]]
    ev = features._signed(events, ["event_class", "status", "direction", "bucket"], pd.Series(1, index=events.index))
    sides = opinions.groupby(["friday", "base", "direction"], observed=True).size().unstack("direction")
    sides = sides.reindex(columns=["favourable", "unfavourable"]).fillna(0.0)
    parts = [
        features._sum(ev[ev["bucket"] == 0], "materiality", "evt_7d"),
        features._sum(ev[ev["bucket"] >= 1], "materiality", "evt_30d"),
        features._sum(ev[(ev["bucket"] == 0) & (ev["direction"] == "unfavourable")], "materiality", "unfav_7d"),
        features._sum(ev[ev["status"] == "scheduled"], "materiality", "sched_30d"),
        features._sum(ev[ev["status"] == "proposed_or_rumoured"], "materiality", "rumour_30d"),
        sides.min(axis=1).rename("split_7d"),
        subj[subj["recent"]].groupby(["friday", "base"]).size().rename("n_subject_7d"),
        subj.groupby(["friday", "base"]).size().rename("n_subject_30d"),
    ]
    out = pd.concat(parts, axis=1).fillna(0.0).reset_index()
    return out.rename(columns={"friday": "date"})


def text_features(items: pd.DataFrame, sets: pd.DataFrame, records: pd.DataFrame, top: pd.DataFrame) -> pd.DataFrame:
    """One row per universe row (date, symbol, base) with block A, block V and the record counts. Block A and
    the check that the records cover the work list exactly are those of Charter 2; the two columns that both
    charters define must agree."""
    base = charter2.text_features(items, sets, records, top)
    out = base[["date", "symbol", "base", *BLOCK_A]].merge(block_v(sets, records), on=["date", "base"], how="left", validate="m:1")
    cols = [*BLOCK_V, *COUNTS]
    out[cols] = out[cols].fillna(0.0)
    for col in ("unfav_7d", "n_subject_7d", "n_subject_30d"):
        if not np.array_equal(out[col].to_numpy(dtype=float), base[col].to_numpy(dtype=float)):
            raise ValueError(f"{col} differs from the Charter 2 feature of the same name")
    return out


# ---------------------------------------------------------------- panel
def _keyed(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = frame[["date", "symbol", *cols]].copy()
    out["date"] = _utc(out["date"].to_numpy()).to_numpy()
    return out


def assemble_panel(top: pd.DataFrame, feats: pd.DataFrame, hist: pd.DataFrame, fwd: pd.DataFrame) -> pd.DataFrame:
    """Universe rows joined with the text features, the bar history and the forward targets. Every join is
    one-to-one on (date, symbol); every universe row needs its text row and its history row."""
    key = ["date", "symbol"]
    panel = _keyed(top, ["base", *CARD_COLUMNS])
    if panel.duplicated(key).any():
        raise ValueError("universe rows are not unique on (date, symbol)")
    panel["abs_funding_3d"] = panel["funding_3d"].abs()
    for frame, cols, label in ((feats, TEXT_COLUMNS, "text features"), (hist, HIST_BARS, "bar history")):
        panel = panel.merge(_keyed(frame, cols), on=key, how="left", validate="1:1", indicator=True)
        if (panel.pop("_merge") != "both").any():
            raise ValueError(f"universe rows without {label}")
    filled = [c for c in TEXT_COLUMNS if c != "attn_abn"]            # attn_abn alone may be missing (short own history)
    if panel[filled].isna().any().any():
        raise ValueError("text features with missing values")
    panel = panel.merge(_keyed(fwd, TARGET_COLUMNS), on=key, how="left", validate="1:1")
    for col in TARGET_COLUMNS:
        panel[col] = pd.to_numeric(panel[col], errors="coerce")
    return panel.sort_values(key).reset_index(drop=True)[PANEL_COLUMNS]


# ---------------------------------------------------------------- ranks, residuals, walk-forward
def _dates(panel: pd.DataFrame) -> np.ndarray:
    return pd.to_datetime(panel["date"], utc=True).dt.as_unit("ns").astype("int64").to_numpy()


def _stamp(d) -> pd.Timestamp:
    return pd.Timestamp(int(d), tz="UTC")


def feature_ranks(panel: pd.DataFrame, cols) -> np.ndarray:
    """Within-week percentile rank minus 0.5 of every column; a missing value sits at the neutral rank 0."""
    return model.xs_rank(panel, list(cols)).to_numpy(dtype=float)


def target_rank(panel: pd.DataFrame, col: str = TARGET) -> np.ndarray:
    """Within-week percentile rank minus 0.5 over the rows that have the target; missing stays missing."""
    return (panel.groupby("date")[col].rank(pct=True) - 0.5).to_numpy(dtype=float)


def log_target(panel: pd.DataFrame, col: str = TARGET) -> np.ndarray:
    """Within-week standardised log of the target (descriptive variant)."""
    logs = np.log(panel[col].clip(lower=LOG_FLOOR))
    grp = logs.groupby(panel["date"])
    return ((logs - grp.transform("mean")) / grp.transform("std")).to_numpy(dtype=float)


def control_matrix(panel: pd.DataFrame, controls, squares=()) -> np.ndarray:
    ranks = feature_ranks(panel, controls)
    return np.column_stack([ranks, feature_ranks(panel, squares) ** 2]) if len(squares) else ranks


def residuals(values: np.ndarray, controls: np.ndarray, dates: np.ndarray, min_rows: int | None = None) -> np.ndarray:
    """Within-week OLS residual of every column of ``values`` on an intercept and the controls. A column is
    fitted on the rows of the week where it is present; with fewer than ``min_rows`` such rows it is missing
    in that week."""
    min_rows = MIN_WEEK_ROWS if min_rows is None else min_rows
    out = np.full(values.shape, np.nan)
    for d in np.unique(dates):
        idx = np.flatnonzero(dates == d)
        design = np.column_stack([np.ones(len(idx)), controls[idx]])
        for j in range(values.shape[1]):
            y = values[idx, j]
            have = np.isfinite(y)
            if have.sum() < min_rows:
                continue
            beta, *_ = np.linalg.lstsq(design[have], y[have], rcond=None)
            out[idx[have], j] = y[have] - design[have] @ beta
    return out


def walk_forward(X: np.ndarray, y: np.ndarray, dates: np.ndarray, fit=model.fit_ridge, burn_in: int = BURN_IN_WEEKS):
    """(score per row, fit information per test week). A week is forecast from the weeks whose 7-day outcome is
    realised by its Friday; the first ``burn_in`` weeks are training only (score missing)."""
    weeks = np.unique(dates)
    usable = np.isfinite(y) & np.isfinite(X).all(axis=1)
    score, info = np.full(len(y), np.nan), {}
    for d in weeks:
        past = weeks[weeks + model.HORIZON.value <= d]
        if len(past) < burn_in:
            continue
        train = np.isin(dates, past) & usable
        if not train.any():
            continue
        predict, detail = fit(X[train], y[train])
        rows = np.flatnonzero((dates == d) & np.isfinite(X).all(axis=1))
        score[rows] = predict(X[rows])
        info[_stamp(d)] = detail
    return score, info


def _week_index(dates: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(weeks in time order, position of every row's week). Two panel weeks are at least the horizon apart, so
    the outcome of every earlier week is realised by the decision of a week."""
    weeks = np.unique(dates)
    if len(weeks) > 1 and (np.diff(weeks) < model.HORIZON.value).any():
        raise ValueError("panel weeks closer than the forward horizon")
    return weeks, np.searchsorted(weeks, dates)


def past_trees(values: np.ndarray, controls: np.ndarray, dates: np.ndarray) -> np.ndarray:
    """Every column of ``values`` minus what boosted trees predict from the controls. The trees that serve a
    week are fitted on earlier weeks only: they are refitted every ``CLEAN_EVERY`` weeks on all weeks before the
    refit week. The first ``CLEAN_FIRST`` weeks are fitted on themselves; they lie inside the burn-in and are
    never scored."""
    import lightgbm as lgb

    if not (np.isfinite(values).all() and np.isfinite(controls).all()):
        raise ValueError("flexible step: missing value in a rank")
    weeks, widx = _week_index(dates)
    out = np.full(values.shape, np.nan)

    def fit(rows):
        return [lgb.train(dict(CLEAN_PARAMS), lgb.Dataset(controls[rows], label=values[rows, j]), num_boost_round=CLEAN_ROUNDS)
                for j in range(values.shape[1])]

    def subtract(rows, boosters):
        out[rows] = values[rows] - np.column_stack([b.predict(controls[rows]) for b in boosters])

    head = widx < CLEAN_FIRST
    boosters = fit(head)
    subtract(head, boosters)
    for w in range(CLEAN_FIRST, len(weeks)):
        if (w - CLEAN_FIRST) % CLEAN_EVERY == 0:
            boosters = fit(widx < w)
        subtract(widx == w, boosters)
    return out


def quadratic_basis(controls: np.ndarray) -> np.ndarray:
    """Intercept, the control ranks, their centred squares and their pairwise products."""
    k = controls.shape[1]
    cross = [controls[:, i] * controls[:, j] for i in range(k) for j in range(i + 1, k)]
    return np.column_stack([np.ones(len(controls)), controls, controls ** 2 - 1.0 / 12.0, *cross])


def past_surface(values: np.ndarray, controls: np.ndarray, dates: np.ndarray) -> np.ndarray:
    """``values`` (one value per row, missing allowed) minus a quadratic surface of the controls, fitted by ridge
    on the rows of all earlier weeks, whose outcome is realised by the decision. The first ``CLEAN_FIRST`` weeks
    are fitted on themselves; they lie inside the burn-in and are never scored. A missing value stays missing."""
    weeks, widx = _week_index(dates)
    basis = quadratic_basis(controls)
    have = np.isfinite(values)
    rows = [np.flatnonzero((widx == w) & have) for w in range(len(weeks))]
    gram = np.cumsum(np.stack([basis[r].T @ basis[r] for r in rows]), axis=0)        # weeks 0..w
    moment = np.cumsum(np.stack([basis[r].T @ values[r] for r in rows]), axis=0)
    penalty = CLEAN_ALPHA * np.eye(basis.shape[1])
    penalty[0, 0] = 0.0
    out = np.full(len(values), np.nan)

    def solve(last):                                                # fit on the weeks 0..last; no row there: no surface
        if gram[last][0, 0] <= 0:
            return np.zeros(basis.shape[1])
        return linalg.solve(gram[last] + penalty, moment[last], assume_a="pos")   # positive definite once a row is there

    beta = solve(min(CLEAN_FIRST, len(weeks)) - 1)
    for w in range(len(weeks)):
        if w >= CLEAN_FIRST:
            beta = solve(w - 1)
        out[rows[w]] = values[rows[w]] - basis[rows[w]] @ beta
    return out


def feature_residuals(panel: pd.DataFrame, feats, controls, squares=(), flexible: bool = False, cache: dict | None = None) -> np.ndarray:
    """The feature ranks with the controls removed: within every week the OLS residual on the control ranks.
    ``flexible`` subtracts before that what boosted trees fitted on earlier weeks predict from the control
    ranks (``past_trees``). ``cache`` keeps the tree step of a (feature, controls) pair for a later call."""
    dates, ranks = _dates(panel), feature_ranks(panel, feats)
    if flexible:
        cache, key = ({} if cache is None else cache), tuple(controls)
        todo = [f for f in feats if (f, key) not in cache]
        if todo:
            cleaned = past_trees(feature_ranks(panel, todo), feature_ranks(panel, controls), dates)
            cache.update({(f, key): cleaned[:, j] for j, f in enumerate(todo)})
        ranks = np.column_stack([cache[(f, key)] for f in feats])
    return residuals(ranks, control_matrix(panel, controls, squares), dates)


def target_residual(panel: pd.DataFrame, target: np.ndarray, controls, squares=(), flexible: bool = False) -> np.ndarray:
    """The target with the controls removed: within every week the OLS residual on the control ranks.
    ``flexible`` subtracts before that a quadratic surface of the control ranks fitted on earlier weeks
    (``past_surface``)."""
    dates = _dates(panel)
    if flexible:
        target = past_surface(target, feature_ranks(panel, controls), dates)
    return residuals(target[:, None], control_matrix(panel, controls, squares), dates)[:, 0]


def partial_score(panel: pd.DataFrame, feats, controls, squares=(), flexible: bool = False, target: np.ndarray | None = None,
                  X: np.ndarray | None = None, cache: dict | None = None):
    """(walk-forward ridge score, target residual, feature residuals, coefficients per test week) of one
    partial question: do ``feats`` carry information on the target beyond ``controls``? ``X`` hands in feature
    residuals that were already built for the same features and controls."""
    dates = _dates(panel)
    if X is None:
        X = feature_residuals(panel, feats, controls, squares, flexible, cache)
    e = target_residual(panel, target_rank(panel) if target is None else target, controls, squares, flexible)
    score, info = walk_forward(X, e, dates)
    frame = pd.DataFrame.from_dict(info, orient="index", columns=list(feats)).sort_index() if info else pd.DataFrame(columns=list(feats))
    return score, e, X, frame


# ---------------------------------------------------------------- statistics
def weekly_corr(dates: np.ndarray, a: np.ndarray, b: np.ndarray, min_rows: int | None = None) -> pd.Series:
    """Pearson correlation of ``a`` and ``b`` per week over the rows where both exist."""
    min_rows = MIN_WEEK_ROWS if min_rows is None else min_rows
    out = {}
    for d in np.unique(dates):
        idx = np.flatnonzero((dates == d) & np.isfinite(a) & np.isfinite(b))
        if len(idx) < min_rows or np.ptp(a[idx]) == 0 or np.ptp(b[idx]) == 0:
            continue
        out[_stamp(d)] = float(np.corrcoef(a[idx], b[idx])[0, 1])
    return pd.Series(out, dtype=float).sort_index()


def _years(index) -> np.ndarray:
    return np.asarray(pd.DatetimeIndex(index).year) if len(index) else np.array([], dtype=int)


def ic_stats(ic: pd.Series) -> dict:
    ic = ic.dropna()
    if len(ic) < 3:
        return {"weeks": int(len(ic)), "mean": None, "nw_t": None, "hit_rate": None, "by_year": {}}
    by_year = {str(int(y)): float(v.mean()) for y, v in ic.groupby(_years(ic.index))}
    return {"weeks": int(len(ic)), "mean": float(ic.mean()), "nw_t": newey_west_t(ic), "hit_rate": float((ic > 0).mean()),
            "by_year": by_year}


def gate_statistics(dates: np.ndarray, score: np.ndarray, resid: np.ndarray) -> tuple[dict, pd.Series]:
    """The two registered statistics and the weekly partial correlations they are built from."""
    ic = weekly_corr(dates, score, resid)
    years = _years(ic.index)
    by_year = {}
    for y in GATE_YEARS:
        vals = ic.to_numpy()[years == y]
        by_year[str(y)] = {"weeks": int(len(vals)), "mean": float(vals.mean()) if len(vals) else None}
    summary = {"weeks": int(len(ic)), "mean": float(ic.mean()) if len(ic) else None,
               "nw_t": newey_west_t(ic) if len(ic) >= 3 else None}
    return {"reader_partial_ic": summary, "reader_partial_ic_by_year": by_year}, ic


def size_statistics(score: np.ndarray, resid: np.ndarray, target: np.ndarray) -> dict:
    """Share of the residual variance that the score explains out of sample (score used as it is), the share of
    the target variance that the residual holds, and their product."""
    both = np.isfinite(score) & np.isfinite(resid)
    sse, sst = float(((resid[both] - score[both]) ** 2).sum()), float((resid[both] ** 2).sum())
    centred = float(((target[both] - target[both].mean()) ** 2).sum())
    r2 = 1.0 - sse / sst if sst > 0 else None
    share = sst / centred if centred > 0 else None
    return {"rows": int(both.sum()), "oos_r2_residual": r2, "residual_share_of_target": share,
            "oos_r2_target": r2 * share if r2 is not None and share is not None else None}


def residual_autocorrelation(panel: pd.DataFrame, resid: np.ndarray) -> dict:
    """Correlation of an asset's target residual with its own residual k weeks earlier, pooled over the panel."""
    frame = pd.DataFrame({"date": _utc(panel["date"].to_numpy()).to_numpy(), "symbol": panel["symbol"].to_numpy(), "e": resid}).dropna()
    out = {}
    for lag in AUTOCORR_LAGS:
        earlier = frame.assign(date=frame["date"] + lag * features.WEEK).rename(columns={"e": "e_lag"})
        pair = frame.merge(earlier, on=["date", "symbol"], how="inner")
        out[str(lag)] = {"pairs": int(len(pair)), "corr": float(pair["e"].corr(pair["e_lag"])) if len(pair) > 2 else None}
    return out


def univariate(dates: np.ndarray, X: np.ndarray, resid: np.ndarray, names) -> dict:
    """Weekly correlation of every residualised feature with the target residual (no fit)."""
    return {name: ic_stats(weekly_corr(dates, X[:, j], resid)) for j, name in enumerate(names)}


def coefficient_summary(frame: pd.DataFrame) -> dict:
    return {"weeks": int(len(frame)),
            "features": {c: {"mean": float(frame[c].mean()), "sd": float(frame[c].std()),
                             "share_positive": float((frame[c] > 0).mean())} for c in frame.columns},
            "path": {"dates": list(frame.index), **{c: frame[c].to_numpy() for c in frame.columns}}}


def permutation_placebo(dates: np.ndarray, X: np.ndarray, resid: np.ndarray, observed_t, draws: int, seed: int = PLACEBO_SEED) -> dict:
    """The gate statistic after the feature rows are permuted across the assets of every week (the link between
    features and target is broken, the persistence of the features within an asset as well)."""
    rng = np.random.default_rng(seed)
    weeks = [np.flatnonzero(dates == d) for d in np.unique(dates)]
    ts = []
    for _ in range(draws):
        shuffled = X.copy()
        for idx in weeks:
            shuffled[idx] = X[rng.permutation(idx)]
        score, _ = walk_forward(shuffled, resid, dates)
        t = gate_statistics(dates, score, resid)[0]["reader_partial_ic"]["nw_t"]
        ts.append(np.nan if t is None else t)
    ts = np.asarray(ts, dtype=float)
    ts = ts[np.isfinite(ts)]
    if not len(ts):
        return {"draws": 0, "t_observed": observed_t, "share_ge_observed": None, "t_mean": None, "t_sd": None, "t_q975": None}
    share = float((ts >= observed_t).mean()) if _finite(observed_t) else None
    return {"draws": int(len(ts)), "t_observed": observed_t, "share_ge_observed": share, "t_mean": float(ts.mean()),
            "t_sd": float(ts.std()), "t_q975": float(np.quantile(ts, 0.975))}


def shift_placebo(panel: pd.DataFrame, X: np.ndarray, resid: np.ndarray) -> dict:
    """The gate statistic with every asset's feature residuals taken from ``k`` weeks later or earlier (the asset
    is kept, the timing is broken). A row whose shifted week is outside the asset's universe weeks is neutral."""
    dates = _dates(panel)
    cols = [f"x{j}" for j in range(X.shape[1])]
    frame = pd.DataFrame(X, columns=cols).assign(date=_utc(panel["date"].to_numpy()).to_numpy(), symbol=panel["symbol"].to_numpy())
    out = {}
    for k in SHIFT_WEEKS:
        moved = frame.assign(date=frame["date"] - k * features.WEEK)
        shifted = frame[["date", "symbol"]].merge(moved, on=["date", "symbol"], how="left")[cols].fillna(0.0).to_numpy()
        score, _ = walk_forward(shifted, resid, dates)
        out[str(k)] = gate_statistics(dates, score, resid)[0]["reader_partial_ic"]
    return out


def feature_coverage(panel: pd.DataFrame) -> dict:
    per_week = panel.groupby("date")
    out = {"rows": int(len(panel)), "weeks": int(panel["date"].nunique()), "features": {}}
    for c in [*HIST, *TEXT_COLUMNS]:
        out["features"][c] = {"missing": float(panel[c].isna().mean()), "nonzero": float((panel[c].fillna(0.0) != 0).mean()),
                              "mean_assets_nonzero_per_week": float(per_week[c].apply(lambda s: (s.fillna(0.0) != 0).sum()).mean())}
    return out


def target_coverage(panel: pd.DataFrame) -> dict:
    return {"rows": int(len(panel)), "missing": {c: int(panel[c].isna().sum()) for c in [TARGET, *TAILS]},
            "short_weeks": int((panel["fwd_bars"] < HORIZON_DAYS).sum()), "zero_variance": int((panel[TARGET] == 0).sum())}


# ---------------------------------------------------------------- fitted scores
def fit_scores(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict, dict]:
    """(panel with the gate residual and one column per score, working arrays of the partial scores, errors).
    The gate score is fitted unguarded; a failure of any other fit leaves its column missing and is recorded."""
    out, parts, errors, cache = panel.copy(), {}, {}, {}
    dates, y = _dates(panel), target_rank(panel)
    feats, controls, squares, flexible = PARTIAL_SCORES[GATE_SCORE]
    score, e, X, frame = partial_score(panel, feats, controls, squares, flexible)
    out[GATE_RESIDUAL], out[GATE_SCORE] = e, score
    parts[GATE_SCORE] = {"resid": e, "X": X, "coefficients": frame, "features": list(feats)}

    def _partial(name):
        f, c, s, flex = PARTIAL_SCORES[name]
        score, e, X, frame = partial_score(panel, f, c, s, flex, cache=cache)
        parts[name] = {"resid": e, "X": X, "coefficients": frame, "features": list(f)}
        return score

    def _forecast(cols, fit):
        return walk_forward(feature_ranks(panel, cols), y, dates, fit=fit)[0]

    jobs = [(n, lambda n=n: _partial(n)) for n in PARTIAL_SCORES if n != GATE_SCORE]
    jobs += [(n, lambda c=c: _forecast(c, model.fit_ridge)) for n, c in FORECASTS.items()]
    jobs += [(n, lambda c=c: _forecast(c, model.fit_gbm)) for n, c in GBM_FORECASTS.items()]
    for name, job in jobs:
        try:
            out[name] = job()
        except Exception as exc:                                    # noqa: BLE001
            out[name], errors[name] = np.nan, {"error": f"{type(exc).__name__}: {exc}"}
    return out, parts, errors


def partial_summary(dates: np.ndarray, score: np.ndarray, part: dict, target: np.ndarray) -> dict:
    """Weekly partial correlation, size and feature detail of one partial score."""
    ic = weekly_corr(dates, score, part["resid"])
    return {"partial_ic": ic_stats(ic), "nw_t_long_lag": newey_west_t(ic, lag=LONG_LAG) if len(ic) >= 3 else None,
            "size": size_statistics(score, part["resid"], target),
            "univariate": univariate(dates[np.isfinite(score)], part["X"][np.isfinite(score)], part["resid"][np.isfinite(score)],
                                     part["features"]),
            "coefficients": coefficient_summary(part["coefficients"])}


def forecast_table(test: pd.DataFrame) -> dict:
    """Rank IC and mean squared error of every walk-forward forecast of the target rank on the test weeks, and
    the weekly loss differences of the nested pairs (positive: the larger model has the smaller error)."""
    dates, y = _dates(test), target_rank(test)
    out, mse = {"scores": {}, "loss_difference": {}}, {}
    for name in [*FORECASTS, *GBM_FORECASTS]:
        v = test[name].to_numpy(dtype=float)
        if not np.isfinite(v).any():
            continue                                                # a failed fit, recorded under fit_errors
        ranked = (test.groupby("date")[name].rank(pct=True) - 0.5).to_numpy(dtype=float)
        err = pd.Series((y - v) ** 2).groupby(dates).mean()
        mse[name] = err
        out["scores"][name] = {"rank_ic": ic_stats(weekly_corr(dates, ranked, y)), "mse": float(np.nanmean((y - v) ** 2))}
    for small, large in LOSS_PAIRS:
        if small not in mse or large not in mse:
            continue
        diff = (mse[small] - mse[large]).dropna()
        base = float(mse[small].mean())
        out["loss_difference"][f"{small}_minus_{large}"] = {
            "weeks": int(len(diff)), "mean": float(diff.mean()), "nw_t": newey_west_t(diff),
            "relative": float(diff.mean() / base) if base > 0 else None}
    return out


def variants(panel: pd.DataFrame, X: np.ndarray) -> dict:
    """The gate statistics with another target and the registered features and controls (all descriptive).
    ``X`` are the feature residuals of the gate score."""
    feats, controls, squares, flexible = PARTIAL_SCORES[GATE_SCORE]
    dates, out = _dates(panel), {}
    targets = {"log_variance": lambda: log_target(panel), **{c: (lambda c=c: target_rank(panel, c)) for c in TAILS}}
    for name, build in targets.items():
        def _one(build=build):
            score, e, _, _ = partial_score(panel, feats, controls, squares, flexible, target=build(), X=X)
            ic = weekly_corr(dates, score, e)
            return {"partial_ic": ic_stats(ic)}
        out[name] = _guard(_one)
    return out


def control_removal(panel: pd.DataFrame, X: np.ndarray, resid: np.ndarray, scored: np.ndarray) -> dict:
    """Share of the rank variance of every gate feature and of the target that is left on the test weeks after
    the within-week step alone and after both steps."""
    feats, controls, squares, _ = PARTIAL_SCORES[GATE_SCORE]
    dates = _dates(panel)
    ranks, y = feature_ranks(panel, feats), target_rank(panel)
    linear = residuals(ranks, control_matrix(panel, controls, squares), dates)
    e_linear = target_residual(panel, y, controls, squares, False)

    def share(part, whole):
        ok = scored & np.isfinite(part) & np.isfinite(whole)
        total = float(((whole[ok] - whole[ok].mean()) ** 2).sum()) if ok.any() else 0.0
        return float((part[ok] ** 2).sum() / total) if total > 0 else None

    return {"features": {f: {"within_week_step_alone": share(linear[:, j], ranks[:, j]), "both_steps": share(X[:, j], ranks[:, j])}
                         for j, f in enumerate(feats)},
            "target": {"within_week_step_alone": share(e_linear, y), "both_steps": share(resid, y)}}


def evaluate(panel: pd.DataFrame, parts: dict, fit_errors: dict, n_placebo: int = PLACEBO_DRAWS) -> dict:
    """evaluation.json: the gate statistics on the test weeks and the descriptive panels of Charter 3 §5."""
    dates, y = _dates(panel), target_rank(panel)
    score, gate = panel[GATE_SCORE].to_numpy(dtype=float), parts[GATE_SCORE]
    gates, ic = gate_statistics(dates, score, gate["resid"])
    scored = np.isfinite(score)
    test = panel[scored]
    days = sorted(test["date"].unique())
    observed_t = gates["reader_partial_ic"]["nw_t"]
    return {"gates": gates,
            "gate_weekly_partial_ic": [{"date": d, "ic": v} for d, v in ic.items()],
            "weeks": {"panel": int(panel["date"].nunique()), "test": len(days), "first_test": days[0] if days else None,
                      "last_test": days[-1] if days else None},
            "fit_errors": fit_errors,
            "partial_scores": {name: _guard(lambda name=name: partial_summary(dates, panel[name].to_numpy(dtype=float), parts[name], y))
                               for name in PARTIAL_SCORES if name in parts},
            "forecasts": _guard(forecast_table, test),
            "variants": variants(panel, gate["X"]),
            "control_removal": _guard(control_removal, panel, gate["X"], gate["resid"], scored),
            "placebo_permutation": _guard(permutation_placebo, dates, gate["X"], gate["resid"], observed_t, n_placebo),
            "placebo_shift": _guard(shift_placebo, panel, gate["X"], gate["resid"]),
            "residual_autocorrelation": _guard(residual_autocorrelation, panel, gate["resid"]),
            "feature_coverage": {"all_weeks": _guard(feature_coverage, panel), "test_weeks": _guard(feature_coverage, test)},
            "target_coverage": {"all_weeks": _guard(target_coverage, panel), "test_weeks": _guard(target_coverage, test)}}


# ---------------------------------------------------------------- verdict
def build_verdict(evaluation: dict, reader: dict) -> dict:
    """The registered gates applied by code. A statistic that cannot be computed fails its gate."""
    g = evaluation["gates"]
    stat, years = g["reader_partial_ic"], g["reader_partial_ic_by_year"]
    t, mean = stat["nw_t"], stat["mean"]
    means = {str(y): years.get(str(y), {}).get("mean") for y in GATE_YEARS}
    gates = {
        "reader_partial_ic": {"value": {"nw_t": t, "mean": mean, "weeks": stat["weeks"]},
                              "rule": f"Newey-West t >= {GATE_T} and mean weekly partial correlation > 0",
                              "pass": bool(_finite(t) and _finite(mean) and t >= GATE_T and mean > 0)},
        "reader_partial_ic_sign_by_year": {"value": means, "weeks": {y: years.get(y, {}).get("weeks") for y in means},
                                           "rule": "mean weekly partial correlation > 0 in " + " and in ".join(means),
                                           "pass": bool(all(_finite(v) and v > 0 for v in means.values()))},
    }
    failed = [k for k, v in gates.items() if not v["pass"]]
    size = None
    if not failed:
        size = "visible" if mean >= SIZE_VISIBLE else "thin"
    errors = _errors({k: v for k, v in evaluation.items() if k != "gates"}, "evaluation") + _errors(reader, "reader")
    return {"charter": "llm-v2 Charter 3 (target change: next-week volatility)", "test_weeks": evaluation["weeks"]["test"],
            "gates": gates, "failed_gates": failed, "size_reading": size, "descriptive_errors": errors,
            "verdict": "FAIL" if failed else "PASS"}


def finalize(top: pd.DataFrame, feats: pd.DataFrame, hist: pd.DataFrame, fwd: pd.DataFrame, records: pd.DataFrame,
             extraction: dict | None = None, n_placebo: int = PLACEBO_DRAWS) -> dict:
    """Everything after the feature build: panel, fitted scores, gates, descriptive panels and the verdict,
    already in JSON-safe form (file name -> object)."""
    panel = assemble_panel(top, feats, hist, fwd)
    panel, parts, fit_errors = fit_scores(panel)
    evaluation = evaluate(panel, parts, fit_errors, n_placebo=n_placebo)
    reader = {"quality": _guard(lambda: consensus.quality(consensus.record_rows(records))), "extraction": extraction}
    verdict = build_verdict(evaluation, reader)
    shown = panel[OUTPUT_COLUMNS]
    rows = shown.astype(object).where(shown.notna(), None).to_numpy().tolist()          # one list per row, column order below
    return {"forecasts.json": json_safe({"columns": OUTPUT_COLUMNS, "rows": rows}), "evaluation.json": json_safe(evaluation),
            "reader.json": json_safe(reader), "verdict.json": json_safe(verdict)}
