# scripts/carry_xs_dev.py
"""carry_xs_t1 dev grid: 6 pre-registered configs (L x leg_frac), no benchmark
(dollar-neutral; rf embedded). Ledger: carry_xs_t1. Gates:
data/rebuild/gates.json["carry_xs_t1"]. Mechanics per
docs/superpowers/specs/2026-07-28-carry-xs-design.md."""
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
from tradingagents.xsect.carry_xs import (  # noqa: E402
    RF_DAILY, build_funding_matrix, carry_signal, carry_weights,
    run_ls_portfolio,
)
from tradingagents.xsect.portfolio import maxdd, rank_placebo_pvalue, sr  # noqa: E402
from tradingagents.xsect.trend import (  # noqa: E402
    circular_shift_weights, monthly_refresh_dates, shared_shift_weights,
)
from tradingagents.xsect.universe import eligibility, load_klines  # noqa: E402

DEV = ("2021-01-01", "2025-03-31")
GRID = list(product([1, 7, 30], [0.10, 0.20]))  # L, leg_frac — frozen, 6 configs
GATE = {"net_sr_min": 1.0, "placebo_p_max": 0.05, "dsr_min": 0.9}
OUT = Path("data/rebuild/carry_xs")
N_PLACEBO = 500
COST_BPS = 10.0
TOP_N = 50
KLINE_DIR = Path("data/xsect/klines")
FUND_DIR = Path("data/xsect/funding")


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


def main() -> None:
    t_start = time.time()
    klines = load_klines(KLINE_DIR)
    refresh = monthly_refresh_dates(*DEV)
    hi = pd.Timestamp(DEV[1], tz="UTC")

    members = {}
    for d in refresh:
        members[d] = eligibility(klines, d, top_n=TOP_N)
    counts = [len(v) for v in members.values()]
    print(f"[universe] refreshes={len(refresh)} min/med members="
          f"{min(counts)}/{int(np.median(counts))}")

    union = sorted(set().union(*[set(v) for v in members.values()]))
    all_days = pd.DatetimeIndex(sorted(set().union(
        *[klines[s].index for s in union])))
    R = pd.DataFrame(index=all_days, columns=union, dtype=float)
    for s in union:
        R[s] = np.log(klines[s]["close"]).diff().reindex(all_days)
    funding = {s: pd.read_parquet(FUND_DIR / f"{s}.parquet")
               for s in union if (FUND_DIR / f"{s}.parquet").exists()}
    F = build_funding_matrix(funding, all_days, union)
    print(f"[matrices] union={len(union)} days={len(all_days)} "
          f"funding_files={len(funding)} ({time.time() - t_start:.1f}s)")

    SIG30 = R.rolling(30, min_periods=30).std()  # config-independent, hoisted

    results, series_by_cfg = [], {}
    for L, leg_frac in GRID:
        t_cfg = time.time()
        S = carry_signal(F, L)
        W = carry_weights(all_days, S, F, members, leg_frac)
        real = run_ls_portfolio(W, R, F, COST_BPS, RF_DAILY).loc[:hi]
        real = real.loc[real.index > refresh[0]]
        real_sr = sr(real)

        # sanity (frozen): dollar-neutrality + gross exposure on active days
        act = W.abs().sum(axis=1)
        active = act[act > 0]
        assert np.allclose(W.sum(axis=1), 0.0, atol=1e-9), "net exposure != 0"
        assert np.allclose(active, 1.0, atol=1e-9), "gross != 1 on active days"

        def _placebo_p(shift_fn):
            srs_ = []
            for p in range(N_PLACEBO):
                rng = np.random.default_rng(seed=p)
                ps = run_ls_portfolio(shift_fn(W, rng), R, F,
                                      COST_BPS, RF_DAILY).loc[:hi]
                srs_.append(sr(ps.loc[ps.index > refresh[0]]))
            return rank_placebo_pvalue(real_sr, srs_)

        p_indep = _placebo_p(circular_shift_weights)
        p_shared = _placebo_p(shared_shift_weights)
        placebo_p = max(p_indep, p_shared)

        # non-gating vol-selection diagnostic (section-43 check)
        active_days = W.index[act > 0]
        rcs = [pd.Series(S.loc[t]).corr(pd.Series(SIG30.loc[t]), method="spearman")
               for t in active_days[::21]]
        vol_rank_corr = float(np.nanmean(rcs))

        # per-leg mean 30d realized vol (section-43 vol-selection check), same
        # sampled dates and SIG30 frame as vol_rank_corr_diag above
        short_vols, long_vols = [], []
        for t in active_days[::21]:
            w_row = W.loc[t]
            sv = SIG30.loc[t, w_row[w_row < 0].index].mean()
            lv = SIG30.loc[t, w_row[w_row > 0].index].mean()
            short_vols.append(sv); long_vols.append(lv)
        mean_vol_short_leg = float(np.nanmean(short_vols))
        mean_vol_long_leg = float(np.nanmean(long_vols))

        cfg = {"L": L, "leg_frac": leg_frac, "top_n": TOP_N, "cost_bps": COST_BPS,
               "rf_daily": RF_DAILY, "refresh": "monthly_first_monday"}
        metrics = {"net_sr": real_sr, "maxdd": maxdd(real),
                   "total_logret": float(real.sum()),
                   "placebo_p": placebo_p, "placebo_p_indep": p_indep,
                   "placebo_p_shared": p_shared, "n_days": len(real),
                   "n_active_days": int((act.loc[real.index] > 0).sum()),
                   "mean_gross_turnover": float(W.diff().abs().sum(axis=1).mean()),
                   "vol_rank_corr_diag": vol_rank_corr,
                   "mean_vol_short_leg_diag": mean_vol_short_leg,
                   "mean_vol_long_leg_diag": mean_vol_long_leg}
        log_trial("carry_xs_t1", cfg, DEV, metrics)
        series_by_cfg[(L, leg_frac)] = real
        results.append({"config": cfg, "metrics": metrics})
        print(f"L={L} leg={leg_frac}: SR={real_sr:+.3f} placebo_p={placebo_p:.3f} "
              f"turnover={metrics['mean_gross_turnover']:.3f} "
              f"volcorr={vol_rank_corr:+.2f} ({time.time() - t_cfg:.1f}s)")

    n_trials = _unique_config_hashes()
    for r in results:
        cand = series_by_cfg[(r["config"]["L"], r["config"]["leg_frac"])].values
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
