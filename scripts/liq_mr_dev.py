# scripts/liq_mr_dev.py
"""liq_mr_t1 dev grid: 6 pre-registered configs (thr x H), fixed 8-major
universe. Ledger: liq_mr_t1. Gates: data/rebuild/gates.json["liq_mr_t1"].
Mechanics per docs/superpowers/specs/2026-07-28-liq-mr-design.md.

Dev calendar starts at DEV[0]: liquidation data is nonzero only from
2020-12-23, so there is no usable pre-window history — the 90d/60 z warmup
runs inside the dev window (signals live ~2021-03), identically across all
six configs (registered convention)."""
import json
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.rebuild.ledger import DEFAULT_LEDGER, log_trial  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect.liq_mr import (  # noqa: E402
    RF_DAILY, event_weights, liq_zscore, run_liq_portfolio,
)
from tradingagents.xsect.portfolio import maxdd, rank_placebo_pvalue, sr  # noqa: E402
from tradingagents.xsect.trend import (  # noqa: E402
    circular_shift_weights, shared_shift_weights,
)

DEV = ("2021-01-01", "2025-03-31")
GRID = list(product([1.5, 2.5], [1, 3, 5]))  # thr, H — frozen, 6 configs
GATE = {"net_sr_min": 1.0, "placebo_p_max": 0.05, "dsr_min": 0.9}
OUT = Path("data/rebuild/liq_mr")
N_PLACEBO = 500
COST_BPS = 10.0
KLINE_DIR = Path("data/xsect/klines")
DERIV_DIR = Path("data/derivatives")
COINS = {  # coin slug (derivatives store) -> klines symbol; fixed 8 majors
    "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "binancecoin": "BNBUSDT",
    "solana": "SOLUSDT", "cardano": "ADAUSDT", "dogecoin": "DOGEUSDT",
    "ripple": "XRPUSDT", "tron": "TRXUSDT",
}


def _unique_config_hashes(ledger_path=DEFAULT_LEDGER) -> int:
    seen = set()
    with open(ledger_path) as f:
        for line in f:
            if line.strip():
                seen.add(json.loads(line)["config_hash"])
    return len(seen)


