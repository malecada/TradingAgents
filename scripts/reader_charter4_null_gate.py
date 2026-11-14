"""Pass rate and power of the Charter 4 gate on synthetic targets (zero cost, no bar of the panel window at or after a decision).

Kinds of work, none of which joins a text feature with a real outcome:

``panel``    build the decision-time panel of the 54,300 daily universe rows from the stores: card columns, bar
             history up to the bar that closes at the decision, attention counts and reader features. No bar
             that opens at or after a decision is read.
``real``     each draw keeps the regressors of that panel and replaces the next-day return by a synthetic one
             (cells below), optionally with a planted reader effect (power). The feature side of the gate is
             the same in every draw and is built once; the target side, the walk-forward ridge and the daily
             statistics run by the registered functions on a batch of draws at a time. Both forms of the daily
             statistic are recorded per draw: the form of the gate is chosen from these draws before any outcome
             is opened.
``history``  on bars dated before 2022-01-01 only (before the panel window, no card and no text): daily top-50
             by 30-day volume, the next-day return rank and the bar-history ranks as registered. How persistent
             the target residual is within an asset, how curved its relation to the history is, and the
             one-day reversal.
``shapes``   the same measures on the synthetic targets of the ``real`` kind.
``summary``  pass rates per cell and form.

Cells of the synthetic return (parts in units of the asset's own daily volatility):
  noise      independent standard normal returns on one scale
  factor     market return times the real ``beta_60d``, plus own volatility (root of the real ``rv_30d``) times
             noise, minus ``REVERSAL`` times the standardised real ``ret_1d``
  drift      factor plus a per-asset AR(1) drift that no regressor sees (daily persistence ``DRIFT_RHO``)
  curved     factor plus a curved function of the history ranks
  attention  factor plus an unsigned drift after news and posts (a function of the attention counts only)
  stress     drift with ``STRESS_MARKET`` times the market volatility and ``STRESS_DRIFT`` times the unseen drift:
             more of the return explained by the bar history and a more persistent residual than the bars
             before 2022 show (``history``)
Planted effects (power): ``fresh`` adds ``kappa`` times the sign of ``tone_1d``; ``week`` adds ``kappa`` times the
sign of ``tone_1d + tone_prev6``.

    python scripts/reader_charter4_null_gate.py panel /tmp/c4/panel.parquet
    python scripts/reader_charter4_null_gate.py real /tmp/c4/panel.parquet 0 400 --cell drift --features /tmp/c4/x.npy
    python scripts/reader_charter4_null_gate.py real /tmp/c4/panel.parquet 0 200 --cell factor --kappa 0.1
    python scripts/reader_charter4_null_gate.py history
    python scripts/reader_charter4_null_gate.py shapes /tmp/c4/panel.parquet
    python scripts/reader_charter4_null_gate.py summary research/multiagent-v2/charter4_design/null_gate.jsonl
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from tradingagents.reader import charter2 as c2, charter3 as c3, charter4 as c4  # noqa: E402

KLINES = "data/xsect/klines"
PANEL_BEGINS = pd.Timestamp("2022-01-01", tz="UTC")                 # no bar from here on in the ``history`` mode
HISTORY_DAYS = ("2021-01-02", "2021-12-31")                         # decision days; the last outcome bar closes at 2022-01-01
STORE_COLUMNS = [c for c in c4.PANEL_COLUMNS if c not in c4.TARGET_COLUMNS]
FORMS = ("corr", "cov")
BATCH = 50
MARKET_VOL = 0.03                                                   # daily volatility of the synthetic market return
REVERSAL = 0.05
DRIFT, DRIFT_RHO = 0.10, 0.95
CURVE = 0.30
ATTENTION = {"news": 0.10, "news_log": 0.05, "posts": 0.05}
STRESS_MARKET, STRESS_DRIFT = 3.0, 2.0
CELLS = ("noise", "factor", "drift", "curved", "attention", "stress")
PLANTS = ("fresh", "week")
CURVE_BLOCKS = 4
SHAPE_SEEDS = 3


# ---------------------------------------------------------------- decision-time panel of the stores
def decision_panel(root: Path = ROOT) -> pd.DataFrame:
    """Card columns, bar history, attention counts and reader features of every daily universe row.
    Decision-time data only: ``history_features`` reads no bar that opens at or after the decision."""
    from reader_charter4_register import INPUTS

    items, docs, cards, records = (pd.read_parquet(root / INPUTS[name]) for name in ("items", "docs", "cards", "records"))
    universe = c4.daily_universe(c2.universe(cards))
    feats = c4.text_features(items, docs, records, universe)
    hist = c4.history_features(root / KLINES, universe[["date", "symbol"]].reset_index(drop=True))
    empty = pd.DataFrame({"date": pd.Series(dtype="datetime64[ns, UTC]"), "symbol": pd.Series(dtype=object),
                          **{c: pd.Series(dtype=float) for c in c4.TARGET_COLUMNS}})
    return c4.assemble_panel(universe, feats, hist, empty)[STORE_COLUMNS]


# ---------------------------------------------------------------- the registered gate on arrays
def gate_row(dates: np.ndarray, score: np.ndarray, resid: np.ndarray) -> dict:
    """One column through the registered gate code (the registered form of the daily statistic)."""
    gates, daily = c4.gate_statistics(dates, score, resid)
    verdict = c4.build_verdict({"gates": gates, "days": {"test": int(len(daily))}}, {})
    stat, years = gates["reader_partial"], gates["reader_partial_by_year"]
    return {"t": stat["nw_t"], "mean": stat["mean"], "days": stat["days"], "y2023": years["2023"]["mean"],
            "y2024": years["2024"]["mean"], "verdict": verdict["verdict"]}


def form_rows(days: np.ndarray, series: np.ndarray) -> list[dict]:
    """The gate statistics of every column of a daily series (days x columns), by the rule of the charter."""
    years = c3._years(pd.DatetimeIndex([c4._stamp(d) for d in days]))
    t = c4.nw_t(series)
    out = []
    for j in range(series.shape[1]):
        col = series[:, j]
        have = np.isfinite(col)
        mean = float(col[have].mean()) if have.any() else None
        by_year = [float(col[have & (years == y)].mean()) if (have & (years == y)).any() else None for y in c4.GATE_YEARS]
        ok = bool(mean is not None and np.isfinite(t[j]) and t[j] >= c4.GATE_T and mean > 0 and all(v is not None and v > 0 for v in by_year))
        out.append({"t": float(t[j]) if np.isfinite(t[j]) else None, "mean": mean, "days": int(have.sum()),
                    "y2023": by_year[0], "y2024": by_year[1], "verdict": "PASS" if ok else "FAIL"})
    return out


# ---------------------------------------------------------------- synthetic returns on the real regressors
class Fixed:
    """The part of a draw that does not change: the control ranks, the feature residuals of the gate score and
    the real decision-time regressors that shape the synthetic return."""

    def __init__(self, stored: pd.DataFrame, features: Path | None = None, gate: bool = True):
        """``features`` names a file that keeps the feature residuals between processes; ``gate`` false skips
        them (synthetic targets only)."""
        frame = stored.sort_values(["date", "symbol"]).reset_index(drop=True)
        feats, self.names, self.flexible = c4.PARTIAL_SCORES[c4.GATE_SCORE]
        self.frame, self.dates = frame, c4._dates(frame)
        self.controls = c4.feature_ranks(frame, self.names)
        self.X = None
        if gate and features is not None and Path(features).exists():
            self.X = np.load(features)
        elif gate:
            self.X = c4.feature_residuals(frame, feats, self.names, self.flexible)
            if features is not None:
                np.save(features, self.X)
        if gate and self.X.shape != (len(frame), len(feats)):
            raise SystemExit("the stored feature residuals do not fit the panel")
        self.days, self.day_index = c4._day_index(self.dates)
        self.symbols, self.symbol_index = np.unique(frame["symbol"].to_numpy(), return_inverse=True)
        by_day = frame.groupby("date")
        fill = lambda col: frame[col].fillna(by_day[col].transform("median")).to_numpy(dtype=float)       # noqa: E731
        self.sigma, self.beta = np.sqrt(fill("rv_30d")), fill("beta_60d")
        z = (frame["ret_1d"] - by_day["ret_1d"].transform("mean")) / by_day["ret_1d"].transform("std")
        self.last_return = z.fillna(0.0).clip(-3.0, 3.0).to_numpy()
        r = dict(zip(c4.HIST, c4.feature_ranks(frame, c4.HIST).T))
        curve = 4.0 * r["rv_1d"] ** 2 + 3.0 * r["ret_1d"] * r["vsurge_1d"] + 4.0 * np.maximum(r["ret_7d"] - 0.3, 0.0)
        self.curve = curve - curve.mean()
        news, posts = frame["news_1d"].to_numpy(dtype=float), frame["posts_1d"].to_numpy(dtype=float)
        self.attention = ATTENTION["news"] * (news > 0) + ATTENTION["news_log"] * np.log1p(news) + ATTENTION["posts"] * (posts > 0)
        tone, prev = frame["tone_1d"].to_numpy(dtype=float), frame["tone_prev6"].to_numpy(dtype=float)
        self.plant = {"fresh": np.sign(tone), "week": np.sign(tone + prev)}
        self.checked = False

    def returns(self, seed: int, cell: str, kappa: float = 0.0, plant: str = "fresh") -> np.ndarray:
        """One synthetic next-day return per panel row."""
        if cell not in CELLS:
            raise SystemExit(f"unknown cell {cell}")
        rng = np.random.default_rng([seed, 4])
        shape = (len(self.days), len(self.symbols))
        at = (self.day_index, self.symbol_index)
        parts = rng.normal(size=shape)[at]
        if cell == "noise":
            return parts + kappa * self.plant[plant]
        strong = cell == "stress"
        market = (STRESS_MARKET if strong else 1.0) * MARKET_VOL * rng.normal(size=len(self.days))[self.day_index] * self.beta
        parts = parts - REVERSAL * self.last_return
        if cell in ("drift", "stress"):             # unit-variance AR(1) per asset, unseen by every regressor
            eps = rng.normal(size=shape)
            u = eps.copy()
            for d in range(1, shape[0]):
                u[d] = DRIFT_RHO * u[d - 1] + math.sqrt(1 - DRIFT_RHO ** 2) * eps[d]
            parts = parts + (STRESS_DRIFT if strong else 1.0) * DRIFT * u[at]
        elif cell == "curved":
            parts = parts + CURVE * self.curve
        elif cell == "attention":
            parts = parts + self.attention
        return market + self.sigma * (parts + kappa * self.plant[plant])

    def targets(self, seeds, cell: str, kappa: float = 0.0, plant: str = "fresh") -> np.ndarray:
        """Within-day rank minus 0.5 of the synthetic return, one column per seed."""
        returns = np.column_stack([self.returns(seed, cell, kappa, plant) for seed in seeds])
        return (pd.DataFrame(returns).groupby(self.dates).rank(pct=True) - 0.5).to_numpy(dtype=float)

    def _check(self, y: np.ndarray, e: np.ndarray, score: np.ndarray, row: dict) -> None:
        """Once per process: the batch path gives what the registered functions give on one column."""
        if not np.allclose(c4.target_residual(self.frame, y, self.names, self.flexible)[:, 0], e, equal_nan=True, atol=1e-10):
            raise SystemExit("batch target residual differs from the registered function")
        registered = gate_row(self.dates, score, e)
        if registered["verdict"] != row["verdict"] or any(abs(registered[k] - row[k]) > 1e-9 for k in ("t", "mean", "y2023", "y2024")):
            raise SystemExit("batch gate statistics differ from the registered functions")
        self.checked = True

    def draw(self, seeds, cell: str, kappa: float = 0.0, plant: str = "fresh") -> list[dict]:
        seeds = list(seeds)
        Y = self.targets(seeds, cell, kappa, plant)
        E = c4.residuals(c4.past_surface(Y, self.controls, self.dates), self.controls, self.dates)      # as c4.target_residual
        score, _ = c4.walk_forward(self.X, E, self.dates)
        days, corr, cov = c4.daily_stats(self.dates, score, E)
        rows = {"corr": form_rows(days, corr), "cov": form_rows(days, cov)}
        if not self.checked:
            self._check(Y[:, 0], E[:, 0], score[:, 0], rows[c4.GATE_FORM][0])
        extra = {}
        if kappa:
            planted = (self.plant[plant] != 0) & np.isfinite(score[:, 0])
            extra = {"events": int(planted.sum()), "event_bp": float(1e4 * kappa * np.median(self.sigma[planted]))}
        return [{"kind": "real", "cell": cell, "plant": plant if kappa else None, "kappa": kappa, "seed": seed, **extra,
                 "days": rows["corr"][j]["days"],
                 **{f"{k}_{form}": rows[form][j][k] for form in FORMS for k in ("t", "mean", "y2023", "y2024", "verdict")}}
                for j, seed in enumerate(seeds)]


# ---------------------------------------------------------------- persistence, curvature and reversal of a target
def curved_share(controls: np.ndarray, resid: np.ndarray, dates: np.ndarray, blocks: int = CURVE_BLOCKS) -> float:
    """Out-of-sample share of a within-day linear residual that a boosted-tree function of the control ranks
    explains, cross-fitted over blocks of consecutive days. Near zero: no curvature the trees can find."""
    import lightgbm as lgb

    days, have = np.unique(dates), np.isfinite(resid)
    pred = np.full(len(resid), np.nan)
    for block in np.array_split(np.arange(len(days)), blocks):
        inside = np.isin(dates, days[block])
        booster = lgb.train(dict(c4.CLEAN_PARAMS), lgb.Dataset(controls[~inside & have], label=resid[~inside & have]),
                            num_boost_round=c4.CLEAN_ROUNDS)
        pred[inside & have] = booster.predict(controls[inside & have])
    return float(1 - ((resid[have] - pred[have]) ** 2).sum() / (resid[have] ** 2).sum())


def target_shape(frame: pd.DataFrame, y: np.ndarray, cols: list[str]) -> dict:
    """Of a target rank ``y`` against the control columns ``cols``: the share of its variance left by the within-day
    linear regression, the persistence of that residual within an asset, the daily correlation with the rank of
    yesterday's return, and the curved share of the linear residual."""
    dates, ranks = c4._dates(frame), c4.feature_ranks(frame, cols)
    resid = c4.residuals(y[:, None], ranks, dates)[:, 0]
    have = np.isfinite(resid)
    total = ((y[have] - y[have].mean()) ** 2).sum()
    days, corr, _ = c4.daily_stats(dates, ranks[:, cols.index("ret_1d")], y)
    return {"rows_with_target": int(np.isfinite(y).sum()), "residual_share_of_target": float((resid[have] ** 2).sum() / total),
            "residual_autocorrelation": c4.residual_autocorrelation(frame, resid),
            "reversal": {"mean_daily_corr": float(np.nanmean(corr[:, 0])), "nw_t": float(c4.nw_t(corr)[0])},
            "curved_share_of_linear_residual": curved_share(ranks, resid, dates)}


