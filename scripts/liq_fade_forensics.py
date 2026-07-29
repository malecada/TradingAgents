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

Addendum (reviewer-requested, appended without re-running F1-F7):
  F8  - placebo distribution sanity + planted-uplift kill-test (§47 P5 pattern)
  F9  - event-day realized-vol percentile (§47-style regime-proxy check)
  F10 - per-symbol SR table, top-15 by event count (§47 P6 pattern)

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
from tradingagents.xsect.portfolio import rank_placebo_pvalue  # noqa: E402

OUT = PROJECT_ROOT / "data" / "rebuild" / "liq_fade" / "forensics.json"

BEST_THR, BEST_H = 3.5, 48
N_PLACEBO_ADDENDUM = 150   # ad-hoc sanity draws; registered grid used 500
UPLIFT_BPS = 0.0050        # 50bp planted kill-test uplift


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

    # ── F8: placebo distribution sanity + planted-uplift kill-test ──────────
    # F8a — re-derive the placebo SR distribution ad-hoc (independent draws,
    # fresh RNG stream, N_PLACEBO_ADDENDUM << the registered 500) and report
    # its shape, confirming it is non-degenerate and that real_sr sits far
    # in its tail.
    mask_active = mask_full.loc[row_sel][active_cols]
    rng_a = np.random.default_rng(4001)
    shift_srs = []
    for _ in range(N_PLACEBO_ADDENDUM):
        trig_p = lfd._shift_triggers(trig_active, rng_a)
        Wp = event_weights_hourly(trig_p, BEST_H, w_per=lfd.W_PER, cap=lfd.CAP)
        netp = run_hourly_portfolio(Wp, R_active, cost_bps=lfd.COST_BPS, rf_annual=lfd.RF_ANNUAL)
        shift_srs.append(sharpe_daily(netp))
    rng_b = np.random.default_rng(4002)
    rand_srs = []
    for _ in range(N_PLACEBO_ADDENDUM):
        trig_p = lfd._redraw_random_triggers(trig_active, mask_active, rng_b)
        Wp = event_weights_hourly(trig_p, BEST_H, w_per=lfd.W_PER, cap=lfd.CAP)
        netp = run_hourly_portfolio(Wp, R_active, cost_bps=lfd.COST_BPS, rf_annual=lfd.RF_ANNUAL)
        rand_srs.append(sharpe_daily(netp))
    shift_arr, rand_arr = np.array(shift_srs), np.array(rand_srs)
    p_shift_a = rank_placebo_pvalue(real_sr, shift_srs)
    p_rand_a = rank_placebo_pvalue(real_sr, rand_srs)

    def _dist_stats(a: np.ndarray) -> dict:
        return {"mean": float(a.mean()), "sd": float(a.std(ddof=1)),
                "q05": float(np.quantile(a, 0.05)), "q25": float(np.quantile(a, 0.25)),
                "q50": float(np.quantile(a, 0.50)), "q75": float(np.quantile(a, 0.75)),
                "q95": float(np.quantile(a, 0.95)), "q99": float(np.quantile(a, 0.99)),
                "max": float(a.max())}

    f8a = {"n_draws_per_family": N_PLACEBO_ADDENDUM, "real_sr": real_sr,
           "shift_family": _dist_stats(shift_arr), "rand_family": _dist_stats(rand_arr),
           "p_shift": p_shift_a, "p_rand": p_rand_a,
           "shift_sd_nonzero": bool(shift_arr.std(ddof=1) > 1e-6),
           "rand_sd_nonzero": bool(rand_arr.std(ddof=1) > 1e-6)}
    print(f"[F8a placebo sanity] shift: mean={f8a['shift_family']['mean']:.3f} "
          f"sd={f8a['shift_family']['sd']:.3f} max={f8a['shift_family']['max']:.3f} "
          f"p={p_shift_a:.4f} | rand: mean={f8a['rand_family']['mean']:.3f} "
          f"sd={f8a['rand_family']['sd']:.3f} max={f8a['rand_family']['max']:.3f} "
          f"p={p_rand_a:.4f} | real={real_sr:.3f}")

    # F8b — positive control: plant a +50bp uplift at the REAL trigger's own
    # entry bar (t+1, the bar the position first earns), rerun the real
    # config against the boosted returns, then rebuild a placebo distribution
    # (shift family, fresh draws) against the SAME boosted returns using
    # placebo-generated (misaligned) trigger sets. If the mechanism tracks
    # genuine timing, real_sr should jump and p should stay low (placebo sets
    # mostly miss the bump).
    T = trig_active.to_numpy()
    rows, cols = np.where(T)
    Rb = R_active.to_numpy().copy()
    valid = rows + 1 < Rb.shape[0]
    np.add.at(Rb, (rows[valid] + 1, cols[valid]), UPLIFT_BPS)
    R_boost = pd.DataFrame(Rb, index=R_active.index, columns=R_active.columns)
    net_boost = run_hourly_portfolio(W_real, R_boost, cost_bps=lfd.COST_BPS, rf_annual=lfd.RF_ANNUAL)
    real_boost_sr = sharpe_daily(net_boost)
    rng_c = np.random.default_rng(4003)
    boost_placebo_srs = []
    for _ in range(N_PLACEBO_ADDENDUM):
        trig_p = lfd._shift_triggers(trig_active, rng_c)
        Wp = event_weights_hourly(trig_p, BEST_H, w_per=lfd.W_PER, cap=lfd.CAP)
        netp = run_hourly_portfolio(Wp, R_boost, cost_bps=lfd.COST_BPS, rf_annual=lfd.RF_ANNUAL)
        boost_placebo_srs.append(sharpe_daily(netp))
    p_boost = rank_placebo_pvalue(real_boost_sr, boost_placebo_srs)
    f8b_positive = {"uplift_bps": UPLIFT_BPS * 1e4, "real_sr_baseline": real_sr,
                    "real_sr_boosted": real_boost_sr, "placebo_p_boosted": p_boost,
                    "placebo_dist_mean": float(np.mean(boost_placebo_srs))}
    print(f"[F8b kill-test +] real baseline={real_sr:.3f} -> boosted={real_boost_sr:.3f} "
          f"(placebo mean={f8b_positive['placebo_dist_mean']:.3f}) p_boosted={p_boost:.4f}")

    # F8c — negative control ("bookkeeping, not timing"). The uplift stays at
    # the REAL trigger locations (same R_boost as F8b -- the bump is real and
    # present in the data). What's swapped is which trigger set is asked to
    # detect it: a SCRAMBLED (one fixed circular-shift draw of the real
    # triggers -- same event count/clustering structure, wrong calendar
    # alignment) set is evaluated against R_boost, benchmarked against a
    # placebo cloud built by further shifting that SAME scrambled set. A
    # trigger set that is mistimed relative to the genuine boost should look
    # statistically ordinary against further mistimed draws -- i.e. merely
    # having *some* alpha present in the return series, with the wrong
    # candidate asked to find it, should NOT manufacture significance. This
    # is the direct converse of F8b (there, the alpha and the candidate were
    # aligned; here they are deliberately misaligned).
    trig_scrambled = lfd._shift_triggers(trig_active, np.random.default_rng(9999))
    W_scrambled = event_weights_hourly(trig_scrambled, BEST_H, w_per=lfd.W_PER, cap=lfd.CAP)
    net_scrambled_vs_boost = run_hourly_portfolio(W_scrambled, R_boost,
                                                  cost_bps=lfd.COST_BPS, rf_annual=lfd.RF_ANNUAL)
    scrambled_vs_boost_sr = sharpe_daily(net_scrambled_vs_boost)
    rng_d = np.random.default_rng(4004)
    control_placebo_srs = []
    for _ in range(N_PLACEBO_ADDENDUM):
        trig_p = lfd._shift_triggers(trig_scrambled, rng_d)   # further-shift the mistimed set
        Wp = event_weights_hourly(trig_p, BEST_H, w_per=lfd.W_PER, cap=lfd.CAP)
        netp = run_hourly_portfolio(Wp, R_boost, cost_bps=lfd.COST_BPS, rf_annual=lfd.RF_ANNUAL)
        control_placebo_srs.append(sharpe_daily(netp))
    p_control = rank_placebo_pvalue(scrambled_vs_boost_sr, control_placebo_srs)
    f8c_control = {"uplift_bps": UPLIFT_BPS * 1e4,
                   "scrambled_sr_vs_realboost": scrambled_vs_boost_sr,
                   "real_sr_boosted_reference": real_boost_sr,
                   "placebo_p_control": p_control,
                   "placebo_dist_mean": float(np.mean(control_placebo_srs)),
                   "placebo_dist_sd": float(np.std(control_placebo_srs, ddof=1)),
                   "p_toward_uniform": bool(p_control > 0.20)}
    print(f"[F8c kill-test control] mistimed candidate vs real boost="
          f"{scrambled_vs_boost_sr:.3f} (aligned reference from F8b={real_boost_sr:.3f}) "
          f"p_control={p_control:.4f} (>0.20 expected -- mistimed candidate should NOT "
          f"look significant even though the boost is genuinely present in the data)")

    f8 = {"f8a_distribution_sanity": f8a, "f8b_positive_control": f8b_positive,
          "f8c_negative_control": f8c_control}

    # ── F9: event-day realized-vol percentile (regime-proxy check) ──────────
    daily_vol = R_active.groupby(R_active.index.tz_convert("UTC").normalize()).std()
    background = daily_vol.to_numpy().flatten()
    background = background[~np.isnan(background)]
    background_sorted = np.sort(background)
    event_days = trig_active.index[rows].normalize()
    event_syms = [active_cols[c] for c in cols]
    pctiles = []
    for d, s in zip(event_days, event_syms):
        v = daily_vol.at[d, s] if d in daily_vol.index else np.nan
        if pd.isna(v):
            continue
        rank = np.searchsorted(background_sorted, v, side="left")
        pctiles.append(rank / len(background_sorted))
    pctiles = np.array(pctiles)
    f9 = {"n_events_scored": int(len(pctiles)), "n_events_total": n_events,
          "median_percentile": float(np.median(pctiles)) if len(pctiles) else None,
          "mean_percentile": float(np.mean(pctiles)) if len(pctiles) else None,
          "q25_percentile": float(np.quantile(pctiles, 0.25)) if len(pctiles) else None,
          "q75_percentile": float(np.quantile(pctiles, 0.75)) if len(pctiles) else None,
          "is_regime_proxy": bool(len(pctiles) and abs(np.median(pctiles) - 0.5) > 0.15)}
    print(f"[F9 vol percentile] median={f9['median_percentile']:.3f} "
          f"mean={f9['mean_percentile']:.3f} n_scored={f9['n_events_scored']}/{n_events}")

    # ── F10: per-symbol SR table, top-15 by event count (§47 P6 pattern) ────
    # Costs, no rf (isolates price/cost effect per symbol from the constant
    # full-capital rf drag, matching liq_mr_t1's P6 convention).
    n_events_by_symbol = trig_active.sum(axis=0)
    top15_syms = n_events_by_symbol.sort_values(ascending=False).head(15).index.tolist()
    per_symbol_sr = []
    for s in top15_syms:
        Ws = W_real[[s]]
        Rs_sym = R_active[[s]]
        net_s = run_hourly_portfolio(Ws, Rs_sym, cost_bps=lfd.COST_BPS, rf_annual=0.0)
        per_symbol_sr.append({"symbol": s, "n_events": int(n_events_by_symbol[s]),
                              "sr_costs_no_rf": sharpe_daily(net_s),
                              "gross_pnl_share": float(shares.get(s, 0.0))})
    n_positive = sum(1 for r in per_symbol_sr if r["sr_costs_no_rf"] > 0)
    f10 = {"top15_by_event_count": per_symbol_sr, "n_positive_of_15": n_positive}
    print(f"[F10 per-symbol SR] {n_positive}/15 top-event-count symbols SR>0; "
          f"top3: {[(r['symbol'], round(r['sr_costs_no_rf'], 2)) for r in per_symbol_sr[:3]]}")

    payload = {"generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
               "best_config": {"thr": BEST_THR, "H": BEST_H},
               "recomputed_net_sr": real_sr, "n_events": n_events,
               "n_symbols_active": len(active_cols),
               "f1_inversion": f1, "f2_concentration": f2, "f3_yearly_sr": f3,
               "f4_events_per_year": f4, "f5_dsr_sensitivity": f5,
               "f6_cost_sensitivity": f6, "f7_p2_reconciliation": f7,
               "f8_placebo_kill_test": f8, "f9_vol_percentile": f9,
               "f10_per_symbol_sr": f10}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
