"""Phase-P engine (registered: predlab_pp) — strategy layer over FROZEN
stored forecasts. No model refitting anywhere in this module.

S1: T7 park_5 low-vol long-short (quintiles, 5bp taker/side + funding carry)
S2: BTC HARQ vol-target overlay (sizing value; tracking-error claim)
S3: exploratory 1h sign filter (cannot graduate past dev this cycle)

Timing conventions (all verified against the P5 runner):
- T7: signal row t is pre-shifted (info through day t-1); return row t is the
  day-t simple return -> weights formed from row t trade day t. Contracts
  drift between rebalances; costs apply to actual notional changes.
- S2/S3: stored forecast row ts predicts the bar labeled ts using info
  through ts-1 -> position from row ts applies to store ret row ts.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.accounting import calendar_index, run_target_book

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
    eq = np.r_[1.0, np.cumprod(1 + np.asarray(rets, dtype=np.float64))]
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
    # A single accounting implementation keeps S1 and the default Opt cell in
    # parity, including held units, missing signals and entry/maintenance fees.
    from tradingagents.predlab.opt import OptConfig, run_ls
    result = run_ls(sig, ret, uni, fund_daily,
                    OptConfig(weighting=weighting, smooth=smooth, taker_bp=TAKER_BP),
                    start, end)
    return {key: result[key] for key in
            ("rets", "sr_gross", "sr_net", "maxdd", "avg_turnover", "n_days")}


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
    clock = calendar_index(common)
    v = var_fc.reindex(clock).where(lambda x: np.isfinite(x) & (x > 0))
    pos = (target_ann / np.sqrt(v * ANN_DAYS)).clip(0., lev_cap)
    book = run_target_book(pos.to_frame("asset"), ret.reindex(clock).to_frame("asset"),
                           fee_rate=TAKER_BP/1e4)
    real = book["net"]
    roll_vol = real.rolling(20).std() * np.sqrt(ANN_DAYS)
    errors = (roll_vol.dropna() - target_ann) ** 2
    te = float(np.sqrt(errors.mean())) if len(errors) else float('nan')
    return {"rets": real, "sr_net": ann_sr(real.to_numpy()), "maxdd": max_drawdown(real.to_numpy()),
            "tracking_err": te, "roll_vol": roll_vol,
            "avg_pos": float(book.attrs['accounting_inputs'].weights.asset.mean()) if len(book) else 0.,
            "n_days": int(len(real)), "accounting": book}


# ------------------------------------------------------------ S3: sign filter

def run_s3(prob: pd.Series, ret: pd.Series, thresh: float, smooth: int) -> dict:
    """Long/flat 1h filter: long when smoothed P(up) > thresh."""
    common = prob.index.intersection(ret.index)
    clock = calendar_index(common, 'h')
    raw = prob.reindex(clock).where(lambda x: np.isfinite(x))
    p = raw.rolling(smooth, min_periods=1).mean() if smooth > 1 else raw
    pos = (p > thresh).astype(float).where(raw.notna())
    book = run_target_book(pos.to_frame("asset"), ret.reindex(clock).to_frame("asset"),
                           fee_rate=TAKER_BP/1e4)
    real = book["net"]
    return {"rets": real,
            "sr_net": ann_sr(real.to_numpy(), periods_per_year=24 * ANN_DAYS),
            "maxdd": max_drawdown(real.to_numpy()),
            "time_in_mkt": float((book.attrs['accounting_inputs'].weights.asset != 0).mean()) if len(book) else 0.,
            "n_hours": int(len(real)), "accounting": book}


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