def history_frame(klines_dir: Path, n: int = c2.UNIVERSE_N) -> pd.DataFrame:
    """Daily top-``n`` by 30-day volume on bars before the panel window: the bar history read at the decision
    (the bar of the day before) and the simple return of the bar that opens at the decision."""
    days = pd.date_range(*HISTORY_DAYS, freq="D", tz="UTC")
    market = c4.market_returns(klines_dir, PANEL_BEGINS)
    parts = []
    for path in sorted(Path(klines_dir).glob("*.parquet")):
        bars = c3.load_bars(path.parent, path.stem)
        bars = bars[bars.index < PANEL_BEGINS]
        keep = days[(days - c4.DAY).isin(bars.index)]
        if len(bars) <= c4.MIN_BARS_LONG or not len(keep):
            continue
        close = bars["close"].where(bars["close"] > 0)
        hist = c4.bar_history(bars, market).reindex(keep - c4.DAY).reset_index(drop=True)
        target = close.reindex(keep).to_numpy() / close.reindex(keep - c4.DAY).to_numpy() - 1.0
        parts.append(hist.assign(date=keep, symbol=path.stem, **{c4.TARGET: target}))
    frame = pd.concat(parts, ignore_index=True).dropna(subset=["dvol_30d"])
    frame = frame[frame.groupby("date")["dvol_30d"].rank(ascending=False, method="first") <= n]
    return frame.sort_values(["date", "symbol"]).reset_index(drop=True)


