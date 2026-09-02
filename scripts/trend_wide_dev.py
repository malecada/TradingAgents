"""trend_wide_t1 dev grid: 6 pre-registered configs vs per-N EW B&H benchmark.

Ledger: trend_wide_t1. Gates: data/rebuild/gates.json["trend_wide_t1"].
Mechanics per docs/superpowers/specs/2026-07-28-trend-wide-design.md.
"""
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
from tradingagents.xsect.portfolio import (  # noqa: E402
    maxdd, paired_bootstrap, rank_placebo_pvalue, sr,
)
from tradingagents.xsect.trend import (  # noqa: E402
    build_matrices, circular_shift_weights, ew_benchmark_weights,
    monthly_refresh_dates, run_daily_portfolio, shared_shift_weights,
    trend_weights,
)
from tradingagents.xsect.universe import eligibility, load_klines  # noqa: E402

DEV = ("2021-01-01", "2025-03-31")
GRID = list(product([10, 20], [0.20, 0.30, 0.40]))  # N, vol_target — frozen, 6 configs
GATE = {"net_sr_min": 1.0, "delta_sr_vs_benchmark_min": 0.0, "p_pos_min": 0.90,
        "placebo_p_max": 0.05, "dsr_min": 0.9}
OUT = Path("data/rebuild/trend_wide")
N_PLACEBO = 500
COST_BPS = 10.0
MIN_HISTORY_BARS = 90
KLINE_DIR = Path("data/xsect/klines")


