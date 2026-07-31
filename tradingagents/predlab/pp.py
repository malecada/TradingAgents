"""Phase-P engine (registered: predlab_pp) — strategy layer over FROZEN
stored forecasts. No model refitting anywhere in this module.

S1: T7 park_5 low-vol long-short (quintiles, 5bp taker/side + funding carry)
S2: BTC HARQ vol-target overlay (sizing value; tracking-error claim)
S3: exploratory 1h sign filter (cannot graduate past dev this cycle)

Timing conventions (all verified against the P5 runner):
- T7: signal row t is pre-shifted (info through day t-1); return row t is the
  day-t log return -> weights formed from row t trade day t. Positions are
  therefore w_t applied to ret_t, turnover charged on w_t - w_{t-1}.
- S2/S3: stored forecast row ts predicts the bar labeled ts using info
  through ts-1 -> position from row ts applies to store ret row ts.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TAKER_BP = 5.0  # per side, per unit turnover
ANN_DAYS = 365.0


# ---------------------------------------------------------------- metrics

def ann_sr(rets: np.ndarray, periods_per_year: float = ANN_DAYS) -> float:
    r = np.asarray(rets, dtype=np.float64)
    r = r[~np.isnan(r)]
    if len(r) < 20 or np.nanstd(r) == 0:
        return 0.0
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(periods_per_year))


def max_drawdown(rets: np.ndarray) -> float:
    eq = np.cumprod(1 + np.asarray(rets, dtype=np.float64))
    peak = np.maximum.accumulate(eq)
    return float(np.max(1 - eq / peak))


def dsr(sr_ann: float, sr_all_trials_ann: "list[float]", n_obs: int,
        rets: np.ndarray, periods_per_year: float = ANN_DAYS) -> float:
    """Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014).

    Expected-max SR benchmark uses the observed cross-trial SR variance;
    skew/kurtosis corrections from the candidate's own return series.
    """
    from scipy.stats import kurtosis, norm, skew

    sr = sr_ann / np.sqrt(periods_per_year)  # per-period
    trials = np.asarray(sr_all_trials_ann, dtype=np.float64) / np.sqrt(periods_per_year)
    n = max(len(trials), 2)
    var_tr = float(np.var(trials, ddof=1)) if len(trials) > 1 else 1.0 / n_obs
    var_tr = max(var_tr, 1e-12)
    emc = 0.5772156649
    sr_star = np.sqrt(var_tr) * ((1 - emc) * norm.ppf(1 - 1 / n)
                                 + emc * norm.ppf(1 - 1 / (n * np.e)))
    r = np.asarray(rets, dtype=np.float64)
    r = r[~np.isnan(r)]
    g3, g4 = float(skew(r)), float(kurtosis(r, fisher=False))
    denom = np.sqrt(max(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2, 1e-12))
    z = (sr - sr_star) * np.sqrt(max(n_obs - 1, 1)) / denom
    return float(norm.cdf(z))


# ---------------------------------------------------------------- S1: T7 LS

def quintile_weights(sig_row: pd.Series, weighting: str) -> pd.Series:
    """Long bottom-signal quintile, short top-signal quintile; each leg
    sums to 1 (gross 2). weighting: 'eq' or 'rank' (linear within leg)."""
    s = sig_row.dropna()
    n = len(s)
    if n < 25:
        return pd.Series(dtype=np.float64)
    q = max(n // 5, 1)
    order = s.sort_values()
    lo, hi = order.index[:q], order.index[-q:]
    w = pd.Series(0.0, index=s.index)
    if weighting == "eq":
        w[lo] = 1.0 / q
        w[hi] = -1.0 / q
    else:  # rank: strongest conviction at the extremes
        rl = np.arange(q, 0, -1, dtype=np.float64) / np.arange(q, 0, -1).sum()
        w[lo] = rl            # lowest signal = largest long
        w[hi] = -rl[::-1]     # highest signal = largest short
    return w


def run_s1(sig: pd.DataFrame, ret: pd.DataFrame, uni: pd.DataFrame,
           fund_daily: "pd.DataFrame | None", weighting: str, smooth: int,
           start: str, end: str) -> dict:
    """Daily long-short on park_5 ranks. Costs: TAKER_BP x turnover +
    funding carry (position pays +funding when long)."""
    lo, hi = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    sig = sig.where(uni)
    days = [d for d in ret.index if lo <= d <= hi]
    prev_w = pd.Series(dtype=np.float64)
    targets: "list[pd.Series]" = []
    out = []
    for d in days:
        if d not in sig.index:
            continue
        w_tgt = quintile_weights(sig.loc[d], weighting)
        if len(w_tgt) == 0:
            continue
        targets.append(w_tgt)
        if len(targets) > smooth:
            targets.pop(0)
        w = pd.concat(targets, axis=1).fillna(0.0).mean(axis=1)
        r_row = ret.loc[d].reindex(w.index)
        gross = float((w * r_row).sum())
        both = w.index.union(prev_w.index)
        turn = float((w.reindex(both, fill_value=0.0)
                      - prev_w.reindex(both, fill_value=0.0)).abs().sum())
        cost = TAKER_BP / 1e4 * turn
        carry = 0.0
        if fund_daily is not None and d in fund_daily.index:
            f = fund_daily.loc[d].reindex(w.index).fillna(0.0)
            carry = float(-(w * f).sum())  # long pays positive funding
        out.append({"date": d, "gross": gross, "net": gross - cost + carry,
                    "turnover": turn, "carry": carry})
        prev_w = w
    df = pd.DataFrame(out).set_index("date")
    return {"rets": df, "sr_gross": ann_sr(df["gross"].to_numpy()),
            "sr_net": ann_sr(df["net"].to_numpy()),
            "maxdd": max_drawdown(df["net"].to_numpy()),
            "avg_turnover": float(df["turnover"].mean()),
            "n_days": int(len(df))}


def build_funding_daily(symbols: "list[str]", store_dir, index: pd.DatetimeIndex
                        ) -> pd.DataFrame:
    """Daily funding sum per symbol (UTC-day of fundingTime)."""
    cols = {}
    for sym in symbols:
        p = store_dir / f"{sym}.parquet"
        if not p.exists():
            continue
        r = pd.read_parquet(p)["fundingRate"].astype(float)
        cols[sym] = r.groupby(r.index.floor("D")).sum()
    return pd.DataFrame(cols).reindex(index)


# ------------------------------------------------------- S2: vol targeting

def run_s2(var_fc: pd.Series, ret: pd.Series, target_ann: float = 0.20,
           lev_cap: float = 3.0) -> dict:
    """Vol-target overlay: pos_t = clip(target / ann_vol_hat_t, 0, cap),
    applied to same-row daily return; 5bp on position changes."""
    common = var_fc.index.intersection(ret.index)
    v = np.maximum(var_fc.loc[common].to_numpy(dtype=np.float64), 1e-10)
    sig_ann = np.sqrt(v * ANN_DAYS)
    pos = np.clip(target_ann / sig_ann, 0.0, lev_cap)
    r = ret.loc[common].to_numpy(dtype=np.float64)
    strat = pos * r
    cost = TAKER_BP / 1e4 * np.abs(np.diff(pos, prepend=pos[0]))
    net = strat - cost
    real = pd.Series(net, index=common)
    roll_vol = real.rolling(20).std() * np.sqrt(ANN_DAYS)
    te = float(np.sqrt(np.nanmean((roll_vol - target_ann) ** 2)))
    return {"rets": real, "sr_net": ann_sr(net), "maxdd": max_drawdown(net),
            "tracking_err": te, "roll_vol": roll_vol,
            "avg_pos": float(np.mean(pos)), "n_days": int(len(net))}


# ------------------------------------------------------------ S3: sign filter

def run_s3(prob: pd.Series, ret: pd.Series, thresh: float, smooth: int) -> dict:
    """Long/flat 1h filter: long when smoothed P(up) > thresh."""
    common = prob.index.intersection(ret.index)
    p = prob.loc[common]
    if smooth > 1:
        p = p.rolling(smooth, min_periods=1).mean()
    pos = (p > thresh).astype(float).to_numpy()
    r = ret.loc[common].to_numpy(dtype=np.float64)
    strat = pos * r
    cost = TAKER_BP / 1e4 * np.abs(np.diff(pos, prepend=0.0))
    net = strat - cost
    return {"rets": pd.Series(net, index=common),
            "sr_net": ann_sr(net, periods_per_year=24 * ANN_DAYS),
            "maxdd": max_drawdown(net),
            "time_in_mkt": float(np.mean(pos)), "n_hours": int(len(net))}


# ---------------------------------------------------------------- placebos

def placebo_shift(run_fn, sig_obj, n_draws: int = 200, min_shift: int = 30,
                  seed: int = 0) -> "list[float]":
    """Family A: circular time-shift of the signal object (preserves its
    autocorrelation, breaks alignment). run_fn(shifted_sig) -> net SR."""
    rng = np.random.default_rng(seed)
    n = len(sig_obj)
    out = []
    for _ in range(n_draws):
        k = int(rng.integers(min_shift, n - min_shift))
        shifted = sig_obj.copy()
        vals = np.roll(np.asarray(sig_obj.to_numpy()), k, axis=0)
        if isinstance(sig_obj, pd.DataFrame):
            shifted = pd.DataFrame(vals, index=sig_obj.index, columns=sig_obj.columns)
        else:
            shifted = pd.Series(vals, index=sig_obj.index)
        out.append(run_fn(shifted))
    return out


def placebo_pvalue(real_sr: float, null_srs: "list[float]") -> float:
    null = np.asarray(null_srs, dtype=np.float64)
    return float((np.sum(null >= real_sr) + 1) / (len(null) + 1))
