"""Rejection rate and power of the Charter 5 gates on synthetic outcomes and synthetic comparison scores.

Usage: cmp_null_gate.py [--draws 400] [--out data/compare/null_gate.json]
The panel has the registered shape: the test universe with its real controls, the real quant forecast, the real
attention counts (present store and linked archive) and a real dossier structure. Two structures are used: the
dossiers the present records give (``present``) and a denser one in which an asset-week with at least three
archive documents of the typing scope also has a dossier (``dense``). Scores and returns are drawn; no return of
the window is read and no model is called. The fast path used for the draws is compared with
``charter5.gate_statistics`` on the first draws of every scenario.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import rankdata

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.agents_v2.evaluate import newey_west_t  # noqa: E402
from tradingagents.compare import charter5, dossier  # noqa: E402
from tradingagents.dossier.universe import load_cards  # noqa: E402
from tradingagents.reader import charter2  # noqa: E402
from tradingagents.reader.reading import DECISION_OFFSET  # noqa: E402

SEED = 20261115
CHECK_DRAWS = 5
POWER = (0.02, 0.03, 0.04, 0.06, 0.08)
DENSE_MIN_DOCS = 3
# Attention scenarios: (per-week standardised variable, loading of the return on it and on having a dossier). ``attn``
# is the registered control ``attn_7d`` (the log count), whose standardised form has a long right tail that its rank
# does not carry; ``attn_log`` compresses that tail once more. 0.3 is about ten times the attention effect measured
# on this window under Charter 2 (rank correlation 0.031); 0.03 is that measured size.
ATTENTION = {"attention": ("attn", 0.3), "attention_measured": ("attn", 0.03), "attention_compressed": ("attn_log", 0.3)}
SCENARIOS = {"noise": 0, "attention": 1, "momentum": 2, "persistent": 3, "attention_measured": 4, "attention_compressed": 5}


def structure(root: Path) -> pd.DataFrame:
    """Test-universe rows with controls, quant forecast, attention and the two dossier structures."""
    top = charter2.universe(load_cards())
    test = charter5.test_universe(top)
    items, docs = pd.read_parquet(root / "data/reader/items.parquet"), pd.read_parquet(root / "data/reader/docs.parquet")
    records = pd.read_parquet(root / "data/reader/records.parquet")
    archive = pd.read_parquet(root / "data/compare/items.parquet")
    cols = ["doc_id", "base", "event_ts", "as_of_ts"]
    attention = charter5.attention_7d(pd.concat([items[cols], archive[cols]], ignore_index=True), test)
    sets = dossier.weekly_sets(items, docs, top, fridays=sorted(test["date"].unique()))
    cands, _ = dossier.candidates(sets, records, docs)
    n_lines = dossier.line_table(cands).groupby(["friday", "base"]).size().rename("n_present").reset_index()
    panel = test[["date", "symbol", "base", *charter5.CONTROLS]].merge(attention, on=["date", "base"], how="left", validate="1:1")
    panel = panel.merge(n_lines.rename(columns={"friday": "date"}), on=["date", "base"], how="left", validate="1:1")
    quant = pd.read_parquet(root / "data/dossier/quant_forecasts.parquet").rename(columns={"pred_rank_pct": charter5.QUANT})
    panel = panel.merge(quant[["date", "symbol", charter5.QUANT]], on=["date", "symbol"], how="left", validate="1:1")
    scope = archive[(archive["salience"] == "primary") & ~archive["base"].isin(["BTC", "ETH"])]
    counts = []
    for friday in sorted(test["date"].unique()):
        dec = friday + DECISION_OFFSET
        win = scope[(scope["event_ts"] >= dec - pd.Timedelta(days=7)) & (scope["event_ts"] <= dec) & (scope["as_of_ts"] <= dec)]
        counts.append(win.groupby("base")["doc_id"].nunique().rename("n_archive").reset_index().assign(date=friday))
    panel = panel.merge(pd.concat(counts, ignore_index=True), on=["date", "base"], how="left", validate="1:1")
    panel["n_present"] = panel["n_present"].fillna(0.0)
    panel["n_archive"] = panel["n_archive"].fillna(0.0)
    extra = np.where(panel["n_archive"] >= DENSE_MIN_DOCS, np.round(np.log2(1 + panel["n_archive"])), 0.0)
    panel["n_dense"] = np.minimum(dossier.MAX_LINES, panel["n_present"] + extra)
    return panel.sort_values(["date", "symbol"]).reset_index(drop=True)


def _z(v: np.ndarray) -> np.ndarray:
    sd = v.std()
    return (v - v.mean()) / sd if sd > 0 else np.zeros_like(v)


class Weeks:
    """Per-week arrays of one dossier structure: the annihilator of the control ranks and what the draws need."""

    def __init__(self, panel: pd.DataFrame, lines_col: str):
        frame = panel.assign(n_lines=panel[lines_col], has_dossier=(panel[lines_col] > 0).astype(float))
        self.frame = frame
        self.weeks = []
        for date, day in frame.groupby("date"):
            day = day.dropna(subset=[charter5.QUANT])
            use = len(day) >= charter5.MIN_WEEK_ROWS and day["has_dossier"].sum() >= charter5.MIN_WEEK_DOSSIERS
            z = np.column_stack([np.ones(len(day))] + [day[c].astype(float).rank(pct=True).fillna(0.5).to_numpy()
                                                      for c in charter5.GATE_CONTROLS])
            m = np.eye(len(day)) - z @ np.linalg.pinv(z)
            self.weeks.append({"date": date, "index": day.index.to_numpy(), "m": m, "use": use,
                               "has": day["has_dossier"].to_numpy() > 0, "attn": _z(day["attn_7d"].to_numpy()),
                               "attn_log": _z(np.log1p(day["attn_7d"].to_numpy())),
                               "mom": _z(day["ret_4w"].rank(pct=True).fillna(0.5).to_numpy()), "base": day["base"].to_numpy()})
        self.years = np.array([w["date"].year for w in self.weeks if w["use"]])
        self.bases = sorted(frame["base"].unique())

    def statistic(self, score: dict, ret: dict) -> tuple[float, bool, bool]:
        betas = []
        for i, w in enumerate(self.weeks):
            if not w["use"]:
                continue
            n = len(w["index"])
            ry, rx = w["m"] @ (rankdata(ret[i]) / n), w["m"] @ (rankdata(score[i]) / n)
            ss = rx @ rx
            betas.append(rx @ ry / ss if ss > 1e-9 else np.nan)
        betas = np.array(betas)
        ok = np.isfinite(betas)
        series = pd.Series(betas[ok])
        t = newey_west_t(series)
        g1 = bool(ok.sum() >= charter5.MIN_GATE_WEEKS and t >= charter5.GATE_T and series.mean() > 0)
        g2 = bool(all(betas[ok & (self.years == y)].mean() > 0 for y in charter5.GATE_YEARS))
        return float(t), g1, g1 and g2

    def panel_of(self, score: dict, ret: dict) -> pd.DataFrame:
        out = self.frame.assign(cmp_score=np.nan, fwd_ret=np.nan)
        for i, w in enumerate(self.weeks):
            out.loc[w["index"], "cmp_score"] = score[i]
            out.loc[w["index"], "fwd_ret"] = ret[i]
        return out


def draw(weeks: Weeks, rng, scenario: str, rho: float = 0.0) -> tuple[dict, dict]:
    """Synthetic scores (zero for assets without a dossier) and returns of one panel."""
    score, ret = {}, {}
    state = {b: (rng.normal(), rng.normal()) for b in weeks.bases}
    for i, w in enumerate(weeks.weeks):
        n = len(w["index"])
        s, e = rng.normal(size=n), rng.normal(size=n)
        if scenario in ATTENTION:              # returns and scores both load on attention and on having a dossier
            key, load = ATTENTION[scenario]
            s = 0.5 * w[key] + np.sqrt(0.75) * s
            e = e + load * w[key] + load * w["has"]
        elif scenario == "momentum":           # returns and scores both load on the four-week return
            s = 0.5 * w["mom"] + np.sqrt(0.75) * s
            e = e + 0.3 * w["mom"]
        elif scenario == "persistent":         # persistent scores, independent persistent return component
            for j, b in enumerate(w["base"]):
                ps, pr = state[b]
                ps, pr = 0.8 * ps + 0.6 * rng.normal(), 0.8 * pr + 0.6 * rng.normal()
                state[b] = (ps, pr)
                s[j], e[j] = ps, e[j] + 0.5 * pr
        elif scenario == "signal":
            e = np.where(w["has"], rho * _z(s) + np.sqrt(1 - rho ** 2) * e, e)
        score[i] = np.where(w["has"], s, 0.0)
        ret[i] = 0.1 * e
    return score, ret


def run(weeks: Weeks, scenario: str, draws: int, seed: int, rho: float = 0.0) -> dict:
    rng = np.random.default_rng(seed)
    ts, g1, g12 = [], 0, 0
    for k in range(draws):
        score, ret = draw(weeks, rng, scenario, rho)
        t, a, b = weeks.statistic(score, ret)
        if k < CHECK_DRAWS:
            stat, _ = charter5.gate_statistics(weeks.panel_of(score, ret))
            if abs(stat["nw_t"] - t) > 1e-8:
                raise SystemExit(f"fast path differs from charter5.gate_statistics: {stat['nw_t']} vs {t}")
        ts.append(t)
        g1 += a
        g12 += b
    return {"draws": draws, "g1": g1 / draws, "g1_and_g2": g12 / draws, "t_mean": float(np.mean(ts)), "t_sd": float(np.std(ts))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=400)
    ap.add_argument("--out", default="data/compare/null_gate.json")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    panel = structure(root)
    out = {"draws": args.draws, "seed": SEED, "rows": int(len(panel)), "weeks": int(panel["date"].nunique()), "structures": {}}
    for name, col in (("present", "n_present"), ("dense", "n_dense")):
        weeks = Weeks(panel, col)
        res = {"dossier_share": float((panel[col] > 0).mean()), "gate_weeks": int(len(weeks.years)), "null": {}, "power": {}}
        for scenario, offset in SCENARIOS.items():
            res["null"][scenario] = run(weeks, scenario, args.draws, SEED + offset)
            print(name, scenario, json.dumps(res["null"][scenario]), flush=True)
        for j, rho in enumerate(POWER):
            res["power"][str(rho)] = run(weeks, "signal", args.draws, SEED + 100 + j, rho)
            print(name, "signal", rho, json.dumps(res["power"][str(rho)]), flush=True)
        out["structures"][name] = res
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
