"""llm_c3p_pair_xs P2 (part 2) — residual IC gates + GBDT twin (charter §5).

Frozen pre-result:
- Residualization: per week, pct-rank the score and the three factors
  {vol_ewma20, ret_4w, size_rank}; cross-sectional OLS with intercept;
  residual is the signal. IC = Spearman(residual, forward log return).
- Primary horizon 5d (10d, 21d reported). Weeks with < 20 joint
  observations are skipped.
- NW t-stat: Newey-West (Bartlett) lag 4 on the weekly IC series.
- GBDT twin: LightGBM regression on identical numeric card features
  (category as pandas categorical), target = 5d forward log return,
  walk-forward: expanding history, min 52 weeks, refit every 13 weeks.
  Twin predictions residualized and scored identically.
- Gates: (a) mean residual IC > 0 AND NW-t >= 2.0;
         (b) LLM residual IC >= GBDT residual IC. STOP on either.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_pair_xs_p0 import DEV_END, LEDGER, MODEL, OUT, SEED  # noqa: E402
from llm_rank_xs_cards import load_panels  # noqa: E402

SCORES = OUT / "scores_dev.parquet"
RESULT = OUT / "p2_incremental.json"
FACTORS = ["vol_ewma20", "ret_4w", "size_rank"]
NUM_FEATURES = ["ret_4w", "ret_12w", "dist_26w_high", "vol_ewma20",
                "volvol_20", "dvol_rank", "mcap_cm", "funding_3d",
                "funding_30d", "d_adract_30d", "d_txcnt_30d",
                "unlock_next30_pct", "unlock_prev30_pct", "age_weeks"]
NW_LAG = 4
MIN_TRAIN_WEEKS = 52
REFIT_EVERY = 13
MIN_OBS = 20


def nw_tstat(x: np.ndarray, lag: int = NW_LAG) -> float:
    x = x[np.isfinite(x)]
    n = len(x)
    e = x - x.mean()
    s = float(e @ e) / n
    for k in range(1, lag + 1):
        w = 1 - k / (lag + 1)
        s += 2 * w * float(e[k:] @ e[:-k]) / n
    return float(x.mean() / np.sqrt(s / n))


def residualize(week_df: pd.DataFrame, col: str) -> pd.Series:
    """Pct-rank col and FACTORS, OLS with intercept, return residuals."""
    d = week_df.dropna(subset=[col])
    y = d[col].rank(pct=True)
    X = [np.ones(len(d))]
    for f in FACTORS:
        X.append(d[f].rank(pct=True).fillna(0.5))
    X = np.column_stack(X)
    beta, *_ = np.linalg.lstsq(X, y.values, rcond=None)
    return pd.Series(y.values - X @ beta, index=d["symbol"].values)


def ic_series(scores: pd.DataFrame, cards: pd.DataFrame, fwd: pd.DataFrame,
              col: str = "score") -> pd.Series:
    out = {}
    for d, wk_scores in scores.groupby("date"):
        wk = cards[cards["date"] == d].merge(
            wk_scores[["symbol", col]], on="symbol")
        if d not in fwd.index:
            continue
        resid = residualize(wk, col)
        f = fwd.loc[d]
        common = resid.index.intersection(f.dropna().index)
        if len(common) < MIN_OBS:
            continue
        v = float(spearmanr(resid[common], f[common]).statistic)
        if np.isfinite(v):
            out[d] = v
    return pd.Series(out).sort_index()


def gbdt_twin(cards: pd.DataFrame, fwd5: pd.DataFrame) -> pd.DataFrame:
    import lightgbm as lgb
    df = cards.copy()
    df["category"] = df["category"].astype("category")
    tgt = []
    for d, wk in df.groupby("date"):
        if d not in fwd5.index:
            tgt.append(pd.Series(np.nan, index=wk.index))
            continue
        tgt.append(wk["symbol"].map(fwd5.loc[d]))
    df["target"] = pd.concat(tgt)
    dates = sorted(df["date"].unique())
    preds = []
    model = None
    feats = NUM_FEATURES + ["category"]
    for i, d in enumerate(dates):
        if i < MIN_TRAIN_WEEKS:
            continue
        if model is None or (i - MIN_TRAIN_WEEKS) % REFIT_EVERY == 0:
            train = df[(df["date"] < d)].dropna(subset=["target"])
            model = lgb.LGBMRegressor(
                n_estimators=500, learning_rate=0.05, num_leaves=31,
                min_child_samples=50, random_state=SEED, verbose=-1)
            model.fit(train[feats], train["target"],
                      categorical_feature=["category"])
        wk = df[df["date"] == d]
        p = model.predict(wk[feats])
        preds.append(pd.DataFrame({"date": d, "symbol": wk["symbol"].values,
                                   "twin": p}))
    return pd.concat(preds, ignore_index=True)


def main() -> int:
    if RESULT.exists():
        print(f"{RESULT} exists — refusing to overwrite (stop rule)")
        return 1
    scores = pd.read_parquet(SCORES)
    scores["date"] = pd.to_datetime(scores["date"], utc=True)
    cards = pd.read_parquet(Path("data/llm_rank_xs") / "cards.parquet")
    cards["date"] = pd.to_datetime(cards["date"], utc=True)
    cards = cards[cards["date"] <= DEV_END]

    close, _o, _v = load_panels()
    close.index = pd.to_datetime(close.index, utc=True)
    fwd = {h: np.log(close.shift(-h) / close) for h in (5, 10, 21)}

    ic5 = ic_series(scores, cards, fwd[5])
    ic10 = ic_series(scores, cards, fwd[10])
    ic21 = ic_series(scores, cards, fwd[21])
    t5 = nw_tstat(ic5.values)
    gate_a = bool(ic5.mean() > 0 and t5 >= 2.0)

    twin = gbdt_twin(cards, fwd[5])
    twin_ic5 = ic_series(twin, cards, fwd[5], col="twin")
    # twin comparison on the common week set (twin needs 52-wk burn-in)
    common = ic5.index.intersection(twin_ic5.index)
    llm_common, twin_common = float(ic5[common].mean()), float(twin_ic5[common].mean())
    gate_b = bool(llm_common >= twin_common)
    verdict = "PASS" if (gate_a and gate_b) else "STOP"

    res = {"experiment": "llm_c3p_pair_xs", "probe": "P2_incremental",
           "llm": {"mean_resid_ic_5d": float(ic5.mean()), "nw_t_5d": t5,
                   "n_weeks": int(len(ic5)),
                   "mean_resid_ic_10d": float(ic10.mean()),
                   "nw_t_10d": nw_tstat(ic10.values),
                   "mean_resid_ic_21d": float(ic21.mean()),
                   "nw_t_21d": nw_tstat(ic21.values)},
           "twin": {"mean_resid_ic_5d": float(twin_ic5.mean()),
                    "nw_t_5d": nw_tstat(twin_ic5.values),
                    "n_weeks": int(len(twin_ic5))},
           "common_weeks": {"n": int(len(common)), "llm": llm_common,
                            "twin": twin_common},
           "gates": {"a_mean_pos_and_nw_t_ge_2": gate_a,
                     "b_llm_ge_twin_common_weeks": gate_b},
           "weekly_ic_5d": {str(k.date()): v for k, v in ic5.items()},
           "verdict": verdict}
    RESULT.write_text(json.dumps(res, indent=1))

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"],
                           capture_output=True, text=True).stdout.strip()
    for cell, m in (("P2_llm_dev", {"mean_resid_ic_5d": float(ic5.mean()),
                                    "nw_t_5d": t5}),
                    ("P2_gbdt_twin", {"mean_resid_ic_5d": float(twin_ic5.mean()),
                                      "common_llm": llm_common,
                                      "common_twin": twin_common})):
        row = {"ts_utc": datetime.now(timezone.utc).isoformat(),
               "experiment": "llm_c3p_pair_xs", "cell": cell,
               "model": MODEL if cell == "P2_llm_dev" else "lightgbm-twin",
               "config": {"factors": FACTORS, "nw_lag": NW_LAG,
                          "min_train_weeks": MIN_TRAIN_WEEKS,
                          "refit_every": REFIT_EVERY},
               "config_hash": cell,
               "git_commit": commit + ("-dirty" if dirty else ""),
               "window": ["2021-01-01", "2025-03-31"],
               "metrics": {**m, "verdict": verdict}}
        with LEDGER.open("a") as f:
            f.write(json.dumps(row) + "\n")
    print(f"P2 verdict: {verdict} | LLM IC5 {ic5.mean():.4f} (NW-t {t5:.2f}) | "
          f"twin common {twin_common:.4f} vs LLM {llm_common:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
