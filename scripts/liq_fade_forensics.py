"""liq_fade_i1 forensic verification (Task 10, house §47 style). READ-ONLY:
reuses the registered engine/loaders from scripts/liq_fade_dev.py without
modifying it. Computes, for the best config (thr=3.5, H=48) only:

  F1 - inversion test (short instead of long-fade)
  F2 - per-symbol P&L decomposition (top-10, HHI, top-5 share)
  F3 - yearly net SR stability (2021..2025Q1)
  F4 - event-count-per-year honesty table
  F5 - DSR sensitivity: n_trials=6 (this experiment alone) vs 100 (registered)
  F6 - cost sensitivity: +30bps row (20bps already in dev_results.json)
  F7 - P2-vs-grid order-of-magnitude reconciliation

Writes data/rebuild/liq_fade/forensics.json (machine-readable); forensics.md
(prose, house style) is hand-written from this output. Not part of the
registered gate -- diagnostic only, run AFTER the dev grid verdict landed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import liq_fade_dev as lfd  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect.liq_fade import (  # noqa: E402
    cascade_triggers, event_weights_hourly, run_hourly_portfolio, sharpe_daily,
)

OUT = PROJECT_ROOT / "data" / "rebuild" / "liq_fade" / "forensics.json"

BEST_THR, BEST_H = 3.5, 48


def _sanitize(obj):
    if isinstance(obj, float):
        return None if (np.isnan(obj) or np.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


def main() -> None:
    lfd._assert_data_complete()
    symbols = lfd.load_symbols(smoke=False)
    universe = json.loads(lfd.UNIVERSE_FILE.read_text())
    close, qvol = lfd.load_hourly_panel(symbols)
    R = close.pct_change()
    mask_full = lfd.membership_mask_hourly(universe, close.columns.tolist(), close.index)

    dev_lo = pd.Timestamp(lfd.DEV[0], tz="UTC")
    dev_hi = pd.Timestamp(lfd.DEV[1], tz="UTC") + pd.Timedelta(hours=23)
    row_sel = (close.index >= dev_lo) & (close.index <= dev_hi)

    trig_raw = cascade_triggers(close, qvol, thr=BEST_THR)
    trig_masked = trig_raw & mask_full
    trig_dev = trig_masked.loc[row_sel]
    R_dev = R.loc[row_sel]

    active_cols = trig_dev.columns[trig_dev.to_numpy().any(axis=0)].tolist()
    trig_active = trig_dev[active_cols]
    R_active = R_dev[active_cols]

    n_events = int(trig_active.to_numpy().sum())
    print(f"[setup] best config thr={BEST_THR} H={BEST_H}: {n_events} events, "
          f"{len(active_cols)} active symbols")

    W_real = event_weights_hourly(trig_active, BEST_H, w_per=lfd.W_PER, cap=lfd.CAP)
    net_real = run_hourly_portfolio(W_real, R_active, cost_bps=lfd.COST_BPS,
                                    rf_annual=lfd.RF_ANNUAL)
    real_sr = sharpe_daily(net_real)
    print(f"[F0 sanity] recomputed net_sr={real_sr:.4f} (dev_results.json: 1.3047)")

    # ── F1: inversion test (short-fade instead of long-fade) ────────────────
    W_inv = -W_real
    net_inv = run_hourly_portfolio(W_inv, R_active, cost_bps=lfd.COST_BPS,
                                   rf_annual=lfd.RF_ANNUAL)
    inv_sr = sharpe_daily(net_inv)
    f1 = {"long_fade_sr": real_sr, "short_inverted_sr": inv_sr,
          "long_beats_short": bool(real_sr > inv_sr)}
    print(f"[F1 inversion] long={real_sr:.4f} short={inv_sr:.4f} "
          f"long_beats_short={f1['long_beats_short']}")

    # ── F2: per-symbol P&L decomposition (gross, pre-cost) ──────────────────
    gross_by_symbol = (W_real * R_active.fillna(0.0)).sum(axis=0)
    total_gross = float(gross_by_symbol.sum())
    ranked = gross_by_symbol.sort_values(ascending=False)
    top10 = [{"symbol": s, "gross_pnl": float(v),
              "share_of_total": float(v / total_gross) if total_gross else None}
             for s, v in ranked.head(10).items()]
    shares = (gross_by_symbol / total_gross) if total_gross else gross_by_symbol * 0.0
    hhi = float((shares ** 2).sum())
    top5_share = float(shares.sort_values(ascending=False).head(5).sum())
    n_active_symbols = int((gross_by_symbol != 0).sum())
    f2 = {"total_gross_pnl": total_gross, "n_symbols_with_nonzero_pnl": n_active_symbols,
          "top10": top10, "hhi": hhi, "top5_share": top5_share}
    print(f"[F2 concentration] total_gross={total_gross:.4f} HHI={hhi:.4f} "
          f"top5_share={top5_share:.4f} n_symbols_active={n_active_symbols}")

    # ── F3: yearly net SR stability ──────────────────────────────────────────
    f3 = {}
    for yr, sl in net_real.groupby(net_real.index.year):
        f3[str(yr)] = {"sr": sharpe_daily(sl), "n_days": int(len(sl)),
                       "mean_daily_net": float(sl.mean())}
    print(f"[F3 yearly SR] {[(k, round(v['sr'], 3)) for k, v in f3.items()]}")

    # ── F4: event-count-per-year honesty ─────────────────────────────────────
    ev_by_day = trig_active.to_numpy().sum(axis=1)
    ev_series = pd.Series(ev_by_day, index=trig_active.index)
    f4 = {}
    for yr, sl in ev_series.groupby(ev_series.index.year):
        f4[str(yr)] = int(sl.sum())
    f4["total"] = int(sum(f4.values()))
    n_years = len(f4) - 1
    f4["n_years_spanned"] = n_years
    f4["min_events_per_year"] = min(v for k, v in f4.items()
                                     if k not in ("total", "n_years_spanned"))
    print(f"[F4 events/year] {f4}")

    # ── F5: DSR sensitivity (n_trials=6 vs 100) ──────────────────────────────
    cand = net_real.to_numpy()
    var_sr = variance_of_sr(cand)
    se_sr = float(np.sqrt(var_sr))
    sr_perbar = float(cand.mean() / cand.std(ddof=1))
    f5 = {"sr_perbar": sr_perbar, "se_sr": se_sr, "var_sr": var_sr}
    for n_trials in (6, 100):
        exp_max = expected_max_sharpe(n_trials, var_sr)
        dsr = deflated_sharpe_ratio(sr_perbar, exp_max, se_sr)
        f5[f"n_trials_{n_trials}"] = {"expected_max_sharpe_null": exp_max, "dsr": dsr,
                                       "dsr_pass": bool(dsr >= 0.9)}
    print(f"[F5 DSR] n_trials=6 -> dsr={f5['n_trials_6']['dsr']:.4f}  "
          f"n_trials=100 -> dsr={f5['n_trials_100']['dsr']:.4f}")

    # ── F6: cost sensitivity (+30bps row) ────────────────────────────────────
    net_30 = run_hourly_portfolio(W_real, R_active, cost_bps=30.0, rf_annual=lfd.RF_ANNUAL)
    sr_30 = sharpe_daily(net_30)
    net_20 = run_hourly_portfolio(W_real, R_active, cost_bps=20.0, rf_annual=lfd.RF_ANNUAL)
    sr_20 = sharpe_daily(net_20)
    f6 = {"sr_cost_10bps_registered": real_sr, "sr_stress_20bps_recomputed": sr_20,
          "sr_stress_30bps": sr_30}
    print(f"[F6 cost] 10bps={real_sr:.4f} 20bps={sr_20:.4f} 30bps={sr_30:.4f}")

    # ── F7: P2-vs-grid order-of-magnitude reconciliation ─────────────────────
    p2_mean_fwd_ret = 0.027718009760558316  # probes.json thr=3.5 H=48
    naive_undiscounted = n_events * p2_mean_fwd_ret * lfd.W_PER
    realized_cum_gross = float((1.0 + (W_real * R_active.fillna(0.0)).sum(axis=1)).prod() - 1.0)
    realized_cum_net = float((1.0 + net_real).prod() - 1.0)
    years_spanned = (net_real.index[-1] - net_real.index[0]).days / 365.25
    f7 = {"p2_mean_fwd_ret_per_event": p2_mean_fwd_ret, "n_events": n_events,
          "w_per": lfd.W_PER,
          "naive_undiscounted_sum_event_contributions": naive_undiscounted,
          "realized_cum_gross_return": realized_cum_gross,
          "realized_cum_net_return": realized_cum_net,
          "years_spanned": years_spanned}
    print(f"[F7 P2 reconcile] naive_sum={naive_undiscounted:.3f} "
          f"realized_cum_gross={realized_cum_gross:.3f} "
          f"realized_cum_net={realized_cum_net:.3f} over {years_spanned:.2f}y")

    payload = {"generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
               "best_config": {"thr": BEST_THR, "H": BEST_H},
               "recomputed_net_sr": real_sr, "n_events": n_events,
               "n_symbols_active": len(active_cols),
               "f1_inversion": f1, "f2_concentration": f2, "f3_yearly_sr": f3,
               "f4_events_per_year": f4, "f5_dsr_sensitivity": f5,
               "f6_cost_sensitivity": f6, "f7_p2_reconciliation": f7}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
