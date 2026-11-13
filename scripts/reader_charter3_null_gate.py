"""Pass rate and power of the Charter 3 gates on synthetic targets (zero cost, no forward bar of the panel window).

Three kinds of work, none of which joins a text feature with a real outcome:

``synthetic``  each draw is a panel of the registered shape made by the fixture of the tests (no market data).
``panel``      build the decision-time panel of the 7,800 universe rows from the stores: card columns, bar history
               up to the decision, attention counts and reader features. No bar after a decision is read.
``real``       each draw keeps the regressors of that panel and replaces the target by a synthetic one: a function
               of the price history (optionally nonlinear) plus a per-asset AR(1) component that no regressor
               sees, plus an optional planted reader effect (power). The registered gate statistics are computed
               by the registered code.
``history``    persistence and curvature of the target residual on bars dated before 2022-01-01 only (before the
               panel window, no card and no text): weekly top-50 by 30-day volume, target and bar-history ranks
               as registered.
``shapes``     the same curvature measure on the synthetic targets of the ``real`` kind.

``--score`` names the partial score whose design is simulated: the gate score by default, ``s_reader_lin`` for
the first design of the charter (within-week linear removal only).

    python scripts/reader_charter3_null_gate.py synthetic 0 400 --rho 0.3 --score s_reader_lin > draws.jsonl
    python scripts/reader_charter3_null_gate.py panel /tmp/c3/panel.parquet
    python scripts/reader_charter3_null_gate.py real /tmp/c3/panel.parquet 0 400 --rho 0.3 --shape nonlinear --signal 0.1
    python scripts/reader_charter3_null_gate.py history
    python scripts/reader_charter3_null_gate.py shapes /tmp/c3/panel.parquet
    python scripts/reader_charter3_null_gate.py summary research/multiagent-v2/charter3_null_gate.jsonl
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
sys.path.insert(0, str(ROOT / "tests" / "research"))

from tradingagents.reader import charter2 as c2, charter3 as c3, model  # noqa: E402

KLINES = "data/xsect/klines"
PANEL_BEGINS = pd.Timestamp("2022-01-01", tz="UTC")                 # no bar from here on in the ``history`` mode
HISTORY_FRIDAYS = ("2021-01-01", "2021-12-24")                      # the last forward week ends on 2021-12-31
PLANTED = {"evt_7d": 1.0, "unfav_7d": 1.0, "sched_30d": 1.0, "rumour_30d": 1.0}
LINEAR = {"rv_7d": 1.4, "rv_30d": 1.0, "rv_90d": 0.6, "rv_1d": 0.5, "vol_ewma20": 0.4, "absret_7d": 0.3, "vsurge_7d": 0.3}
STORE_COLUMNS = ["date", "symbol", "base", *c3.CARD_COLUMNS, *c3.HIST_BARS, *c3.TEXT_COLUMNS]
CURVE_FITS = {"weak": (model.GBM_PARAMS, model.GBM_ROUNDS), "strong": (c3.CLEAN_PARAMS, c3.CLEAN_ROUNDS)}
SHAPE_SEEDS = 5


# ---------------------------------------------------------------- the registered gate on arrays
def gate_row(dates: np.ndarray, score: np.ndarray, resid: np.ndarray) -> dict:
    gates, ic = c3.gate_statistics(dates, score, resid)
    verdict = c3.build_verdict({"gates": gates, "weeks": {"test": int(len(ic))}}, {})
    stat, years = gates["reader_partial_ic"], gates["reader_partial_ic_by_year"]
    return {"t": stat["nw_t"], "mean": stat["mean"], "weeks": stat["weeks"], "y2023": years["2023"]["mean"],
            "y2024": years["2024"]["mean"], "t_long": c3.newey_west_t(ic, lag=c3.LONG_LAG), "verdict": verdict["verdict"]}


def gate_of_panel(panel: pd.DataFrame, score: str = c3.GATE_SCORE) -> dict:
    """The gate statistics of an assembled panel under the design of one partial score, by the registered code."""
    feats, controls, squares, flexible = c3.PARTIAL_SCORES[score]
    values, resid, _, _ = c3.partial_score(panel, feats, controls, squares, flexible)
    return gate_row(c3._dates(panel), values, resid)


# ---------------------------------------------------------------- synthetic panels
def synthetic_draw(seed: int, rho: float = 0.0, signal: float = 0.0, score: str = c3.GATE_SCORE) -> dict:
    from test_reader_charter3 import synth          # the synthetic panel of the tests, one definition

    top, feats, hist, fwd = synth(signal, seed=seed, rho=rho)
    return {"kind": "synthetic", "score": score, "seed": seed, "rho": rho, "signal": signal,
            **gate_of_panel(c3.assemble_panel(top, feats, hist, fwd), score)}


# ---------------------------------------------------------------- decision-time panel of the stores
def decision_panel(root: Path = ROOT) -> pd.DataFrame:
    """Card columns, bar history, attention counts and reader features of every universe row. Decision-time
    data only: ``history_features`` reads no bar after the Friday bar, which closes at the decision."""
    from reader_charter3_register import INPUTS

    items, docs, cards, records = (pd.read_parquet(root / INPUTS[name]) for name in ("items", "docs", "cards", "records"))
    top = c2.universe(cards)
    sets, _ = c2.reading(items, docs, top)
    feats = c3.text_features(items, sets, records, top)
    hist = c3.history_features(root / KLINES, top[["date", "symbol"]].reset_index(drop=True))
    empty = pd.DataFrame({"date": pd.Series(dtype="datetime64[ns, UTC]"), "symbol": pd.Series(dtype=object),
                          **{c: pd.Series(dtype=float) for c in c3.TARGET_COLUMNS}})
    panel = c3.assemble_panel(top, feats, hist, empty)
    return panel.merge(c3._keyed(top, ["funding_3d"]), on=["date", "symbol"], validate="1:1")[STORE_COLUMNS]


class RealPanel:
    """The fixed part of a draw on the decision-time panel: ranks and the feature residuals of one partial score."""

    def __init__(self, stored: pd.DataFrame, score: str = c3.GATE_SCORE):
        frame = stored.sort_values(["date", "symbol"]).reset_index(drop=True)
        frame["abs_funding_3d"] = frame["funding_3d"].abs()
        feats, self.controls, self.squares, self.flexible = c3.PARTIAL_SCORES[score]
        self.score, self.frame, self.dates = score, frame, c3._dates(frame)
        self.design = c3.control_matrix(frame, self.controls, self.squares)
        self.X = c3.feature_residuals(frame, feats, self.controls, self.squares, self.flexible)
        self.rank = dict(zip([*c3.HIST, *c3.BLOCK_V], c3.feature_ranks(frame, [*c3.HIST, *c3.BLOCK_V]).T))
        self.weeks = np.unique(self.dates)
        self.week_index = np.searchsorted(self.weeks, self.dates)
        self.symbols, self.symbol_index = np.unique(frame["symbol"].to_numpy(), return_inverse=True)
        planted = sum(w * self.rank[c] for c, w in PLANTED.items())
        self.planted = self._standardise(planted)

    def _standardise(self, values: np.ndarray) -> np.ndarray:
        s = pd.Series(values).groupby(self.dates)
        return ((values - s.transform("mean")) / s.transform("std")).to_numpy()

    def base(self, shape: str) -> np.ndarray:
        r = self.rank
        out = sum(w * r[c] for c, w in LINEAR.items())
        if shape == "nonlinear":                    # convex in last week's variance, an interaction and a kink
            out = out + 4.0 * (r["rv_7d"] ** 2) + 3.0 * r["rv_max_7d"] * r["vsurge_7d"] + 4.0 * np.maximum(r["absret_7d"] - 0.3, 0.0)
        elif shape != "linear":
            raise SystemExit(f"unknown shape {shape}")
        return out

    def target(self, seed: int, rho: float, shape: str, signal: float, noise: float) -> np.ndarray:
        """Within-week rank of a synthetic log variance: history part, an AR(1) component per asset that no
        regressor sees (unit variance, weekly persistence ``rho``) scaled by ``noise``, planted reader effect."""
        rng = np.random.default_rng([seed, 3])
        eps = rng.normal(size=(len(self.weeks), len(self.symbols)))
        u = eps.copy()
        for w in range(1, len(self.weeks)):
            u[w] = rho * u[w - 1] + math.sqrt(1 - rho * rho) * eps[w]
        log_var = self.base(shape) + noise * u[self.week_index, self.symbol_index] + signal * self.planted
        return (pd.Series(log_var).groupby(self.dates).rank(pct=True) - 0.5).to_numpy()

    def draw(self, seed: int, rho: float = 0.0, shape: str = "linear", signal: float = 0.0, noise: float = 1.0) -> dict:
        y = self.target(seed, rho, shape, signal, noise)
        resid = c3.target_residual(self.frame, y, self.controls, self.squares, self.flexible)
        score, _ = c3.walk_forward(self.X, resid, self.dates)
        size = c3.size_statistics(score, resid, y)
        return {"kind": "real", "score": self.score, "seed": seed, "rho": rho, "shape": shape, "signal": signal, "noise": noise,
                "residual_share": size["residual_share_of_target"], "oos_r2_residual": size["oos_r2_residual"],
                **gate_row(self.dates, score, resid)}


# ---------------------------------------------------------------- persistence before the panel window
def curved_share(controls: np.ndarray, resid: np.ndarray, dates: np.ndarray, params: dict, rounds: int, blocks: int) -> float:
    """Out-of-sample share of a within-week linear residual that a boosted-tree function of the control ranks
    explains, cross-fitted over blocks of consecutive weeks. Near zero: no curvature the trees can find."""
    import lightgbm as lgb

    weeks, have = np.unique(dates), np.isfinite(resid)
    pred = np.full(len(resid), np.nan)
    for block in np.array_split(np.arange(len(weeks)), blocks):
        inside = np.isin(dates, weeks[block])
        booster = lgb.train(dict(params), lgb.Dataset(controls[~inside & have], label=resid[~inside & have]), num_boost_round=rounds)
        pred[inside & have] = booster.predict(controls[inside & have])
    return float(1 - ((resid[have] - pred[have]) ** 2).sum() / (resid[have] ** 2).sum())


def history_frame(klines_dir: Path, n: int = c2.UNIVERSE_N) -> pd.DataFrame:
    """Weekly top-``n`` by 30-day volume on bars before the panel window: bar history and the target."""
    fridays = pd.date_range(*HISTORY_FRIDAYS, freq="7D", tz="UTC")
    parts = []
    for path in sorted(Path(klines_dir).glob("*.parquet")):
        bars = c3.load_bars(path.parent, path.stem)
        bars = bars[bars.index < PANEL_BEGINS]
        if len(bars) < c3.MIN_BARS_LONG or bars.index[0] > fridays[-1]:
            continue
        keys = pd.DataFrame({"date": fridays[fridays.isin(bars.index)], "symbol": path.stem})
        if keys.empty:
            continue
        hist = c3.bar_history(bars).reindex(keys["date"]).reset_index(drop=True)
        volume = bars["quote_volume"].rolling("30D", min_periods=c3.MIN_BARS_LONG).mean().reindex(keys["date"]).to_numpy()
        gk = c3.gk_variance(bars).dropna()
        fwd = [gk[(gk.index > f) & (gk.index <= f + c3.FORWARD)].mean() for f in keys["date"]]
        parts.append(pd.concat([keys, hist], axis=1).assign(volume=volume, **{c3.TARGET: fwd}))
    frame = pd.concat(parts, ignore_index=True).dropna(subset=["volume"])
    frame = frame[frame.groupby("date")["volume"].rank(ascending=False, method="first") <= n]
    return frame.sort_values(["date", "symbol"]).reset_index(drop=True)


def history_calibration(klines_dir: Path, n: int = c2.UNIVERSE_N) -> dict:
    """On bars before the panel window: share of the target-rank variance left by the bar-history ranks, the
    persistence of that residual within an asset and how curved the relation is (squares of the ranks added to
    the within-week regression; boosted trees fitted to the linear residual)."""
    frame = history_frame(klines_dir, n)
    dates, y = c3._dates(frame), c3.target_rank(frame)
    ranks = c3.feature_ranks(frame, c3.HIST_BARS)
    resid = c3.residuals(y[:, None], ranks, dates)[:, 0]
    squared = c3.residuals(y[:, None], np.column_stack([ranks, ranks ** 2]), dates)[:, 0]
    have = np.isfinite(resid)
    total, k = ((y[have] - y[have].mean()) ** 2).sum(), ranks.shape[1]
    share = float((resid[have] ** 2).sum() / total)
    return {"bars_before": str(PANEL_BEGINS.date()), "weeks": int(frame["date"].nunique()), "rows": int(len(frame)),
            "assets": int(frame["symbol"].nunique()), "rows_with_target": int(np.isfinite(y).sum()),
            "residual_share_of_target": share,
            "residual_autocorrelation": c3.residual_autocorrelation(frame, resid),
            "residual_share_with_squares": float((squared[have] ** 2).sum() / total),
            "residual_share_with_squares_if_no_curvature": share * (n - 1 - 2 * k) / (n - 1 - k),
            "curved_share_of_linear_residual": {name: curved_share(ranks, resid, dates, params, rounds, blocks=4)
                                                for name, (params, rounds) in CURVE_FITS.items()}}


def shape_curvature(stored: pd.DataFrame, seeds: int = SHAPE_SEEDS) -> dict:
    """The curvature measure of ``history_calibration`` on the synthetic targets of the ``real`` kind (pure noise
    draws, first-design residual), mean over ``seeds`` draws per shape."""
    fixed = RealPanel(stored, "s_reader_lin")
    ranks = c3.feature_ranks(fixed.frame, c3.HIST)
    out = {}
    for shape in ("linear", "nonlinear"):
        resid = [c3.residuals(fixed.target(seed, 0.0, shape, 0.0, 1.0)[:, None], fixed.design, fixed.dates)[:, 0] for seed in range(seeds)]
        out[shape] = {name: float(np.mean([curved_share(ranks, e, fixed.dates, params, rounds, blocks=6) for e in resid]))
                      for name, (params, rounds) in CURVE_FITS.items()}
    return {"seeds": seeds, "curved_share_of_linear_residual": out}


# ---------------------------------------------------------------- summary
def summary(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    frame = pd.DataFrame(rows)
    keys = [c for c in ("kind", "score", "rho", "shape", "signal", "noise") if c in frame.columns]
    out = []
    for values, group in frame.groupby(keys, dropna=False):
        if group["seed"].duplicated().any():
            raise SystemExit(f"a seed occurs twice in {values}")
        t, mean, n = group["t"].to_numpy(dtype=float), group["mean"].to_numpy(dtype=float), len(group)
        passed = (group["verdict"] == "PASS").to_numpy()
        rate = float(passed.mean())
        half = 1.96 * math.sqrt(rate * (1 - rate) / n)
        row = {**dict(zip(keys, values)), "draws": n, "seeds": [int(group["seed"].min()), int(group["seed"].max())],
               "passes": int(passed.sum()), "pass_rate": rate, "pass_rate_95": [rate - half, rate + half],
               "first_gate_alone": int(((t >= c3.GATE_T) & (mean > 0)).sum()),
               "pass_long_lag": int(((group["t_long"] >= c3.GATE_T) & (group["y2023"] > 0) & (group["y2024"] > 0)).sum()),
               "pass_visible": int((passed & (mean >= c3.SIZE_VISIBLE)).sum()), "pass_thin": int((passed & (mean < c3.SIZE_VISIBLE)).sum()),
               "mean_ic": float(mean.mean()), "t_mean": float(t.mean()), "t_sd": float(t.std(ddof=1)),
               "t_q975": float(np.quantile(t, 0.975))}
        if "residual_share" in group:
            row["residual_share"] = float(group["residual_share"].mean())
        out.append(row)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    syn = sub.add_parser("synthetic")
    real = sub.add_parser("real")
    real.add_argument("panel")
    for p in (syn, real):
        p.add_argument("first", type=int)
        p.add_argument("last", type=int)
        p.add_argument("--rho", type=float, default=0.0)
        p.add_argument("--signal", type=float, default=0.0)
        p.add_argument("--score", default=c3.GATE_SCORE, choices=list(c3.PARTIAL_SCORES))
    real.add_argument("--shape", default="linear")
    real.add_argument("--noise", type=float, default=1.0)
    sub.add_parser("panel").add_argument("target")
    sub.add_parser("history")
    sub.add_parser("shapes").add_argument("panel")
    sub.add_parser("summary").add_argument("path")
    args = ap.parse_args(argv)
    if args.mode == "summary":
        print(json.dumps(summary(Path(args.path)), indent=1))
    elif args.mode == "history":
        print(json.dumps(history_calibration(ROOT / KLINES), indent=1))
    elif args.mode == "shapes":
        print(json.dumps(shape_curvature(pd.read_parquet(args.panel)), indent=1))
    elif args.mode == "panel":
        panel = decision_panel()
        panel.to_parquet(args.target, index=False)
        print(json.dumps({"rows": len(panel), "weeks": int(panel["date"].nunique()), "columns": list(panel.columns)}))
    elif args.mode == "synthetic":
        for seed in range(args.first, args.last):
            print(json.dumps(synthetic_draw(seed, args.rho, args.signal, args.score)), flush=True)
    else:
        fixed = RealPanel(pd.read_parquet(args.panel), args.score)
        for seed in range(args.first, args.last):
            print(json.dumps(fixed.draw(seed, args.rho, args.shape, args.signal, args.noise)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
