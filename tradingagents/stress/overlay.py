"""Flatten-while-WARN de-risk overlay + paired metrics."""
import numpy as np
import pandas as pd


def flat_mask(warn: pd.Series, index: pd.DatetimeIndex, cooldown: int = 5) -> pd.Series:
    """True while WARN is active and for `cooldown` days after release."""
    warn = warn.reindex(index).fillna(False).astype(bool)
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
    return pd.Series(out_flags, index=index)


def apply_overlay(returns: pd.Series, warn: pd.Series, cooldown: int = 5) -> pd.Series:
    mask = flat_mask(warn, returns.index, cooldown)
    return returns.where(~mask, 0.0)


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
    mask = flat_mask(warn, returns.index, cooldown)
    ov = returns.where(~mask, 0.0)
    return {
        "sr_base": _sr(returns),
        "sr_overlay": _sr(ov),
        "delta_sr": _sr(ov) - _sr(returns),
        "maxdd_base": _maxdd(returns),
        "maxdd_overlay": _maxdd(ov),
        "delta_maxdd": _maxdd(ov) - _maxdd(returns),
        "exposure_frac": 1.0 - float(mask.mean()),
    }
