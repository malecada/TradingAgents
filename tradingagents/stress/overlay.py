"""Flatten-while-WARN de-risk overlay + paired metrics."""
import numpy as np
import pandas as pd


def apply_overlay(returns: pd.Series, warn: pd.Series, cooldown: int = 5) -> pd.Series:
    warn = warn.reindex(returns.index).fillna(False).astype(bool)
    flat = warn.copy()
    release_count = 0
    out_flags = []
    for on in warn:
        if on:
            release_count = cooldown
            out_flags.append(True)
        elif release_count > 0:
            release_count -= 1
            out_flags.append(True)
        else:
            out_flags.append(False)
    flat = pd.Series(out_flags, index=returns.index)
    return returns.where(~flat, 0.0)


def _sr(returns: pd.Series) -> float:
    sd = returns.std()
    if sd == 0 or np.isnan(sd):
        return 0.0
    return float(returns.mean() / sd * np.sqrt(365))


def _maxdd(returns: pd.Series) -> float:
    """Max drawdown as positive magnitude; delta_maxdd = overlay - base, improvement < 0 (matches frozen gate overlay_delta_maxdd_max = 0.0)."""
    cum = returns.cumsum()
    dd = cum - cum.cummax()
    return float(-np.expm1(dd.min()))


def overlay_metrics(returns: pd.Series, warn: pd.Series, cooldown: int = 5) -> dict:
    ov = apply_overlay(returns, warn, cooldown)
    flat_frac = float((ov == 0.0).mean())
    return {
        "sr_base": _sr(returns),
        "sr_overlay": _sr(ov),
        "delta_sr": _sr(ov) - _sr(returns),
        "maxdd_base": _maxdd(returns),
        "maxdd_overlay": _maxdd(ov),
        "delta_maxdd": _maxdd(ov) - _maxdd(returns),
        "exposure_frac": 1.0 - flat_frac,
    }