def _sanitize(obj):
    if isinstance(obj, float):
        return None if (np.isnan(obj) or np.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


def build_inputs():
    """(all_days, R, ZL, ZS, SIG30) on the dev calendar, columns = symbols."""
    lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")
    syms = list(COINS.values())
    closes, liq_l, liq_s, oi = {}, {}, {}, {}
    for coin, sym in COINS.items():
        k = pd.read_parquet(KLINE_DIR / f"{sym}.parquet")
        d = pd.read_parquet(DERIV_DIR / f"{coin}.parquet")
        closes[sym] = k["close"]
        liq_l[sym], liq_s[sym] = d["liq_long_usd"], d["liq_short_usd"]
        oi[sym] = d["oi_close"]
    all_days = pd.DatetimeIndex(sorted(set().union(
        *[c.index for c in closes.values()])))
    all_days = all_days[(all_days >= lo) & (all_days <= hi)]

    def mat(d):
        return pd.DataFrame({s: d[s].reindex(all_days) for s in syms},
                            index=all_days, columns=syms)

    R = mat(closes).pct_change()  # simple returns per spec (trend/carry use log)
    ZL = liq_zscore(mat(liq_l), mat(oi))
    ZS = liq_zscore(mat(liq_s), mat(oi))
    SIG30 = R.rolling(30, min_periods=30).std()
    return all_days, R, ZL, ZS, SIG30


def main() -> None:
    t_start = time.time()
    all_days, R, ZL, ZS, SIG30 = build_inputs()
    print(f"[inputs] days={len(all_days)} {all_days[0].date()}..{all_days[-1].date()} "
          f"({time.time() - t_start:.1f}s)")

    vol_pct = SIG30.rank(pct=True, axis=0)  # config-independent, hoisted
    results, series_by_cfg = [], {}
    for thr, H in GRID:
        t_cfg = time.time()
        W = event_weights(ZL, ZS, thr=thr, hold=H)
        real = run_liq_portfolio(W, R, COST_BPS, RF_DAILY)
        real_sr = sr(real)

        # sanity (frozen): weights in {-1/8, 0, +1/8}; gross <= 1
        assert set(np.round(np.unique(W.to_numpy()), 10)) <= {-0.125, 0.0, 0.125}
        assert (W.abs().sum(axis=1) <= 1.0 + 1e-9).all()

        def _placebo_p(shift_fn):
            srs_ = []
            for p in range(N_PLACEBO):
                rng = np.random.default_rng(seed=p)
                srs_.append(sr(run_liq_portfolio(shift_fn(W, rng), R,
                                                 COST_BPS, RF_DAILY)))
            return rank_placebo_pvalue(real_sr, srs_)

        p_indep = _placebo_p(circular_shift_weights)
        p_shared = _placebo_p(shared_shift_weights)
        placebo_p = max(p_indep, p_shared)

        # ── diagnostics (non-gating, registered) ────────────────────────────
        evL = (ZL >= thr)
        evS = (ZS >= thr)
        n_ev_long = int(evL.to_numpy().sum())
        n_ev_short = int(evS.to_numpy().sum())
        # direction decomposition: same conventions, one direction disabled
        WL = event_weights(ZL, ZS.where(pd.DataFrame(False, index=ZS.index,
                                                     columns=ZS.columns)), thr=thr, hold=H)
        WS = event_weights(ZL.where(pd.DataFrame(False, index=ZL.index,
                                                 columns=ZL.columns)), ZS, thr=thr, hold=H)
        sr_long = sr(run_liq_portfolio(WL, R, COST_BPS, RF_DAILY))
        sr_short = sr(run_liq_portfolio(WS, R, COST_BPS, RF_DAILY))
        act = W.abs().sum(axis=1)
        pct_active = float((act > 0).mean())
        sr_gross_rf = sr(real + RF_DAILY)
        # event-day vol regime: mean cross-coin 30d-vol percentile on event days
        ev_any = (evL | evS).to_numpy()
        ev_vols = vol_pct.to_numpy()[ev_any]
        event_vol_pctile = float(np.nanmean(ev_vols)) if ev_any.sum() else float("nan")
        # post-event signed fade return profile (raw effect, no costs):
        # fwd_h at row t = sum of R[t+1 .. t+h]
        prof = {}
        for h in (1, 3, 5):
            fwd = R.rolling(h, min_periods=h).sum().shift(-h)
            vals = np.concatenate([fwd.to_numpy()[evL.to_numpy()],
                                   -fwd.to_numpy()[evS.to_numpy()]])
            prof[f"mean_fade_ret_{h}d"] = (float(np.nanmean(vals))
                                           if len(vals) else float("nan"))

        cfg = {"thr": thr, "H": H, "z_window": 90, "z_min": 60, "n_coins": 8,
               "cost_bps": COST_BPS, "rf_daily": RF_DAILY}
        metrics = {"net_sr": real_sr, "maxdd": maxdd(real),
                   "total_ret_sum": float(real.sum()),
                   "placebo_p": placebo_p, "placebo_p_indep": p_indep,
                   "placebo_p_shared": p_shared, "n_days": len(real),
                   "n_events_long": n_ev_long, "n_events_short": n_ev_short,
                   "sr_long_fade_diag": sr_long, "sr_short_fade_diag": sr_short,
                   "pct_days_active": pct_active,
                   "sr_gross_of_rf_diag": sr_gross_rf,
                   "event_vol_pctile_diag": event_vol_pctile,
                   "mean_gross_turnover": float(W.diff().abs().sum(axis=1).mean()),
                   **prof}
        log_trial("liq_mr_t1", cfg, DEV, metrics)
        series_by_cfg[(thr, H)] = real
        results.append({"config": cfg, "metrics": metrics})
        print(f"thr={thr} H={H}: SR={real_sr:+.3f} placebo_p={placebo_p:.3f} "
              f"ev={n_ev_long}L/{n_ev_short}S act={pct_active:.1%} "
              f"L/S SR={sr_long:+.2f}/{sr_short:+.2f} ({time.time() - t_cfg:.1f}s)")

    n_trials = _unique_config_hashes()
    for r in results:
        cand = series_by_cfg[(r["config"]["thr"], r["config"]["H"])].values
        var_sr = variance_of_sr(cand)
        se_sr = float(np.sqrt(var_sr))
        sr_perbar = float(cand.mean() / cand.std(ddof=1)) if cand.std(ddof=1) > 0 else 0.0
        dsr = deflated_sharpe_ratio(sr_perbar, expected_max_sharpe(n_trials, var_sr), se_sr)
        r["metrics"]["dsr"] = dsr
        r["metrics"]["n_trials_at_eval"] = n_trials
        m = r["metrics"]
        r["gate_pass"] = bool(m["net_sr"] >= GATE["net_sr_min"]
                              and m["placebo_p"] <= GATE["placebo_p_max"]
                              and m["dsr"] >= GATE["dsr_min"])

    passing = [r for r in results if r["gate_pass"]]
    selected = (max(passing, key=lambda r: (r["metrics"]["dsr"],
                                            -r["metrics"]["placebo_p"]))
                if passing else None)
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"results": results, "selected": selected,
               "n_trials_at_eval": n_trials,
               "total_runtime_sec": time.time() - t_start}
    with open(OUT / "dev_results.json", "w") as f:
        json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)
    print(f"\nselected: {json.dumps(selected['config']) if selected else 'NONE'}")
    print(f"total runtime: {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