def history_calibration(klines_dir: Path, n: int = c2.UNIVERSE_N) -> dict:
    frame = history_frame(klines_dir, n)
    return {"bars_before": str(PANEL_BEGINS.date()), "days": int(frame["date"].nunique()), "rows": int(len(frame)),
            "assets": int(frame["symbol"].nunique()), **target_shape(frame, c4.target_rank(frame), list(c4.HIST_BARS))}


def shape_cells(stored: pd.DataFrame, seeds: int = SHAPE_SEEDS, cells=CELLS) -> dict:
    """The measures of ``history_calibration`` on the synthetic targets of every cell (mean over ``seeds`` draws),
    against the same bar-history columns."""
    fixed = Fixed(stored, gate=False)
    out = {}
    for cell in cells:
        shapes = [target_shape(fixed.frame, fixed.targets([seed], cell)[:, 0], list(c4.HIST_BARS)) for seed in range(seeds)]
        out[cell] = {"residual_share_of_target": float(np.mean([s["residual_share_of_target"] for s in shapes])),
                     "residual_autocorrelation": {lag: float(np.mean([s["residual_autocorrelation"][lag]["corr"] for s in shapes]))
                                                  for lag in shapes[0]["residual_autocorrelation"]},
                     "reversal_mean_daily_corr": float(np.mean([s["reversal"]["mean_daily_corr"] for s in shapes])),
                     "curved_share_of_linear_residual": float(np.mean([s["curved_share_of_linear_residual"] for s in shapes]))}
    return {"seeds": seeds, "cells": out}