def _unique_config_hashes(ledger_path: Path = DEFAULT_LEDGER) -> int:
    """House convention for DSR n_trials (scripts/xs_mom_dev.py)."""
    seen = set()
    with open(ledger_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
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


def _blocked(reason: str, diagnostics: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = _sanitize({"blocked": True, "reason": reason, "diagnostics": diagnostics})
    with open(OUT / "dev_results.json", "w") as f:
        json.dump(payload, f, indent=1, allow_nan=False)
    print(f"\nBLOCKED: {reason}")
    print(json.dumps(_sanitize(diagnostics), indent=1))


def main() -> None:
    t_start = time.time()
    klines = load_klines(KLINE_DIR)
    refresh = monthly_refresh_dates(*DEV)
    hi = pd.Timestamp(DEV[1], tz="UTC")

    # ── Universe per refresh date, per N (eligibility + >=90-bar history) ──
    t0 = time.time()
    members = {N: {} for N, _ in set((n, v) for n, v in GRID)}
    for d in refresh:
        base = eligibility(klines, d, top_n=100)
        aged = [s for s in base
                if len(klines[s].loc[:d]) >= MIN_HISTORY_BARS]
        for N in (10, 20):
            ranked = aged[:N]  # eligibility already volume-ranked
            members[N][d] = ranked
    counts = {N: [len(v) for v in members[N].values()] for N in (10, 20)}
    print(f"[universe] refreshes={len(refresh)} "
          f"N=10 min/med={min(counts[10])}/{int(np.median(counts[10]))} "
          f"N=20 min/med={min(counts[20])}/{int(np.median(counts[20]))} "
          f"({time.time() - t0:.1f}s)")
    if min(counts[20]) < 20:
        short = [(str(d.date()), len(members[20][d])) for d in refresh
                 if len(members[20][d]) < 20]
        # spec: use all eligible, log count — proceed, do not block
        print(f"[universe] WARNING: {len(short)} refreshes with <20 members: {short[:6]}")

    # ── Matrices over the union of all symbols ever selected ──
    t0 = time.time()
    union = sorted(set().union(*[set(v) for N in (10, 20) for v in members[N].values()]))
    # Lead-0 fix (2026-09-02): R (log) feeds SIGMA/VOTES; PnL consumes R_pnl
    # (simple). Registered July numbers fed R (log) — audit 2026-09-02 section 2.
    all_days, R, VOTES, SIGMA, R_pnl = build_matrices(klines, union, with_simple=True)
    print(f"[matrices] union_symbols={len(union)} days={len(all_days)} "
          f"({time.time() - t0:.1f}s)")

    # ── Benchmarks per N ──
    bench = {}
    for N in (10, 20):
        Wb = ew_benchmark_weights(all_days, R, members[N], n_slots=N)
        s = run_daily_portfolio(Wb, R_pnl, COST_BPS).loc[:hi]
        s = s.loc[s.index > refresh[0]]
        bench[N] = s
        print(f"[benchmark N={N}] SR={sr(s):+.4f} maxdd={maxdd(s):.4f} n_days={len(s)}")

    # ── Sanity gates (frozen) ──
    problems = []
    for N in (10, 20):
        nd = len(bench[N])
        if not (1450 <= nd <= 1560):
            problems.append(f"benchmark N={N} n_days={nd} outside 1505+/-55")
        if not (-1.5 < sr(bench[N]) < 2.5):
            problems.append(f"benchmark N={N} SR={sr(bench[N]):.4f} outside (-1.5, 2.5)")
    if problems:
        _blocked("; ".join(problems), {f"bench_{N}": sr(bench[N]) for N in (10, 20)})
        return

    # ── Grid: 6 configs; placebos shared per N via identical seeds ──
    results = []
    series_by_cfg = {}
    for N, vt in GRID:
        t_cfg = time.time()
        W = trend_weights(all_days, R, VOTES, SIGMA, members[N], n_slots=N, vol_target=vt)
        real = run_daily_portfolio(W, R_pnl, COST_BPS).loc[:hi]
        real = real.loc[real.index > refresh[0]]
        real_sr = sr(real)
        pb = paired_bootstrap(real, bench[N])
        def _placebo_p(shift_fn):
            srs_ = []
            for p in range(N_PLACEBO):
                rng = np.random.default_rng(seed=p)
                ps = run_daily_portfolio(shift_fn(W, rng), R_pnl, COST_BPS).loc[:hi]
                ps = ps.loc[ps.index > refresh[0]]
                srs_.append(sr(ps))
            return rank_placebo_pvalue(real_sr, srs_)

        placebo_p_indep = _placebo_p(circular_shift_weights)
        placebo_p_shared = _placebo_p(shared_shift_weights)
        placebo_p = max(placebo_p_indep, placebo_p_shared)  # gate on the WORSE family
        cfg = {"N": N, "vol_target": vt, "cost_bps": COST_BPS,
               "min_history_bars": MIN_HISTORY_BARS, "refresh": "monthly_first_monday"}
        metrics = {"net_sr": real_sr, "maxdd": maxdd(real),
                   "total_logret": float(real.sum()),
                   "bench_sr": sr(bench[N]), "delta_sr": pb["delta_sr"],
                   "p_pos": pb["p_pos"], "placebo_p": placebo_p,
                   "placebo_p_indep": placebo_p_indep,
                   "placebo_p_shared": placebo_p_shared, "n_days": len(real)}
        log_trial("trend_wide_t1", cfg, DEV, metrics)
        series_by_cfg[(N, vt)] = real
        results.append({"config": cfg, "metrics": metrics})
        print(f"N={N} vt={vt}: SR={real_sr:+.3f} dSR={pb['delta_sr']:+.3f} "
              f"p_pos={pb['p_pos']:.3f} placebo_p={placebo_p:.3f} "
              f"({time.time() - t_cfg:.1f}s)")

    # ── DSR after all 6 logged (house recipe) ──
    n_trials = _unique_config_hashes()
    for r in results:
        cand = series_by_cfg[(r["config"]["N"], r["config"]["vol_target"])].values
        var_sr = variance_of_sr(cand)
        se_sr = float(np.sqrt(var_sr))
        sr_perbar = float(cand.mean() / cand.std(ddof=1)) if cand.std(ddof=1) > 0 else 0.0
        dsr = deflated_sharpe_ratio(sr_perbar, expected_max_sharpe(n_trials, var_sr), se_sr)
        r["metrics"]["dsr"] = dsr
        r["metrics"]["n_trials_at_eval"] = n_trials
        m = r["metrics"]
        r["gate_pass"] = bool(
            m["net_sr"] >= GATE["net_sr_min"]
            and m["delta_sr"] > GATE["delta_sr_vs_benchmark_min"]
            and m["p_pos"] >= GATE["p_pos_min"]
            and m["placebo_p"] <= GATE["placebo_p_max"]
            and m["dsr"] >= GATE["dsr_min"]
        )

    passing = [r for r in results if r["gate_pass"]]
    selected = (max(passing, key=lambda r: (r["metrics"]["dsr"], -r["metrics"]["placebo_p"]))
                if passing else None)

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"benchmarks": {str(N): {"sr": sr(bench[N]), "maxdd": maxdd(bench[N]),
                                        "n_days": len(bench[N])} for N in (10, 20)},
               "results": results, "selected": selected,
               "n_trials_at_eval": n_trials,
               "total_runtime_sec": time.time() - t_start}
    with open(OUT / "dev_results.json", "w") as f:
        json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)

    print(f"\nselected: {json.dumps(selected['config']) if selected else 'NONE'}")
    print(f"total runtime: {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
