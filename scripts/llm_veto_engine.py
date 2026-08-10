"""llm_c2_veto_ovl engine — champion book reproduction + reduce-only veto.

Charter: docs/superpowers/specs/2026-08-10-llm-c2-veto-charter.md
Registered: gates.json key `llm_c2_veto_ovl` (2026-08-10, pre-result).

The champion book (ewma_20 eq_h1 top-200 + vt15_naive20_b100, O4 formula)
is reproduced verbatim from `predlab_champion_backtest.py`. The veto is a
daily multiplier m_t in {0, 0.5, 1} applied to the overlay scale; the O4
cost formula is recomputed on the vetoed scale so de-risk/re-risk
transitions are charged.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import opt  # noqa: E402
from tradingagents.predlab.pp import ANN_DAYS, TAKER_BP, ann_sr, max_drawdown  # noqa: E402

FULL = ("2021-01-01", "2026-07-01")
DEV_D = opt.DESIGN_D  # ("2021-01-01", "2025-03-31")
VETO_BUDGET_PER_YEAR = 10
VT_TARGET = 0.15


def load_book() -> dict:
    """Champion base book + O4 overlay inputs (frozen configs, no new trials)."""
    from predlab_opt_o1 import inputs

    close, park, ret, uni, fund = inputs()
    cfg = opt.OptConfig()
    sig = opt.build_signal(park, close, "ewma_20")
    raw = opt.run_ls(sig, ret, uni, fund, cfg, *FULL)
    base = raw["rets"]
    breadth = (~sig.where(uni).isna()).sum(axis=1).reindex(base.index)
    return {"base": base, "breadth": breadth}


def o4_scale(base: pd.DataFrame, breadth: pd.Series, target: float = VT_TARGET,
             cap: float = 2.0, breadth_floor: int = 100) -> pd.Series:
    """O4 overlay scale series (verbatim formula from predlab_champion_backtest)."""
    net = base["net"]
    sh = net.rolling(20).std().shift(1) * np.sqrt(ANN_DAYS)
    s = (target / sh).clip(0.0, cap).fillna(0.0)
    return s.where(breadth >= breadth_floor, 0.0)


def overlay_net(base: pd.DataFrame, scale: pd.Series) -> pd.Series:
    """O4 overlay net given an (optionally vetoed) scale series."""
    cost = TAKER_BP / 1e4 * (scale * base["turnover"]
                             + scale.diff().abs().fillna(0.0) * 2.0)
    return scale * base["net"] - cost


def apply_budget(m_raw: pd.Series, budget: int = VETO_BUDGET_PER_YEAR) -> pd.Series:
    """Enforce <=budget veto-days (m<1) per calendar year, calendar order."""
    m = m_raw.copy()
    for year in sorted(set(m.index.year)):
        idx = m.index[m.index.year == year]
        used = 0
        for t in idx:
            if m.loc[t] < 1.0:
                used += 1
                if used > budget:
                    m.loc[t] = 1.0
    return m


def oracle_m(ovl_net: pd.Series, lo: str, hi: str,
             k: int = VETO_BUDGET_PER_YEAR) -> pd.Series:
    """P0 oracle: m=0 on the k worst un-vetoed overlaid-book days per year."""
    seg = ovl_net[(ovl_net.index >= lo) & (ovl_net.index <= hi)].dropna()
    m = pd.Series(1.0, index=ovl_net.index)
    for year in sorted(set(seg.index.year)):
        yr = seg[seg.index.year == year]
        worst = yr.nsmallest(min(k, len(yr))).index
        m.loc[worst] = 0.0
    return m


def cvar5(net: pd.Series) -> float:
    x = net.dropna().to_numpy()
    q = np.quantile(x, 0.05)
    return float(x[x <= q].mean())


def seg(net: pd.Series, lo: str, hi: str) -> pd.Series:
    return net[(net.index >= lo) & (net.index <= hi)].dropna()


def book_metrics(net: pd.Series, lo: str, hi: str) -> dict:
    s = seg(net, lo, hi)
    return {"sr": ann_sr(s.to_numpy()), "maxdd": max_drawdown(s.to_numpy()),
            "cvar5": cvar5(s), "n_days": int(len(s)),
            "ret": float(np.expm1(np.log1p(s).sum()))}