# ---------------------------------------------------------------- summary
def summary(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    frame = pd.DataFrame(rows)
    keys = ["kind", "cell", "plant", "kappa"]
    out = []
    for values, group in frame.groupby(keys, dropna=False):
        if group["seed"].duplicated().any():
            raise SystemExit(f"a seed occurs twice in {values}")
        n = len(group)
        row = {**{k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in zip(keys, values)}, "draws": n,
               "seeds": [int(group["seed"].min()), int(group["seed"].max())]}
        if "event_bp" in group and group["event_bp"].notna().any():
            row.update(events=int(group["events"].iloc[0]), event_bp=float(group["event_bp"].iloc[0]))
        for form in FORMS:
            t, mean = group[f"t_{form}"].to_numpy(dtype=float), group[f"mean_{form}"].to_numpy(dtype=float)
            passed = (group[f"verdict_{form}"] == "PASS").to_numpy()
            rate = float(passed.mean())
            half = 1.96 * math.sqrt(rate * (1 - rate) / n)
            row[form] = {"passes": int(passed.sum()), "pass_rate": rate, "pass_rate_95": [rate - half, rate + half],
                         "first_gate_alone": int(((t >= c4.GATE_T) & (mean > 0)).sum()), "mean_statistic": float(mean.mean()),
                         "t_mean": float(t.mean()), "t_sd": float(t.std(ddof=1)), "t_q975": float(np.quantile(t, 0.975))}
        out.append(row)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    real = sub.add_parser("real")
    real.add_argument("panel")
    real.add_argument("first", type=int)
    real.add_argument("last", type=int)
    real.add_argument("--cell", default="noise", choices=CELLS)
    real.add_argument("--kappa", type=float, default=0.0)
    real.add_argument("--plant", default="fresh", choices=PLANTS)
    real.add_argument("--features", default=None, help="file that keeps the feature residuals of the gate between processes")
    real.add_argument("--batch", type=int, default=BATCH)
    sub.add_parser("panel").add_argument("target")
    sub.add_parser("history")
    shapes = sub.add_parser("shapes")
    shapes.add_argument("panel")
    shapes.add_argument("--cells", nargs="+", default=list(CELLS), choices=CELLS)
    sub.add_parser("summary").add_argument("path")
    args = ap.parse_args(argv)
    if args.mode == "summary":
        print(json.dumps(summary(Path(args.path)), indent=1))
    elif args.mode == "history":
        print(json.dumps(history_calibration(ROOT / KLINES), indent=1))
    elif args.mode == "shapes":
        print(json.dumps(shape_cells(pd.read_parquet(args.panel), cells=args.cells), indent=1))
    elif args.mode == "panel":
        panel = decision_panel()
        panel.to_parquet(args.target, index=False)
        print(json.dumps({"rows": len(panel), "days": int(panel["date"].nunique()), "columns": list(panel.columns)}))
    else:
        fixed = Fixed(pd.read_parquet(args.panel), None if args.features is None else Path(args.features))
        for start in range(args.first, args.last, args.batch):
            for row in fixed.draw(range(start, min(start + args.batch, args.last)), args.cell, args.kappa, args.plant):
                print(json.dumps(row), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
